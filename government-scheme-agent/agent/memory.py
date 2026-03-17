from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentMemory:
    last_profile: dict[str, Any] | None = None
    last_output: dict[str, Any] | None = None


def load_memory(session_state) -> AgentMemory:
    return AgentMemory(
        last_profile=session_state.get("memory_last_profile"),
        last_output=session_state.get("memory_last_output"),
    )


def save_memory(session_state, profile, output) -> None:
    session_state["memory_last_profile"] = profile.model_dump()
    session_state["memory_last_output"] = output.model_dump()
