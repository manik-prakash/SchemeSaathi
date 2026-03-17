from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    age: int = Field(..., ge=0, le=120)
    gender: str
    state: str
    student_status: str
    annual_family_income: int = Field(..., ge=0)
    category: str
    disability_status: str
    education_level: str
    occupation: str
    area_type: str


class SchemeRecord(BaseModel):
    scheme_name: str
    ministry_or_department: str
    states_applicable: list[str]
    age_min: int
    age_max: int
    gender: str
    income_limit: int
    education_requirement: str
    category_requirement: list[str]
    occupation_requirement: str
    disability_requirement: bool
    benefits: str
    required_documents: list[str]
    official_link: str
    application_mode: str
    notes: str


class EligibilityResult(BaseModel):
    scheme_name: str
    verdict: str
    matched_conditions: list[str]
    failed_conditions: list[str]
    confidence: float
    reason: str
    required_documents: list[str]
    official_link: str
    benefits: str
    is_national: bool = False


class AgentTraceStep(BaseModel):
    step_number: int
    action: str
    tool_name: str
    tool_input: dict[str, Any]
    observation: str


class AgentOutput(BaseModel):
    final_answer: str
    results: list[EligibilityResult]
    trace_steps: list[AgentTraceStep]