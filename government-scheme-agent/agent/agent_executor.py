from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from agent.prompts import SYSTEM_PROMPT
from models.schemas import AgentOutput, AgentTraceStep, EligibilityResult, UserProfile
from tools.calculator import score_result
from tools.eligibility_checker import check_eligibility
from tools.scheme_finder import shortlist_schemes
from tools.web_search import search_official_link
from utils.logger import summarize_observation

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / '.env')

_MAX_ITERATIONS = 12

_REACT_INSTRUCTIONS = """
You have access to these tools:

  scheme_finder       - Finds candidate government schemes for the user.
                        Input: any string (e.g. "find schemes").
  eligibility_checker - Checks if the user meets the criteria for ONE scheme.
                        Input: EXACT scheme name returned by scheme_finder.
  web_search          - Finds the official government website for a scheme.
                        Input: scheme name.

Use EXACTLY this format every time:

Thought: <your reasoning about what to do next>
Action: <one of: scheme_finder, eligibility_checker, web_search>
Action Input: <input to the tool>

After you receive an Observation, continue with another Thought/Action pair, OR end with:

Final Answer: <comprehensive answer for the user>

Important rules:
- Start by calling scheme_finder.
- Call eligibility_checker for each scheme you want to assess, one at a time.
- Call web_search for the top 2-3 eligible schemes.
- End with Final Answer that lists eligible schemes, their benefits, and a disclaimer
  that results are informational only.
"""


def _get_llm() -> ChatOpenAI | None:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key or api_key == 'your_key_here':
        return None
    return ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'),
        model=os.getenv('MODEL_NAME', 'openai/gpt-4o-mini'),
        temperature=0.2,
    )


def _build_question(profile: UserProfile, follow_up: str | None) -> str:
    lines = [
        "Find government schemes this user is eligible for:",
        f"Age: {profile.age}, Gender: {profile.gender}, State: {profile.state}",
        f"Category: {profile.category}, Annual Family Income: Rs.{profile.annual_family_income}",
        f"Education: {profile.education_level}, Occupation: {profile.occupation}",
        f"Student: {profile.student_status}, Area: {profile.area_type}, Disability: {profile.disability_status}",
    ]
    if follow_up:
        lines.append(f"Additional query: {follow_up}")
    return "\n".join(lines)


def _parse_action(text: str) -> tuple[str, str] | None:
    """Extract (action, action_input) from an LLM response, or None if not found."""
    action_match = re.search(r"Action\s*:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    input_match = re.search(r"Action\s*Input\s*:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if action_match and input_match:
        return action_match.group(1).strip(), input_match.group(1).strip()
    return None


def _parse_final_answer(text: str) -> str | None:
    match = re.search(r"Final\s*Answer\s*:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def _react_loop(
    llm: ChatOpenAI,
    tool_map: dict,
    system_prompt: str,
    question: str,
) -> tuple[str, list[AgentTraceStep]]:
    """
    Manual ReAct loop: LLM reasons → picks tool → observes → repeats.
    Returns (final_answer, trace_steps).
    """
    # Gemma and many open-weight models don't support SystemMessage — embed it in the first human turn.
    messages = [
        HumanMessage(content=f"{system_prompt}\n\n{question}"),
    ]
    trace_steps: list[AgentTraceStep] = []

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=3, max=20),
        reraise=True,
    )
    def _call_llm(msgs):
        # Stop before the LLM writes a fake Observation — we inject the real one.
        return llm.invoke(msgs, stop=["Observation:"])

    for iteration in range(_MAX_ITERATIONS):
        response = _call_llm(messages)
        text = str(response.content).strip()

        # Check for final answer first
        final = _parse_final_answer(text)
        if final:
            return final, trace_steps

        # Try to parse a tool call
        parsed = _parse_action(text)
        if parsed is None:
            # LLM deviated from format — nudge it back
            messages.append(AIMessage(content=text))
            messages.append(HumanMessage(
                content=(
                    "Please follow the format exactly:\n"
                    "Thought: ...\nAction: ...\nAction Input: ...\n\n"
                    "Or end with:\nFinal Answer: ..."
                )
            ))
            continue

        action, action_input = parsed
        tool_fn = tool_map.get(action.lower().replace(" ", "_"))
        if tool_fn is None:
            observation = (
                f"Unknown tool '{action}'. "
                f"Available tools: {', '.join(tool_map.keys())}."
            )
        else:
            try:
                observation = tool_fn(action_input)
            except Exception as exc:
                observation = f"Tool error: {exc}"

        trace_steps.append(AgentTraceStep(
            step_number=len(trace_steps) + 1,
            action=text.splitlines()[0] if text else action,
            tool_name=action,
            tool_input={"input": action_input},
            observation=str(observation)[:400],
        ))

        # Feed observation back to the LLM
        messages.append(AIMessage(content=text))
        messages.append(HumanMessage(content=f"Observation: {observation}"))

    return "Agent reached maximum reasoning steps without a final answer.", trace_steps


