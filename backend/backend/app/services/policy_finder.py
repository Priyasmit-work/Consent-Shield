"""
Policy finder.

Section 6 (Analysis) / Section 14 (webcmd requirements): find cookie and
privacy-policy links through footer links, visible page text, navigation,
and consent interfaces. Extracted here as its own step so a live webcmd
integration can replace `find_policy_urls` without touching the rest of
the orchestrator in browser_agent.py.
"""
from __future__ import annotations


def find_policy_urls(origin: str, learned_urls: list[str] | None = None) -> list[str]:
    if learned_urls:
        return learned_urls
    return [f"{origin}/privacy", f"{origin}/cookie-policy"]
