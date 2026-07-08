from __future__ import annotations

from dataclasses import dataclass


FRIENDLY_PILOT_LAUNCH_BASELINE_STAGE = "222P"
FRIENDLY_PILOT_LAUNCH_BASELINE_STATUS = "local_friendly_pilot_launch_baseline_v0"


@dataclass(frozen=True, slots=True)
class FriendlyPilotLaunchStep:
    name: str
    command: str
    expected_receipt: str
    status: str

    def __post_init__(self) -> None:
        if not all((self.name, self.command, self.expected_receipt, self.status)):
            raise ValueError("222P friendly pilot launch steps require name, command, receipt, and status.")
        if self.status not in {"available_local", "fallback_explicit", "blocked_until_setup"}:
            raise ValueError("222P friendly pilot launch step status is unsupported.")


@dataclass(frozen=True, slots=True)
class FriendlyPilotLaunchBaseline:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    pilot_alias: str
    launch_steps: tuple[FriendlyPilotLaunchStep, ...]
    pass_conditions: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    fallback_policy: str
    local_baseline_only: bool
    live_data_claimed: bool
    external_invite_sent: bool
    connector_activation_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool
    source_trace_preserved: bool
    usage_cost_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != FRIENDLY_PILOT_LAUNCH_BASELINE_STAGE:
            raise ValueError("222P friendly pilot launch baselines must identify the 222P stage.")
        if self.status != FRIENDLY_PILOT_LAUNCH_BASELINE_STATUS:
            raise ValueError("222P friendly pilot launch baselines must use the launch baseline status.")
        if len(self.launch_steps) < 10:
            raise ValueError("222P friendly pilot launch baseline requires the full 10-step pilot launch flow.")
        if not self.pass_conditions or not self.stop_conditions:
            raise ValueError("222P friendly pilot launch baseline requires pass and stop conditions.")
        if not self.local_baseline_only or self.live_data_claimed or self.external_invite_sent:
            raise ValueError("222P friendly pilot launch baseline must remain local and avoid live-data claims.")
        if any(
            (
                self.connector_activation_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("222P friendly pilot launch baseline must not expand external authority.")
        if not all((self.secrets_redacted, self.approval_gate_preserved, self.source_trace_preserved, self.usage_cost_preserved)):
            raise ValueError("222P friendly pilot launch baseline must preserve redaction, approval, trace, and cost semantics.")


def build_friendly_pilot_launch_baseline(
    *,
    owner_id: str,
    robot_id: str,
    pilot_alias: str = "Friendly pilot",
) -> FriendlyPilotLaunchBaseline:
    alias = pilot_alias.strip() or "Friendly pilot"
    return FriendlyPilotLaunchBaseline(
        stage=FRIENDLY_PILOT_LAUNCH_BASELINE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FRIENDLY_PILOT_LAUNCH_BASELINE_STATUS,
        pilot_alias=alias,
        launch_steps=(
            FriendlyPilotLaunchStep("Allowlisted user", "/pilot_allowlist", "strict local allowlist receipt", "available_local"),
            FriendlyPilotLaunchStep("Consent presented", "/pilot_consent <alias>", "local consent text receipt", "available_local"),
            FriendlyPilotLaunchStep("Runbook available", "/pilot_runbook", "Day 0-Day 7 runbook receipt", "available_local"),
            FriendlyPilotLaunchStep("Data boundary passes", "/pilot_boundary", "owner/robot scope boundary report", "available_local"),
            FriendlyPilotLaunchStep("Daily loop runs", "/founder_loop", "daily operating card or explicit fallback", "available_local"),
            FriendlyPilotLaunchStep("Feedback captured", "/feedback useful <item_id>", "local feedback receipt", "available_local"),
            FriendlyPilotLaunchStep("Issue captured", "/report_issue medium <item_id>", "local issue receipt", "available_local"),
            FriendlyPilotLaunchStep("Safety log visible", "/pilot_safety", "local safety incident log", "available_local"),
            FriendlyPilotLaunchStep("Weekly report generated", "/pilot_weekly_report", "local weekly learning report", "available_local"),
            FriendlyPilotLaunchStep("Exit flow available", "/end_pilot", "local exit/data-removal receipt", "available_local"),
        ),
        pass_conditions=(
            "A friendly pilot can be allowlisted locally.",
            "Consent, blocked actions, logging, memory removal, and stop instructions are visible.",
            "Daily loop, feedback, issue capture, safety, weekly report, and exit flow all render from Telegram.",
            "Fallback status is explicit when live connectors or local data are unavailable.",
            "Source trace, approval, and usage/cost semantics remain visible where applicable.",
        ),
        stop_conditions=(
            "Gmail send appears.",
            "Calendar write appears.",
            "CRM write appears.",
            "WhatsApp appears.",
            "External delete/export/connector mutation is claimed.",
            "Secrets appear in output, logs, docs, tests, or receipts.",
        ),
        fallback_policy="Use explicit local fallback receipts; do not fake live pilot data or external actions.",
        local_baseline_only=True,
        live_data_claimed=False,
        external_invite_sent=False,
        connector_activation_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
        source_trace_preserved=True,
        usage_cost_preserved=True,
    )


def render_friendly_pilot_launch_baseline(baseline: FriendlyPilotLaunchBaseline) -> str:
    lines = [
        "Friendly Pilot Launch Baseline",
        "",
        f"Stage: {baseline.stage}",
        f"Status: {baseline.status}",
        f"Pilot: {baseline.pilot_alias}",
        "",
        "Launch flow:",
    ]
    lines.extend(
        f"- {step.name}: {step.command} | {step.expected_receipt} | {step.status}" for step in baseline.launch_steps
    )
    lines.extend(["", "Pass conditions:"])
    lines.extend(f"- {condition}" for condition in baseline.pass_conditions)
    lines.extend(["", "Stop conditions:"])
    lines.extend(f"- {condition}" for condition in baseline.stop_conditions)
    lines.extend(
        [
            "",
            f"Fallback policy: {baseline.fallback_policy}",
            "",
            "Safety:",
            "- Local baseline only: yes",
            "- Live data claimed: no",
            "- External invite sent: no",
            "- Connector activation: disabled",
            "- Gmail send: disabled",
            "- Calendar writes: disabled",
            "- CRM writes: disabled",
            "- WhatsApp: disabled",
            "- Destructive actions: disabled",
            "- External writes: disabled",
            "- Approval gate: preserved",
            "- Source trace: preserved",
            "- Usage/cost: preserved",
            "- Secrets: redacted",
        ]
    )
    return "\n".join(lines)
