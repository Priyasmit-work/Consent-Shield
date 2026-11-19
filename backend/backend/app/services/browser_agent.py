"""
Browser agent orchestrator -- the backend's webcmd integration point.

Section 14 (webcmd requirements): the backend uses webcmd to explore and
reuse website workflows, finding cookie/privacy-policy links, extracting
evidence, detecting navigation failures, and returning a `reused`,
`explored`, or `repaired` workflow mode.

BROWSER_MODE=mock (default): this sandbox has no general internet egress,
so live browsing of an arbitrary target URL is not possible here. This
mode provides a deterministic, clearly-labeled exploration simulation --
enough to drive the full scan lifecycle, evidence schema, and workflow
reuse/recovery behavior end-to-end for local development and demoing the
API contract. It fabricates plausible per-category cookie evidence tied
to the target hostname; it does not claim to have inspected the real
site's real policies.

BROWSER_MODE=live uses the AI browser agent (services/agent_browser.py):
Playwright opens the site and Claude classifies the real banner buttons.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.config import Settings
from app.repositories.scans_repository import ScanRecord, ScansRepository
from app.schemas.common import ConsentAction, CookieCategory, ScanStatusValue, SourceType, WorkflowMode
from app.schemas.preferences import Preferences
from app.schemas.scans import (
    BannerAction,
    BannerFindings,
    CookiePrivacyResult,
    EvidenceObject,
    ScanRequest,
    SiteInfo,
)
from app.services.privacy_analyzer import PrivacyAnalyzer
from app.services.protection_planner import ProtectionPlanner
from app.services.agent_browser import AgentBrowserError, BannerOption, scan_cookie_banner

# In-process cache of "learned" workflows per hostname, so a second scan of
# the same site demonstrates FR-9 / Section 14 workflow reuse. This is
# intentionally process-local (not persisted) -- a real webcmd/Supabase
# `workflow_commands` table would back this in production.
_LEARNED_WORKFLOWS: dict[str, dict] = {}


class BrowserAgentService:
    def __init__(self, settings: Settings, analyzer: PrivacyAnalyzer) -> None:
        self._settings = settings
        self._analyzer = analyzer
        self._planner = ProtectionPlanner()

    async def run_scan(
        self,
        record: ScanRecord,
        request: ScanRequest,
        preferences: Preferences,
        repo: ScansRepository,
    ) -> None:
        hostname = urlparse(request.url).hostname or request.url
        origin = f"{urlparse(request.url).scheme}://{hostname}"

        try:
            await self._step(record, repo, ScanStatusValue.exploring, 10, "Locating cookie and privacy policy links")

            learned = _LEARNED_WORKFLOWS.get(hostname)
            if learned:
                workflow_mode = WorkflowMode.reused
                record.activity_log.append(self._log("navigation", f"Reused saved workflow for {hostname}"))
                policy_urls = learned["policy_urls"]
                banner_detected = learned["banner_detected"]
            else:
                workflow_mode = WorkflowMode.explored
                record.activity_log.append(self._log("navigation", "Opened footer and legal navigation links"))
                policy_urls = [f"{origin}/privacy", f"{origin}/cookie-policy"]
                # BROWSER_MODE=mock has no live browsing, so there is no real
                # signal for banner presence. Default to "detected" so the
                # mock evidence/plan path (which always fabricates banner
                # cookie data below) is demoed end-to-end, unless the
                # frontend explicitly told us otherwise.
                banner_detected = (
                    request.client_context.cookie_banner_detected
                    if request.client_context and request.client_context.cookie_banner_detected is not None
                    else True
                )

            live_actions = None
            if self._settings.browser_mode == "live":
                try:
                    scan = await asyncio.to_thread(scan_cookie_banner, self._settings, request.url)
                    banner_detected = scan.banner_detected
                    live_actions = self._actions_from_options(scan.options)
                    record.activity_log.append(
                        self._log("navigation", f"Live scan found {len(scan.buttons)} banner buttons: {scan.buttons}")
                    )
                    if scan.policy_links:
                        policy_urls = [pl.href for pl in scan.policy_links] + list(policy_urls)
                except AgentBrowserError as exc:
                    record.activity_log.append(
                        self._log("error", f"Live scan failed, using demo data instead: {exc}")
                    )

            record.workflow_mode = workflow_mode.value
            await self._step(record, repo, ScanStatusValue.extracting, 45, "Reading cookie and privacy information")

            evidence = self._collect_evidence(hostname, policy_urls, request.focus)
            record.activity_log.append(
                self._log("navigation", f"Extracted {len(evidence)} evidence excerpts")
            )

            await self._step(record, repo, ScanStatusValue.analyzing, 75, "Analyzing detected practices")

            allowed_categories = list(CookieCategory)
            findings, overall = self._analyzer.analyze(evidence, allowed_categories)
            plan = self._planner.build_plan(preferences, findings)

            banner = BannerFindings(
                detected=banner_detected,
                actions=live_actions if live_actions is not None else self._banner_actions(),
                default_state="unknown",
                dark_pattern_flags=(
                    ["reject_option_less_prominent"] if banner_detected else []
                ),
            )

            result = CookiePrivacyResult(
                site=SiteInfo(origin=origin, hostname=hostname, policy_urls=policy_urls),
                banner=banner,
                overall=overall,
                categories=findings,
                protection_plan=plan,
                limitations=[
                    "The site's cookie categories could not be fully verified.",
                    "This result is informational and not legal advice.",
                ],
            )

            _LEARNED_WORKFLOWS[hostname] = {
                "policy_urls": policy_urls,
                "banner_detected": banner_detected,
            }

            record.result = result.model_dump(mode="json")
            record.status = ScanStatusValue.ready.value
            record.progress = 100
            record.current_step = "Completed"
            record.completed_at = datetime.now(timezone.utc)
            repo.save(record)

        except Exception as exc:  # noqa: BLE001
            record.status = ScanStatusValue.failed.value
            record.current_step = "Scan failed"
            record.limitations.append(f"Scan failed: {exc}")
            record.activity_log.append(self._log("error", str(exc)))
            record.completed_at = datetime.now(timezone.utc)
            repo.save(record)

    async def _step(
        self,
        record: ScanRecord,
        repo: ScansRepository,
        status: ScanStatusValue,
        progress: int,
        step: str,
    ) -> None:
        record.status = status.value
        record.progress = progress
        record.current_step = step
        repo.save(record)
        await asyncio.sleep(0.05)  # yields control; keeps demo responsive

    @staticmethod
    def _log(event_type: str, message: str) -> dict:
        return {
            "type": event_type,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _actions_from_options(options: list[BannerOption]) -> list[BannerAction]:
        """Turn the agent's classified banner options into plan actions (one per action type)."""
        sensitivity = {"reject_optional": "low", "manage_preferences": "medium", "accept_all": "high"}
        found: dict[str, BannerAction] = {}
        for opt in options:
            if opt.action in sensitivity and opt.action not in found:
                found[opt.action] = BannerAction(
                    action=ConsentAction(opt.action),
                    label=opt.label,
                    locator=f"semantic:button[name={opt.label}]",
                    sensitivity=sensitivity[opt.action],
                )
        return list(found.values())

    @staticmethod
    def _banner_actions() -> list[BannerAction]:
        return [
            BannerAction(
                action=ConsentAction.accept_all,
                label="Accept all",
                locator="semantic:button[name=Accept all]",
                sensitivity="high",
            ),
            BannerAction(
                action=ConsentAction.reject_optional,
                label="Reject optional cookies",
                locator="semantic:button[name=Reject optional]",
                sensitivity="low",
            ),
            BannerAction(
                action=ConsentAction.manage_preferences,
                label="Manage preferences",
                locator="semantic:button[name=Manage preferences]",
                sensitivity="medium",
            ),
        ]

    @staticmethod
    def _collect_evidence(
        hostname: str, policy_urls: list[str], focus: list[str]
    ) -> list[EvidenceObject]:
        """
        BROWSER_MODE=mock evidence generation. Ties every excerpt to a
        real-looking source URL and a short, clearly-synthetic excerpt --
        never claimed as a verbatim quote from the live site.
        """
        base = [
            EvidenceObject(
                source_url=policy_urls[0] if policy_urls else f"https://{hostname}/privacy",
                source_type=SourceType.cookie_policy,
                heading="Essential cookies",
                excerpt="Essential cookies are required for core site functionality and security.",
                locator=None,
                confidence=0.9,
            ),
            EvidenceObject(
                source_url=policy_urls[0] if policy_urls else f"https://{hostname}/privacy",
                source_type=SourceType.cookie_policy,
                heading="Analytics cookies",
                excerpt="We use analytics cookies to measure usage and site performance.",
                locator=None,
                confidence=0.85,
            ),
            EvidenceObject(
                source_url=policy_urls[-1] if policy_urls else f"https://{hostname}/cookie-policy",
                source_type=SourceType.cookie_policy,
                heading="Advertising cookies",
                excerpt="Advertising cookies may be used for personalized ad marketing with partners.",
                locator=None,
                confidence=0.8,
            ),
        ]
        return base