from __future__ import annotations

from dataclasses import dataclass

from app.pilot_user_provisioning import PilotUserProvisioningRecord


PILOT_EXIT_DATA_REMOVAL_STAGE = "221P"
PILOT_EXIT_DATA_REMOVAL_STATUS = "local_pilot_exit_receipt_v0"
PILOT_EXIT_COMMANDS = (
    "/end_pilot",
    "/export_pilot_data",
    "/delete_pilot_memory",
    "/disable_pilot_connectors",
)
PILOT_EXIT_ACTION_BY_COMMAND = {
    "/end_pilot": "end_pilot",
    "/export_pilot_data": "export_pilot_data",
    "/delete_pilot_memory": "delete_pilot_memory",
    "/disable_pilot_connectors": "disable_pilot_connectors",
}


@dataclass(frozen=True, slots=True)
class PilotExitDataRemovalReceipt:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    command: str
    action: str
    pilot_user_id: str
    pilot_alias: str
    requested_scope: str
    local_receipt_created: bool
    local_policy: str
    export_manifest: tuple[str, ...]
    deletion_manifest: tuple[str, ...]
    connector_disable_manifest: tuple[str, ...]
    external_deletion_claimed: bool
    external_connector_disabled: bool
    data_exported_externally: bool
    memory_store_mutated: bool
    connector_activation_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_EXIT_DATA_REMOVAL_STAGE:
            raise ValueError("221P pilot exit receipts must identify the 221P stage.")
        if self.status != PILOT_EXIT_DATA_REMOVAL_STATUS:
            raise ValueError("221P pilot exit receipts must use the exit receipt status.")
        if self.command not in PILOT_EXIT_COMMANDS:
            raise ValueError("221P pilot exit command is unsupported.")
        if self.action != PILOT_EXIT_ACTION_BY_COMMAND[self.command]:
            raise ValueError("221P pilot exit action must match command.")
        if not all((self.owner_id, self.robot_id, self.pilot_user_id, self.pilot_alias, self.requested_scope)):
            raise ValueError("221P pilot exit receipts require identity and scope.")
        if not self.local_receipt_created:
            raise ValueError("221P pilot exit must create a local receipt.")
        if any(
            (
                self.external_deletion_claimed,
                self.external_connector_disabled,
                self.data_exported_externally,
                self.memory_store_mutated,
                self.connector_activation_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("221P pilot exit receipts must not claim external or destructive authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("221P pilot exit receipts must be redacted and approval-preserving.")


def parse_pilot_exit_argument(argument: str | None, *, fallback_pilot_user_id: str) -> tuple[str, str]:
    parts = (argument or "").strip().split(maxsplit=1)
    if not parts:
        return fallback_pilot_user_id, "local_pilot_scope"
    pilot_user_id = parts[0].strip()
    scope = parts[1].strip() if len(parts) == 2 else "local_pilot_scope"
    return pilot_user_id or fallback_pilot_user_id, scope or "local_pilot_scope"


def build_pilot_exit_data_removal_receipt(
    *,
    owner_id: str,
    robot_id: str,
    command: str,
    pilot_user_id: str,
    requested_scope: str = "local_pilot_scope",
    pilot_users: tuple[PilotUserProvisioningRecord, ...] = (),
) -> PilotExitDataRemovalReceipt:
    normalized_command = command.strip()
    normalized_user_id = pilot_user_id.strip() or "local-pilot-user"
    matched_user = _find_pilot_user(normalized_user_id, pilot_users)
    action = PILOT_EXIT_ACTION_BY_COMMAND[normalized_command]
    return PilotExitDataRemovalReceipt(
        stage=PILOT_EXIT_DATA_REMOVAL_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_EXIT_DATA_REMOVAL_STATUS,
        command=normalized_command,
        action=action,
        pilot_user_id=normalized_user_id,
        pilot_alias=matched_user.user_alias if matched_user else "local pilot user",
        requested_scope=requested_scope.strip() or "local_pilot_scope",
        local_receipt_created=True,
        local_policy=_local_policy(action),
        export_manifest=_export_manifest(action),
        deletion_manifest=_deletion_manifest(action),
        connector_disable_manifest=_connector_disable_manifest(action),
        external_deletion_claimed=False,
        external_connector_disabled=False,
        data_exported_externally=False,
        memory_store_mutated=False,
        connector_activation_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_pilot_exit_data_removal_receipt(receipt: PilotExitDataRemovalReceipt) -> str:
    lines = [
        "Pilot Exit / Data Removal",
        "",
        f"Stage: {receipt.stage}",
        f"Status: {receipt.status}",
        f"Command: {receipt.command}",
        f"Action: {receipt.action}",
        f"Pilot user: {receipt.pilot_user_id}",
        f"Alias: {receipt.pilot_alias}",
        f"Requested scope: {receipt.requested_scope}",
        f"Local policy: {receipt.local_policy}",
        "",
        "Export manifest:",
        *_bullet_lines(receipt.export_manifest),
        "",
        "Deletion manifest:",
        *_bullet_lines(receipt.deletion_manifest),
        "",
        "Connector disable manifest:",
        *_bullet_lines(receipt.connector_disable_manifest),
        "",
        "Receipt:",
        "- Local receipt created: yes",
        "- External deletion claimed: no",
        "- External connector disabled: no",
        "- External data export: no",
        "- Memory Store mutation: disabled",
        "- Gmail send: disabled",
        "- Calendar writes: disabled",
        "- CRM writes: disabled",
        "- WhatsApp: disabled",
        "- Destructive actions: disabled",
        "- Approval gate: preserved",
        "- Secrets: redacted",
    ]
    return "\n".join(lines)


def render_pilot_exit_usage() -> str:
    return "\n".join(
        [
            "Pilot Exit / Data Removal",
            "",
            "Usage:",
            "- /end_pilot [pilot_user_id] [scope]",
            "- /export_pilot_data [pilot_user_id] [scope]",
            "- /delete_pilot_memory [pilot_user_id] [scope]",
            "- /disable_pilot_connectors [pilot_user_id] [scope]",
            "",
            "Boundary:",
            "- Local receipt only until live data removal is separately approved.",
            "- External deletes and connector changes are not claimed.",
        ]
    )


def _find_pilot_user(
    pilot_user_id: str,
    pilot_users: tuple[PilotUserProvisioningRecord, ...],
) -> PilotUserProvisioningRecord | None:
    for user in pilot_users:
        if str(user.allowed_telegram_user_id) == pilot_user_id:
            return user
    return None


def _local_policy(action: str) -> str:
    if action == "end_pilot":
        return "mark pilot exit intent locally; no account or connector mutation performed"
    if action == "export_pilot_data":
        return "show local export manifest only; no external file or provider export performed"
    if action == "delete_pilot_memory":
        return "record local memory deletion request only; Memory Store is not mutated"
    if action == "disable_pilot_connectors":
        return "record connector-disable request only; provider connectors are not changed"
    return "local receipt only"


def _export_manifest(action: str) -> tuple[str, ...]:
    if action == "export_pilot_data":
        return (
            "pilot profile and consent receipts",
            "feedback and issue receipts",
            "usage and cost estimates",
            "safety incident receipts",
            "local memory provenance summaries",
        )
    return ("available via /export_pilot_data",)


def _deletion_manifest(action: str) -> tuple[str, ...]:
    if action == "delete_pilot_memory":
        return (
            "approved local memory ids for this pilot",
            "memory correction receipts",
            "source provenance retained as receipt references only",
        )
    if action == "end_pilot":
        return ("no deletion performed; use /delete_pilot_memory for local memory removal request receipt",)
    return ("no deletion performed by this command",)


def _connector_disable_manifest(action: str) -> tuple[str, ...]:
    if action == "disable_pilot_connectors":
        return (
            "calendar read-only connector disable request",
            "gmail read-only connector disable request",
            "local memory context disable request",
        )
    if action == "end_pilot":
        return ("connector disable not performed; use /disable_pilot_connectors for local disable request receipt",)
    return ("no connector change performed by this command",)


def _bullet_lines(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- none"]
