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
    re-render identically) and we want each scan to be independent.
  - All subprocess calls have a timeout; failures raise WebcmdError so
    the caller (browser_agent.py) can fall back to mock evidence or
    surface a scan failure cleanly instead of hanging.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DEFAULT_TIMEOUT_SECONDS = 45


def _resolve_webcmd_bin() -> str:
    """
    Resolve the webcmd executable to an absolute path.

    On Windows, `npm install -g` creates a `webcmd.cmd` shim (plus a
    `webcmd.ps1` and extensionless `webcmd`). subprocess.run(["webcmd", ...])
    without shell=True cannot execute a .cmd file directly via Windows'
    CreateProcess -- it needs either shell=True or the resolved path
    (including the .cmd extension) so Windows' own PATHEXT handling kicks
    in. shutil.which already applies PATHEXT resolution correctly, so we
    use it here instead of relying on the bare command name.
    """
    override = os.environ.get("WEBCMD_BIN")
    if override:
        return override

    resolved = shutil.which("webcmd")
    if resolved:
        return resolved

    # Fall back to the bare name; _run's FileNotFoundError handling will
    # surface a clear error if this truly isn't installed/on PATH.
    return "webcmd"


WEBCMD_BIN = _resolve_webcmd_bin()
_USE_SHELL = sys.platform == "win32"

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


def _run(args: list[str], timeout: int) -> dict:
    try:
        proc = subprocess.run(
            [WEBCMD_BIN, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=_USE_SHELL,
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


def _create_session(timeout: int) -> str:
    data = _run(["session", "create"], timeout=timeout)
    # `webcmd session create` prints plain text ("id: session_xxx\nkind: explicit"),
    # not JSON -- handle both shapes defensively.
    if isinstance(data, dict) and "id" in data:
        return data["id"]
    raise WebcmdError(f"Could not parse session id from webcmd output: {data}")


def _create_session_text(timeout: int) -> str:
    """`session create` outputs plain text (id: ..., kind: ...), not JSON."""
    try:
        proc = subprocess.run(
            [WEBCMD_BIN, "session", "create"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=_USE_SHELL,
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
            shell=_USE_SHELL,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Best-effort cleanup; a leaked session isn't fatal to the caller.
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

    script = _SCRIPT_TEMPLATE.replace(
        "__TARGET_URL_JSON__", json.dumps(target_url)
    )

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
            raise WebcmdError(
                f"webcmd browser run failed: {error.get('message', data)}"
            )

        result = data.get("result") or {}
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
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
        _close_session(session_id, timeout=timeout)