from __future__ import annotations

from dataclasses import dataclass


FRIENDLY_PILOT_INVITE_CONSENT_STAGE = "214P"
FRIENDLY_PILOT_INVITE_CONSENT_STATUS = "local_invite_consent_text_v0"


@dataclass(frozen=True, slots=True)
class FriendlyPilotInviteConsent:
    stage: str
    owner_id: str
    robot_id: str
    pilot_alias: str
    status: str
    invite_text: str
    readable_sources: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    approval_required_for: tuple[str, ...]
    logged_items: tuple[str, ...]
    stop_instructions: tuple[str, ...]
    memory_removal_instructions: tuple[str, ...]
    local_text_only: bool
    external_invite_sent: bool
    connector_activation_allowed: bool
    provisioning_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != FRIENDLY_PILOT_INVITE_CONSENT_STAGE:
            raise ValueError("214P invite consent records must identify the 214P stage.")
        if self.status != FRIENDLY_PILOT_INVITE_CONSENT_STATUS:
            raise ValueError("214P invite consent records must use the consent status.")
        if not self.pilot_alias.strip():
            raise ValueError("214P invite consent records require a pilot alias.")
        if not self.invite_text.strip():
            raise ValueError("214P invite consent records require invite text.")
        required_sections = (
            self.readable_sources,
            self.blocked_actions,
            self.approval_required_for,
            self.logged_items,
            self.stop_instructions,
            self.memory_removal_instructions,
        )
        if any(not section for section in required_sections):
            raise ValueError("214P invite consent records require all consent sections.")
        if any(
            (
                not self.local_text_only,
                self.external_invite_sent,
                self.connector_activation_allowed,
                self.provisioning_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("214P invite consent records must not create external authority.")
        if not self.secrets_redacted:
            raise ValueError("214P invite consent records must be redacted.")


def build_friendly_pilot_invite_consent(
    *,
    owner_id: str,
    robot_id: str,
    pilot_alias: str = "Friendly pilot",
) -> FriendlyPilotInviteConsent:
    alias = pilot_alias.strip() or "Friendly pilot"
    return FriendlyPilotInviteConsent(
        stage=FRIENDLY_PILOT_INVITE_CONSENT_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        pilot_alias=alias,
        status=FRIENDLY_PILOT_INVITE_CONSENT_STATUS,
        invite_text=(
            f"{alias}, Roboticxs is a controlled personal robot pilot. It can summarize approved context, "
            "prepare drafts, track memory proposals, and show receipts. It cannot send, delete, schedule, "
            "or change external systems without explicit approval."
        ),
        readable_sources=(
            "Telegram commands you send to the bot",
            "Calendar context only when connected in read-only mode",
            "Gmail context only when connected in read-only mode",
            "approved Roboticxs memory for your pilot user and robot",
            "documents you explicitly upload for review",
        ),
        blocked_actions=(
            "Gmail send, archive, delete, or mailbox modification",
            "Calendar create, update, delete, invites, or availability changes",
            "CRM writes or lead pipeline changes",
            "WhatsApp access or messaging",
            "external destructive actions",
        ),
        approval_required_for=(
            "saving or changing memory",
            "creating a Gmail draft",
            "exporting drafts or reviewed content",
            "using sensitive source context in an output",
        ),
        logged_items=(
            "commands used",
            "feedback and issue tags",
            "approval, rejection, and stale-block receipts",
            "source trace ids for important outputs",
            "usage and estimated cost receipts",
            "blocked safety events",
        ),
        stop_instructions=(
            "Use /end_pilot when the exit flow is enabled",
            "Ask the operator to disable connectors before continuing",
            "Stop using the bot if consent is unclear or a source looks wrong",
        ),
        memory_removal_instructions=(
            "Use /memory_wrong, /memory_stale, /memory_duplicate, or /memory_never_use for corrections",
            "Use /delete_pilot_memory when the removal flow is enabled",
            "Ask the operator for a local data review before pilot exit",
        ),
        local_text_only=True,
        external_invite_sent=False,
        connector_activation_allowed=False,
        provisioning_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
    )


def render_pilot_invite(consent: FriendlyPilotInviteConsent) -> str:
    lines = [
        "Friendly Pilot Invite",
        "",
        f"Stage: {consent.stage}",
        f"Status: {consent.status}",
        f"Pilot: {consent.pilot_alias}",
        "",
        consent.invite_text,
    ]
    lines.extend(_authority_lines(consent))
    return "\n".join(lines)


def render_pilot_consent(consent: FriendlyPilotInviteConsent) -> str:
    lines = [
        "Friendly Pilot Consent",
        "",
        f"Stage: {consent.stage}",
        f"Status: {consent.status}",
        f"Pilot: {consent.pilot_alias}",
        "",
        "What the robot can read:",
        *_bullet_lines(consent.readable_sources),
        "",
        "What the robot cannot do:",
        *_bullet_lines(consent.blocked_actions),
        "",
        "What requires approval:",
        *_bullet_lines(consent.approval_required_for),
        "",
        "What is logged:",
        *_bullet_lines(consent.logged_items),
        "",
        "How to stop:",
        *_bullet_lines(consent.stop_instructions),
        "",
        "How to remove or correct memory:",
        *_bullet_lines(consent.memory_removal_instructions),
    ]
    lines.extend(_authority_lines(consent))
    return "\n".join(lines)


def _bullet_lines(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items]


def _authority_lines(consent: FriendlyPilotInviteConsent) -> list[str]:
    return [
        "",
        "Local text only: yes" if consent.local_text_only else "Local text only: no",
        "External invite sent: no",
        "Connector activation: disabled",
        "Provisioning: disabled",
        "Gmail send: disabled",
        "Calendar writes: disabled",
        "CRM writes: disabled",
        "WhatsApp: disabled",
        "Destructive actions: disabled",
        "Secrets: redacted",
    ]
