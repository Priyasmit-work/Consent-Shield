"""
webcmd_client.py

Thin subprocess wrapper around the `webcmd` CLI (https://webcmd.dev),
used to drive a real, live-rendered browser check for cookie-consent
banners on a target site.

This replaces the WEBCMD_MODE=mock fabricated evidence with a real,
one-time-per-scan browser inspection: it navigates to the target URL,
locates the consent-management-platform (CMP) iframe if one exists
(Sourcepoint, OneTrust, Cookiebot, Didomi, Quantcast, TrustArc, or any
frame whose URL/name contains "consent"/"cmp"), and extracts:
  - whether a banner was detected
  - the banner's button labels
  - any cookie/privacy policy links found inside the banner

It also exposes click_banner_action(), which drives a fresh webcmd
session to the same site and clicks whichever banner button matches an
approved plan's label -- this is how an approved execution plan (see
app/api/v1/routes/execution.py) is actually carried out against the
live site once WEBCMD_MODE=live and the plan has been approved.

Design notes:
  - webcmd's `browser run` executes scripts in a QuickJS sandbox, which
    does NOT expose `process.env`. The target URL therefore cannot be
    passed as an environment variable -- instead we write a small,
    per-call temp .js file with the URL substituted directly into the
    script text (see _build_script). The URL is JSON-encoded before
    substitution so it is always a syntactically valid, safely-escaped
    JS string literal -- this is not string concatenation of untrusted
    code, just a safely-quoted data value inside a fixed script.
  - Every call creates a fresh webcmd session and closes it afterwards,
    since sessions are stateful (a banner already "seen" once may not
    re-render identically) and we want each scan/action to be
    independent.
  - All subprocess calls have a timeout; failures raise WebcmdError so
    the caller (browser_agent.py / execution.py) can fall back to mock
    evidence, report failure, or surface a scan failure cleanly instead
    of hanging.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

WEBCMD_BIN = os.environ.get("WEBCMD_BIN", "webcmd")
DEFAULT_TIMEOUT_SECONDS = 45

_SCRIPT_TEMPLATE = r"""
const targetUrl = __TARGET_URL_JSON__;

await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
await page.waitForTimeout(3000);

const mainFrame = page.mainFrame();
const childFrames = page.frames().filter((f) => f !== mainFrame);

const cmpPattern = /sourcepoint|onetrust|cookiebot|didomi|quantcast|trustarc|consent|cmp/i;

let bannerFrame = null;

for (const frame of childFrames) {
  const url = frame.url() || "";
  const name = frame.name() || "";
  if (cmpPattern.test(url) || cmpPattern.test(name)) {
    bannerFrame = frame;
    break;
  }
}

if (!bannerFrame) {
  let bestLen = 0;
  for (const frame of childFrames) {
    const body = await frame
      .locator("body")
      .innerText({ timeout: 1000 })
      .catch(() => "");
    if (body.length > bestLen && /cookie|consent|privacy/i.test(body)) {
      bestLen = body.length;
      bannerFrame = frame;
    }
  }
}

let buttons = [];
let policyLinks = [];

if (bannerFrame) {
  const buttonEls = await bannerFrame.locator("button").all();
  for (const b of buttonEls) {
    const label = (await b.innerText().catch(() => "")).trim();
    if (label) buttons.push(label);
  }

  const linkEls = await bannerFrame.locator("a[href]").all();
  for (const l of linkEls) {
    const href = await l.getAttribute("href").catch(() => null);
    const label = (await l.innerText().catch(() => "")).trim().toLowerCase();
    if (href && (label.includes("cookie") || label.includes("privacy"))) {
      let absoluteHref = href;
      try {
        absoluteHref = new URL(href, bannerFrame.url()).toString();
      } catch (e) {}
      policyLinks.push({ label, href: absoluteHref });
    }
  }
}

