from __future__ import annotations

from dataclasses import dataclass


LIVE_SMOKE_SCRIPT_STAGE = "201P"
LIVE_SMOKE_SCRIPT_STATUS = "ready_for_manual_live_smoke_v0"


@dataclass(frozen=True, slots=True)
class LiveSmokeStep:
    step_id: str
    command: str
    expected: str
    fallback: str
    stop_if_missing: bool

    def __post_init__(self) -> None:
        if not self.step_id or not self.command or not self.expected or not self.fallback:
            raise ValueError("201P live smoke steps require id, command, expected result, and fallback.")
        if not self.command.startswith("/"):
            raise ValueError("201P live smoke steps must be Telegram commands.")


@dataclass(frozen=True, slots=True)
class LiveSmokeScript:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    smoke_steps: tuple[LiveSmokeStep, ...]
    operator_prerequisites: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    pass_condition: str
    local_script_only: bool
    telegram_owner_gate_required: bool
    real_sources_or_fallback_required: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != LIVE_SMOKE_SCRIPT_STAGE:
            raise ValueError("201P live smoke scripts must identify the 201P stage.")
        if self.status != LIVE_SMOKE_SCRIPT_STATUS:
            raise ValueError("201P live smoke scripts must use the live smoke status.")
        if len(self.smoke_steps) < 9:
            raise ValueError("201P live smoke scripts must cover the complete pilot loop.")
        if any(not section for section in (self.operator_prerequisites, self.stop_conditions)):
            raise ValueError("201P live smoke scripts require prerequisites and stop conditions.")
        if not all(
            (
                self.local_script_only,
                self.telegram_owner_gate_required,
                self.real_sources_or_fallback_required,
                self.secrets_redacted,
                self.approval_gate_preserved,
            )
        ):
            raise ValueError("201P live smoke scripts must preserve owner, fallback, redaction, and approval gates.")
        if any(
            (
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("201P live smoke scripts must not expand external action authority.")


def build_live_smoke_script(*, owner_id: str, robot_id: str) -> LiveSmokeScript:
    return LiveSmokeScript(
        stage=LIVE_SMOKE_SCRIPT_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=LIVE_SMOKE_SCRIPT_STATUS,
        smoke_steps=(
            _step("owner_gate", "/start", "Roboticxs product shell renders for the owner.", "Owner mismatch refuses access.", True),
            _step("pilot_pack", "/pilot_pack", "Pilot checklist, blocked actions, demo script, source examples, usage expectations, and onboarding copy are visible.", "No fallback accepted; the pilot pack must render.", True),
            _step("pilot_audit", "/pilot_audit", "Audit gate shows PASS for the 190P-199P loop and residue policy.", "No fallback accepted; audit gate must pass before live smoke.", True),
            _step("daily_brief", "/daily_brief", "Daily brief shows Calendar, Gmail, Memory, and Document context where available plus source trace.", "Explicit unavailable-source fallback is acceptable; fake source data is not.", False),
            _step("prep", "/prep", "Prep output shows Calendar, Gmail, Memory, document context, smart ranking, and source receipt where available.", "Explicit read-only connector fallback is acceptable.", False),
            _step("suggestions", "/suggestions", "Suggestion inbox shows P0-P3 priority, reason codes, confidence, safe next action, and source trace.", "Empty inbox is acceptable only if it says no local suggestions.", False),
            _step("drafts", "/drafts", "Draft queue shows intent, audience, tone, source basis, risk note, approval state, expiry, and editable body.", "Empty draft queue is acceptable only after no suggestion draft was created.", False),
            _step("usage", "/usage", "Usage output shows local estimated cost ledger and no live billing claim.", "Empty ledger is acceptable only if local estimated boundary is visible.", False),
            _step("pilot", "/pilot", "Controlled pilot receipt ties daily brief, prep, suggestion, draft, approval, Gmail draft/export, source receipt, and usage receipt.", "Fixture mode is acceptable; dangerous writes are not.", True),
            _step("blocked_actions", "/pilot_pack", "Blocked actions remain visible after the run.", "No fallback accepted for blocked-action visibility.", True),
        ),
        operator_prerequisites=(
            "Run from an owner-gated Telegram account.",
            "Use real Calendar/Gmail/Memory sources where configured.",
            "Accept explicit fallback only when a source is unavailable.",
            "Do not paste secrets, tokens, client secrets, or OAuth material into Telegram.",
            "Do not continue if a command claims Gmail send, Calendar write, CRM write, WhatsApp, or destructive authority.",
        ),
        stop_conditions=(
            "Any Telegram owner gate failure for the pilot owner.",
            "Missing /pilot_pack or /pilot_audit output.",
            "Missing source trace on daily/prep/pilot outputs.",
            "Cost or usage output claims live billing without authority.",
            "Gmail send/archive/delete/modify appears as enabled.",
            "Calendar write, CRM write, WhatsApp, or destructive action appears as enabled.",
            "A secret or token appears in output.",
        ),
        pass_condition="All required smoke commands render real source context or explicit fallback, with source trace, approval boundaries, and usage/cost visibility, and no dangerous writes.",
        local_script_only=True,
        telegram_owner_gate_required=True,
        real_sources_or_fallback_required=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_live_smoke_script(script: LiveSmokeScript) -> str:
    return "\n".join(
        [
            "Live Smoke Script",
            "",
            f"Stage: {script.stage}",
            f"Status: {script.status}",
            "",
            "Operator prerequisites:",
            *[f"- {item}" for item in script.operator_prerequisites],
            "",
            "Smoke steps:",
            *[
                f"{index}. {step.command} [{step.step_id}]\n   Expected: {step.expected}\n   Fallback: {step.fallback}\n   Stop if missing: {'yes' if step.stop_if_missing else 'no'}"
                for index, step in enumerate(script.smoke_steps, start=1)
            ],
            "",
            "Stop conditions:",
            *[f"- {item}" for item in script.stop_conditions],
            "",
            "Pass condition:",
            f"- {script.pass_condition}",
            "",
            "Gmail send: disabled",
            "Gmail modify/archive/delete: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )


def _step(step_id: str, command: str, expected: str, fallback: str, stop_if_missing: bool) -> LiveSmokeStep:
    return LiveSmokeStep(
        step_id=step_id,
        command=command,
        expected=expected,
        fallback=fallback,
        stop_if_missing=stop_if_missing,
    )
