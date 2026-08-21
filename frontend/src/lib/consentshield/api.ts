import type { CategoryKey, Finding, Recommendation, ScanResult, Settings } from "./types";

/**
 * Single service layer for the extension frontend.
 * Every network call the popup makes lives here, talking to the real
 * ConsentShield FastAPI backend (see /backend in the combined project).
 *
 * Configure the backend location via VITE_API_BASE_URL (defaults to
 * http://localhost:8000) and, while the backend runs in its default
 * AUTH_MODE=dev, a stable per-device id via VITE_DEV_USER_ID -- see
 * .env.example.
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const DEV_USER_ID = import.meta.env.VITE_DEV_USER_ID ?? "demo-user";
const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  status: number | undefined;
  code: string | undefined;
  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function authHeaders(): Record<string, string> {
  // AUTH_MODE=dev (the backend's default, hackathon-only mode) accepts a
  // plain header instead of a real Supabase JWT. Swap this for
  // `Authorization: Bearer <supabase-jwt>` once AUTH_MODE=supabase_jwt.
  return { "X-Dev-User-Id": DEV_USER_ID };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
        ...(init.headers ?? {}),
      },
    });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network request failed",
    );
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const body = await res.json().catch(() => null);

  if (!res.ok) {
    const message = body?.error?.message ?? `Request failed with status ${res.status}`;
    throw new ApiError(message, res.status, body?.error?.code);
  }

  return (body?.data ?? body) as T;
}

/* ------------------------------ Backend DTOs ------------------------------ */
/* These mirror app/schemas/*.py on the backend. */

type BackendScanStatusValue =
  | "queued"
  | "exploring"
  | "extracting"
  | "analyzing"
  | "ready"
  | "partial"
  | "failed"
  | "cancelled";

interface BackendScanAccepted {
  scan_id: string;
  status: BackendScanStatusValue;
  created_at: string;
  poll_after_ms: number;
}

interface BackendEvidence {
  source_url: string;
  source_type: string;
  heading: string;
  excerpt: string;
  locator?: string | null;
  confidence: number;
}

interface BackendCategoryFinding {
  category: CategoryKey;
  classification: "detected" | "not_detected" | "unknown";
  recommendation: "allow" | "block" | "review" | "unknown";
  reason: string;
  evidence: BackendEvidence[];
}

interface BackendProtectionPlan {
  mode: string;
  recommended_action: string;
  allowed_categories: CategoryKey[];
  blocked_categories: CategoryKey[];
  unknown_categories: CategoryKey[];
  requires_user_confirmation: boolean;
  executable: boolean;
}

interface BackendCookiePrivacyResult {
  site: { origin: string; hostname: string; policy_urls: string[] };
  banner: { detected: boolean; actions: unknown[]; default_state: string; dark_pattern_flags: string[] };
  overall: {
    privacy_risk: "low" | "medium" | "high" | "critical" | "unknown";
    tracking_detected: boolean;
    third_party_sharing_detected: boolean;
    unknown_count: number;
    confidence: number;
  };
  categories: BackendCategoryFinding[];
  protection_plan: BackendProtectionPlan;
  limitations: string[];
}

interface BackendScanStatus {
  scan_id: string;
  status: BackendScanStatusValue;
  progress: number;
  current_step: string;
  workflow_mode?: string | null;
  events: { type: string; message: string; created_at: string }[];
  result: BackendCookiePrivacyResult | null;
}

interface BackendPreferences {
  mode: "strict" | "balanced" | "functional" | "custom" | "manual";
  categories: {
    essential: boolean;
    functional: boolean;
    analytics: boolean;
    advertising: boolean;
    social: boolean;
    unknown: boolean;
  };
  auto_apply: boolean;
  require_confirmation_for_unknown: boolean;
  allow_network_observation: boolean;
  save_scan_history: boolean;
  updated_at: string;
}

interface BackendApplyPlanResponse {
  execution_id: string;
  status: "awaiting_user_confirmation" | "approved" | "rejected";
  action: string;
  message?: string | null;
  allowed_locators?: string[] | null;
  blocked_actions?: string[] | null;
  expires_at: string;
}

/* ------------------------------- Mappers ---------------------------------- */

const CATEGORY_LABEL: Record<CategoryKey, string> = {
  essential: "Essential",
  functional: "Functional",
  analytics: "Analytics",
  advertising: "Advertising",
  social: "Social",
  unknown: "Unknown",
};

