"""
Apply protection plan route.

Per Section 8, the authoritative rule for this endpoint is stated
explicitly: "This endpoint must not directly click a consent button by
default. It returns a validated, extension-executable plan only when the
user has explicitly enabled automatic protection." That single rule
drives the branch below:

  - preferences.auto_apply is False (the default) -> always respond
    `awaiting_user_confirmation`, regardless of the client's
    `confirmation` flag, since the endpoint must never hand back an
    executable plan by default.
  - the client explicitly declines (`confirmation: false`) -> `rejected`.
  - preferences.auto_apply is True -> `approved`, with a short-lived,
    hostname- and page-instance-bound plan.

The plan is always bound to the scan's origin hostname; a client_context
whose page_url hostname does not match is rejected as a mismatch rather
than silently accepted, consistent with "reject stale or mismatched
action plans" (Section 6) and "must reject stale plans" (Section 8).
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.dependencies import AuthenticatedUser, get_preferences_repository, get_scans_repository, require_user
from app.repositories.preferences_repository import PreferencesRepository
from app.repositories.scans_repository import ExecutionPlanRecord, ScansRepository
from app.schemas.common import ApiResponse
from app.schemas.execution import ApplyPlanRequest, ApplyPlanResponse, ApplyPlanStatus, default_expiry

router = APIRouter(tags=["execution"])


@router.post("/scans/{scan_id}/apply-plan", response_model=ApiResponse[ApplyPlanResponse])
async def apply_plan(
    scan_id: UUID,
    body: ApplyPlanRequest,
    user: AuthenticatedUser = Depends(require_user),
    settings: Settings = Depends(get_settings),
    repo: ScansRepository = Depends(get_scans_repository),
    prefs_repo: PreferencesRepository = Depends(get_preferences_repository),
):
    record = repo.get(scan_id, user.user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    if record.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A protection plan can only be applied for a scan in 'ready' status",
        )

    scan_hostname = urlparse(record.target_url).hostname
    requested_hostname = urlparse(body.client_context.page_url).hostname
    if scan_hostname != requested_hostname:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Hostname mismatch: plan was generated for '{scan_hostname}' "
                f"but request is for '{requested_hostname}'"
            ),
        )

    if not body.confirmation:
        return ApiResponse(
            data=ApplyPlanResponse(
                status=ApplyPlanStatus.rejected,
                action=body.requested_action,
                message="The user did not confirm this action.",
                expires_at=default_expiry(settings.execution_plan_ttl_seconds),
            )
        )

    preferences = prefs_repo.get(user.user_id)
    execution_id = uuid4()
    expires_at = default_expiry(settings.execution_plan_ttl_seconds)

    if not preferences.auto_apply:
        return ApiResponse(
            data=ApplyPlanResponse(
                execution_id=execution_id,
                status=ApplyPlanStatus.awaiting_user_confirmation,
                action=body.requested_action,
                message="Confirm in the extension before changing cookie consent.",
                expires_at=expires_at,
            )
        )

    plan_result = record.result or {}
    protection_plan = plan_result.get("protection_plan", {})
    banner = plan_result.get("banner", {})
    matching_action = next(
        (
            a
            for a in banner.get("actions", [])
            if a.get("action") == body.requested_action.value
        ),
        None,
    )
    allowed_locators = [matching_action["locator"]] if matching_action else []
    all_actions = {a.get("action") for a in banner.get("actions", [])}
    blocked_actions = sorted(all_actions - {body.requested_action.value})

    plan_record = ExecutionPlanRecord(
        id=execution_id,
        scan_id=scan_id,
        user_id=user.user_id,
        hostname=scan_hostname or "",
        page_instance_id=body.client_context.page_instance_id,
        action=body.requested_action.value,
        status="approved",
        expires_at=expires_at,
        allowed_locators=allowed_locators,
        blocked_actions=list(blocked_actions),
    )
    repo.save_plan(plan_record)

    return ApiResponse(
        data=ApplyPlanResponse(
            execution_id=execution_id,
            status=ApplyPlanStatus.approved,
            action=body.requested_action,
            allowed_locators=allowed_locators,
            blocked_actions=list(blocked_actions),
            expires_at=expires_at,
        )
    )
