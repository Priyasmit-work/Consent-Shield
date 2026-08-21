import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { BrandHeader, SiteContext } from "@/components/cs/header";
import { ExtensionShell, ShellBody, ShellFooter } from "@/components/cs/primitives";
import {
  ConfirmationDialog,
  ExecutionProgress,
  ResultState,
  ScanIntro,
  ScanProgress,
  SettingsView,
  SuccessState,
} from "@/components/cs/screens";
import {
  BackendUnavailableState,
  NoBannerState,
  PartialResultState,
  StalePlanState,
  UnsupportedPageState,
} from "@/components/cs/edge-states";
import { api, defaultSettings } from "@/lib/consentshield/api";
import type { ScanResult, Settings } from "@/lib/consentshield/types";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ConsentShield — Privacy protection for the web" },
      {
        name: "description",
        content:
          "ConsentShield popup interface: detect cookie banners, read privacy evidence, and approve a safer consent choice before anything changes.",
      },
      { property: "og:title", content: "ConsentShield — Privacy protection for the web" },
      {
        property: "og:description",
        content:
          "A calm, evidence-backed browser extension popup for reviewing cookie consent and applying protection you approve.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Popup,
});

type ScreenKey =
  | "idle"
  | "scanning"
  | "result"
  | "confirm"
  | "executing"
  | "success"
  | "partial"
  | "unsupported"
  | "backend"
  | "stale"
  | "nobanner"
  | "settings";

const STATES: { key: ScreenKey; label: string }[] = [
  { key: "idle", label: "Site analysis" },
  { key: "scanning", label: "Scan in progress" },
  { key: "result", label: "Privacy snapshot" },
  { key: "confirm", label: "Confirmation" },
  { key: "executing", label: "Execution" },
  { key: "success", label: "Success" },
  { key: "partial", label: "Partial result" },
  { key: "nobanner", label: "No banner" },
  { key: "unsupported", label: "Unsupported page" },
  { key: "backend", label: "Backend unavailable" },
  { key: "stale", label: "Stale plan" },
  { key: "settings", label: "Settings" },
];

const PLACEHOLDER_SCAN: ScanResult = {
  site: { hostname: "", pageTitle: "", status: "" },
  scannedAt: "",
  workflowStatus: "",
  confidence: 0,
  exposure: "Low",
  exposureNote: "",
  metrics: [],
  findings: [],
  plan: { title: "", summary: "", allow: [], block: [], review: [] },
};

