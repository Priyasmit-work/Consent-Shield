/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the ConsentShield FastAPI backend, e.g. http://localhost:8000 */
  readonly VITE_API_BASE_URL?: string;
  /**
   * Dev-mode user id sent as the `X-Dev-User-Id` header.
   * Only used while the backend runs with AUTH_MODE=dev (the hackathon default).
   */
  readonly VITE_DEV_USER_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
