import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import Settings
from app.schemas.common import CookieCategory
from app.schemas.scans import EvidenceObject
from app.services.model_service import ModelService
from app.services.privacy_analyzer import PrivacyAnalyzer


def test_analyzer_flags_categories_only_with_evidence():
    analyzer = PrivacyAnalyzer(ModelService(Settings(model_mode="heuristic")))
    evidence = [
        EvidenceObject(
            source_url="https://example.com/privacy",
            source_type="cookie_policy",
            heading="Analytics",
            excerpt="We use analytics cookies to measure usage.",
            confidence=0.9,
        )
    ]
    findings, overall = analyzer.analyze(evidence, list(CookieCategory))

    analytics_finding = next(f for f in findings if f.category == CookieCategory.analytics)
    assert analytics_finding.classification == "detected"
    assert len(analytics_finding.evidence) == 1

    social_finding = next(f for f in findings if f.category == CookieCategory.social)
    assert social_finding.classification != "detected"

    assert overall.tracking_detected is True


def test_analyzer_returns_unknown_with_no_evidence():
    analyzer = PrivacyAnalyzer(ModelService(Settings(model_mode="heuristic")))
    findings, overall = analyzer.analyze([], list(CookieCategory))
    assert all(f.classification == "unknown" for f in findings)
    assert overall.unknown_count == len(findings)
