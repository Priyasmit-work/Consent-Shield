"""
Preferences schemas.

Validation rules, all directly derived from the API contract (Section 5)
and PRD (Section 7/8):
  - `essential` must always be True.
  - `categories.unknown` must never be True (unknown categories must never
    be automatically allowed -- PRD Section 8).
  - `mode == manual` implies `auto_apply` must be False (manual mode means
    "analyze and recommend only; never apply an action automatically" --
    PRD Section 7). Sending auto_apply=true with mode=manual is a
    contradictory combination and must be rejected with 422, not silently
    corrected.
Any other combination is accepted as-is; the contract does not specify
further cross-field constraints, so none are invented here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import CookieCategory, PrivacyMode


class CategoryPreferences(BaseModel):
    essential: bool = True
    functional: bool = False
    analytics: bool = False
    advertising: bool = False
    social: bool = False
    unknown: bool = False

    def as_dict(self) -> Dict[str, bool]:
        return self.model_dump()


class PreferencesBase(BaseModel):
    mode: PrivacyMode = PrivacyMode.manual
    categories: CategoryPreferences = Field(default_factory=CategoryPreferences)
    auto_apply: bool = False
    require_confirmation_for_unknown: bool = True
    allow_network_observation: bool = True
    save_scan_history: bool = True


class PreferencesUpdateRequest(PreferencesBase):
    """Body for PUT /me/preferences. Replaces the full preference object."""

    @model_validator(mode="after")
    def validate_contradictions(self) -> "PreferencesUpdateRequest":
        errors = []

        if not self.categories.essential:
            errors.append("categories.essential must always be true")

        if self.categories.unknown:
            errors.append(
                "categories.unknown must never be true; unknown categories "
                "must never be automatically allowed"
            )

        if self.mode == PrivacyMode.manual and self.auto_apply:
            errors.append(
                "auto_apply cannot be true while mode is 'manual'; manual "
                "mode never applies an action automatically"
            )

        if errors:
            raise ValueError("; ".join(errors))

        return self


class Preferences(PreferencesBase):
    """Stored / returned preferences object, matching GET and PUT responses."""

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def default_preferences() -> Preferences:
    """New users default to manual mode per PRD Section 7."""
    return Preferences(
        mode=PrivacyMode.manual,
        categories=CategoryPreferences(),
        auto_apply=False,
        require_confirmation_for_unknown=True,
        allow_network_observation=True,
        save_scan_history=True,
    )
