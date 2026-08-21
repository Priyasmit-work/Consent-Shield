"""
Supabase client wrapper.

Per Section 12 / Security Requirements: the service-role key and other
secrets must remain in the FastAPI backend only, initialized from
environment variables -- never accepted from the extension or any request
body. If Supabase is not configured (no URL / service key set), callers
fall back to in-memory storage so the backend stays runnable for local
hackathon development.
"""
from __future__ import annotations

from typing import Optional

from app.config import get_settings

_client = None
_client_initialized = False


def get_supabase_client() -> Optional["Client"]:  # noqa: F821
    global _client, _client_initialized
    if _client_initialized:
        return _client

    settings = get_settings()
    _client_initialized = True

    if not settings.supabase_configured:
        _client = None
        return _client

    from supabase import create_client  # imported lazily; optional dependency

    _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client
