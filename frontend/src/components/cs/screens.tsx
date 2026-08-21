import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  CircleHelp,
  FileSearch,
  Radar,
  ScanLine,
  ShieldCheck,
  Share2,
  Trash2,
  Ban,
} from "lucide-react";
import {
  Button,
  Card,
  ConfidenceBadge,
  EvidenceTag,
  RecommendationTag,
  SectionTitle,
  SourceLink,
  ToggleRow,
} from "./primitives";
import type { Finding, ScanResult, Settings, PrivacyMode } from "@/lib/consentshield/types";

/* ------------------------------ Scan intro ------------------------------- */

export function ScanIntro({
  onScan,
  busy,
  url,
  onUrlChange,
  error,
}: {
  onScan: () => void;
  busy?: boolean;
  url?: string;
  onUrlChange?: (url: string) => void;
  error?: string | null;
}) {
  return (
    <div className="cs-rise px-4 py-5">
      <h2 className="text-[21px] font-semibold leading-tight tracking-[-0.02em] text-foreground">
        Privacy scan
      </h2>
      <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
        ConsentShield will read this page&rsquo;s consent controls and published cookie evidence
        before recommending anything.
      </p>

      {onUrlChange ? (
        <div className="mt-3">
          <label htmlFor="cs-scan-url" className="sr-only">
            Site URL to scan
          </label>
          <input
            id="cs-scan-url"
            type="url"
            inputMode="url"
            placeholder="https://example.com"
            value={url ?? ""}
            onChange={(e) => onUrlChange(e.target.value)}
            disabled={busy}
            className="w-full rounded-[10px] border border-border bg-surface px-3 py-2 text-[13px] text-foreground outline-none focus:border-forest disabled:opacity-60"
          />
          {error ? <p className="mt-1.5 text-[11px] text-critical">{error}</p> : null}
        </div>
      ) : null}

      <Card className="mt-4 divide-y divide-border">
        {[
          { icon: <ScanLine className="size-4" />, t: "Detect", d: "Find the consent banner and its controls." },
          { icon: <FileSearch className="size-4" />, t: "Analyze", d: "Read the cookie and privacy policies." },
          { icon: <ShieldCheck className="size-4" />, t: "Recommend", d: "Propose a choice you approve first." },
        ].map((s) => (
          <div key={s.t} className="flex items-start gap-3 px-3 py-2.5">
            <span aria-hidden="true" className="mt-0.5 text-forest">
              {s.icon}
            </span>
            <div>
              <div className="text-[13px] font-medium text-foreground">{s.t}</div>
              <div className="text-[11px] leading-relaxed text-muted-foreground">{s.d}</div>
            </div>
          </div>
        ))}
      </Card>

      <div className="mt-4">
        <Button onClick={onScan} disabled={busy}>
          <Radar aria-hidden="true" className="size-4" />
          {busy ? "Scanning\u2026" : "Scan privacy"}
        </Button>
        <p className="mt-2 text-center text-[11px] leading-relaxed text-muted-foreground">
          Read-only analysis. Nothing will be changed yet.
        </p>
      </div>
    </div>
  );
}

/* ----------------------------- Scan progress ----------------------------- */

const SCAN_STEPS = [
  "Detecting consent controls",
  "Finding cookie policy",
  "Reading privacy evidence",
  "Preparing recommendation",
];

const SCAN_LOG = [
  "Cookie banner detected",
  "Privacy Policy found",
  "Analyzing analytics practices",
];

