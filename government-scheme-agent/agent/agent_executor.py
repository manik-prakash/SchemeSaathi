from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from agent.prompts import SYSTEM_PROMPT
from models.schemas import AgentOutput, AgentTraceStep, EligibilityResult, UserProfile
from tools.calculator import score_result
from tools.eligibility_checker import check_eligibility
from tools.scheme_finder import shortlist_schemes
from tools.web_search import search_official_link
from utils.logger import summarize_observation


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / '.env')


def _build_tool_registry() -> list[StructuredTool]:
    return [
        StructuredTool.from_function(
            func=shortlist_schemes,
            name='scheme_finder',
            description='Shortlist candidate schemes based on the user profile from the local scheme database.',
        ),
        StructuredTool.from_function(
            func=check_eligibility,
            name='eligibility_checker',
            description='Check whether a user profile matches a scheme\'s structured eligibility criteria.',
        ),
        StructuredTool.from_function(
            func=score_result,
            name='calculator',
            description='Score and rank scheme eligibility results.',
        ),
        StructuredTool.from_function(
            func=search_official_link,
            name='web_search',
            description='Search the web for a likely official scheme page when a better source is needed.',
        ),
    ]


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


def _fallback_summary(results: list[EligibilityResult]) -> str:
    if not results:
        return (
            'I could not find a strong scheme match from the current profile. '
            'Try adjusting income, education level, or state details and run the agent again. '
            'This is only an informational estimate.'
        )

    lines = ['Here are the strongest scheme matches from the current profile:']
    for item in results[:3]:
        scope = 'National' if item.is_national else 'State'
        lines.append(f'- {item.scheme_name} ({scope}): {item.verdict} because {item.reason}')
    lines.append('These results are informational only and final eligibility depends on official verification.')
    return '\n'.join(lines)


def _llm_summary(profile: UserProfile, results: list[EligibilityResult], follow_up: str | None) -> str:
    llm = _get_llm()
    if llm is None:
        return _fallback_summary(results)

    payload = {
        'profile': profile.model_dump(),
        'follow_up': follow_up,
        'results': [item.model_dump() for item in results[:5]],
    }
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        'Based on the structured results below, write a concise final answer for the user.\n'
        'Mention the strongest matches first, include whether they are national or state-level schemes, explain the main eligibility reasons, and end with an informational disclaimer.\n\n'
        f"{json.dumps(payload, indent=2)}"
    )
    try:
        response = llm.invoke(prompt)
        return response.content if isinstance(response.content, str) else _fallback_summary(results)
    except Exception:
        return _fallback_summary(results)


def _preference_score(result: EligibilityResult, follow_up: str | None, profile: UserProfile) -> float:
    if not follow_up:
        return 0.0

    text = follow_up.lower()
    scheme_text = ' '.join([
        result.scheme_name.lower(),
        result.benefits.lower(),
        ' '.join(result.required_documents).lower(),
        result.reason.lower(),
    ])

    score = 0.0

    if 'scholarship' in text and 'scholarship' in scheme_text:
        score += 0.35

    low_income_terms = ['low income', 'poor', 'poverty', 'below poverty line', 'bpl', 'economically weaker']
    if any(term in text for term in low_income_terms):
        if profile.annual_family_income <= 250000:
            score += 0.25
        elif profile.annual_family_income <= 500000:
            score += 0.10

        if any(term in scheme_text for term in ['income support', 'maintenance allowance', 'financial assistance', 'scholarship', 'fee reimbursement', 'tuition']):
            score += 0.35

        if any(term in result.scheme_name.lower() for term in ['scholarship', 'reimbursement', 'pension']):
            score += 0.20

    if 'student' in text and 'scholarship' in scheme_text:
        score += 0.15

    if 'rural' in text and profile.area_type == 'Rural':
        score += 0.10

    national_terms = ['national', 'central', 'all india', 'india wide', 'pan india']
    if any(term in text for term in national_terms) and result.is_national:
        score += 0.40

    return score


def _apply_follow_up_preferences(results: list[EligibilityResult], follow_up: str | None, profile: UserProfile) -> list[EligibilityResult]:
    if not follow_up:
        return results

    scored_results = []
    for item in results:
        preference_score = _preference_score(item, follow_up, profile)
        scored_results.append((item, preference_score))

    scored_results.sort(
        key=lambda pair: (
            pair[1],
            1 if pair[0].verdict == 'Clearly Eligible' else 0,
            1 if pair[0].verdict == 'Maybe Eligible' else 0,
            1 if pair[0].is_national else 0,
            pair[0].confidence,
        ),
        reverse=True,
    )

    reordered = [item for item, _ in scored_results]

    if 'scholarship' in follow_up.lower():
        scholarship_first = [item for item in reordered if 'scholarship' in item.scheme_name.lower() or 'scholarship' in item.benefits.lower()]
        others = [item for item in reordered if item not in scholarship_first]
        reordered = scholarship_first + others

    return reordered


