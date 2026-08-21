from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.schemas.common import ConsentAction


class ApplyPlanClientContext(BaseModel):
    tab_id: str
    page_url: str
    page_instance_id: str


class ApplyPlanRequest(BaseModel):
    confirmation: bool
    requested_action: ConsentAction
    client_context: ApplyPlanClientContext


class ApplyPlanStatus:
    awaiting_user_confirmation = "awaiting_user_confirmation"
    approved = "approved"
    rejected = "rejected"


class ApplyPlanResponse(BaseModel):
    execution_id: UUID = Field(default_factory=uuid4)
    status: str  # awaiting_user_confirmation | approved | rejected
    action: ConsentAction
    message: Optional[str] = None
    allowed_locators: Optional[List[str]] = None
    blocked_actions: Optional[List[str]] = None
    expires_at: datetime


def default_expiry(ttl_seconds: int) -> datetime:
    from datetime import timedelta

    return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
