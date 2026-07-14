from __future__ import annotations

from dataclasses import dataclass


PILOT_DATA_BOUNDARY_STAGE = "216P"
PILOT_DATA_BOUNDARY_STATUS = "local_scope_boundary_v0"
PILOT_DATA_BOUNDARY_ITEM_TYPES = (
    "memory",
    "approval",
    "draft",
    "feedback",
    "usage",
    "source_trace",
    "gmail_trace",
    "document_trace",
)


@dataclass(frozen=True, slots=True)
class PilotDataBoundaryItem:
    item_id: str
    item_type: str
    owner_id: str
    robot_id: str
    scope_label: str

    def __post_init__(self) -> None:
        if not all((self.item_id, self.item_type, self.owner_id, self.robot_id, self.scope_label)):
            raise ValueError("216P boundary items require identity and scope.")
        if self.item_type not in PILOT_DATA_BOUNDARY_ITEM_TYPES:
            raise ValueError("216P boundary item type is unsupported.")


@dataclass(frozen=True, slots=True)
class PilotDataBoundaryReport:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    items: tuple[PilotDataBoundaryItem, ...]
    scoped_items: int
    cross_scope_items: tuple[PilotDataBoundaryItem, ...]
    memory_scoped: bool
    approvals_scoped: bool
    drafts_scoped: bool
    feedback_scoped: bool
    usage_scoped: bool
    source_traces_scoped: bool
    gmail_traces_scoped: bool
    document_traces_scoped: bool
    local_report_only: bool
    data_migration_allowed: bool
    external_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_DATA_BOUNDARY_STAGE:
            raise ValueError("216P data boundary reports must identify the 216P stage.")
        if self.status != PILOT_DATA_BOUNDARY_STATUS:
            raise ValueError("216P data boundary reports must use the boundary status.")
        if self.scoped_items + len(self.cross_scope_items) != len(self.items):
            raise ValueError("216P data boundary counts must match report items.")
        if any(
            (
                not self.local_report_only,
                self.data_migration_allowed,
                self.external_write_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("216P data boundary reports must not expand write authority.")
        if not self.secrets_redacted:
            raise ValueError("216P data boundary reports must be redacted.")


def build_pilot_data_boundary_report(
    *,
    owner_id: str,
    robot_id: str,
    items: tuple[PilotDataBoundaryItem, ...] = (),
) -> PilotDataBoundaryReport:
    scoped_items = tuple(item for item in items if item.owner_id == owner_id and item.robot_id == robot_id)
    cross_scope_items = tuple(item for item in items if item not in scoped_items)
    scoped_types = {item.item_type for item in scoped_items}
    cross_scope_types = {item.item_type for item in cross_scope_items}
    return PilotDataBoundaryReport(
        stage=PILOT_DATA_BOUNDARY_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_DATA_BOUNDARY_STATUS,
        items=items,
        scoped_items=len(scoped_items),
        cross_scope_items=cross_scope_items,
        memory_scoped=_type_is_scoped("memory", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        approvals_scoped=_type_is_scoped("approval", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        drafts_scoped=_type_is_scoped("draft", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        feedback_scoped=_type_is_scoped("feedback", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        usage_scoped=_type_is_scoped("usage", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        source_traces_scoped=_type_is_scoped("source_trace", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        gmail_traces_scoped=_type_is_scoped("gmail_trace", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        document_traces_scoped=_type_is_scoped("document_trace", scoped_types=scoped_types, cross_scope_types=cross_scope_types),
        local_report_only=True,
        data_migration_allowed=False,
        external_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
    )


def render_pilot_data_boundary(report: PilotDataBoundaryReport) -> str:
    lines = [
        "Pilot Data Boundary",
        "",
        f"Stage: {report.stage}",
        f"Status: {report.status}",
        f"Owner: {report.owner_id}",
        f"Robot: {report.robot_id}",
        f"Items checked: {len(report.items)}",
        f"Scoped items: {report.scoped_items}",
        f"Cross-scope items: {len(report.cross_scope_items)}",
        f"Boundary health: {_boundary_health(report)}",
        "",
        "Scoped surfaces:",
        f"- Memory: {_yes_no(report.memory_scoped)}",
        f"- Approvals: {_yes_no(report.approvals_scoped)}",
        f"- Drafts: {_yes_no(report.drafts_scoped)}",
        f"- Feedback: {_yes_no(report.feedback_scoped)}",
        f"- Usage: {_yes_no(report.usage_scoped)}",
        f"- Source traces: {_yes_no(report.source_traces_scoped)}",
        f"- Gmail traces: {_yes_no(report.gmail_traces_scoped)}",
        f"- Document traces: {_yes_no(report.document_traces_scoped)}",
    ]
    if report.cross_scope_items:
        lines.extend(["", "Cross-scope findings:"])
        lines.extend(
            f"- {item.item_type} {item.item_id} owner={item.owner_id} robot={item.robot_id} scope={item.scope_label}"
            for item in report.cross_scope_items
        )
    lines.extend(_authority_lines())
    return "\n".join(lines)


def _type_is_scoped(item_type: str, *, scoped_types: set[str], cross_scope_types: set[str]) -> bool:
    return item_type in scoped_types and item_type not in cross_scope_types


def _boundary_health(report: PilotDataBoundaryReport) -> str:
    if report.cross_scope_items:
        return "blocked_cross_scope_items"
    if not report.items:
        return "fallback_no_local_items"
    return "ready_local"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _authority_lines() -> list[str]:
    return [
        "",
        "Local report only: yes",
        "Data migration: disabled",
        "External writes: disabled",
        "Gmail send: disabled",
        "Calendar writes: disabled",
        "CRM writes: disabled",
        "WhatsApp: disabled",
        "Destructive actions: disabled",
        "Secrets: redacted",
    ]
