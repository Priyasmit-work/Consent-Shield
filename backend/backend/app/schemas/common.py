"""
Common response envelope and enums shared across the API.

The API contract specifies every successful response as:
    { "data": ..., "meta": { "request_id": uuid, "api_version": "v1" } }
and structured 4xx errors (401 unauthenticated, 422 invalid combinations).
"""
from __future__ import annotations

from enum import Enum
from typing import Generic, Optional, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiMeta(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    api_version: str = "v1"


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ApiMeta = Field(default_factory=ApiMeta)


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorDetail
    meta: ApiMeta = Field(default_factory=ApiMeta)


class PrivacyMode(str, Enum):
    strict = "strict"
    balanced = "balanced"
    functional = "functional"
    custom = "custom"
    manual = "manual"


class CookieCategory(str, Enum):
    essential = "essential"
    functional = "functional"
    analytics = "analytics"
    advertising = "advertising"
    social = "social"
    unknown = "unknown"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    unknown = "unknown"


class ConsentAction(str, Enum):
    accept_all = "accept_all"
    reject_optional = "reject_optional"
    manage_preferences = "manage_preferences"
    close_banner = "close_banner"
    no_action = "no_action"
    unknown = "unknown"


class ScanStatusValue(str, Enum):
    queued = "queued"
    exploring = "exploring"
    extracting = "extracting"
    analyzing = "analyzing"
    ready = "ready"
    partial = "partial"
    failed = "failed"
    cancelled = "cancelled"


class WorkflowMode(str, Enum):
    reused = "reused"
    explored = "explored"
    repaired = "repaired"


class SourceType(str, Enum):
    cookie_banner = "cookie_banner"
    cookie_policy = "cookie_policy"
    privacy_policy = "privacy_policy"
    network_observation = "network_observation"
    dom = "dom"


ALL_CATEGORIES = list(CookieCategory)
