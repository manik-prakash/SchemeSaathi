# Government Scheme Eligibility Agent — Architecture Document

---

## Table of Contents

1. [Surface-Level Overview](#1-surface-level-overview)
2. [Detailed Architecture](#2-detailed-architecture)
3. [Professor Presentation Section](#3-professor-presentation-section)

---

# 1. Surface-Level Overview

## What the System Does

A user fills out a 10-field profile form (age, income, category, state, etc.) and clicks **"Check My Eligibility"**. The system checks their profile against a database of 40+ Indian government schemes and returns:
- A list of matched schemes with verdicts (Eligible / Maybe / Not Eligible)
- A confidence score for each match
- An LLM-generated natural language summary
- A full trace of every step the agent took

## High-Level Flow

```
User fills form
      │
      ▼
  run_agent()               ← agent/agent_executor.py
      │
      ├─→ Filter schemes    ← tools/scheme_finder.py  → data/schemes.json
      ├─→ Check eligibility ← tools/eligibility_checker.py
      ├─→ Score confidence  ← tools/calculator.py
      ├─→ Validate links    ← tools/web_search.py  → DuckDuckGo
      └─→ Summarize         ← LLM via OpenRouter API
      │
      ▼
  AgentOutput
      │
      ▼
Streamlit UI renders results  ← app.py
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web UI | Streamlit |
| Agent Orchestration | Python (custom pipeline) |
| Tool Framework | LangChain `StructuredTool` |
| Data Models | Pydantic |
| LLM | OpenRouter (Gemma 3 27B or any model) |
| Web Search | DuckDuckGo (`ddgs`) |
| Scheme Database | Local `schemes.json` |

---

# 2. Detailed Architecture

## 2.1 Project Structure

```
government-scheme-agent/
├── app.py                        ← Streamlit UI entry point
├── data/
│   └── schemes.json              ← 40+ scheme records (static database)
├── agent/
│   ├── agent_executor.py         ← 7-step orchestration pipeline
│   ├── prompts.py                ← LLM system prompt
│   └── memory.py                 ← Streamlit session persistence
├── tools/
│   ├── scheme_finder.py          ← Scheme filtering (Step 2)
│   ├── eligibility_checker.py    ← Rule-based verdict engine (Step 3)
│   ├── calculator.py             ← Confidence scoring (Step 3)
│   └── web_search.py             ← DuckDuckGo link validation (Step 7)
├── models/
│   └── schemas.py                ← Pydantic data models
└── utils/
    └── logger.py                 ← Observation string formatter
```

---

## 2.2 Data Models (`models/schemas.py`)

All data passed between components is typed with Pydantic.

```
UserProfile
├── age: int
├── gender: str
├── state: str
├── student_status: str
├── annual_family_income: int
├── category: str          (General / OBC / SC / ST / Minority)
├── disability_status: str
├── education_level: str
├── occupation: str
└── area_type: str         (Rural / Urban)

SchemeRecord
├── scheme_name: str
├── ministry_or_department: str
├── states_applicable: list[str]     (["All"] = national)
├── age_min, age_max: int
├── gender: str
├── income_limit: int
├── education_requirement: str
├── category_requirement: list[str]
├── occupation_requirement: str
├── disability_requirement: bool
├── benefits: str
├── required_documents: list[str]
├── official_link: str
└── application_mode: str

EligibilityResult
├── scheme_name: str
├── verdict: str           ("Clearly Eligible" | "Maybe Eligible" | "Likely Not Eligible")
├── matched_conditions: list[str]
├── failed_conditions: list[str]
├── confidence: float      (0.0 – 1.0)
├── reason: str
├── required_documents: list[str]
├── official_link: str
├── benefits: str
└── is_national: bool

AgentOutput
├── final_answer: str          (LLM narrative summary)
├── results: list[EligibilityResult]
└── trace_steps: list[AgentTraceStep]
```

---

## 2.3 The 7-Step Agent Pipeline (`agent/agent_executor.py`)

The core of the system. `run_agent()` executes a **fixed, deterministic pipeline** — the LLM does NOT decide which tools to call. Each step appends an `AgentTraceStep` to the trace log.

```
Step 1 ─ Profile Understanding
         Tool: session_context
         Action: Normalize and log the user's profile.
         Output: Profile dict → trace log

Step 2 ─ Scheme Shortlisting
         Tool: scheme_finder
         Action: Filter all schemes in schemes.json by state, occupation,
                 and student status.
         Output: list[SchemeRecord]  (typically 10–20 candidates)

Step 3 ─ Eligibility Checking + Scoring
         Tool: eligibility_checker + calculator
         Action: For each candidate scheme, evaluate 8 criteria and
                 compute a confidence score.
         Output: list[EligibilityResult]

Step 4 ─ Ranking
         Tool: (internal sort)
         Action: Sort by verdict level → is_national → confidence.
                 Remove all "Likely Not Eligible" results.
         Output: list[EligibilityResult]  (sorted, filtered)

Step 5 ─ Follow-up Preference Reranking  (only if user typed a hint)
         Tool: session_context
         Action: Re-sort by keyword matching against the follow_up hint
                 (e.g., "scholarship", "low income", "national").
         Output: list[EligibilityResult]  (re-ordered)

Step 6 ─ National / State Balancing
         Tool: calculator
         Action: Reserve the top 2 slots for national schemes, then fill
                 remaining slots with state schemes. Cap at 5 results.
         Output: list[EligibilityResult]  (max 5, balanced)

Step 7 ─ Official Link Validation
         Tool: web_search
         Action: DuckDuckGo search for each of the top 3 schemes using
                 query: "{scheme_name} official government scheme site:gov.in"
                 Replace stored link if a .gov.in URL is found.
         Output: list[EligibilityResult]  (validated links)

─── LLM Summary (outside numbered steps) ─────────────────────────────
         Function: _llm_summary()
         Action: Send profile + top 5 results to LLM (via OpenRouter).
                 Uses SYSTEM_PROMPT that instructs the model to explain
                 eligibility concisely without claiming final approval.
         Fallback: If no API key or LLM call fails, _fallback_summary()
                   formats a plain-text summary from the top 3 results.
         Output: final_answer: str
```

---

## 2.4 Eligibility Checker — 8 Criteria (`tools/eligibility_checker.py`)

Each criterion is evaluated independently. Hard failures immediately push the verdict to "Likely Not Eligible".

| # | Criterion | Check | Failure Type |
|---|-----------|-------|--------------|
| 1 | Age | `age_min ≤ profile.age ≤ age_max` | **Hard** |
| 2 | Gender | `scheme.gender in {Any, profile.gender}` | Soft |
| 3 | State | `"All" in states OR profile.state in states` | **Hard** |
| 4 | Income | `profile.income ≤ scheme.income_limit` | **Hard** |
| 5 | Education | Hierarchy: School < Post-Matric < UG < Graduate < PG | Soft |
| 6 | Category | `"Any" in requirement OR profile.category matches` | Soft |
| 7 | Occupation | `requirement in {Any, profile.occupation}` | Soft |
| 8 | Disability | `disability_requirement=False OR profile.disability=Yes` | **Hard** |

**Verdict Logic:**

```
any hard failure     → "Likely Not Eligible"
0 soft failures      → "Clearly Eligible"
1–2 soft failures    → "Maybe Eligible"
3+ soft failures     → "Likely Not Eligible"
```

**Confidence Score** (`tools/calculator.py`):

```
confidence = matched_conditions / (matched_conditions + failed_conditions)
```

---

## 2.5 Scheme Database (`data/schemes.json`)

Static JSON array of 40+ government schemes. Example entry:

```json
{
  "scheme_name": "Post Matric Scholarship for OBC Students",
  "ministry_or_department": "Ministry of Social Justice and Empowerment",
  "states_applicable": ["All"],
  "age_min": 16,  "age_max": 30,
  "gender": "Any",
  "income_limit": 250000,
  "education_requirement": "Post-Matric",
  "category_requirement": ["OBC"],
  "occupation_requirement": "Student",
  "disability_requirement": false,
  "benefits": "Tuition support and maintenance allowance",
  "required_documents": ["Aadhaar", "Income Certificate", "Caste Certificate"],
  "official_link": "https://socialjustice.gov.in",
  "application_mode": "Online"
}
```

Schemes covered include: education scholarships (SC/ST/OBC/Minority), disability welfare, rural livelihoods (MGNREGA, PM-KISAN), women-focused schemes, and state-specific schemes for Karnataka, Maharashtra, Delhi, Tamil Nadu.

---

## 2.6 LLM Integration (`agent/agent_executor.py`)

- **Provider:** OpenRouter (wraps many models behind one API)
- **Current Model:** `google/gemma-3-27b-it:free`
- **Temperature:** 0.2 (low, keeps responses factual)
- **Role:** Only used at the very end for natural language summarization
- **Fallback:** If `OPENROUTER_API_KEY` is missing or invalid, a structured text summary is generated without any LLM call

The LLM **does not** make eligibility decisions. It only narrates the results computed by the deterministic pipeline.

---

## 2.7 Web Search (`tools/web_search.py`)

```python
query = f"{scheme_name} official government scheme site:gov.in"
# Returns first result with .gov.in domain
# Falls back to stored link on timeout or no result
```

Runs for top 3 schemes only. 4-second timeout per query.

---

## 2.8 Memory (`agent/memory.py`)

Simple Streamlit session state wrapper. Persists the last profile and output within the browser session (not across sessions). Shown in the sidebar as "Previous profile loaded."

---

## 2.9 UI (`app.py`)

Two-column Streamlit layout:

```
┌──────────────────────┬──────────────────────────────────────┐
│   LEFT COLUMN        │   RIGHT COLUMN                       │
│                      │                                      │
│  Personal Details    │  LLM Summary (final_answer)          │
│  - Age, Gender       │                                      │
│  - State, Area       │  Result Cards (per scheme):          │
│                      │  - Name + Verdict badge (color)      │
│  Education & Work    │  - Confidence bar                    │
│  - Student, Edu      │  - Reason                            │
│  - Occupation        │  - ✅ Matched / ❌ Failed conditions  │
│                      │  - 📄 Required documents             │
│  Financial & Social  │  - Apply Here → (official link)      │
│  - Income            │  - "What you get" expander           │
│  - Category          │                                      │
│  - Disability        │  Agent Trace (collapsed by default): │
│                      │  - 👤 Step 1: Profile Understanding  │
│  Optional hint       │  - 🔍 Step 2: Scheme shortlisting    │
│  [text area]         │  - ✅ Step 3: Eligibility checking   │
│                      │  - 📊 Step 4: Ranking                │
│  [Check Eligibility] │  - 🌐 Step 7: Link validation        │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 2.10 Graceful Degradation

| Failure | Behavior |
|---------|----------|
| No API key | `_fallback_summary()` generates plain-text summary — app fully functional |
| Web search timeout | Keeps original `official_link` from `schemes.json` |
| No schemes match | Warning message shown; user prompted to adjust profile |
| Previous session lost | `AgentMemory` returns `None` values — no crash |

---

# 3. Professor Presentation Section

## Slide 1 — Problem Statement

> Millions of eligible Indians miss out on government welfare schemes due to lack of awareness and the complexity of eligibility rules spread across hundreds of portals.

**Goal:** Build an AI agent that takes a user's demographic profile and automatically identifies which government schemes they likely qualify for — with full reasoning transparency.

---

## Slide 2 — System Architecture (One Slide View)

```
┌──────────┐     ┌─────────────────────────────────────────────┐
│  User    │────▶│              Streamlit Web App               │
│ Profile  │     │                  (app.py)                    │
└──────────┘     └────────────────────┬────────────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │    Agent Executor      │
                          │  (7-Step Pipeline)     │
                          └──┬──────────┬──────────┘
                             │          │
                    ┌────────┘          └─────────┐
                    ▼                             ▼
         ┌──────────────────┐        ┌─────────────────────┐
         │  Local Database  │        │   OpenRouter LLM    │
         │  (schemes.json)  │        │  (Summary only)     │
         │  40+ schemes     │        │  Fallback: no LLM   │
         └──────────────────┘        └─────────────────────┘
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
┌──────────────────┐  ┌──────────────────────┐
│ Eligibility      │  │  DuckDuckGo Search   │
│ Rules Engine     │  │  (Link validation)   │
│ (8 criteria,     │  │  Fallback: stored    │
│  deterministic)  │  │  link               │
└──────────────────┘  └──────────────────────┘
```

---

## Slide 3 — What Makes This an "Agent"?

A standard program runs a fixed script. An agent uses **tools** to reason step-by-step toward a goal.

| Feature | This Project |
|---------|-------------|
| Tool use | 4 LangChain `StructuredTool`s (finder, checker, calculator, search) |
| Multi-step reasoning | 7-step pipeline with trace logging at each step |
| Environment interaction | Reads local DB, calls web search API, calls LLM |
| Memory | Streamlit session state for cross-interaction memory |
| Graceful fallback | Works without LLM; works without internet |

> **Key design choice:** The agent pipeline is *deterministic* (not LLM-driven tool selection). This was intentional — it makes eligibility results stable, auditable, and explainable, which is critical for a welfare application.

---

## Slide 4 — Eligibility Engine (The Core Logic)

The eligibility check is **rule-based, not ML-based**. This was a deliberate design decision.

**8 criteria per scheme:**

```
Age range          ──── HARD FAILURE (age is non-negotiable)
Gender             ──── soft failure
State              ──── HARD FAILURE
Income limit       ──── HARD FAILURE
Education level    ──── soft failure (hierarchy-aware)
Social category    ──── soft failure
Occupation         ──── soft failure
Disability status  ──── HARD FAILURE
```

**Why deterministic?**
- LLMs hallucinate eligibility rules
- Government rules are structured and binary
- Results must be auditable and reproducible
- No training data required

---

## Slide 5 — LLM's Limited but Important Role

The LLM is used **only at the end** to generate a friendly, natural-language summary of results already computed by the rules engine.

```
Rules engine  ──▶  "Clearly Eligible | confidence: 87%"
      ↓
LLM prompt:   "Given this profile and these results, write a
               concise, supportive eligibility summary."
      ↓
LLM output:   "Based on your profile as an OBC undergraduate
               student with a family income of ₹2L in Karnataka,
               you are strongly eligible for the Post Matric
               Scholarship. Your main advantage is..."
```

If the LLM is unavailable, the app **still works fully** — the summary is generated programmatically from the structured results.

---

## Slide 6 — Key Engineering Decisions

| Decision | Rationale |
|----------|-----------|
| Deterministic pipeline over LLM tool-calling | Stability and auditability for welfare use |
| Local JSON database over live API | No dependency on government portals; faster; offline-capable |
| Hard vs soft failure distinction | Mimics real eligibility logic (age/income are absolute; education/category are flexible) |
| National/State balancing | Prevents results dominated by one state; ensures central schemes always surface |
| Confidence score | Gives users a quantitative sense of how "borderline" their eligibility is |
| Web search only for link validation | Reduces hallucination risk; keeps core logic deterministic |

---

## Slide 7 — What I Learned / Contributions

**Technical skills demonstrated:**
- Agentic AI design with LangChain tool registration
- Pydantic data modeling for type-safe AI pipelines
- Streamlit UI development with custom CSS
- OpenRouter LLM API integration with fallback handling
- DuckDuckGo web search integration
- Session state management

**Design thinking demonstrated:**
- Separating deterministic logic from LLM (reliability vs. flexibility)
- Building for failure (graceful degradation at every layer)
- Transparency through trace logging (every step is visible to the user)
- Balancing national vs. state results (fairness in recommendations)

---

## Slide 8 — Demo Profile Examples

**Profile A — Low-income OBC student, Karnataka**
```
Age: 21 | Gender: Female | State: Karnataka
Student: Yes | Income: ₹1,80,000 | Category: OBC
Education: Undergraduate | Area: Rural
```
→ Expected: Post Matric Scholarship, NSP, Karnataka Vidya Siri

**Profile B — SC student with disability**
```
Age: 19 | Gender: Male | State: Maharashtra
Student: Yes | Income: ₹1,20,000 | Category: SC | Disability: Yes
Education: Undergraduate
```
→ Expected: NHFDC, National Scholarship for SC, NISWASS

**Profile C — Farmer, any state**
```
Age: 45 | Gender: Male | State: All
Occupation: Farmer | Income: ₹3,00,000 | Category: General
```
→ Expected: PM-KISAN, PMFBY (crop insurance), Kisan Credit Card

---

*This document was generated from a complete source-code analysis of the `government-scheme-agent` project.*
