import { cn } from "@/lib/utils";
import { Settings as SettingsIcon, ArrowLeft, Globe } from "lucide-react";
import type { PrivacyMode } from "@/lib/consentshield/types";

export function ShieldMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" aria-hidden="true" className={cn("size-7", className)}>
      <path
        d="M14 2.5 24 6v8.2c0 5.6-4.1 9.9-10 11.3C8.1 24.1 4 19.8 4 14.2V6l10-3.5Z"
        fill="#183C32"
      />
      <circle cx="14" cy="13.4" r="5.1" fill="#F7F5F0" />
      <circle cx="12" cy="11.6" r="1" fill="#183C32" />
      <circle cx="15.6" cy="13.2" r="1.15" fill="#183C32" />
      <circle cx="12.6" cy="15.6" r="0.9" fill="#A7B7A3" />
    </svg>
  );
}

export function PrivacyModePill({ mode }: { mode: PrivacyMode }) {
  return (
    <span
      title={`Privacy mode: ${mode}. Determines which categories ConsentShield proposes.`}
      className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground"
    >
      <span aria-hidden="true" className="size-1.5 rounded-full bg-sage" />
      {mode}
    </span>
  );
}

export function BrandHeader({
  mode,
  onSettings,
  onBack,
  showBack,
}: {
  mode: PrivacyMode;
  onSettings: () => void;
  onBack?: () => void;
  showBack?: boolean;
}) {
  return (
    <header className="flex items-center justify-between gap-2 border-b border-border bg-surface px-4 py-3">
      <div className="flex min-w-0 items-center gap-2.5">
        {showBack ? (
          <button
            type="button"
            aria-label="Back"
            onClick={onBack}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ArrowLeft aria-hidden="true" className="size-4" />
          </button>
        ) : (
          <ShieldMark />
        )}
        <div className="min-w-0">
          <div className="truncate text-[14px] font-bold tracking-[-0.02em] text-foreground">
            ConsentShield
          </div>
          <div className="truncate text-[11px] text-muted-foreground">
            Privacy protection for the web.
          </div>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        <PrivacyModePill mode={mode} />
        <button
          type="button"
          aria-label="Open settings"
          onClick={onSettings}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <SettingsIcon aria-hidden="true" className="size-4" />
        </button>
      </div>
    </header>
  );
}

export function SiteContext({
  hostname,
  pageTitle,
  status,
  tone = "neutral",
}: {
  hostname: string;
  pageTitle: string;
  status?: string;
  tone?: "neutral" | "warning";
}) {
  return (
    <div className="flex items-center gap-3 border-b border-border bg-background/60 px-4 py-3">
      <div
        aria-hidden="true"
        className="flex size-8 shrink-0 items-center justify-center rounded-[8px] border border-border bg-surface text-muted-foreground"
      >
        <Globe className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] font-semibold text-foreground">{hostname}</div>
        <div className="truncate text-[11px] text-muted-foreground">{pageTitle}</div>
      </div>
      {status ? (
        <span
          className={cn(
            "shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-medium",
            tone === "warning"
              ? "border-warning/30 bg-warning/8 text-warning"
              : "border-border bg-surface text-muted-foreground",
          )}
        >
          {status}
        </span>
      ) : null}
    </div>
  );
}
