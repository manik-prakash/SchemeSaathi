from __future__ import annotations

import json
from pathlib import Path

from models.schemas import SchemeRecord, UserProfile


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "schemes.json"


def load_schemes() -> list[SchemeRecord]:
    records = json.loads(DATA_PATH.read_text(encoding="utf-8-sig"))
    return [SchemeRecord(**item) for item in records]


def shortlist_schemes(profile: UserProfile) -> list[SchemeRecord]:
    schemes = load_schemes()
    shortlisted: list[SchemeRecord] = []

    for scheme in schemes:
        if "All" not in scheme.states_applicable and profile.state not in scheme.states_applicable:
            continue
        if scheme.occupation_requirement == "Student" and profile.student_status == "No":
            continue
        if scheme.occupation_requirement not in {"Any", profile.occupation}:
            continue
        shortlisted.append(scheme)

    return shortlisted