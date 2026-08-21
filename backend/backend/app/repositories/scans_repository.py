from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID


@dataclass
class ScanRecord:
    id: UUID
    user_id: str
    origin: str
    target_url: str
    scan_mode: str
    execution_mode: str
    status: str
    created_at: datetime
    workflow_mode: Optional[str] = None
    progress: int = 0
    current_step: str = ""
    activity_log: list = field(default_factory=list)  # internal workflow events
    result: Optional[dict] = None
    limitations: list = field(default_factory=list)
    completed_at: Optional[datetime] = None


@dataclass
class ExecutionPlanRecord:
    id: UUID
    scan_id: UUID
    user_id: str
    hostname: str
    page_instance_id: str
    action: str
    status: str
    expires_at: datetime
    allowed_locators: list = field(default_factory=list)
    blocked_actions: list = field(default_factory=list)


def site_key_for(url: str) -> str:
    """Hostname is used as the site key for GET /sites/{site_key}/latest."""
    return urlparse(url).hostname or url


class ScansRepository:
    """
    Backed by the `scans` / `execution_plans` tables when Supabase is
    configured; in-memory otherwise. The Supabase write path is included
    for completeness but the in-memory path is what the hackathon demo
    exercises by default (see supabase_client.py).
    """

    SCANS_TABLE = "scans"
    PLANS_TABLE = "execution_plans"

    def __init__(self, supabase_client) -> None:
        self._client = supabase_client
        self._scans: dict[UUID, ScanRecord] = {}
        self._idempotency: dict[tuple[str, str], UUID] = {}
        self._plans: dict[UUID, ExecutionPlanRecord] = {}

    # --- Scans ---

    def create(self, record: ScanRecord, idempotency_key: Optional[str]) -> ScanRecord:
        self._scans[record.id] = record
        if idempotency_key:
            self._idempotency[(record.user_id, idempotency_key)] = record.id
        if self._client is not None:
            self._client.table(self.SCANS_TABLE).insert(self._to_row(record)).execute()
        return record

    def find_by_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Optional[ScanRecord]:
        scan_id = self._idempotency.get((user_id, idempotency_key))
        return self._scans.get(scan_id) if scan_id else None

    def get(self, scan_id: UUID, user_id: str) -> Optional[ScanRecord]:
        record = self._scans.get(scan_id)
        if record and record.user_id == user_id:
            return record
        return None

    def save(self, record: ScanRecord) -> ScanRecord:
        self._scans[record.id] = record
        if self._client is not None:
            self._client.table(self.SCANS_TABLE).update(
                self._to_row(record)
            ).eq("id", str(record.id)).execute()
        return record

    def delete(self, scan_id: UUID, user_id: str) -> bool:
        record = self.get(scan_id, user_id)
        if not record:
            return False
        del self._scans[scan_id]
        self._idempotency = {
            k: v for k, v in self._idempotency.items() if v != scan_id
        }
        self._plans = {
            k: v for k, v in self._plans.items() if v.scan_id != scan_id
        }
        if self._client is not None:
            self._client.table(self.SCANS_TABLE).delete().eq(
                "id", str(scan_id)
            ).execute()
        return True

    def latest_for_site(self, site_key: str, user_id: str) -> Optional[ScanRecord]:
        candidates = [
            r
            for r in self._scans.values()
            if r.user_id == user_id and site_key_for(r.target_url) == site_key
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.created_at)

    # --- Execution plans ---

    def save_plan(self, plan: ExecutionPlanRecord) -> ExecutionPlanRecord:
        self._plans[plan.id] = plan
        return plan

    def get_plan(self, execution_id: UUID) -> Optional[ExecutionPlanRecord]:
        return self._plans.get(execution_id)

    @staticmethod
    def _to_row(record: ScanRecord) -> dict:
        return {
            "id": str(record.id),
            "user_id": record.user_id,
            "origin": record.origin,
            "target_url": record.target_url,
            "scan_mode": record.scan_mode,
            "execution_mode": record.execution_mode,
            "status": record.status,
            "workflow_mode": record.workflow_mode,
            "result": record.result,
            "limitations": record.limitations,
            "created_at": record.created_at.isoformat(),
            "completed_at": record.completed_at.isoformat()
            if record.completed_at
            else None,
        }