function toRecommendation(value: BackendCategoryFinding["recommendation"]): Recommendation {
  switch (value) {
    case "allow":
      return "Allow";
    case "block":
      return "Block";
    default:
      return "Review";
  }
}

function toExposure(risk: BackendCookiePrivacyResult["overall"]["privacy_risk"]): ScanResult["exposure"] {
  if (risk === "high" || risk === "critical") return "High";
  if (risk === "medium") return "Moderate";
  return "Low";
}

function formatScannedAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Just now";
  return d.toLocaleString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  });
}

function mapFinding(c: BackendCategoryFinding): Finding {
  const topEvidence = c.evidence[0];
  const base: Finding = {
    key: c.category,
    name: CATEGORY_LABEL[c.category] ?? c.category,
    recommendation: toRecommendation(c.recommendation),
    explanation: c.reason,
    confidence: Math.round((topEvidence?.confidence ?? 0) * 100),
    whyItMatters: c.reason,
  };
  // exactOptionalPropertyTypes: only set these keys when we actually have a
  // value, rather than assigning `undefined` to an optional field.
  if (topEvidence?.excerpt !== undefined) base.evidence = topEvidence.excerpt;
  if (topEvidence !== undefined) {
    base.sourceType = topEvidence.source_type
      .split("_")
      .map((w) => w[0]!.toUpperCase() + w.slice(1))
      .join(" ");
  }
  if (topEvidence?.source_url !== undefined) base.sourceUrl = topEvidence.source_url;
  return base;
}

/** Maps the backend's ScanStatus (once status === "ready"/"partial") to the frontend's ScanResult shape. */
function mapScanStatusToResult(status: BackendScanStatus): ScanResult {
  const result = status.result;
  if (!result) {
    throw new ApiError("Scan finished without a result payload");
  }

  const { overall, protection_plan: plan, categories, banner } = result;

  return {
    site: {
      hostname: result.site.hostname,
      pageTitle: result.site.hostname,
      status: banner.detected ? "Cookie banner detected" : "No cookie banner detected",
    },
    scannedAt: formatScannedAt(status.events[status.events.length - 1]?.created_at ?? new Date().toISOString()),
    workflowStatus:
      status.status === "partial" ? "Partially verified from site evidence." : "Verified from site evidence.",
    confidence: Math.round(overall.confidence * 100),
    exposure: toExposure(overall.privacy_risk),
    exposureNote: overall.tracking_detected
      ? "Optional tracking and third-party sharing were detected."
      : "No optional tracking was detected.",
    metrics: [
      {
        key: "tracking",
        label: "Tracking",
        status: overall.tracking_detected ? "Detected" : "Not detected",
        description: "Cookies that measure how you browse this site were found in the cookie policy.",
      },
      {
        key: "third-parties",
        label: "Third parties",
        status: overall.third_party_sharing_detected ? "Detected" : "Not detected",
        description: "The policy names external companies that receive data from this page.",
      },
      {
        key: "unknown",
        label: "Unknown categories",
        status: String(overall.unknown_count),
        description: "Categories that could not be classified from the available evidence.",
      },
    ],
    findings: categories.map(mapFinding),
    plan: {
      title:
        plan.recommended_action === "reject_optional"
          ? "Reject optional cookies"
          : plan.recommended_action.replace(/_/g, " "),
      summary: "Keep essential cookies available while blocking optional categories this site does not require.",
      allow: plan.allowed_categories.map((c) => CATEGORY_LABEL[c] ?? c),
      block: plan.blocked_categories.map((c) => CATEGORY_LABEL[c] ?? c),
      review: plan.unknown_categories.map((c) => CATEGORY_LABEL[c] ?? c),
    },
    // Extra fields the UI doesn't render directly but api.applyPlan() and
    // screen-routing in index.tsx need.
    _scanId: status.scan_id,
    _targetUrl: result.site.origin,
    _recommendedAction: plan.recommended_action,
    _requiresConfirmation: plan.requires_user_confirmation,
    _bannerDetected: banner.detected,
    _scanStatus: status.status === "partial" ? "partial" : "ready",
  };
}

const PRIVACY_MODE_TO_BACKEND: Record<Settings["mode"], BackendPreferences["mode"]> = {
  Manual: "manual",
  Strict: "strict",
  Balanced: "balanced",
  Functional: "functional",
  Custom: "custom",
};

const PRIVACY_MODE_FROM_BACKEND: Record<BackendPreferences["mode"], Settings["mode"]> = {
  manual: "Manual",
  strict: "Strict",
  balanced: "Balanced",
  functional: "Functional",
  custom: "Custom",
};

