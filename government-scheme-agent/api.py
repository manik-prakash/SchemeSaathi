from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent_executor import run_agent
from models.schemas import AgentOutput, UserProfile


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(
    title="Government Scheme Eligibility API",
    description="LLM-powered eligibility checker for Indian government schemes.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class EligibilityRequest(BaseModel):
    profile: UserProfile
    follow_up: str | None = None


@app.post("/check-eligibility", response_model=AgentOutput)
async def check_eligibility(request: EligibilityRequest) -> AgentOutput:
    return run_agent(
        profile=request.profile,
        follow_up=request.follow_up or None,
        memory=None,
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