def _balance_national_and_state(results: list[EligibilityResult], limit: int = 5) -> list[EligibilityResult]:
    if not results:
        return []

    national_results = [item for item in results if item.is_national]
    state_results = [item for item in results if not item.is_national]

    balanced: list[EligibilityResult] = []

    if national_results:
        balanced.extend(national_results[:2])

    for item in results:
        if item not in balanced:
            balanced.append(item)
        if len(balanced) >= limit:
            break

    if len(balanced) < limit:
        for item in state_results:
            if item not in balanced:
                balanced.append(item)
            if len(balanced) >= limit:
                break

    return balanced[:limit]


def run_agent(profile: UserProfile, follow_up: str | None = None, memory=None) -> AgentOutput:
    _build_tool_registry()
    trace_steps: list[AgentTraceStep] = []

    trace_steps.append(
        AgentTraceStep(
            step_number=1,
            action='Understand user profile',
            tool_name='session_context',
            tool_input=profile.model_dump(),
            observation='Profile captured and normalized for agent processing.',
        )
    )

    candidate_schemes = shortlist_schemes(profile=profile)
    trace_steps.append(
        AgentTraceStep(
            step_number=2,
            action='Discover relevant schemes via web search',
            tool_name='scheme_finder',
            tool_input={'state': profile.state, 'occupation': profile.occupation, 'student_status': profile.student_status},
            observation=summarize_observation(candidate_schemes, 'candidate schemes discovered (web search + LLM extraction, JSON fallback if offline)'),
        )
    )

    evaluated_results: list[EligibilityResult] = []
    for scheme in candidate_schemes:
        result = check_eligibility(profile=profile, scheme=scheme)
        score_result(result=result)
        evaluated_results.append(result)

    trace_steps.append(
        AgentTraceStep(
            step_number=3,
            action='Check eligibility against structured rules',
            tool_name='eligibility_checker',
            tool_input={'candidate_count': len(candidate_schemes)},
            observation=summarize_observation(evaluated_results, 'schemes evaluated'),
        )
    )

    ranked_results = sorted(
        evaluated_results,
        key=lambda item: (
            1 if item.verdict == 'Clearly Eligible' else 0,
            1 if item.verdict == 'Maybe Eligible' else 0,
            1 if item.is_national else 0,
            item.confidence,
        ),
        reverse=True,
    )
    ranked_results = [item for item in ranked_results if item.verdict != 'Likely Not Eligible']

    trace_steps.append(
        AgentTraceStep(
            step_number=4,
            action='Rank scheme matches',
            tool_name='calculator',
            tool_input={'evaluated_count': len(evaluated_results)},
            observation=summarize_observation(ranked_results[:5], 'top schemes ranked before balancing'),
        )
    )

    if follow_up:
        ranked_results = _apply_follow_up_preferences(ranked_results, follow_up, profile)
        trace_steps.append(
            AgentTraceStep(
                step_number=5,
                action='Apply follow-up preference',
                tool_name='session_context',
                tool_input={'follow_up': follow_up},
                observation='Applied a stronger ranking boost based on the optional refinement text.',
            )
        )

    ranked_results = _balance_national_and_state(ranked_results, limit=5)
    trace_steps.append(
        AgentTraceStep(
            step_number=6,
            action='Balance national and state schemes',
            tool_name='calculator',
            tool_input={'final_limit': 5},
            observation='Reserved room for national-level schemes so the final list includes broader central options when available.',
        )
    )

    for item in ranked_results[:3]:
        validated_link = search_official_link(item.scheme_name, item.official_link)
        if validated_link:
            item.official_link = validated_link

    trace_steps.append(
        AgentTraceStep(
            step_number=7,
            action='Validate official links',
            tool_name='web_search',
            tool_input={'top_result_count': min(3, len(ranked_results))},
            observation='Checked top results for likely official links or kept stored links as fallback.',
        )
    )

    final_answer = _llm_summary(profile=profile, results=ranked_results, follow_up=follow_up)
    return AgentOutput(final_answer=final_answer, results=ranked_results, trace_steps=trace_steps)