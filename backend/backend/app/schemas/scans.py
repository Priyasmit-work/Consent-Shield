from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import (
    ConsentAction,
    CookieCategory,
    PrivacyMode,
    RiskLevel,
    ScanStatusValue,
    SourceType,
    WorkflowMode,
)

SUPPORTED_SCHEMES = ("http://", "https://")


class ClientContext(BaseModel):
    tab_id: Optional[str] = None
    page_title: Optional[str] = None
    cookie_banner_detected: Optional[bool] = None
    visible_banner_text: Optional[str] = None
    language: Optional[str] = None

    @field_validator("tab_id")
    @classmethod
    def tab_id_must_be_opaque(cls, v: Optional[str]) -> Optional[str]:
        # FR-4 / Section 6: tab_id must not contain an email, username, or
        # raw cookie -- reject anything that looks like one.
        if v and ("@" in v or len(v) > 128):
            raise ValueError(
                "tab_id must be an opaque identifier, not an email or raw value"
            )
        return v


class ScanOptions(BaseModel):
    observe_network_requests: bool = True
    follow_policy_links: bool = True
    max_pages: int = 5
    timeout_seconds: int = 45


class ScanRequest(BaseModel):
    url: str
    scan_mode: str = "cookie_privacy"
    execution_mode: str = "manual"  # manual | assisted | automatic
    focus: List[str] = Field(default_factory=list)
    client_context: Optional[ClientContext] = None
    options: ScanOptions = Field(default_factory=ScanOptions)

    @field_validator("url")
    @classmethod
    def url_must_be_supported_protocol(cls, v: str) -> str:
        if not v.lower().startswith(SUPPORTED_SCHEMES):
            raise ValueError(
                "Unsupported protocol; only http:// and https:// URLs are accepted"
            )
        return v


class ScanAccepted(BaseModel):
    scan_id: UUID
    status: ScanStatusValue = ScanStatusValue.queued
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    poll_after_ms: int = 1000


class ScanEventEntry(BaseModel):
    type: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceObject(BaseModel):
    source_url: str
    source_type: SourceType
    heading: str
    excerpt: str
    locator: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class BannerAction(BaseModel):
    action: ConsentAction
    label: str
    locator: str
    sensitivity: str  # low | medium | high


class BannerFindings(BaseModel):
    detected: bool
    actions: List[BannerAction] = Field(default_factory=list)
    default_state: str = "unknown"
    dark_pattern_flags: List[str] = Field(default_factory=list)


class OverallFindings(BaseModel):
    privacy_risk: RiskLevel
    tracking_detected: bool
    third_party_sharing_detected: bool
    unknown_count: int
    confidence: float = Field(ge=0.0, le=1.0)


class CategoryFinding(BaseModel):
    category: CookieCategory
    classification: str  # detected | not_detected | unknown
    recommendation: str  # allow | block | review | unknown
    reason: str
    evidence: List[EvidenceObject] = Field(default_factory=list)


class ProtectionPlan(BaseModel):
    mode: PrivacyMode
    recommended_action: ConsentAction
    allowed_categories: List[CookieCategory]
    blocked_categories: List[CookieCategory]
    unknown_categories: List[CookieCategory]
    requires_user_confirmation: bool
    executable: bool


class SiteInfo(BaseModel):
    origin: str
    hostname: str
    policy_urls: List[str] = Field(default_factory=list)


class CookiePrivacyResult(BaseModel):
    site: SiteInfo
    banner: BannerFindings
    overall: OverallFindings
    categories: List[CategoryFinding]
    protection_plan: ProtectionPlan
    limitations: List[str] = Field(default_factory=list)


class ScanStatus(BaseModel):
    scan_id: UUID
    status: ScanStatusValue
    progress: int = 0
    current_step: str = ""
    workflow_mode: Optional[WorkflowMode] = None
    events: List[ScanEventEntry] = Field(default_factory=list)
    result: Optional[CookiePrivacyResult] = None


def new_scan_id() -> UUID:
    return uuid4()
