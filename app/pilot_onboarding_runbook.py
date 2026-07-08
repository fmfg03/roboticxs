from __future__ import annotations

from dataclasses import dataclass


PILOT_ONBOARDING_RUNBOOK_STAGE = "217P"
PILOT_ONBOARDING_RUNBOOK_STATUS = "local_day_0_day_7_runbook_v0"


@dataclass(frozen=True, slots=True)
class PilotRunbookDay:
    day: str
    title: str
    command: str
    expected_result: str
    fallback_status: str
    stop_condition: str

    def __post_init__(self) -> None:
        if not all((self.day, self.title, self.command, self.expected_result, self.fallback_status, self.stop_condition)):
            raise ValueError("217P runbook days require complete operational details.")


@dataclass(frozen=True, slots=True)
class PilotOnboardingRunbook:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    days: tuple[PilotRunbookDay, ...]
    prerequisites: tuple[str, ...]
    pass_condition: str
    local_runbook_only: bool
    external_invite_allowed: bool
    provisioning_write_allowed: bool
    connector_activation_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_ONBOARDING_RUNBOOK_STAGE:
            raise ValueError("217P runbooks must identify the 217P stage.")
        if self.status != PILOT_ONBOARDING_RUNBOOK_STATUS:
            raise ValueError("217P runbooks must use the runbook status.")
        if tuple(day.day for day in self.days) != ("Day 0", "Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"):
            raise ValueError("217P runbooks must cover Day 0 through Day 7.")
        if not self.prerequisites or not self.pass_condition:
            raise ValueError("217P runbooks require prerequisites and a pass condition.")
        if any(
            (
                not self.local_runbook_only,
                self.external_invite_allowed,
                self.provisioning_write_allowed,
                self.connector_activation_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("217P runbooks must not expand pilot authority.")
        if not self.secrets_redacted:
            raise ValueError("217P runbooks must be redacted.")


def build_pilot_onboarding_runbook(*, owner_id: str, robot_id: str) -> PilotOnboardingRunbook:
    return PilotOnboardingRunbook(
        stage=PILOT_ONBOARDING_RUNBOOK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_ONBOARDING_RUNBOOK_STATUS,
        prerequisites=(
            "pilot user appears in strict local allowlist",
            "consent text has been presented",
            "pilot data boundary is ready_local or has explicit cross-scope findings",
            "live connectors are read-only or show fallback status",
        ),
        days=(
            PilotRunbookDay(
                day="Day 0",
                title="setup, consent, allowlist",
                command="/pilot_consent <alias> then /pilot_provision <telegram_id> <alias>",
                expected_result="pilot has clear consent text and local allowlist receipt",
                fallback_status="manual setup review if consent or Telegram id is missing",
                stop_condition="stop if consent is unclear or owner/robot scope does not match",
            ),
            PilotRunbookDay(
                day="Day 1",
                title="first daily loop",
                command="/founder_loop or /daily_brief",
                expected_result="first useful daily operating card with setup warnings and source trace where available",
                fallback_status="explicit fallback if Calendar, Gmail, or Memory is unavailable",
                stop_condition="stop if output pretends live data exists without connector evidence",
            ),
            PilotRunbookDay(
                day="Day 2",
                title="memory review",
                command="/memory_review then memory decision commands",
                expected_result="approved, corrected, or rejected memory receipts stay user/robot scoped",
                fallback_status="no_pending_memory is acceptable",
                stop_condition="stop if another user's memory appears",
            ),
            PilotRunbookDay(
                day="Day 3",
                title="meeting prep",
                command="/prep",
                expected_result="meeting prep uses Calendar, Gmail, Memory, or fallback status with source trace",
                fallback_status="read-only context unavailable is shown explicitly",
                stop_condition="stop if prep contains unsourced sensitive claims",
            ),
            PilotRunbookDay(
                day="Day 4",
                title="document review",
                command="send a document or use document review flow",
                expected_result="document review proposes safe downstream actions without external writes",
                fallback_status="document text unavailable is shown explicitly",
                stop_condition="stop if legal, financial, or medical claims appear as advice",
            ),
            PilotRunbookDay(
                day="Day 5",
                title="draft, revision, approval",
                command="/drafts then /draft_revise and approval/export commands",
                expected_result="draft can be revised and approved for export or Gmail draft only",
                fallback_status="no_pending_drafts is acceptable",
                stop_condition="stop if Gmail send or Calendar write is attempted",
            ),
            PilotRunbookDay(
                day="Day 6",
                title="feedback and issue capture",
                command="/feedback then 218P issue commands when available",
                expected_result="useful, wrong, noisy, stale, missing_source, bad_draft, or too_verbose feedback is captured",
                fallback_status="issue capture is pending until 218P",
                stop_condition="stop if pilot friction is only captured outside Roboticxs",
            ),
            PilotRunbookDay(
                day="Day 7",
                title="weekly report and decision",
                command="/pilot_metrics then 220P weekly report when available",
                expected_result="operator can decide continue, pause, fix, or exit using visible receipts",
                fallback_status="weekly report is pending until 220P",
                stop_condition="stop if value, cost, safety, or issue status cannot be explained",
            ),
        ),
        pass_condition=(
            "A friendly pilot can run Day 0 through Day 7 with consent, boundary visibility, daily use, memory, prep, "
            "documents, drafts, feedback, and decision points without dangerous writes or fake live data."
        ),
        local_runbook_only=True,
        external_invite_allowed=False,
        provisioning_write_allowed=False,
        connector_activation_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
    )


def render_pilot_onboarding_runbook(runbook: PilotOnboardingRunbook) -> str:
    lines = [
        "Pilot Onboarding Runbook",
        "",
        f"Stage: {runbook.stage}",
        f"Status: {runbook.status}",
        f"Owner: {runbook.owner_id}",
        f"Robot: {runbook.robot_id}",
        "",
        "Prerequisites:",
        *[f"- {item}" for item in runbook.prerequisites],
        "",
        "Day 0-Day 7:",
    ]
    for day in runbook.days:
        lines.extend(
            [
                f"- {day.day}: {day.title}",
                f"  Command: {day.command}",
                f"  Expected: {day.expected_result}",
                f"  Fallback: {day.fallback_status}",
                f"  Stop: {day.stop_condition}",
            ]
        )
    lines.extend(
        [
            "",
            f"Pass condition: {runbook.pass_condition}",
            "",
            "Local runbook only: yes",
            "External invite: disabled",
            "Provisioning writes: disabled",
            "Connector activation: disabled",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "Destructive actions: disabled",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)
