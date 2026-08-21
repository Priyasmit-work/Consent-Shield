export type Recommendation = "Allow" | "Review" | "Block";

export type CategoryKey =
  | "essential"
  | "functional"
  | "analytics"
  | "advertising"
  | "social"
  | "unknown";

export interface Finding {
  key: CategoryKey;
  name: string;
  recommendation: Recommendation;
  explanation: string;
  confidence: number;
  evidence?: string;
  sourceType?: string;
  sourceUrl?: string;
  whyItMatters: string;
}

export interface SiteContextData {
  hostname: string;
  pageTitle: string;
  status: string;
}

export interface ScanResult {
  site: SiteContextData;
  scannedAt: string;
  workflowStatus: string;
  confidence: number;
  exposure: "Low" | "Moderate" | "High";
  exposureNote: string;
  metrics: { key: string; label: string; status: string; description: string }[];
  findings: Finding[];
  plan: {
    title: string;
    summary: string;
    allow: string[];
    block: string[];
    review: string[];
  };
  /**
   * Internal bookkeeping populated by the real API client so that a later
   * apply-plan call can be tied back to the backend scan that produced this
   * result. Not rendered by any component -- optional so mock data (or
   * other callers) can omit it.
   */
  _scanId?: string;
  _targetUrl?: string;
  _recommendedAction?: string;
  _requiresConfirmation?: boolean;
  _bannerDetected?: boolean;
  _scanStatus?: "ready" | "partial";
}

export type PrivacyMode = "Manual" | "Strict" | "Balanced" | "Functional" | "Custom";

export interface Settings {
  mode: PrivacyMode;
  categories: Record<Exclude<CategoryKey, "essential">, boolean>;
  automaticProtection: boolean;
  confirmUnknown: boolean;
}
