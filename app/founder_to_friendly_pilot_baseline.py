from __future__ import annotations

from dataclasses import dataclass


FOUNDER_TO_FRIENDLY_PILOT_BASELINE_STAGE = "212P"
FOUNDER_TO_FRIENDLY_PILOT_BASELINE_STATUS = "founder_to_friendly_pilot_baseline_v0"


@dataclass(frozen=True, slots=True)
class FounderToFriendlyPilotBaseline:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    flow_steps: tuple[tuple[str, str, str], ...]
    required_receipts: tuple[str, ...]
    readiness_checks: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    local_baseline_only: bool
    dangerous_writes_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != FOUNDER_TO_FRIENDLY_PILOT_BASELINE_STAGE:
            raise ValueError("212P pilot baseline must identify the 212P stage.")
        if self.status != FOUNDER_TO_FRIENDLY_PILOT_BASELINE_STATUS:
            raise ValueError("212P pilot baseline must use the baseline status.")
        if len(self.flow_steps) < 6 or not self.required_receipts or not self.readiness_checks or not self.stop_conditions:
            raise ValueError("212P pilot baseline requires flow, receipts, readiness checks, and stop conditions.")
        if not self.local_baseline_only or self.dangerous_writes_allowed:
            raise ValueError("212P pilot baseline must remain local and block dangerous writes.")
        if any(
            (
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("212P pilot baseline must not expand external write authority.")
        if not self.secrets_redacted:
            raise ValueError("212P pilot baseline must be redacted.")


def build_founder_to_friendly_pilot_baseline(*, owner_id: str, robot_id: str) -> FounderToFriendlyPilotBaseline:
    return FounderToFriendlyPilotBaseline(
        stage=FOUNDER_TO_FRIENDLY_PILOT_BASELINE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FOUNDER_TO_FRIENDLY_PILOT_BASELINE_STATUS,
        flow_steps=(
            ("Founder loop", "/founder_loop", "Run the morning operating card and pick one next action."),
            ("Feedback capture", "/feedback useful <item_id>", "Record useful/wrong/noisy/stale/missing-source feedback on real outputs."),
            ("Draft revision", "/draft_revise <draft_id> shorter", "Revise locally before approval/export/Gmail draft creation."),
            ("Memory correction", "/memory_stale <memory_id>", "Mark wrong/stale/duplicate/merge/never-use memory signals without mutation."),
            ("Pilot metrics", "/pilot_metrics", "Review usage, value, feedback, cost, blocks, and fallback status."),
            ("Friendly onboarding", "/friendly_onboarding", "Use the 1-3 user setup, allowed commands, blocked actions, and stop conditions."),
        ),
        required_receipts=(
            "source trace or explicit fallback",
            "feedback receipt or ledger entry",
            "draft revision receipt before approval/export",
            "memory correction receipt when memory is wrong/stale/duplicate",
            "usage/cost receipt or no_local_metrics_yet fallback",
            "safety receipt showing Gmail send and Calendar writes disabled",
        ),
        readiness_checks=(
            "/setup and /checkup show connector readiness or fallback.",
            "/live_smoke has a manual pass path.",
            "/pilot_pack and /friendly_onboarding are available.",
            "/pilot_metrics can show local data or explicit empty fallback.",
            "Owner gate remains enabled.",
        ),
        stop_conditions=(
            "Any Gmail send, Calendar write, CRM write, WhatsApp, or destructive external action appears.",
            "Any output loses source trace or fallback where source matters.",
            "Any approval gate is bypassed.",
            "Any secret appears in output, docs, receipts, tests, or logs.",
            "The friendly user cannot run the flow without live improvisation.",
        ),
        local_baseline_only=True,
        dangerous_writes_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
    )


def render_founder_to_friendly_pilot_baseline(baseline: FounderToFriendlyPilotBaseline) -> str:
    lines = [
        "Founder-to-Friendly Pilot Baseline",
        "",
        f"Stage: {baseline.stage}",
        f"Status: {baseline.status}",
        "",
        "Pilot flow:",
    ]
    lines.extend(f"- {name}: {command} | {result}" for name, command, result in baseline.flow_steps)
    lines.extend(["", "Required receipts:"])
    lines.extend(f"- {receipt}" for receipt in baseline.required_receipts)
    lines.extend(["", "Readiness checks:"])
    lines.extend(f"- {check}" for check in baseline.readiness_checks)
    lines.extend(["", "Stop conditions:"])
    lines.extend(f"- {condition}" for condition in baseline.stop_conditions)
    lines.extend(
        [
            "",
            "Safety:",
            "- Local baseline only: yes",
            "- Gmail send: disabled",
            "- Calendar writes: disabled",
            "- CRM writes: disabled",
            "- WhatsApp: disabled",
            "- External writes: disabled",
            "- Secrets: redacted",
        ]
    )
    return "\n".join(lines)