return {
  url: targetUrl,
  bannerDetected: !!bannerFrame,
  bannerFrameUrl: bannerFrame ? bannerFrame.url() : null,
  buttons: [...new Set(buttons)],
  policyLinks,
};
"""

# Navigates to the target URL, locates the same consent banner frame as
# the detection script, and clicks whichever button's visible text
# matches __BUTTON_LABEL_JSON__ (exact match first, then substring
# match as a fallback since live sites may render slightly different
# casing/whitespace than what was captured during the scan).
_CLICK_SCRIPT_TEMPLATE = r"""
const targetUrl = __TARGET_URL_JSON__;
const buttonLabel = __BUTTON_LABEL_JSON__;

await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
await page.waitForTimeout(3000);

const mainFrame = page.mainFrame();
const childFrames = page.frames().filter((f) => f !== mainFrame);

const cmpPattern = /sourcepoint|onetrust|cookiebot|didomi|quantcast|trustarc|consent|cmp/i;

let bannerFrame = null;

for (const frame of childFrames) {
  const url = frame.url() || "";
  const name = frame.name() || "";
  if (cmpPattern.test(url) || cmpPattern.test(name)) {
    bannerFrame = frame;
    break;
  }
}

if (!bannerFrame) {
  let bestLen = 0;
  for (const frame of childFrames) {
    const body = await frame
      .locator("body")
      .innerText({ timeout: 1000 })
      .catch(() => "");
    if (body.length > bestLen && /cookie|consent|privacy/i.test(body)) {
      bestLen = body.length;
      bannerFrame = frame;
    }
  }
}

let clicked = false;
let matchedLabel = null;
let clickError = null;

if (bannerFrame) {
  const buttonEls = await bannerFrame.locator("button").all();

  // Pass 1: exact (case-insensitive) label match.
  for (const b of buttonEls) {
    const label = (await b.innerText().catch(() => "")).trim();
    if (label && label.toLowerCase() === buttonLabel.toLowerCase()) {
      try {
        await b.click({ timeout: 5000 });
        clicked = true;
        matchedLabel = label;
      } catch (e) {
        clickError = String(e);
      }
      break;
    }
  }

  // Pass 2: substring match, only if pass 1 found nothing to click.
  if (!clicked && !clickError) {
    for (const b of buttonEls) {
      const label = (await b.innerText().catch(() => "")).trim();
      if (label && label.toLowerCase().includes(buttonLabel.toLowerCase())) {
        try {
          await b.click({ timeout: 5000 });
          clicked = true;
          matchedLabel = label;
        } catch (e) {
          clickError = String(e);
        }
        break;
      }
    }
  }
}

await page.waitForTimeout(1000);