function mapPreferencesToSettings(p: BackendPreferences): Settings {
  return {
    mode: PRIVACY_MODE_FROM_BACKEND[p.mode],
    categories: {
      functional: p.categories.functional,
      analytics: p.categories.analytics,
      advertising: p.categories.advertising,
      social: p.categories.social,
      unknown: p.categories.unknown,
    },
    automaticProtection: p.auto_apply,
    confirmUnknown: p.require_confirmation_for_unknown,
  };
}

function mapSettingsToPreferencesRequest(s: Settings) {
  const mode = PRIVACY_MODE_TO_BACKEND[s.mode];
  return {
    mode,
    categories: {
      essential: true,
      functional: s.categories.functional,
      analytics: s.categories.analytics,
      advertising: s.categories.advertising,
      social: s.categories.social,
      // The backend rejects categories.unknown = true outright (unknown
      // categories must never be auto-allowed) -- never send true here.
      unknown: false,
    },
    // The backend rejects auto_apply = true while mode = "manual".
    auto_apply: mode === "manual" ? false : s.automaticProtection,
    require_confirmation_for_unknown: s.confirmUnknown,
    allow_network_observation: true,
    save_scan_history: true,
  };
}

/* -------------------------------- Fallbacks -------------------------------- */

export const defaultSettings: Settings = {
  mode: "Manual",
  categories: {
    functional: true,
    analytics: false,
    advertising: false,
    social: false,
    unknown: false,
  },
  automaticProtection: false,
  confirmUnknown: true,
};

/* --------------------------------- Public API ------------------------------- */

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface ApplyPlanResult {
  status: "awaiting_user_confirmation" | "approved" | "rejected";
  message: string | undefined;
}

export const api = {
  /**
   * Runs a full scan: POST /scans to kick off the async scan workflow, then
   * polls GET /scans/{id} until the backend reaches a terminal status.
   */
  async getScan(url: string): Promise<ScanResult> {
    const accepted = await request<BackendScanAccepted>(`${API_PREFIX}/scans`, {
      method: "POST",
      headers: { "Idempotency-Key": `${DEV_USER_ID}:${url}:${Date.now()}` },
      body: JSON.stringify({
        url,
        scan_mode: "cookie_privacy",
        execution_mode: "manual",
      }),
    });

    const TERMINAL: BackendScanStatusValue[] = ["ready", "partial", "failed", "cancelled"];
    let pollDelay = accepted.poll_after_ms || 1000;
    let attempts = 0;

    while (attempts < 30) {
      const status = await request<BackendScanStatus>(`${API_PREFIX}/scans/${accepted.scan_id}`);
      if (TERMINAL.includes(status.status)) {
        if (status.status === "failed" || status.status === "cancelled") {
          throw new ApiError(`Scan ${status.status} for ${url}`);
        }
        return mapScanStatusToResult(status);
      }
      attempts += 1;
      await wait(pollDelay);
      pollDelay = Math.min(pollDelay * 1.3, 3000);
    }

    throw new ApiError("Scan timed out waiting for a result");
  },

  async applyPlan(
    scan: ScanResult,
    requestedAction: string,
  ): Promise<ApplyPlanResult> {
    const scanId = scan._scanId;
    const targetUrl = scan._targetUrl;
    if (!scanId || !targetUrl) {
      throw new ApiError("This scan result has no backend scan id to apply a plan for");
    }

    const response = await request<BackendApplyPlanResponse>(`${API_PREFIX}/scans/${scanId}/apply-plan`, {
      method: "POST",
      body: JSON.stringify({
        confirmation: true,
        requested_action: requestedAction,
        client_context: {
          tab_id: "web-preview-tab",
          page_url: targetUrl,
          page_instance_id: `${scanId}-instance`,
        },
      }),
    });

    return { status: response.status, message: response.message ?? undefined };
  },

  async getSettings(): Promise<Settings> {
    const prefs = await request<BackendPreferences>(`${API_PREFIX}/me/preferences`);
    return mapPreferencesToSettings(prefs);
  },

  async saveSettings(next: Settings): Promise<Settings> {
    const prefs = await request<BackendPreferences>(`${API_PREFIX}/me/preferences`, {
      method: "PUT",
      body: JSON.stringify(mapSettingsToPreferencesRequest(next)),
    });
    return mapPreferencesToSettings(prefs);
  },
};
