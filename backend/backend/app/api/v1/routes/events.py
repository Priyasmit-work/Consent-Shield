from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import AuthenticatedUser, get_events_repository, get_scans_repository, require_user
from app.repositories.events_repository import EventsRepository
from app.repositories.scans_repository import ScansRepository
from app.schemas.common import ApiResponse
from app.schemas.events import BrowserEvent, BrowserEventAccepted

router = APIRouter(tags=["events"])


@router.post(
    "/scans/{scan_id}/events",
    response_model=ApiResponse[BrowserEventAccepted],
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_event(
    scan_id: UUID,
    body: BrowserEvent,
    user: AuthenticatedUser = Depends(require_user),
    scans_repo: ScansRepository = Depends(get_scans_repository),
    events_repo: EventsRepository = Depends(get_events_repository),
):
    record = scans_repo.get(scan_id, user.user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    event_record = events_repo.add(
        scan_id=scan_id,
        user_id=user.user_id,
        event_type=body.event_type,
        hostname=body.page.hostname,
        payload=body.payload.model_dump(exclude_none=True),
        occurred_at=body.occurred_at,
    )
    return ApiResponse(data=BrowserEventAccepted(accepted=True, event_id=event_record.id))
