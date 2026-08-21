from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class EventPage(BaseModel):
    url: str
    hostname: str
    page_instance_id: str


class EventPayload(BaseModel):
    action: Optional[str] = None
    success: Optional[bool] = None
    message: Optional[str] = None

    # FR-4 / Section 18: never accept cookies, authorization headers, full
    # DOM snapshots, form values, typed passwords, or arbitrary page content
    # through this endpoint. We enforce this by only exposing these three
    # narrow fields -- extra fields are rejected below.
    model_config = {"extra": "forbid"}


class BrowserEvent(BaseModel):
    event_type: str  # banner_detected | action_clicked | navigation | execution_result | error
    occurred_at: datetime
    page: EventPage
    payload: EventPayload = Field(default_factory=EventPayload)

    @model_validator(mode="after")
    def validate_event_type(self) -> "BrowserEvent":
        allowed = {
            "banner_detected",
            "action_clicked",
            "navigation",
            "execution_result",
            "error",
        }
        if self.event_type not in allowed:
            raise ValueError(f"event_type must be one of {sorted(allowed)}")
        return self


class BrowserEventAccepted(BaseModel):
    accepted: bool = True
    event_id: UUID = Field(default_factory=uuid4)
