"""
Model adapter (Section 13 / Section 15).

Hides the selected model behind one interface so the rest of the backend
never changes when the model changes. Per the contract, the model must:
  - classify only from supplied evidence
  - return valid data matching the fixed category set
  - use `unknown` when evidence is insufficient
  - never invent vendors, purposes, retention periods, or legal conclusions
  - include confidence and a short reason

MODEL_MODE=heuristic (default) runs a small keyword-based classifier so
the backend is fully runnable offline/without a model API key. This is a
reference implementation only -- it does not claim to be a trained model,
and every classification is grounded in the literal evidence text that
was passed in, never in outside knowledge about the site.

MODEL_MODE=live sends the same request shape to MODEL_API_URL instead.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import Settings
from app.schemas.common import CookieCategory

CATEGORY_KEYWORDS: dict[CookieCategory, list[str]] = {
    CookieCategory.essential: ["essential", "necessary", "required", "session", "security"],
    CookieCategory.functional: ["functional", "preference", "language", "settings", "remember"],
    CookieCategory.analytics: ["analytics", "measure", "statistics", "usage", "performance"],
    CookieCategory.advertising: ["advertising", "ad ", "ads", "marketing", "retarget", "personalized ad"],
    CookieCategory.social: ["social", "share button", "facebook", "twitter", "linkedin", "youtube embed"],
}


@dataclass
class EvidenceInput:
    text: str
    source_url: str
    heading: str


@dataclass
class ClassificationResult:
    category: CookieCategory
    classification: str  # detected | not_detected | unknown
    confidence: float
    reason: str


class ModelService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def classify_cookie_evidence(
        self,
        evidence: list[EvidenceInput],
        allowed_categories: list[CookieCategory],
    ) -> list[ClassificationResult]:
        if self._settings.model_mode == "live" and self._settings.model_api_url:
            return self._classify_live(evidence, allowed_categories)
        return self._classify_heuristic(evidence, allowed_categories)

    # --- heuristic (default / offline) ---

    def _classify_heuristic(
        self,
        evidence: list[EvidenceInput],
        allowed_categories: list[CookieCategory],
    ) -> list[ClassificationResult]:
        results: list[ClassificationResult] = []
        combined_text = " ".join(e.text.lower() for e in evidence)

        for category in allowed_categories:
            if category == CookieCategory.unknown:
                continue
            keywords = CATEGORY_KEYWORDS.get(category, [])
            hits = [kw for kw in keywords if kw in combined_text]

            if not evidence:
                results.append(
                    ClassificationResult(
                        category=category,
                        classification="unknown",
                        confidence=0.0,
                        reason="No evidence was supplied for this category.",
                    )
                )
            elif hits:
                confidence = min(0.6 + 0.1 * len(hits), 0.95)
                results.append(
                    ClassificationResult(
                        category=category,
                        classification="detected",
                        confidence=round(confidence, 2),
                        reason=f"Evidence text references: {', '.join(hits)}.",
                    )
                )
            else:
                results.append(
                    ClassificationResult(
                        category=category,
                        classification="not_detected",
                        confidence=0.55,
                        reason="No supplied evidence referenced this category.",
                    )
                )
        return results

    # --- live model adapter ---

    def _classify_live(
        self,
        evidence: list[EvidenceInput],
        allowed_categories: list[CookieCategory],
    ) -> list[ClassificationResult]:
        payload = {
            "task": "classify_cookie_evidence",
            "evidence": [
                {"text": e.text, "source_url": e.source_url, "heading": e.heading}
                for e in evidence
            ],
            "allowed_categories": [c.value for c in allowed_categories],
            "output_schema": "CookieRiskClassificationV1",
        }
        headers = {}
        if self._settings.model_api_key:
            headers["Authorization"] = f"Bearer {self._settings.model_api_key}"

        with httpx.Client(timeout=30) as client:
            resp = client.post(self._settings.model_api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("classifications", []):
            try:
                category = CookieCategory(item["category"])
            except (KeyError, ValueError):
                continue
            results.append(
                ClassificationResult(
                    category=category,
                    classification=item.get("classification", "unknown"),
                    confidence=float(item.get("confidence", 0.0)),
                    reason=item.get("reason", ""),
                )
            )
        return results
