import {
  CircleAlert,
  CircleHelp,
  CloudOff,
  FileSearch,
  RefreshCcw,
  ShieldOff,
} from "lucide-react";
import { Button, Card, EmptyState, EvidenceTag, SourceLink, SectionTitle } from "./primitives";
import type { ScanResult } from "@/lib/consentshield/types";

export function PartialResultState({
  scan,
  onEvidence,
}: {
  scan: ScanResult;
  onEvidence: () => void;
}) {
  const verified = scan.findings.filter((f) => f.evidence);
  const unknown = scan.findings.filter((f) => !f.evidence);

  return (
    <div className="cs-rise space-y-4 px-4 py-4">
      <div>
        <h2 className="text-[20px] font-semibold leading-tight tracking-[-0.02em] text-foreground">
          Some privacy details could not be verified
        </h2>
        <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
          We found useful evidence, but this site did not clearly identify every cookie category.
        </p>
      </div>

      <div>
        <SectionTitle aside={`${verified.length} verified`}>Verified findings</SectionTitle>
        <Card className="divide-y divide-border">
          {verified.map((f) => (
            <div key={f.key} className="flex items-center justify-between gap-2 px-3 py-2">
              <span className="text-[13px] text-foreground">{f.name}</span>
              <EvidenceTag />
            </div>
          ))}
        </Card>
      </div>

      <div>
        <SectionTitle aside={`${unknown.length} unresolved`}>Unknown findings</SectionTitle>
        <Card className="divide-y divide-border">
          {unknown.map((f) => (
            <div key={f.key} className="flex items-center justify-between gap-2 px-3 py-2">
              <span className="text-[13px] text-foreground">{f.name}</span>
              <EvidenceTag verified={false} />
            </div>
          ))}
        </Card>
      </div>

      <Card className="space-y-1.5 p-3">
        <div className="text-[12px] font-semibold text-foreground">Sources reviewed</div>
        <div>
          <SourceLink href="https://example.com/cookie-policy">Cookie Policy</SourceLink>
        </div>
        <div>
          <SourceLink href="https://example.com/privacy">Privacy Policy</SourceLink>
        </div>
      </Card>

      <div className="rounded-[12px] border border-warning/30 bg-warning/8 px-3 py-2.5 text-[12px] leading-relaxed text-warning">
        <span className="font-semibold">Review manually. </span>
        No automatic recommendation is offered while categories remain unverified.
      </div>

      <Button onClick={onEvidence}>
        <FileSearch aria-hidden="true" className="size-4" />
        View evidence
      </Button>
    </div>
  );
}

export function UnsupportedPageState({ onClose }: { onClose: () => void }) {
  return (
    <EmptyState
      icon={<ShieldOff className="size-5" />}
      title="This page cannot be scanned"
      copy="Browser settings and extension pages cannot be inspected by ConsentShield."
      action={
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      }
    />
  );
}

export function BackendUnavailableState({ onRetry }: { onRetry: () => void }) {
  return (
    <EmptyState
      icon={<CloudOff className="size-5" />}
      title="Privacy scan unavailable"
      copy="ConsentShield could not reach its analysis service. Nothing was changed."
      action={
        <Button onClick={onRetry}>
          <RefreshCcw aria-hidden="true" className="size-4" />
          Try again
        </Button>
      }
    />
  );
}

export function StalePlanState({ onRescan }: { onRescan: () => void }) {
  return (
    <EmptyState
      icon={<CircleAlert className="size-5" />}
      title="Page changed"
      copy="The page changed after the scan, so the protection plan was cancelled for safety."
      action={<Button onClick={onRescan}>Scan again</Button>}
    />
  );
}

export function NoBannerState({ onReviewPolicy }: { onReviewPolicy: () => void }) {
  return (
    <EmptyState
      icon={<CircleHelp className="size-5" />}
      title="No consent banner found"
      copy="We could not find a visible cookie control on this page. You can still review the available privacy policy."
      action={
        <Button variant="secondary" onClick={onReviewPolicy}>
          Review policy
        </Button>
      }
    />
  );
}
