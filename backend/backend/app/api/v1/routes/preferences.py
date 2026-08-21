from fastapi import APIRouter, Depends

from app.dependencies import AuthenticatedUser, get_preferences_repository, require_user
from app.repositories.preferences_repository import PreferencesRepository
from app.schemas.common import ApiResponse
from app.schemas.preferences import Preferences, PreferencesUpdateRequest

router = APIRouter(tags=["preferences"])


@router.get("/me/preferences", response_model=ApiResponse[Preferences])
async def get_preferences(
    user: AuthenticatedUser = Depends(require_user),
    repo: PreferencesRepository = Depends(get_preferences_repository),
):
    prefs = repo.get(user.user_id)
    return ApiResponse(data=prefs)


@router.put("/me/preferences", response_model=ApiResponse[Preferences])
async def put_preferences(
    body: PreferencesUpdateRequest,
    user: AuthenticatedUser = Depends(require_user),
    repo: PreferencesRepository = Depends(get_preferences_repository),
):
    # Pydantic validators on PreferencesUpdateRequest already reject
    # contradictory combinations with a 422 before we reach here.
    from datetime import datetime, timezone

    prefs = Preferences(
        mode=body.mode,
        categories=body.categories,
        auto_apply=body.auto_apply,
        require_confirmation_for_unknown=body.require_confirmation_for_unknown,
        allow_network_observation=body.allow_network_observation,
        save_scan_history=body.save_scan_history,
        updated_at=datetime.now(timezone.utc),
    )
    saved = repo.put(user.user_id, prefs)
    return ApiResponse(data=saved)
