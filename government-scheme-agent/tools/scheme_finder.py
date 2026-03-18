from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from models.schemas import SchemeRecord, UserProfile


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATA_PATH = BASE_DIR / "data" / "schemes.json"

# ── Lenient defaults for partial LLM extraction ───────────────────────────────
_SCHEME_DEFAULTS: dict = {
    "ministry_or_department": "Unknown",
    "states_applicable": ["All"],
    "age_min": 0,
    "age_max": 100,
    "gender": "Any",
    "income_limit": 500000,
    "education_requirement": "Any",
    "category_requirement": ["Any"],
    "occupation_requirement": "Any",
    "disability_requirement": False,
    "benefits": "Not specified",
    "required_documents": ["Aadhaar"],
    "official_link": "https://india.gov.in",
    "application_mode": "Online",
    "notes": "",
}

_EXTRACTION_PROMPT_TEMPLATE = """You are a structured data extractor for Indian government schemes.

Given the search result snippets below, extract up to 10 distinct government scheme records.
Return ONLY a valid JSON array. No commentary, no markdown fences, no code blocks.

For each scheme, produce exactly this JSON object:
{{
  "scheme_name": "<official name>",
  "ministry_or_department": "<ministry or 'Unknown'>",
  "states_applicable": ["All"],
  "age_min": 0,
  "age_max": 100,
  "gender": "Any",
  "income_limit": 500000,
  "education_requirement": "Any",
  "category_requirement": ["Any"],
  "occupation_requirement": "Any",
  "disability_requirement": false,
  "benefits": "<brief description or 'Not specified'>",
  "required_documents": ["Aadhaar"],
  "official_link": "<URL from snippet or 'https://india.gov.in'>",
  "application_mode": "Online",
  "notes": "<any relevant detail>"
}}

Rules:
- Only extract schemes explicitly mentioned in the snippets. Do NOT invent schemes.
- Use the defaults above for any field not clearly stated in the snippet.
- income_limit: use 500000 if unknown. Use 0 ONLY if the snippet explicitly says the scheme is for BPL/below-poverty-line households but gives no figure.
- states_applicable: use ["All"] for central/national schemes. Use ["{state}"] when clearly state-specific.
- occupation_requirement: one of "Any", "Student", "Farmer", "Self-Employed", "Unemployed", "Employed".
- category_requirement: list from "Any", "SC", "ST", "OBC", "General", "Minority", "Female".
- Do NOT duplicate entries with the same scheme_name.

Snippets:
{snippets_block}"""


# ── LLM initialisation ────────────────────────────────────────────────────────

def _get_llm() -> ChatOpenAI | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_key_here":
        return None
    return ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        model=os.getenv("MODEL_NAME", "openai/gpt-4o-mini"),
        temperature=0.1,
    )


# ── Query construction ────────────────────────────────────────────────────────

def _build_queries(profile: UserProfile) -> list[str]:
    query_a = (
        f"{profile.category} government scheme {profile.state} "
        f"{profile.occupation} India site:gov.in OR site:india.gov.in"
    )

    if profile.occupation == "Student" or profile.annual_family_income <= 300000:
        query_b = (
            f"scholarship welfare scheme {profile.state} {profile.category} "
            f"India eligibility apply 2024"
        )
    else:
        query_b = (
            f"{profile.occupation} government scheme India {profile.state} "
            f"eligibility apply 2024"
        )

    return [query_a, query_b]


# ── DDGS search with tenacity retry ──────────────────────────────────────────

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
def _run_ddgs_query(query: str, max_results: int = 8) -> list[dict]:
    from ddgs import DDGS
    with DDGS(timeout=6) as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def _fetch_snippets(profile: UserProfile) -> list[dict]:
    queries = _build_queries(profile)
    seen_titles: set[str] = set()
    snippets: list[dict] = []

    for query in queries:
        try:
            results = _run_ddgs_query(query, max_results=8)
        except Exception:
            results = []

        for item in results:
            title = (item.get("title") or "").lower().strip()
            title_key = re.sub(r"[^a-z0-9 ]", "", title)
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                snippets.append({
                    "title": item.get("title", ""),
                    "href": item.get("href") or item.get("url", ""),
                    "body": item.get("body", ""),
                })

    return snippets


# ── LLM extraction ────────────────────────────────────────────────────────────

def _build_snippets_block(snippets: list[dict]) -> str:
    lines = []
    for i, s in enumerate(snippets, 1):
        lines.append(f"[{i}] Title: {s['title']}")
        lines.append(f"    URL: {s['href']}")
        lines.append(f"    Body: {s['body']}")
    return "\n".join(lines)


def _extract_schemes_via_llm(profile: UserProfile, snippets: list[dict]) -> list[SchemeRecord]:
    llm = _get_llm()
    if llm is None:
        return []

    prompt = _EXTRACTION_PROMPT_TEMPLATE.format(
        state=profile.state,
        snippets_block=_build_snippets_block(snippets),
    )

    try:
        response = llm.invoke(prompt)
        raw_text = response.content if isinstance(response.content, str) else ""
    except Exception:
        return []

    # Strip accidental markdown fences
    raw_text = re.sub(r"```(?:json)?", "", raw_text).strip().rstrip("`")

    try:
        raw_list = json.loads(raw_text)
        if not isinstance(raw_list, list):
            return []
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw_text, re.DOTALL)
        if not match:
            return []
        try:
            raw_list = json.loads(match.group())
        except json.JSONDecodeError:
            return []

    records: list[SchemeRecord] = []
    seen_names: set[str] = set()

    for item in raw_list:
        if not isinstance(item, dict):
            continue
        name = (item.get("scheme_name") or "").strip()
        if not name:
            continue
        if name.lower() in seen_names:
            continue
        seen_names.add(name.lower())

        merged = {**_SCHEME_DEFAULTS, **{k: v for k, v in item.items() if v is not None and v != ""}}
        merged["scheme_name"] = name

        try:
            records.append(SchemeRecord(**merged))
        except Exception:
            continue

    return records


# ── Web-search orchestrator ───────────────────────────────────────────────────

def _web_search_schemes(profile: UserProfile) -> list[SchemeRecord]:
    snippets = _fetch_snippets(profile)
    if not snippets:
        return []
    return _extract_schemes_via_llm(profile, snippets)


# ── JSON fallback (original logic) ───────────────────────────────────────────

def load_schemes() -> list[SchemeRecord]:
    records = json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))
    return [SchemeRecord(**item) for item in records]


def _json_shortlist(profile: UserProfile) -> list[SchemeRecord]:
    shortlisted: list[SchemeRecord] = []
    for scheme in load_schemes():
        if "All" not in scheme.states_applicable and profile.state not in scheme.states_applicable:
            continue
        if scheme.occupation_requirement == "Student" and profile.student_status == "No":
            continue
        if scheme.occupation_requirement not in {"Any", profile.occupation}:
            continue
        shortlisted.append(scheme)
    return shortlisted


# ── Public interface (called by agent_executor.py — signature unchanged) ──────

def shortlist_schemes(profile: UserProfile) -> list[SchemeRecord]:
    """Discover schemes via live web search + LLM extraction.
    Falls back to data/schemes.json if web search fails or returns nothing.
    """
    try:
        schemes = _web_search_schemes(profile)
        if schemes:
            return schemes
    except Exception:
        pass
    return _json_shortlist(profile)
