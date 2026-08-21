from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class EventRecord:
    id: UUID
    scan_id: UUID
    user_id: str
    event_type: str
    hostname: str
    payload: dict
    created_at: datetime


class EventsRepository:
    """Backed by `scan_events`. Stores only the sanitized fields defined
    in BrowserEvent -- never raw DOM, cookies, or auth headers (enforced
    upstream by the strict Pydantic schema, not by this repository)."""

    TABLE = "scan_events"

    def __init__(self, supabase_client) -> None:
        self._client = supabase_client
        self._events: list[EventRecord] = []

    def add(
        self,
        scan_id: UUID,
        user_id: str,
        event_type: str,
        hostname: str,
        payload: dict,
        occurred_at: datetime,
    ) -> EventRecord:
        record = EventRecord(
            id=uuid4(),
            scan_id=scan_id,
            user_id=user_id,
            event_type=event_type,
            hostname=hostname,
            payload=payload,
            created_at=occurred_at,
        )
        self._events.append(record)
        if self._client is not None:
            self._client.table(self.TABLE).insert(
                {
                    "id": str(record.id),
                    "scan_id": str(scan_id),
                    "user_id": user_id,
                    "event_type": event_type,
                    "hostname": hostname,
                    "payload": payload,
                    "created_at": occurred_at.isoformat(),
                }
            ).execute()
        return record

    def delete_for_scan(self, scan_id: UUID) -> None:
        self._events = [e for e in self._events if e.scan_id != scan_id]
        if self._client is not None:
            self._client.table(self.TABLE).delete().eq(
                "scan_id", str(scan_id)
            ).execute()
