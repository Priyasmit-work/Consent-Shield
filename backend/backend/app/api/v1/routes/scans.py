from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.dependencies import (
    AuthenticatedUser,
    get_browser_agent,
    get_preferences_repository,
    get_scans_repository,
    get_events_repository,
    require_user,
)
from app.repositories.preferences_repository import PreferencesRepository
from app.repositories.scans_repository import ScanRecord, ScansRepository, site_key_for
from app.repositories.events_repository import EventsRepository
from app.schemas.common import ApiResponse, ScanStatusValue
from app.schemas.scans import ScanAccepted, ScanEventEntry, ScanRequest, ScanStatus
from app.services.browser_agent import BrowserAgentService

router = APIRouter(tags=["scans"])


@router.post("/scans", response_model=ApiResponse[ScanAccepted], status_code=status.HTTP_202_ACCEPTED)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    user: AuthenticatedUser = Depends(require_user),
    settings: Settings = Depends(get_settings),
    repo: ScansRepository = Depends(get_scans_repository),
    prefs_repo: PreferencesRepository = Depends(get_preferences_repository),
    agent: BrowserAgentService = Depends(get_browser_agent),
):
    existing = repo.find_by_idempotency_key(user.user_id, idempotency_key)
    if existing:
        return ApiResponse(
            data=ScanAccepted(
                scan_id=existing.id,
                status=ScanStatusValue(existing.status),
                created_at=existing.created_at,
                poll_after_ms=settings.scan_poll_after_ms,
            )
        )

    from app.schemas.scans import new_scan_id
    from urllib.parse import urlparse

    scan_id = new_scan_id()
    origin_parts = urlparse(request.url)
    record = ScanRecord(
        id=scan_id,
        user_id=user.user_id,
        origin=f"{origin_parts.scheme}://{origin_parts.hostname}",
        target_url=request.url,
        scan_mode=request.scan_mode,
        execution_mode=request.execution_mode,
        status=ScanStatusValue.queued.value,
        created_at=datetime.now(timezone.utc),
    )
    repo.create(record, idempotency_key)

    preferences = prefs_repo.get(user.user_id)
    background_tasks.add_task(agent.run_scan, record, request, preferences, repo)

    return ApiResponse(
        data=ScanAccepted(
            scan_id=scan_id,
            status=ScanStatusValue.queued,
            created_at=record.created_at,
            poll_after_ms=settings.scan_poll_after_ms,
        )
    )


@router.get("/scans/{scan_id}", response_model=ApiResponse[ScanStatus])
async def get_scan(
    scan_id: UUID,
    user: AuthenticatedUser = Depends(require_user),
    repo: ScansRepository = Depends(get_scans_repository),
):
    record = repo.get(scan_id, user.user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    status_value = ScanStatus(
        scan_id=record.id,
        status=ScanStatusValue(record.status),
        progress=record.progress,
        current_step=record.current_step,
        workflow_mode=record.workflow_mode,
        events=[ScanEventEntry(**e) for e in record.activity_log],
        result=record.result,
    )
    return ApiResponse(data=status_value)


@router.delete("/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: UUID,
    user: AuthenticatedUser = Depends(require_user),
    repo: ScansRepository = Depends(get_scans_repository),
    events_repo: EventsRepository = Depends(get_events_repository),
):
    deleted = repo.delete(scan_id, user.user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    events_repo.delete_for_scan(scan_id)
    return None


@router.get("/sites/{site_key}/latest", response_model=ApiResponse[ScanStatus])
async def get_latest_for_site(
    site_key: str,
    user: AuthenticatedUser = Depends(require_user),
    repo: ScansRepository = Depends(get_scans_repository),
):
    record = repo.latest_for_site(site_key, user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scan found for this site",
        )
    status_value = ScanStatus(
        scan_id=record.id,
        status=ScanStatusValue(record.status),
        progress=record.progress,
        current_step=record.current_step,
        workflow_mode=record.workflow_mode,
        events=[ScanEventEntry(**e) for e in record.activity_log],
        result=record.result,
    )
    return ApiResponse(data=status_value)