function Popup() {
  const [screen, setScreen] = useState<ScreenKey>("idle");
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [targetUrl, setTargetUrl] = useState("https://example.com");
  const [scanError, setScanError] = useState<string | null>(null);
  const [scan, setScan] = useState<ScanResult>(PLACEHOLDER_SCAN);
  const [applyMessage, setApplyMessage] = useState<string | null>(null);

  // Load real preferences from the backend on first render. If the backend
  // can't be reached yet, we silently keep the local defaults -- the person
  // will see the real error as soon as they try to scan.
  useEffect(() => {
    let cancelled = false;
    api
      .getSettings()
      .then((s) => {
        if (!cancelled) setSettings(s);
      })
      .catch(() => {
        /* backend not reachable yet; keep local defaults */
      })
      .finally(() => {
        if (!cancelled) setSettingsLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const goResult = useCallback(() => setScreen("result"), []);

  const runScan = useCallback(async () => {
    setScanError(null);
    setScreen("scanning");
    try {
      const result = await api.getScan(targetUrl);
      setScan(result);
      if (result._bannerDetected === false) {
        setScreen("nobanner");
      } else if (result._scanStatus === "partial") {
        setScreen("partial");
      } else {
        setScreen("result");
      }
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Scan failed");
      setScreen("backend");
    }
  }, [targetUrl]);

  const handleApply = useCallback(async () => {
    setApplyMessage(null);
    try {
      const action = scan._recommendedAction ?? "reject_optional";
      const res = await api.applyPlan(scan, action);
      if (res.status === "approved") {
        setScreen("executing");
      } else {
        // Backend only executes when the user's stored preferences have
        // auto_apply enabled (Settings -> Allow automatic protection, with
        // a non-manual privacy mode). Otherwise it always responds
        // "awaiting_user_confirmation" by design -- surface that instead of
        // pretending we executed something.
        setApplyMessage(
          res.message ?? "ConsentShield is waiting for automatic protection to be enabled in Settings.",
        );
        setScreen("result");
      }
    } catch (err) {
      setApplyMessage(err instanceof Error ? err.message : "Could not apply the protection plan");
      setScreen("result");
    }
  }, [scan]);

  const handleSettingsChange = useCallback((next: Settings) => {
    setSettings(next);
    api
      .saveSettings(next)
      .then(setSettings)
      .catch(() => {
        /* keep the optimistic local value; the person can retry the toggle */
      });
  }, []);

  const showSiteContext = !["settings", "unsupported", "backend", "idle"].includes(screen);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <h1 className="sr-only">ConsentShield browser extension popup</h1>

      <div className="mx-auto flex w-full max-w-[900px] flex-col items-center gap-6">
        <ExtensionShell>
          <BrandHeader
            mode={settings.mode}
            onSettings={() => setScreen(screen === "settings" ? "idle" : "settings")}
            onBack={() => setScreen("idle")}
            showBack={screen === "settings"}
          />
          {showSiteContext ? (
            <SiteContext
              hostname={scan.site.hostname || targetUrl}
              pageTitle={scan.site.pageTitle || "Not scanned yet"}
              status={screen === "nobanner" ? "No banner found" : scan.site.status}
              tone={screen === "nobanner" ? "neutral" : "warning"}
            />
          ) : null}

          <ShellBody>
            {screen === "idle" && (
              <ScanIntro onScan={runScan} url={targetUrl} onUrlChange={setTargetUrl} error={scanError} />
            )}
            {screen === "scanning" && <ScanProgress onDone={goResult} />}
            {screen === "result" && (
              <ResultState
                scan={scan}
                onReview={() => setScreen("confirm")}
                onDismiss={() => setScreen("idle")}
              />
            )}
            {screen === "confirm" && (
              <ConfirmationDialog
                scan={scan}
                automatic={settings.automaticProtection}
                onApply={handleApply}
                onCancel={() => setScreen("result")}
              />
            )}
            {screen === "executing" && (
              <ExecutionProgress hostname={scan.site.hostname} onDone={() => setScreen("success")} />
            )}
            {screen === "success" && (
              <SuccessState
                hostname={scan.site.hostname}
                onDetails={() => setScreen("result")}
                onClose={() => setScreen("idle")}
              />
            )}
            {screen === "partial" && (
              <PartialResultState scan={scan} onEvidence={() => setScreen("result")} />
            )}
            {screen === "unsupported" && <UnsupportedPageState onClose={() => setScreen("idle")} />}
            {screen === "backend" && <BackendUnavailableState onRetry={runScan} />}
            {screen === "stale" && <StalePlanState onRescan={runScan} />}
            {screen === "nobanner" && <NoBannerState onReviewPolicy={() => setScreen("result")} />}
            {screen === "settings" && <SettingsView settings={settings} onChange={handleSettingsChange} />}
          </ShellBody>

          <ShellFooter>
            <div className="flex items-center justify-between gap-2">
              <span>
                {applyMessage
                  ? applyMessage
                  : settings.automaticProtection
                    ? "Automatic protection enabled"
                    : "Manual approval required"}
              </span>
              <span className="text-muted-foreground/80">
                {settingsLoaded ? "Connected" : "Connecting…"}
              </span>
            </div>
          </ShellFooter>
        </ExtensionShell>

        <nav
          aria-label="Preview extension states"
          className="flex w-full max-w-[560px] flex-wrap justify-center gap-1.5"
        >
          {STATES.map((s) => (
            <button
              key={s.key}
              type="button"
              aria-pressed={screen === s.key}
              onClick={() => setScreen(s.key)}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors",
                screen === s.key
                  ? "border-forest bg-forest text-[#F7F5F0]"
                  : "border-border bg-surface text-muted-foreground hover:text-foreground",
              )}
            >
              {s.label}
            </button>
          ))}
        </nav>
      </div>
    </main>
  );
}
