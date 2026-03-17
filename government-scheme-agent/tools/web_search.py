from __future__ import annotations

from ddgs import DDGS


def search_official_link(scheme_name: str, fallback_link: str) -> str:
    query = f"{scheme_name} official government scheme site:gov.in"

    try:
        with DDGS(timeout=4) as ddgs:
            results = list(ddgs.text(query, max_results=3))
        for item in results:
            link = item.get("href") or item.get("url")
            if link and ".gov.in" in link:
                return link
    except Exception:
        return fallback_link

    return fallback_link