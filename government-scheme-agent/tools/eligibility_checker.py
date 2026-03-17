from __future__ import annotations

from models.schemas import EligibilityResult, SchemeRecord, UserProfile


def _education_matches(user_education: str, required_education: str) -> bool:
    if required_education == "Any":
        return True

    order = {
        "School": 1,
        "Post-Matric": 2,
        "Undergraduate": 3,
        "Graduate": 4,
        "Postgraduate": 5,
    }
    user_value = order.get(user_education, 0)
    required_value = order.get(required_education, 0)
    return user_value >= required_value


def check_eligibility(profile: UserProfile, scheme: SchemeRecord) -> EligibilityResult:
    matched: list[str] = []
    failed: list[str] = []
    hard_failures: list[str] = []

    if scheme.age_min <= profile.age <= scheme.age_max:
        matched.append("age criteria")
    else:
        failed.append("age criteria")
        hard_failures.append("age criteria")

    if scheme.gender in {"Any", profile.gender}:
        matched.append("gender criteria")
    else:
        failed.append("gender criteria")

    if "All" in scheme.states_applicable or profile.state in scheme.states_applicable:
        matched.append("state criteria")
    else:
        failed.append("state criteria")
        hard_failures.append("state criteria")

    if profile.annual_family_income <= scheme.income_limit:
        matched.append("income criteria")
    else:
        failed.append("income criteria")
        hard_failures.append("income criteria")

    if _education_matches(profile.education_level, scheme.education_requirement):
        matched.append("education criteria")
    else:
        failed.append("education criteria")

    if "Any" in scheme.category_requirement or profile.category in scheme.category_requirement:
        matched.append("category criteria")
    elif "Female" in scheme.category_requirement and profile.gender == "Female":
        matched.append("category/gender criteria")
    else:
        failed.append("category criteria")

    if scheme.occupation_requirement in {"Any", profile.occupation}:
        matched.append("occupation criteria")
    else:
        failed.append("occupation criteria")

    if scheme.disability_requirement is False or profile.disability_status == "Yes":
        matched.append("disability criteria")
    else:
        failed.append("disability criteria")
        hard_failures.append("disability criteria")

    if hard_failures:
        verdict = "Likely Not Eligible"
    elif len(failed) == 0:
        verdict = "Clearly Eligible"
    elif len(failed) <= 2:
        verdict = "Maybe Eligible"
    else:
        verdict = "Likely Not Eligible"

    reason = (
        f"Matched {len(matched)} conditions and failed {len(failed)} conditions."
        if failed
        else "The profile matches all structured conditions in the local dataset."
    )

    return EligibilityResult(
        scheme_name=scheme.scheme_name,
        verdict=verdict,
        matched_conditions=matched,
        failed_conditions=failed,
        confidence=0.0,
        reason=reason,
        required_documents=scheme.required_documents,
        official_link=scheme.official_link,
        benefits=scheme.benefits,
        is_national=("All" in scheme.states_applicable),
    )