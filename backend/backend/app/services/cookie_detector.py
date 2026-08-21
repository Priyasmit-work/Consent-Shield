"""
Cookie banner metadata helper (FR-2, Section 6).

Actual banner *detection* happens client-side in the extension's content
script (out of scope for this backend). This module only validates and
normalizes the safe metadata the client reports, so the backend never
has to trust unbounded free-text banner content.
"""
from __future__ import annotations

MAX_BANNER_TEXT_LENGTH = 500


def normalize_banner_text(visible_banner_text: str | None) -> str | None:
    if not visible_banner_text:
        return None
    return visible_banner_text.strip()[:MAX_BANNER_TEXT_LENGTH]
