from __future__ import annotations

from dataclasses import dataclass


FIRST_FRIENDLY_USER_ACTIVATION_STAGE = "223P"
FIRST_FRIENDLY_USER_ACTIVATION_STATUS = "local_first_friendly_user_activation_v0"


@dataclass(frozen=True, slots=True)
class FirstFriendlyUserActivationChecklistItem:
    name: str
    status: str
    evidence: str

    def __post_init__(self) -> None:
        if not all((self.name, self.status, self.evidence)):
            raise ValueError("223P activation checklist items require name, status, and evidence.")
        if self.status not in {"ready_local", "fallback_explicit", "needs_setup", "not_recorded"}:
            raise ValueError("223P activation checklist status is unsupported.")


@dataclass(frozen=True, slots=True)
class FirstFriendlyUserActivationReceipt:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    pilot_alias: str
    pilot_user_id: str
    activation_status: str
    setup_status: str
    first_successful_command: str
    first_useful_output: str
    first_feedback: str
    first_issue: str
    checklist: tuple[FirstFriendlyUserActivationChecklistItem, ...]
    activation_receipt_id: str
    local_activation_only: bool
    account_provisioned: bool
    external_invite_sent: bool
    connector_activation_allowed: bool
    live_data_claimed: bool
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
        if self.stage != FIRST_FRIENDLY_USER_ACTIVATION_STAGE:
            raise ValueError("223P activation receipts must identify the 223P stage.")
        if self.status != FIRST_FRIENDLY_USER_ACTIVATION_STATUS:
            raise ValueError("223P activation receipts must use the activation status.")
        if self.activation_status not in {"ready_for_first_use", "needs_setup", "blocked"}:
            raise ValueError("223P activation status is unsupported.")
        if not self.pilot_alias.strip() or not self.pilot_user_id.strip():
            raise ValueError("223P activation receipts require pilot alias and user id.")
        if len(self.checklist) < 7:
            raise ValueError("223P activation receipts require the activation checklist.")
        if any(
            (
                not self.local_activation_only,
                self.account_provisioned,
                self.external_invite_sent,
                self.connector_activation_allowed,
                self.live_data_claimed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("223P activation must remain local and must not expand external authority.")
        if not all((self.secrets_redacted, self.approval_gate_preserved, self.source_trace_preserved, self.usage_cost_preserved)):
            raise ValueError("223P activation must preserve redaction, approval, trace, and cost semantics.")


def parse_pilot_activation_argument(argument: str | None, *, fallback_pilot_user_id: str) -> tuple[str, str]:
    if not argument or not argument.strip():
        return fallback_pilot_user_id, "Friendly pilot"
    stripped = argument.strip()
    parts = stripped.split(maxsplit=1)
    if parts[0].isdigit():
        return parts[0], parts[1].strip() if len(parts) > 1 and parts[1].strip() else "Friendly pilot"
    return fallback_pilot_user_id, stripped


def build_first_friendly_user_activation_receipt(
    *,
    owner_id: str,
    robot_id: str,
    pilot_alias: str = "Friendly pilot",
    pilot_user_id: str = "local-friendly-user",
    first_successful_command: str = "/founder_loop",
    first_useful_output: str = "not_recorded_yet",
    first_feedback: str = "not_recorded_yet",
    first_issue: str = "none_recorded",
) -> FirstFriendlyUserActivationReceipt:
    alias = pilot_alias.strip() or "Friendly pilot"
    user_id = pilot_user_id.strip() or "local-friendly-user"
    checklist = (
        FirstFriendlyUserActivationChecklistItem("Allowlist", "ready_local", "/pilot_allowlist local receipt"),
        FirstFriendlyUserActivationChecklistItem("Consent", "ready_local", "/pilot_consent local receipt"),
        FirstFriendlyUserActivationChecklistItem("Setup status", "fallback_explicit", "readonly_or_fallback connectors"),
        FirstFriendlyUserActivationChecklistItem("First command", "ready_local", first_successful_command),
        FirstFriendlyUserActivationChecklistItem("First useful output", "not_recorded", first_useful_output),
        FirstFriendlyUserActivationChecklistItem("First feedback", "not_recorded", first_feedback),
        FirstFriendlyUserActivationChecklistItem("First issue", "not_recorded", first_issue),
    )
    return FirstFriendlyUserActivationReceipt(
        stage=FIRST_FRIENDLY_USER_ACTIVATION_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FIRST_FRIENDLY_USER_ACTIVATION_STATUS,
        pilot_alias=alias,
        pilot_user_id=user_id,
        activation_status="ready_for_first_use",
        setup_status="local_allowlist_and_consent_ready; connectors_readonly_or_explicit_fallback",
        first_successful_command=first_successful_command,
        first_useful_output=first_useful_output,
        first_feedback=first_feedback,
        first_issue=first_issue,
        checklist=checklist,
        activation_receipt_id=f"activation-223p-{_slug(user_id)}",
        local_activation_only=True,
        account_provisioned=False,
        external_invite_sent=False,
        connector_activation_allowed=False,
        live_data_claimed=False,
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


def render_first_friendly_user_activation_receipt(receipt: FirstFriendlyUserActivationReceipt) -> str:
    lines = [
        "First Friendly User Activation",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        f"Activation status: {receipt.activation_status}",
        f"Activation receipt: {receipt.activation_receipt_id}",
        f"Pilot: {receipt.pilot_alias}",
        f"Pilot user id: {receipt.pilot_user_id}",
        f"Setup status: {receipt.setup_status}",
        "",
        "Activation checklist:",
    ]
    lines.extend(f"- {item.name}: {item.status} | {item.evidence}" for item in receipt.checklist)
    lines.extend(
        [
            "",
            "First-use signals:",
            f"- First successful command: {receipt.first_successful_command}",
            f"- First useful output: {receipt.first_useful_output}",
            f"- First feedback: {receipt.first_feedback}",
            f"- First issue: {receipt.first_issue}",
            "",
            "Safety:",
            "- Local activation only: yes",
            "- Account provisioned: no",
            "- External invite sent: no",
            "- Connector activation: disabled",
            "- Live data claimed: no",
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


def _slug(value: str) -> str:
    safe = [character.lower() if character.isalnum() else "-" for character in value.strip()]
    compact = "-".join(part for part in "".join(safe).split("-") if part)
    return compact or "local-friendly-user"