return {
  url: targetUrl,
  bannerFound: !!bannerFrame,
  clicked,
  matchedLabel,
  clickError,
};
"""


class WebcmdError(RuntimeError):
    """Raised when the webcmd CLI fails, times out, or returns bad data."""


@dataclass
class PolicyLink:
    label: str
    href: str


@dataclass
class CookieBannerScanResult:
    url: str
    banner_detected: bool
    banner_frame_url: Optional[str]
    buttons: list[str] = field(default_factory=list)
    policy_links: list[PolicyLink] = field(default_factory=list)


@dataclass
class BannerActionResult:
    url: str
    banner_found: bool
    clicked: bool
    matched_label: Optional[str]
    click_error: Optional[str] = None


def _run(args: list[str], timeout: int) -> dict:
    try:
        proc = subprocess.run(
            [WEBCMD_BIN, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WebcmdError(
            f"'{WEBCMD_BIN}' was not found on PATH. Is webcmd installed "
            "(npm install -g @agentrhq/webcmd)?"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise WebcmdError(f"webcmd command timed out after {timeout}s: {args}") from exc

    stdout = proc.stdout.strip()
    if not stdout:
        raise WebcmdError(
            f"webcmd produced no output (exit {proc.returncode}). stderr: {proc.stderr.strip()}"
        )

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise WebcmdError(f"webcmd output was not valid JSON: {stdout[:500]}") from exc


def _create_session_text(timeout: int) -> str:
    """`session create` outputs plain text (id: ..., kind: ...), not JSON."""
    try:
        proc = subprocess.run(
            [WEBCMD_BIN, "session", "create"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise WebcmdError(
            f"'{WEBCMD_BIN}' was not found on PATH. Is webcmd installed "
            "(npm install -g @agentrhq/webcmd)?"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise WebcmdError(f"webcmd session create timed out after {timeout}s") from exc

    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("id:"):
            return line.split("id:", 1)[1].strip()

    raise WebcmdError(
        f"Could not parse session id from webcmd output: {proc.stdout!r} / {proc.stderr!r}"
    )


def _close_session(session_id: str, timeout: int) -> None:
    try:
        subprocess.run(
            [WEBCMD_BIN, "--session", session_id, "session", "close", session_id],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Best-effort cleanup; a leaked session isn't fatal to the caller.
        pass


def _run_script(session_id: str, script: str, timeout: int) -> dict:
    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(script)
            tmp_path = Path(tmp.name)

        data = _run(
            ["--session", session_id, "browser", "run", "--file", str(tmp_path)],
            timeout=timeout,
        )

        if not data.get("ok"):
            error = data.get("error", {})
            raise WebcmdError(f"webcmd browser run failed: {error.get('message', data)}")

        return data.get("result") or {}
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass


def scan_cookie_banner(
    target_url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> CookieBannerScanResult:
    """
    Launches a fresh webcmd browser session, navigates to `target_url`,
    and extracts real cookie-consent banner evidence (detection, button
    labels, policy links).

    Raises WebcmdError on any failure (webcmd not installed, browser
    bridge unavailable, navigation/timeout failure, unparseable output).
    Callers should catch WebcmdError and decide whether to fall back to
    mock evidence or fail the scan.
    """
    session_id = _create_session_text(timeout=timeout)
    try:
        script = _SCRIPT_TEMPLATE.replace("__TARGET_URL_JSON__", json.dumps(target_url))
        result = _run_script(session_id, script, timeout=timeout)

        return CookieBannerScanResult(
            url=result.get("url", target_url),
            banner_detected=bool(result.get("bannerDetected")),
            banner_frame_url=result.get("bannerFrameUrl"),
            buttons=list(result.get("buttons") or []),
            policy_links=[
                PolicyLink(label=pl.get("label", ""), href=pl.get("href", ""))
                for pl in (result.get("policyLinks") or [])
            ],
        )
    finally:
        _close_session(session_id, timeout=timeout)


def click_banner_action(
    target_url: str, button_label: str, timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> BannerActionResult:
    """
    Launches a fresh webcmd browser session, navigates to `target_url`,
    finds the consent banner, and clicks whichever button's text matches
    `button_label` (exact match first, then substring fallback).

    This is how an *approved* execution plan (execution.py) is actually
    carried out against the live site -- it is only ever called after
    the backend's own confirmation/auto-apply rules have already been
    satisfied; this function itself has no opinion on consent policy,
    it only clicks the button it's told to click.

    Raises WebcmdError on any failure (webcmd not installed, browser
    bridge unavailable, navigation/timeout failure, unparseable output).
    A "no banner / no matching button found" outcome is NOT an error --
    it's reported via `banner_found` / `clicked` on the returned result
    so the caller can decide how to report that back to the user.
    """
    session_id = _create_session_text(timeout=timeout)
    try:
        script = _CLICK_SCRIPT_TEMPLATE.replace(
            "__TARGET_URL_JSON__", json.dumps(target_url)
        ).replace("__BUTTON_LABEL_JSON__", json.dumps(button_label))
        result = _run_script(session_id, script, timeout=timeout)

        return BannerActionResult(
            url=result.get("url", target_url),
            banner_found=bool(result.get("bannerFound")),
            clicked=bool(result.get("clicked")),
            matched_label=result.get("matchedLabel"),
            click_error=result.get("clickError"),
        )
    finally:
        _close_session(session_id, timeout=timeout)