export function ScanProgress({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (step >= SCAN_STEPS.length) {
      const t = setTimeout(onDone, 500);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setStep((s) => s + 1), 900);
    return () => clearTimeout(t);
  }, [step, onDone]);

  return (
    <div className="cs-rise px-4 py-5">
      <div className="flex items-center gap-3">
        <span className="relative flex size-3 items-center justify-center" aria-hidden="true">
          <span className="cs-pulse absolute size-3 rounded-full bg-sage" />
          <span className="size-2 rounded-full bg-forest" />
        </span>
        <h2 className="text-[20px] font-semibold tracking-[-0.02em] text-foreground">
          Inspecting this site
        </h2>
      </div>
      <p className="mt-1.5 text-[13px] text-muted-foreground">
        Read-only. No consent action is being taken.
      </p>

      <ol className="mt-4 space-y-2" aria-live="polite">
        {SCAN_STEPS.map((label, i) => {
          const done = i < step;
          const active = i === step;
          return (
            <li
              key={label}
              className={cn(
                "flex items-center gap-2.5 rounded-[10px] border px-3 py-2.5 text-[13px] transition-colors",
                active
                  ? "border-forest/25 bg-forest/6 text-foreground"
                  : done
                    ? "border-border bg-surface text-muted-foreground"
                    : "border-transparent bg-transparent text-muted-foreground/70",
              )}
            >
              <span
                aria-hidden="true"
                className={cn(
                  "flex size-4 shrink-0 items-center justify-center rounded-full border",
                  done ? "border-positive bg-positive text-[#FFFEFA]" : "border-border",
                )}
              >
                {done ? <CheckCircle2 className="size-3" /> : null}
              </span>
              <span className="font-medium">{label}</span>
              {active ? <span className="ml-auto text-[11px] text-muted-foreground">Working</span> : null}
            </li>
          );
        })}
      </ol>

      <div className="mt-4 rounded-[12px] border border-border bg-background/60 px-3 py-2.5">
        <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          Activity
        </div>
        <ul className="space-y-1">
          {SCAN_LOG.slice(0, Math.max(1, step)).map((l) => (
            <li key={l} className="flex items-center gap-2 text-[12px] text-muted-foreground">
              <Activity aria-hidden="true" className="size-3 text-sage" />
              {l}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/* ------------------------------- Risk result ----------------------------- */

const metricIcon: Record<string, React.ReactNode> = {
  tracking: <Activity className="size-4" />,
  "third-parties": <Share2 className="size-4" />,
  unknown: <CircleHelp className="size-4" />,
};

export function RiskOverview({ scan }: { scan: ScanResult }) {
  const level = scan.exposure;
  const fill = level === "High" ? "88%" : level === "Moderate" ? "56%" : "22%";
  const tone =
    level === "High" ? "text-critical" : level === "Moderate" ? "text-warning" : "text-positive";
  const bar =
    level === "High" ? "bg-critical" : level === "Moderate" ? "bg-warning" : "bg-positive";

  return (
    <Card className="p-3">
      <div className="flex items-baseline justify-between">
        <span className="text-[13px] font-semibold text-foreground">Privacy exposure</span>
        <span className={cn("flex items-center gap-1.5 text-[13px] font-semibold", tone)}>
          <CircleAlert aria-hidden="true" className="size-3.5" />
          {level}
        </span>
      </div>
      <div className="mt-2 flex gap-1" aria-hidden="true">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
          <div className={cn("h-full rounded-full transition-[width] duration-500", bar)} style={{ width: fill }} />
        </div>
      </div>
      <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">{scan.exposureNote}</p>

      <div className="mt-3 grid grid-cols-3 gap-1.5">
        {scan.metrics.map((m) => (
          <div
            key={m.key}
            title={m.description}
            className="rounded-[10px] border border-border bg-background/60 px-2 py-2"
          >
            <span aria-hidden="true" className="text-muted-foreground">
              {metricIcon[m.key]}
            </span>
            <div className="mt-1 text-[11px] leading-tight text-muted-foreground">{m.label}</div>
            <div className="tnum text-[12px] font-semibold text-foreground">{m.status}</div>
            <span className="sr-only">{m.description}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function CategoryFinding({ finding }: { finding: Finding }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-border last:border-b-0">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start gap-2 px-3 py-2.5 text-left transition-colors hover:bg-muted/60"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-semibold text-foreground">{finding.name}</span>
            <RecommendationTag value={finding.recommendation} />
          </div>
          <p className="mt-0.5 text-[12px] leading-relaxed text-muted-foreground">
            {finding.explanation}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5 pt-0.5">
          <ConfidenceBadge value={finding.confidence} />
          <ChevronDown
            aria-hidden="true"
            className={cn(
              "size-4 text-muted-foreground transition-transform duration-200",
              open && "rotate-180",
            )}
          />
        </div>
      </button>

      {open ? (
        <div className="cs-rise bg-background/60 px-3 pb-3 pt-1">
          {finding.evidence ? (
            <blockquote className="rounded-[10px] border border-border bg-surface px-3 py-2 text-[12px] leading-[1.65] text-foreground">
              &ldquo;{finding.evidence}&rdquo;
            </blockquote>
          ) : (
            <div className="rounded-[10px] border border-warning/30 bg-warning/8 px-3 py-2 text-[12px] leading-relaxed text-warning">
              No evidence excerpt was published for this category, so it stays under manual review.
            </div>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <EvidenceTag verified={Boolean(finding.evidence)} />
            {finding.sourceType ? (
              <span className="text-[11px] text-muted-foreground">Source: {finding.sourceType}</span>
            ) : null}
          </div>
          <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">
            <span className="font-semibold text-foreground">Why this matters. </span>
            {finding.whyItMatters}
          </p>
          {finding.sourceUrl ? (
            <div className="mt-2 space-y-1">
              <div className="truncate text-[11px] text-muted-foreground">{finding.sourceUrl}</div>
              <SourceLink href={finding.sourceUrl}>Review original policy</SourceLink>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function ProtectionPlan({
  scan,
  onReview,
  onDismiss,
}: {
  scan: ScanResult;
  onReview: () => void;
  onDismiss: () => void;
}) {
  return (
    <div className="rounded-[12px] bg-forest p-3.5 text-[#F7F5F0]">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-sage">
          Recommended protection
        </span>
        <ConfidenceBadge value={scan.confidence} tone="dark" />
      </div>
      <h3 className="mt-1.5 text-[16px] font-semibold tracking-[-0.01em]">{scan.plan.title}</h3>
      <p className="mt-1 text-[12px] leading-relaxed text-sage">{scan.plan.summary}</p>

      <dl className="mt-3 space-y-1.5 rounded-[10px] border border-sage/20 bg-[#F7F5F0]/6 px-3 py-2.5 text-[12px]">
        {[
          ["Allow", scan.plan.allow],
          ["Block", scan.plan.block],
          ["Review", scan.plan.review],
        ].map(([label, items]) => (
          <div key={label as string} className="flex gap-2">
            <dt className="w-14 shrink-0 font-semibold text-sage">{label as string}</dt>
            <dd className="text-[#F7F5F0]">{(items as string[]).join(", ")}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-2.5 flex items-center gap-1.5 text-[11px] text-sage">
        <ShieldCheck aria-hidden="true" className="size-3.5" />
        Nothing changes until you approve it.
      </p>

      <div className="mt-3 space-y-2">
        <Button variant="onDark" onClick={onReview}>
          Review and apply
        </Button>
        <Button variant="onDarkGhost" onClick={onDismiss}>
          Keep browsing
        </Button>
      </div>
    </div>
  );
}

export function ResultState({
  scan,
  onReview,
  onDismiss,
}: {
  scan: ScanResult;
  onReview: () => void;
  onDismiss: () => void;
}) {
  return (
    <div className="cs-rise space-y-4 px-4 py-4">
      <div>
        <h2 className="text-[20px] font-semibold leading-tight tracking-[-0.02em] text-foreground">
          Your privacy snapshot
        </h2>
        <div className="tnum mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-muted-foreground">
          <span className="font-medium text-foreground">{scan.site.hostname}</span>
          <span aria-hidden="true">·</span>
          <span>{scan.scannedAt}</span>
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full border border-positive/30 bg-positive/8 px-2 py-0.5 text-[11px] font-medium text-positive">
            <CheckCircle2 aria-hidden="true" className="size-3" />
            {scan.workflowStatus}
          </span>
          <ConfidenceBadge value={scan.confidence} />
        </div>
      </div>

      <RiskOverview scan={scan} />

      <div>
        <SectionTitle aside="Tap a row for evidence">Category findings</SectionTitle>
        <Card>
          {scan.findings.map((f) => (
            <CategoryFinding key={f.key} finding={f} />
          ))}
        </Card>
      </div>

      <ProtectionPlan scan={scan} onReview={onReview} onDismiss={onDismiss} />
    </div>
  );
}

/* ---------------------------- Confirmation ------------------------------- */

export function ConfirmationDialog({
  scan,
  automatic,
  onApply,
  onCancel,
}: {
  scan: ScanResult;
  automatic: boolean;
  onApply: () => void;
  onCancel: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Review protection choice"
      className="cs-rise px-4 py-4"
    >
      <h2 className="text-[20px] font-semibold leading-tight tracking-[-0.02em] text-foreground">
        Review protection choice
      </h2>
      <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
        ConsentShield is ready to reject optional cookies on {scan.site.hostname}.
      </p>

      <Card className="mt-3 divide-y divide-border text-[12px]">
        {[
          ["Action", "Reject optional cookies"],
          ["Allowed", "Essential and Functional"],
          ["Blocked", "Analytics, Advertising, Social"],
          ["Unknown", "1 category requires review"],
          ["Source", "Cookie Policy and consent banner"],
        ].map(([k, v]) => (
          <div key={k} className="flex gap-3 px-3 py-2">
            <span className="w-16 shrink-0 text-muted-foreground">{k}</span>
            <span className="font-medium text-foreground">{v}</span>
          </div>
        ))}
      </Card>

      <div className="mt-3 flex items-start gap-2 rounded-[10px] border border-warning/30 bg-warning/8 px-3 py-2.5 text-[12px] leading-relaxed text-warning">
        <CircleAlert aria-hidden="true" className="mt-0.5 size-3.5 shrink-0" />
        Unknown categories will not be automatically accepted.
      </div>

      <p className="mt-2 text-[11px] text-muted-foreground">
        {automatic
          ? "Automatic protection is enabled for your selected privacy mode."
          : "Manual approval is enabled."}
      </p>

      <div className="mt-4 space-y-2">
        <Button onClick={onApply}>Apply protection</Button>
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

/* ------------------------------ Execution -------------------------------- */

const EXEC_STEPS = [
  "Verifying current page",
  "Confirming site identity",
  "Locating consent control",
  "Applying approved preference",
];

export function ExecutionProgress({
  hostname,
  onDone,
}: {
  hostname: string;
  onDone: () => void;
}) {
  const [step, setStep] = useState(0);
  useEffect(() => {
    if (step >= EXEC_STEPS.length) {
      const t = setTimeout(onDone, 450);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setStep((s) => s + 1), 750);
    return () => clearTimeout(t);
  }, [step, onDone]);

  return (
    <div className="cs-rise px-4 py-5">
      <h2 className="text-[20px] font-semibold tracking-[-0.02em] text-foreground">
        Applying your choice
      </h2>
      <p className="tnum mt-1 text-[12px] text-muted-foreground">
        {hostname} · plan valid for this page only
      </p>

      <ol className="mt-4 space-y-2" aria-live="polite">
        {EXEC_STEPS.map((label, i) => {
          const done = i < step;
          const active = i === step;
          return (
            <li
              key={label}
              className={cn(
                "flex items-center gap-2.5 rounded-[10px] border px-3 py-2.5 text-[13px]",
                active
                  ? "border-forest/25 bg-forest/6 text-foreground"
                  : done
                    ? "border-border bg-surface text-muted-foreground"
                    : "border-transparent text-muted-foreground/70",
              )}
            >
              <span
                aria-hidden="true"
                className={cn(
                  "flex size-4 shrink-0 items-center justify-center rounded-full border",
                  done ? "border-positive bg-positive text-[#FFFEFA]" : "border-border",
                )}
              >
                {done ? <CheckCircle2 className="size-3" /> : null}
              </span>
              <span className="font-medium">{label}</span>
            </li>
          );
        })}
      </ol>

      <p className="mt-4 text-[11px] text-muted-foreground">
        This action is limited to the current page.
      </p>
    </div>
  );
}

export function SuccessState({
  hostname,
  onDetails,
  onClose,
}: {
  hostname: string;
  onDetails: () => void;
  onClose: () => void;
}) {
  return (
    <div className="cs-rise px-4 py-5">
      <div className="flex size-10 items-center justify-center rounded-full border border-positive/25 bg-positive/8 text-positive">
        <ShieldCheck aria-hidden="true" className="size-5" />
      </div>
      <h2 className="mt-3 text-[20px] font-semibold tracking-[-0.02em] text-foreground">
        Protection applied
      </h2>
      <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
        Optional cookies were rejected on {hostname}.
      </p>

      <Card className="mt-3 divide-y divide-border text-[12px]">
        {[
          ["Essential", "Allowed", "positive"],
          ["Analytics", "Blocked", "critical"],
          ["Advertising", "Blocked", "critical"],
          ["Social", "Blocked", "critical"],
        ].map(([k, v, tone]) => (
          <div key={k} className="flex items-center justify-between px-3 py-2">
            <span className="text-foreground">{k}</span>
            <span
              className={cn(
                "font-semibold",
                tone === "positive" ? "text-positive" : "text-critical",
              )}
            >
              {v}
            </span>
          </div>
        ))}
      </Card>

      <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
        ConsentShield did not change anything outside this page.
      </p>

      <div className="mt-4 space-y-2">
        <Button onClick={onDetails}>View scan details</Button>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </div>
    </div>
  );
}

/* ------------------------------- Settings -------------------------------- */

const MODES: PrivacyMode[] = ["Manual", "Strict", "Balanced", "Functional", "Custom"];

export function SettingsView({
  settings,
  onChange,
}: {
  settings: Settings;
  onChange: (s: Settings) => void;
}) {
  const set = (patch: Partial<Settings>) => onChange({ ...settings, ...patch });
  const setCat = (k: keyof Settings["categories"], v: boolean) =>
    onChange({ ...settings, mode: "Custom", categories: { ...settings.categories, [k]: v } });

  return (
    <div className="cs-rise space-y-5 px-4 py-4">
      <div>
        <h2 className="text-[20px] font-semibold tracking-[-0.02em] text-foreground">Settings</h2>
        <p className="mt-1 text-[12px] text-muted-foreground">
          Preferences are stored locally on this device.
        </p>
      </div>

      <section>
        <SectionTitle aside="Default: Manual">Privacy mode</SectionTitle>
        <div className="grid grid-cols-2 gap-1.5">
          {MODES.map((m) => {
            const active = settings.mode === m;
            return (
              <button
                key={m}
                type="button"
                aria-pressed={active}
                onClick={() => set({ mode: m })}
                className={cn(
                  "rounded-[10px] border px-3 py-2 text-[12px] font-medium transition-colors",
                  active
                    ? "border-forest bg-forest text-[#F7F5F0]"
                    : "border-border bg-surface text-foreground hover:bg-muted",
                  m === "Custom" && "col-span-2",
                )}
              >
                {m}
              </button>
            );
          })}
        </div>
      </section>

      <section>
        <SectionTitle>Category preferences</SectionTitle>
        <Card>
          <ToggleRow label="Essential" checked locked lockedNote="Always allowed and locked." />
          <ToggleRow
            label="Functional"
            description="Remembers preferences such as language and region."
            checked={settings.categories.functional}
            onChange={(v) => setCat("functional", v)}
          />
          <ToggleRow
            label="Analytics"
            description="Measures behaviour and site usage."
            checked={settings.categories.analytics}
            onChange={(v) => setCat("analytics", v)}
          />
          <ToggleRow
            label="Advertising"
            description="Supports profiling and ad measurement."
            checked={settings.categories.advertising}
            onChange={(v) => setCat("advertising", v)}
          />
          <ToggleRow
            label="Social"
            description="Embedded social widgets and sharing tools."
            checked={settings.categories.social}
            onChange={(v) => setCat("social", v)}
          />
          <ToggleRow
            label="Unknown"
            checked={false}
            locked
            lockedNote="Never automatically allowed."
          />
        </Card>
      </section>

      <section>
        <SectionTitle>Protection behavior</SectionTitle>
        <Card>
          <ToggleRow
            label="Allow automatic protection"
            description="When enabled, ConsentShield may apply your selected privacy preferences after verifying the current page."
            checked={settings.automaticProtection}
            onChange={(v) => set({ automaticProtection: v })}
          />
          <ToggleRow
            label="Require confirmation for unknown categories"
            description="Unclassified consent groups always wait for your approval."
            checked={settings.confirmUnknown}
            onChange={(v) => set({ confirmUnknown: v })}
          />
        </Card>
      </section>

      <section>
        <SectionTitle>Data controls</SectionTitle>
        <div className="space-y-2">
          <Button variant="secondary">
            <Trash2 aria-hidden="true" className="size-4" />
            Clear local preferences
          </Button>
          <Button variant="destructive">
            <Ban aria-hidden="true" className="size-4" />
            Delete saved scan history
          </Button>
          <div className="pt-1 text-center">
            <SourceLink href="https://example.com/privacy">View privacy policy</SourceLink>
          </div>
        </div>
      </section>
    </div>
  );
}