def run_agent(profile: UserProfile, follow_up: str | None = None, memory=None) -> AgentOutput:
    llm = _get_llm()
    if llm is None:
        return _fallback_pipeline(profile, follow_up)

    ctx: dict = {"schemes_map": {}, "results": []}

    # ── Tool functions (closures over profile + ctx) ───────────────────────

    def scheme_finder(query: str) -> str:
        schemes = shortlist_schemes(profile)
        ctx["schemes_map"] = {s.scheme_name: s for s in schemes}
        if not schemes:
            return "No candidate schemes found for this profile."
        names = "\n".join(f"- {s.scheme_name}" for s in schemes[:15])
        return f"Found {len(schemes)} candidate schemes:\n{names}"

    def eligibility_checker(scheme_name: str) -> str:
        name = scheme_name.strip().strip('"\'')
        scheme = ctx["schemes_map"].get(name)
        if scheme is None:
            for key, s in ctx["schemes_map"].items():
                if name.lower() in key.lower() or key.lower() in name.lower():
                    scheme = s
                    break
        if scheme is None:
            sample = ", ".join(list(ctx["schemes_map"].keys())[:5])
            return f"Scheme not found. Known schemes include: {sample}. Use the exact name."
        result = check_eligibility(profile, scheme)
        score_result(result)
        if result.scheme_name not in {r.scheme_name for r in ctx["results"]}:
            ctx["results"].append(result)
        matched = ", ".join(result.matched_conditions) or "none"
        failed = ", ".join(result.failed_conditions) or "none"
        return (
            f"Scheme: {result.scheme_name}\n"
            f"Verdict: {result.verdict} (confidence: {result.confidence:.0%})\n"
            f"Matched: {matched}\n"
            f"Failed: {failed}\n"
            f"Benefits: {result.benefits}"
        )

    def web_search(scheme_name: str) -> str:
        name = scheme_name.strip().strip('"\'')
        fallback = "https://india.gov.in"
        scheme = ctx["schemes_map"].get(name)
        if scheme:
            fallback = scheme.official_link
        link = search_official_link(name, fallback)
        for r in ctx["results"]:
            if r.scheme_name == name:
                r.official_link = link
                break
        return f"Official link for '{name}': {link}"

    tool_map = {
        "scheme_finder": scheme_finder,
        "eligibility_checker": eligibility_checker,
        "web_search": web_search,
    }

    system_prompt = f"{SYSTEM_PROMPT}\n{_REACT_INSTRUCTIONS}"
    question = _build_question(profile, follow_up)

    final_answer, trace_steps = _react_loop(llm, tool_map, system_prompt, question)

    ranked = sorted(
        ctx["results"],
        key=lambda r: (
            1 if r.verdict == "Clearly Eligible" else 0,
            1 if r.verdict == "Maybe Eligible" else 0,
            1 if r.is_national else 0,
            r.confidence,
        ),
        reverse=True,
    )
    ranked = [r for r in ranked if r.verdict != "Likely Not Eligible"][:5]

    return AgentOutput(
        final_answer=final_answer,
        results=ranked,
        trace_steps=trace_steps,
    )


def _fallback_pipeline(profile: UserProfile, follow_up: str | None) -> AgentOutput:
    """Deterministic pipeline used when no LLM API key is configured."""
    trace_steps: list[AgentTraceStep] = []

    schemes = shortlist_schemes(profile)
    trace_steps.append(AgentTraceStep(
        step_number=1,
        action="Find candidate schemes",
        tool_name="scheme_finder",
        tool_input={"state": profile.state, "occupation": profile.occupation},
        observation=summarize_observation(schemes, "candidate schemes found"),
    ))

    results: list[EligibilityResult] = []
    for scheme in schemes:
        result = check_eligibility(profile, scheme)
        score_result(result)
        results.append(result)

    trace_steps.append(AgentTraceStep(
        step_number=2,
        action="Check eligibility for all schemes",
        tool_name="eligibility_checker",
        tool_input={"candidate_count": len(schemes)},
        observation=summarize_observation(results, "schemes evaluated"),
    ))

    ranked = sorted(
        results,
        key=lambda r: (
            1 if r.verdict == "Clearly Eligible" else 0,
            1 if r.verdict == "Maybe Eligible" else 0,
            r.confidence,
        ),
        reverse=True,
    )
    ranked = [r for r in ranked if r.verdict != "Likely Not Eligible"][:5]

    if not ranked:
        answer = (
            "No strong scheme matches found. Try adjusting income, education, or state. "
            "This is informational only."
        )
    else:
        lines = ["Top eligible schemes (informational only):"]
        for r in ranked[:3]:
            scope = "National" if r.is_national else "State"
            lines.append(f"- {r.scheme_name} ({scope}): {r.verdict} - {r.reason}")
        answer = "\n".join(lines)

    return AgentOutput(
        final_answer=answer,
        results=ranked,
        trace_steps=trace_steps,
    )
