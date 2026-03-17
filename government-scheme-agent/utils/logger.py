from __future__ import annotations


def summarize_observation(items, label: str) -> str:
    count = len(items)
    return f"{count} {label}."
