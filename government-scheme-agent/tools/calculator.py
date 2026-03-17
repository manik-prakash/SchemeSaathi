from __future__ import annotations

from models.schemas import EligibilityResult


def score_result(result: EligibilityResult) -> EligibilityResult:
    total_checks = len(result.matched_conditions) + len(result.failed_conditions)
    result.confidence = len(result.matched_conditions) / total_checks if total_checks else 0.0
    return result
