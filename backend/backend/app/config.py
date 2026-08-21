"""
Central configuration for the ConsentShield backend.

All values are sourced from environment variables (see .env.example).
No secrets are hardcoded. Nothing here invents product behavior beyond
what the PRD / API contract specify -- these are operational knobs only
(which storage backend to use, mock vs. live adapters, timeouts).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", protected_namespaces=("settings_",)
    )

    api_version: str = "v1"
    environment: str = "hackathon"  # hackathon | production

    # CORS - comma-separated list of allowed origins for the frontend.
    # Defaults cover the Vite dev server and the TanStack Start dev/preview
    # ports used by the ConsentShield frontend.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Auth
    auth_mode: str = "dev"  # dev | supabase_jwt
    supabase_jwt_secret: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Browser agent (webcmd)
    webcmd_mode: str = "mock"  # mock | live
    webcmd_api_key: str = ""

    # Model adapter
    model_mode: str = "heuristic"  # heuristic | live
    model_api_url: str = ""
    model_api_key: str = ""

    # Scan behavior
    scan_poll_after_ms: int = 1000
    scan_max_pages: int = 5
    scan_timeout_seconds: int = 45
    execution_plan_ttl_seconds: int = 300

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
