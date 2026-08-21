"""
Protection planner.

Implements the privacy-mode table from the PRD (Section 7):

| Mode       | Behavior                                                          |
|------------|--------------------------------------------------------------------|
| strict     | Allow essential only; block optional categories where possible.    |
| balanced   | Allow essential + functional; block advertising and optional       |
|            | analytics.                                                          |
| functional | Allow essential + functional; block advertising.                   |
| custom     | Apply the user's category-level preferences.                       |
| manual     | Analyze and recommend only; never apply an action automatically.   |

Categories a mode's description does not explicitly allow default to
blocked, following the PRD's "recommend the least-permissive practical
choice" principle (Section 6, Protection user stories) rather than being
invented per-mode behavior.

`unknown` categories are never included in allowed_categories, for any
mode -- PRD Section 8: "must not automatically allow unknown categories."
"""
from __future__ import annotations

from app.schemas.common import ConsentAction, CookieCategory, PrivacyMode
from app.schemas.preferences import Preferences
from app.schemas.scans import CategoryFinding, ProtectionPlan

MODE_ALLOWED_BASE: dict[PrivacyMode, set[CookieCategory]] = {
    PrivacyMode.strict: {CookieCategory.essential},
    PrivacyMode.balanced: {CookieCategory.essential, CookieCategory.functional},
    PrivacyMode.functional: {CookieCategory.essential, CookieCategory.functional},
    PrivacyMode.manual: {CookieCategory.essential},
}


class ProtectionPlanner:
    def build_plan(
        self,
        preferences: Preferences,
        findings: list[CategoryFinding],
    ) -> ProtectionPlan:
        detected_categories = {
            f.category
            for f in findings
            if f.classification == "detected" and f.category != CookieCategory.unknown
        }
        unknown_categories = [
            f.category for f in findings if f.classification == "unknown"
        ]

        if preferences.mode == PrivacyMode.custom:
            allowed = {
                cat
                for cat, is_allowed in preferences.categories.as_dict().items()
                if is_allowed and CookieCategory(cat) != CookieCategory.unknown
            }
            allowed = {CookieCategory(c) if isinstance(c, str) else c for c in allowed}
        else:
            allowed = set(MODE_ALLOWED_BASE.get(preferences.mode, {CookieCategory.essential}))

        # Essential is always allowed, regardless of mode.
        allowed.add(CookieCategory.essential)
        # Unknown is never auto-allowed, regardless of mode or preferences.
        allowed.discard(CookieCategory.unknown)

        blocked = sorted(
            (detected_categories | {CookieCategory.functional, CookieCategory.analytics,
                                     CookieCategory.advertising, CookieCategory.social})
            - allowed,
            key=lambda c: c.value,
        )

        recommended_action = self._recommend_action(
            preferences.mode, allowed, blocked, unknown_categories
        )

        requires_confirmation = (
            not preferences.auto_apply or preferences.mode == PrivacyMode.manual
        )
        executable = preferences.auto_apply and preferences.mode != PrivacyMode.manual

        return ProtectionPlan(
            mode=preferences.mode,
            recommended_action=recommended_action,
            allowed_categories=sorted(allowed, key=lambda c: c.value),
            blocked_categories=blocked,
            unknown_categories=sorted(set(unknown_categories), key=lambda c: c.value),
            requires_user_confirmation=requires_confirmation,
            executable=executable,
        )

    @staticmethod
    def _recommend_action(
        mode: PrivacyMode,
        allowed: set[CookieCategory],
        blocked: list[CookieCategory],
        unknown_categories: list[CookieCategory],
    ) -> ConsentAction:
        if mode == PrivacyMode.manual:
            return ConsentAction.no_action
        if unknown_categories:
            return ConsentAction.manage_preferences
        if not blocked:
            return ConsentAction.accept_all
        if allowed == {CookieCategory.essential}:
            return ConsentAction.reject_optional
        return ConsentAction.manage_preferences
