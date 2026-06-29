from __future__ import annotations

from dataclasses import dataclass


PILOT_USER_PROVISIONING_STAGE = "215P"
PILOT_USER_PROVISIONING_STATUS = "local_allowlist_provisioning_v0"
DEFAULT_PILOT_START_DATE = "2026-06-30"
DEFAULT_SKILL_PACKAGES = (
    "basic",
    "daily_brief",
    "meetings",
    "documents",
    "memory",
    "gmail_drafts",
    "usage",
)
DEFAULT_CONNECTOR_STATUS = (
    "telegram: allowlisted",
    "calendar: readonly_or_fallback",
    "gmail: readonly_or_fallback",
    "memory: local_scoped",
)


@dataclass(frozen=True, slots=True)
class PilotUserProvisioningRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    role: str
    user_alias: str
    allowed_telegram_user_id: int
    enabled_skill_packages: tuple[str, ...]
    connector_status: tuple[str, ...]
    pilot_start_date: str
    pilot_status: str
    strict_allowlist: bool
    consent_required: bool
    external_invite_sent: bool
    open_signup_allowed: bool
    connector_activation_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_USER_PROVISIONING_STAGE:
            raise ValueError("215P provisioning records must identify the 215P stage.")
        if self.status != PILOT_USER_PROVISIONING_STATUS:
            raise ValueError("215P provisioning records must use the provisioning status.")
        if self.role not in {"owner_founder", "friendly_user"}:
            raise ValueError("215P provisioning role is unsupported.")
        if not self.user_alias.strip():
            raise ValueError("215P provisioning records require a user alias.")
        if self.allowed_telegram_user_id <= 0:
            raise ValueError("215P provisioning records require a positive Telegram user id.")
        if not self.enabled_skill_packages or not self.connector_status:
            raise ValueError("215P provisioning records require skills and connector status.")
        if self.pilot_status not in {"pending_consent", "active_local", "paused", "ended"}:
            raise ValueError("215P provisioning status is unsupported.")
        if any(
            (
                not self.strict_allowlist,
                not self.consent_required,
                self.external_invite_sent,
                self.open_signup_allowed,
                self.connector_activation_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("215P provisioning must keep strict local allowlist authority.")
        if not self.secrets_redacted:
            raise ValueError("215P provisioning records must be redacted.")


def build_pilot_user_provisioning_record(
    *,
    owner_id: str,
    robot_id: str,
    allowed_telegram_user_id: int,
    user_alias: str,
    role: str = "friendly_user",
    pilot_start_date: str = DEFAULT_PILOT_START_DATE,
    pilot_status: str = "pending_consent",
) -> PilotUserProvisioningRecord:
    return PilotUserProvisioningRecord(
        stage=PILOT_USER_PROVISIONING_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_USER_PROVISIONING_STATUS,
        role=role,
        user_alias=user_alias.strip() or "Friendly pilot",
        allowed_telegram_user_id=allowed_telegram_user_id,
        enabled_skill_packages=DEFAULT_SKILL_PACKAGES,
        connector_status=DEFAULT_CONNECTOR_STATUS,
        pilot_start_date=pilot_start_date,
        pilot_status=pilot_status,
        strict_allowlist=True,
        consent_required=True,
        external_invite_sent=False,
        open_signup_allowed=False,
        connector_activation_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
    )


def parse_pilot_provision_argument(argument: str | None, *, fallback_telegram_user_id: int) -> tuple[int, str]:
    if not argument:
        return fallback_telegram_user_id, "Founder"
    parts = argument.strip().split(maxsplit=1)
    try:
        telegram_user_id = int(parts[0])
    except (TypeError, ValueError):
        return fallback_telegram_user_id, argument.strip() or "Friendly pilot"
    alias = parts[1].strip() if len(parts) > 1 else "Friendly pilot"
    return telegram_user_id, alias


def render_pilot_user_provisioning(record: PilotUserProvisioningRecord) -> str:
    lines = [
        "Pilot User Provisioning",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Alias: {record.user_alias}",
        f"Role: {record.role}",
        f"Robot: {record.robot_id}",
        f"Allowed Telegram user id: {record.allowed_telegram_user_id}",
        f"Pilot start date: {record.pilot_start_date}",
        f"Pilot status: {record.pilot_status}",
        "",
        "Enabled skill packages:",
        *_bullet_lines(record.enabled_skill_packages),
        "",
        "Connector status:",
        *_bullet_lines(record.connector_status),
    ]
    lines.extend(_authority_lines(record))
    return "\n".join(lines)


def render_pilot_allowlist(records: tuple[PilotUserProvisioningRecord, ...]) -> str:
    scoped_records = records or (
        build_pilot_user_provisioning_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            allowed_telegram_user_id=1,
            user_alias="Founder",
            role="owner_founder",
            pilot_status="active_local",
        ),
    )
    lines = [
        "Pilot User Allowlist",
        "",
        f"Stage: {PILOT_USER_PROVISIONING_STAGE}",
        f"Status: {PILOT_USER_PROVISIONING_STATUS}",
        f"Users: {len(scoped_records)}",
        "Strict allowlist: yes",
        "",
        "Allowlisted users:",
    ]
    for record in scoped_records:
        lines.append(
            f"- {record.allowed_telegram_user_id} | {record.user_alias} | {record.role} | "
            f"{record.pilot_status} | robot={record.robot_id}"
        )
    lines.extend(_authority_lines(scoped_records[0]))
    return "\n".join(lines)


def _bullet_lines(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items]


def _authority_lines(record: PilotUserProvisioningRecord) -> list[str]:
    return [
        "",
        "Strict allowlist: yes" if record.strict_allowlist else "Strict allowlist: no",
        "Consent required: yes",
        "External invite sent: no",
        "Open signup: disabled",
        "Connector activation: disabled",
        "Gmail send: disabled",
        "Calendar writes: disabled",
        "CRM writes: disabled",
        "WhatsApp: disabled",
        "Destructive actions: disabled",
        "Secrets: redacted",
    ]
