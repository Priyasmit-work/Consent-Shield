"""
Shared FastAPI dependencies: authentication and repository/service wiring.

Auth: the API contract requires unauthenticated requests to return 401 and
Supabase rows to be scoped by `auth.uid()`, but neither uploaded document
specifies the concrete token format. To keep the backend runnable and
honest about that gap:
  - AUTH_MODE=supabase_jwt verifies a real Supabase-issued JWT and reads
    the user id from its `sub` claim.
  - AUTH_MODE=dev (default, hackathon-only) accepts a plain
    `X-Dev-User-Id` header so the API is exercisable without a live
    Supabase project. This mode is refused outside ENVIRONMENT=hackathon.
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.repositories.events_repository import EventsRepository
from app.repositories.preferences_repository import PreferencesRepository
from app.repositories.scans_repository import ScansRepository
from app.repositories.supabase_client import get_supabase_client
from app.services.browser_agent import BrowserAgentService
from app.services.model_service import ModelService
from app.services.privacy_analyzer import PrivacyAnalyzer
from app.services.protection_planner import ProtectionPlanner


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str


def require_user(
    authorization: str = Header(default=""),
    x_dev_user_id: str = Header(default="", alias="X-Dev-User-Id"),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if settings.auth_mode == "dev":
        if settings.environment != "hackathon":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="dev auth mode is disabled outside hackathon environment",
            )
        if not x_dev_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Dev-User-Id header",
            )
        return AuthenticatedUser(user_id=x_dev_user_id)

    if settings.auth_mode == "supabase_jwt":
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )
        token = authorization.removeprefix("Bearer ").strip()
        if not settings.supabase_jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Server auth is not configured",
            )
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            ) from exc

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
            )
        return AuthenticatedUser(user_id=user_id)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unsupported auth mode configured on server",
    )


# --- Repositories (singletons; in-memory unless Supabase is configured) ---

_preferences_repo: PreferencesRepository | None = None
_scans_repo: ScansRepository | None = None
_events_repo: EventsRepository | None = None


def get_preferences_repository() -> PreferencesRepository:
    global _preferences_repo
    if _preferences_repo is None:
        _preferences_repo = PreferencesRepository(get_supabase_client())
    return _preferences_repo


def get_scans_repository() -> ScansRepository:
    global _scans_repo
    if _scans_repo is None:
        _scans_repo = ScansRepository(get_supabase_client())
    return _scans_repo


def get_events_repository() -> EventsRepository:
    global _events_repo
    if _events_repo is None:
        _events_repo = EventsRepository(get_supabase_client())
    return _events_repo


# --- Services ---


def get_model_service() -> ModelService:
    return ModelService(get_settings())


def get_privacy_analyzer() -> PrivacyAnalyzer:
    return PrivacyAnalyzer(get_model_service())


def get_protection_planner() -> ProtectionPlanner:
    return ProtectionPlanner()


def get_browser_agent() -> BrowserAgentService:
    return BrowserAgentService(get_settings(), get_privacy_analyzer())
