"""
Privacy analyzer.

Turns collected evidence into CategoryFinding objects. Per the contract:
  - "A category should be flagged only when the system can provide
     supporting evidence from the source."
  - Unknown categories are never automatically allowed (enforced later
    by the protection planner, not here).
  - Every detected category includes a recommendation and evidence, or
    is marked unknown.
"""
from __future__ import annotations

from app.schemas.common import CookieCategory, RiskLevel
from app.schemas.scans import CategoryFinding, EvidenceObject, OverallFindings
from app.services.model_service import CATEGORY_KEYWORDS, EvidenceInput, ModelService

RISK_WEIGHT = {
    CookieCategory.advertising: 3,
    CookieCategory.social: 2,
    CookieCategory.analytics: 2,
    CookieCategory.functional: 1,
    CookieCategory.essential: 0,
}


class PrivacyAnalyzer:
    def __init__(self, model_service: ModelService) -> None:
        self._model_service = model_service

    def analyze(
        self,
        evidence: list[EvidenceObject],
        allowed_categories: list[CookieCategory],
    ) -> tuple[list[CategoryFinding], OverallFindings]:
        model_inputs = [
            EvidenceInput(text=e.excerpt, source_url=e.source_url, heading=e.heading)
            for e in evidence
        ]
        classifications = self._model_service.classify_cookie_evidence(
            model_inputs, allowed_categories
        )

        findings: list[CategoryFinding] = []
        risk_score = 0
        detected_count = 0
        unknown_count = 0
        tracking_detected = False
        third_party_sharing_detected = False

        for result in classifications:
            category_evidence = self._evidence_for_category(evidence, result.category)

            if result.classification == "unknown" or (
                result.classification == "detected" and not category_evidence
            ):
                classification = "unknown"
                recommendation = "unknown"
                unknown_count += 1
            elif result.classification == "detected":
                classification = "detected"
                recommendation = "block" if result.category != CookieCategory.essential else "allow"
                detected_count += 1
                risk_score += RISK_WEIGHT.get(result.category, 1)
                if result.category == CookieCategory.analytics:
                    tracking_detected = True
                if result.category in (CookieCategory.advertising, CookieCategory.social):
                    third_party_sharing_detected = True
            else:
                classification = "not_detected"
                recommendation = "allow" if result.category == CookieCategory.essential else "block"

            findings.append(
                CategoryFinding(
                    category=result.category,
                    classification=classification,
                    recommendation=recommendation,
                    reason=result.reason,
                    evidence=category_evidence,
                )
            )

        overall = OverallFindings(
            privacy_risk=self._risk_level(risk_score),
            tracking_detected=tracking_detected,
            third_party_sharing_detected=third_party_sharing_detected,
            unknown_count=unknown_count,
            confidence=self._overall_confidence(classifications),
        )
        return findings, overall

    @staticmethod
    def _evidence_for_category(
        evidence: list[EvidenceObject], category: CookieCategory
    ) -> list[EvidenceObject]:
        keywords = CATEGORY_KEYWORDS.get(category, [])
        return [e for e in evidence if any(kw in e.excerpt.lower() for kw in keywords)]

    @staticmethod
    def _risk_level(score: int) -> RiskLevel:
        if score == 0:
            return RiskLevel.low
        if score <= 2:
            return RiskLevel.medium
        if score <= 4:
            return RiskLevel.high
        return RiskLevel.critical

    @staticmethod
    def _overall_confidence(classifications) -> float:
        if not classifications:
            return 0.0
        return round(sum(c.confidence for c in classifications) / len(classifications), 2)
