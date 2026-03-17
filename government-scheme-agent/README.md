# Government Scheme Eligibility Agent

A Streamlit-based Agentic AI mini-project that helps users estimate their eligibility for government schemes using a combination of:

- LangChain + OpenRouter for LLM-backed reasoning
- Local JSON scheme data for reliable matching
- Tool-based eligibility checks
- DuckDuckGo web search for official link discovery and validation

## Why this project works well

- Real use case with social value
- Meets the assignment requirements for an LLM-based agent
- Uses multiple tools and observable reasoning steps
- Simple enough to build and demo in an undergraduate setting

## Recommended Python version

Use Python `3.10` or `3.11`.

The current machine may have a newer version installed, but this dependency stack is most reliable on 3.10/3.11.

## Project structure

```text
government-scheme-agent/
├─ app.py
├─ requirements.txt
├─ .env
├─ README.md
├─ data/
│  └─ schemes.json
├─ agent/
│  ├─ __init__.py
│  ├─ agent_executor.py
│  ├─ prompts.py
│  └─ memory.py
├─ tools/
│  ├─ __init__.py
│  ├─ scheme_finder.py
│  ├─ eligibility_checker.py
│  ├─ web_search.py
│  └─ calculator.py
├─ models/
│  ├─ __init__.py
│  └─ schemas.py
└─ utils/
   ├─ __init__.py
   └─ logger.py
```

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Add your OpenRouter API key

Edit `.env`:

```env
OPENROUTER_API_KEY=your_actual_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=openai/gpt-4o-mini
```

If your chosen model is not available in the free tier, replace `MODEL_NAME` with a free OpenRouter-compatible chat model.

## Run the app

```powershell
streamlit run app.py
```

## What the agent does

1. Reads the user profile
2. Uses the Scheme Finder tool to shortlist candidate schemes
3. Uses the Eligibility Checker tool to evaluate eligibility condition-by-condition
4. Uses the Calculator tool to compute confidence and ranking
5. Uses the Web Search tool to confirm official links when needed
6. Produces an explanation with traces that show observable agent behavior

## Suggested demo profiles

### Low-income student

- Age: 19
- Gender: Female
- State: Karnataka
- Student: Yes
- Income: 180000
- Category: OBC
- Disability: No
- Education level: Undergraduate
- Occupation: Student
- Rural/Urban: Rural

### Student with disability

- Age: 21
- Gender: Male
- State: Maharashtra
- Student: Yes
- Income: 220000
- Category: General
- Disability: Yes
- Education level: Postgraduate
- Occupation: Student
- Rural/Urban: Urban

### High-income user

- Age: 24
- Gender: Female
- State: Karnataka
- Student: No
- Income: 900000
- Category: General
- Disability: No
- Education level: Graduate
- Occupation: Self-Employed
- Rural/Urban: Urban

## Notes

- This app is informational only. Final eligibility depends on official verification.
- The local JSON dataset is the primary matching source so the demo remains stable.
- Web search is used to enrich results and validate official pages, not to replace the core rules.
