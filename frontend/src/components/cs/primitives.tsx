import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { ArrowUpRight, Check, Info, Lock } from "lucide-react";
import type { Recommendation } from "@/lib/consentshield/types";

/* ---------------------------------- Shell --------------------------------- */

export function ExtensionShell({ children }: { children: ReactNode }) {
  return (
    <div className="w-full max-w-[380px] min-[480px]:max-w-[420px]">
      <div className="flex max-h-[560px] min-h-[120px] flex-col overflow-hidden rounded-[18px] border border-border bg-surface shadow-[var(--shadow-popup)]">
        {children}
      </div>
    </div>
  );
}

export function ShellBody({ children }: { children: ReactNode }) {
  return <div className="cs-scroll flex-1 overflow-y-auto overflow-x-hidden">{children}</div>;
}

export function ShellFooter({ children }: { children: ReactNode }) {
  return (
    <div className="border-t border-border bg-surface px-4 py-3 text-[11px] text-muted-foreground">
      {children}
    </div>
  );
}

/* --------------------------------- Buttons -------------------------------- */

type Variant = "primary" | "secondary" | "ghost" | "destructive" | "onDark" | "onDarkGhost";

const variants: Record<Variant, string> = {
  primary: "bg-forest text-[#F7F5F0] hover:bg-forest-deep active:bg-forest-deep",
  secondary: "bg-surface text-foreground border border-border hover:bg-muted",
  ghost: "text-muted-foreground hover:text-foreground hover:bg-muted",
  destructive: "bg-surface text-critical border border-critical/35 hover:bg-critical/8",
  onDark: "bg-[#F7F5F0] text-forest hover:bg-sage/90",
  onDarkGhost: "text-sage border border-sage/35 hover:bg-[#F7F5F0]/10",
};

export function Button({
  variant = "primary",
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={cn(
        "inline-flex w-full items-center justify-center gap-2 rounded-[10px] px-4 py-2.5 text-[13px] font-semibold transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-45",
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

/* -------------------------------- Sections -------------------------------- */

export function SectionTitle({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="mb-2 flex items-baseline justify-between gap-2">
      <h3 className="text-[13px] font-semibold tracking-[-0.01em] text-foreground">{children}</h3>
      {aside ? <span className="text-[11px] text-muted-foreground">{aside}</span> : null}
    </div>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("rounded-[12px] border border-border bg-surface", className)}>
      {children}
    </div>
  );
}

/* --------------------------------- Badges --------------------------------- */

export function ConfidenceBadge({ value, tone = "light" }: { value: number; tone?: "light" | "dark" }) {
  return (
    <span
      title={`Confidence: how strongly the collected evidence supports this result (${value}%).`}
      className={cn(
        "tnum inline-flex shrink-0 items-center gap-1 rounded-full border px-1.5 py-0.5 text-[11px] font-medium",
        tone === "light"
          ? "border-border bg-muted text-muted-foreground"
          : "border-sage/30 bg-[#F7F5F0]/10 text-sage",
      )}
    >
      <Info aria-hidden="true" className="size-3" />
      {value}%
    </span>
  );
}

const recTone: Record<Recommendation, string> = {
  Allow: "text-positive border-positive/30 bg-positive/8",
  Review: "text-warning border-warning/30 bg-warning/8",
  Block: "text-critical border-critical/30 bg-critical/8",
};

export function RecommendationTag({ value }: { value: Recommendation }) {
  const glyph = value === "Allow" ? "✓" : value === "Review" ? "!" : "×";
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-semibold",
        recTone[value],
      )}
    >
      <span aria-hidden="true" className="text-[10px] leading-none">
        {glyph}
      </span>
      {value}
    </span>
  );
}

export function EvidenceTag({ verified = true }: { verified?: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
        verified
          ? "border-border bg-muted text-muted-foreground"
          : "border-warning/30 bg-warning/8 text-warning",
      )}
    >
      {verified ? <Check aria-hidden="true" className="size-3" /> : <Info aria-hidden="true" className="size-3" />}
      {verified ? "Evidence-backed" : "No evidence found"}
    </span>
  );
}

export function SourceLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className="inline-flex items-center gap-1 text-[12px] font-medium text-forest underline decoration-border underline-offset-4 hover:decoration-forest"
    >
      {children}
      <ArrowUpRight aria-hidden="true" className="size-3.5" />
    </a>
  );
}

/* --------------------------------- Toggles -------------------------------- */

export function ToggleRow({
  label,
  description,
  checked,
  onChange,
  locked,
  lockedNote,
}: {
  label: string;
  description?: string;
  checked: boolean;
  onChange?: (v: boolean) => void;
  locked?: boolean;
  lockedNote?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-border px-3 py-3 last:border-b-0">
      <div className="min-w-0">
        <div className="flex items-center gap-1.5 text-[13px] font-medium text-foreground">
          {label}
          {locked ? <Lock aria-hidden="true" className="size-3 text-muted-foreground" /> : null}
        </div>
        {description ? (
          <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">{description}</p>
        ) : null}
        {locked && lockedNote ? (
          <p className="mt-0.5 text-[11px] font-medium text-muted-foreground">{lockedNote}</p>
        ) : null}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={locked}
        onClick={() => onChange?.(!checked)}
        className={cn(
          "relative mt-0.5 h-[22px] w-[38px] shrink-0 rounded-full border transition-colors duration-150 disabled:opacity-50",
          checked ? "border-forest bg-forest" : "border-border bg-muted",
        )}
      >
        <span
          className={cn(
            "absolute top-[2px] size-[16px] rounded-full bg-surface shadow-[var(--shadow-soft)] transition-[left] duration-150",
            checked ? "left-[18px]" : "left-[2px]",
          )}
        />
      </button>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  copy,
  action,
}: {
  icon: ReactNode;
  title: string;
  copy: string;
  action?: ReactNode;
}) {
  return (
    <div className="cs-rise px-5 py-8 text-center">
      <div className="mx-auto flex size-11 items-center justify-center rounded-full border border-border bg-muted text-forest">
        {icon}
      </div>
      <h2 className="mt-4 text-[20px] font-semibold leading-tight tracking-[-0.02em] text-foreground">
        {title}
      </h2>
      <p className="mx-auto mt-2 max-w-[300px] text-[13px] leading-relaxed text-muted-foreground">
        {copy}
      </p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
