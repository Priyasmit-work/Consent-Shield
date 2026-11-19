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

    # Browser agent (Playwright + a free/open LLM)
    browser_mode: str = "mock"  # mock | live
    agent_headless: bool = False  # False = you can watch the browser click
    # Use your installed browser, so no Chromium download is needed:
    # "chrome" (Google Chrome) | "msedge" (Microsoft Edge) | "" (Playwright's own Chromium)
    agent_browser_channel: str = "chrome"
    agent_browser_path: str = ""  # optional full path to chrome.exe; overrides the channel
    # After the agent clicks, keep its browser window open this many seconds so you
    # can see the result (0 = close immediately). The API replies right away.
    agent_keep_open_seconds: int = 30
    # Any OpenAI-compatible endpoint works: NVIDIA NIM (Nemotron), OpenRouter,
    # Ollama, Groq... Set agent_provider="anthropic" to use Claude instead.
    agent_provider: str = "openai"  # openai | anthropic
    agent_base_url: str = "https://integrate.api.nvidia.com/v1"
    agent_api_key: str = ""  # empty = no model call, keyword rules are used
    agent_model: str = "nvidia/nemotron-3-nano-30b-a3b"

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