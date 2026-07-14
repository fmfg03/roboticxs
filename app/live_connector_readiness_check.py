from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json

from app.hermes_runtime_bootstrap import DEFAULT_GENERATED_AT, DEFAULT_OWNER_ID, DEFAULT_ROBOT_ID
from app.runtime_doctor import RuntimeDoctorStatus, build_runtime_doctor_status


LIVE_CONNECTOR_READINESS_CHECK_STAGE = "181P"
LIVE_CONNECTOR_READINESS_CHECK_STATUS = "completed_live_connector_readiness_check_v0"
ALLOWED_READINESS_STATUSES = frozenset(
    {
        "connected",
        "not_connected",
        "configured_placeholder",
        "disabled",
        "approval_required",
        "not_implemented",
        "blocked",
    }
)


@dataclass(frozen=True, slots=True)
class LiveConnectorReadinessItem:
    name: str
    status: str
    reason: str
    source: str
    safe_next_step: str

    def __post_init__(self) -> None:
        if self.status not in ALLOWED_READINESS_STATUSES:
            raise ValueError("181P readiness item has unsupported status.")


@dataclass(frozen=True, slots=True)
class LiveConnectorReadinessReport:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    overall_status: str
    items: tuple[LiveConnectorReadinessItem, ...]
    secrets_redacted: bool
    connector_activation_allowed: bool
    oauth_generation_allowed: bool
    oauth_refresh_allowed: bool
    gmail_draft_creation_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    external_write_allowed: bool
    memory_mutation_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    generated_at: str

    def __post_init__(self) -> None:
        if self.stage != LIVE_CONNECTOR_READINESS_CHECK_STAGE:
            raise ValueError("181P readiness report must identify the 181P stage.")
        if self.status != LIVE_CONNECTOR_READINESS_CHECK_STATUS:
            raise ValueError("181P readiness report must use the live connector readiness status.")
        if not self.secrets_redacted:
            raise ValueError("181P readiness report must redact secrets.")
        if any(
            (
                self.connector_activation_allowed,
                self.oauth_generation_allowed,
                self.oauth_refresh_allowed,
                self.gmail_draft_creation_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.external_write_allowed,
                self.memory_mutation_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
            )
        ):
            raise ValueError("181P readiness report must not expand authority.")


def build_live_connector_readiness_report(
    *,
    owner_id: str = DEFAULT_OWNER_ID,
    robot_id: str = DEFAULT_ROBOT_ID,
    env: dict[str, str] | None = None,
    generated_at: str = DEFAULT_GENERATED_AT,
) -> LiveConnectorReadinessReport:
    doctor_status = build_runtime_doctor_status(env=env, generated_at=generated_at)
    items = _build_readiness_items(doctor_status)
    return LiveConnectorReadinessReport(
        stage=LIVE_CONNECTOR_READINESS_CHECK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=LIVE_CONNECTOR_READINESS_CHECK_STATUS,
        overall_status=_overall_status(items),
        items=items,
        secrets_redacted=True,
        connector_activation_allowed=False,
        oauth_generation_allowed=False,
        oauth_refresh_allowed=False,
        gmail_draft_creation_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        external_write_allowed=False,
        memory_mutation_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        generated_at=generated_at,
    )


def render_live_connector_readiness_report(report: LiveConnectorReadinessReport) -> str:
    lines = [
        "Live Connector Readiness",
        "",
        f"Stage: {report.stage}",
        f"Status: {report.status}",
        f"Overall: {report.overall_status}",
        f"Robot: {report.robot_id}",
        "",
        "Sources:",
    ]
    lines.extend(f"- {item.name}: {item.status} ({item.reason})" for item in report.items)
    lines.extend(
        [
            "",
            "Boundaries:",
            "Secrets: redacted",
            "Connector activation: disabled",
            "OAuth generation: disabled",
            "OAuth refresh: disabled",
            "Gmail draft creation: disabled",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "External writes: disabled",
            "Memory mutation: disabled",
            "Model calls: disabled",
            "Tool calls: disabled",
            "",
            "No connector was activated.",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)


def render_compact_live_connector_readiness_block(report: LiveConnectorReadinessReport) -> tuple[str, ...]:
    summary_by_name = {item.name: item.status for item in report.items}
    return (
        "Live connector readiness:",
        f"- Calendar: {summary_by_name['Calendar read-only']}",
        f"- Gmail: {summary_by_name['Gmail context']}",
        f"- Documents: {summary_by_name['Documents intake']} / {summary_by_name['Document review']}",
        f"- Memory: {summary_by_name['Memory approval mode']}",
        f"- External writes: {summary_by_name['External writes']}",
        "- Full check: /checkup",
    )


def _build_readiness_items(doctor_status: RuntimeDoctorStatus) -> tuple[LiveConnectorReadinessItem, ...]:
    readiness = {item.service: item for item in doctor_status.service_readiness}
    calendar = readiness.get("calendar_readonly")
    gmail_metadata = readiness.get("gmail_metadata")
    gmail_readonly = readiness.get("gmail_readonly")

    calendar_status = "connected" if calendar and calendar.ready else "not_connected"
    gmail_status = "connected" if (gmail_metadata and gmail_metadata.ready) or (gmail_readonly and gmail_readonly.ready) else "not_connected"
    gmail_reason = _gmail_reason(gmail_metadata, gmail_readonly)
    return (
        LiveConnectorReadinessItem(
            name="Calendar read-only",
            status=calendar_status,
            reason=calendar.reason if calendar is not None else "calendar_readiness_missing",
            source="runtime_doctor_service_readiness",
            safe_next_step="Use read-only Calendar setup; Calendar writes remain disabled.",
        ),
        LiveConnectorReadinessItem(
            name="Gmail context",
            status=gmail_status,
            reason=gmail_reason,
            source="runtime_doctor_service_readiness",
            safe_next_step="Use Gmail read-only setup for future context scans; sends remain disabled.",
        ),
        LiveConnectorReadinessItem(
            name="Documents intake",
            status="configured_placeholder",
            reason="telegram_document_metadata_intake_available_draft_only",
            source="local_runtime_capability",
            safe_next_step="Send files only for draft metadata intake until document review is enabled.",
        ),
        LiveConnectorReadinessItem(
            name="Document review",
            status="not_implemented",
            reason="live_document_review_not_enabled_in_181p",
            source="stage_boundary",
            safe_next_step="Wait for the approved document review stage before parsing contents.",
        ),
        LiveConnectorReadinessItem(
            name="Memory approval mode",
            status="approval_required",
            reason="memory_changes_require_owner_approval",
            source="product_boundary",
            safe_next_step="Review proposed memories before they influence future outputs.",
        ),
        LiveConnectorReadinessItem(
            name="Gmail draft creation",
            status="disabled",
            reason="gmail_draft_creation_not_authorized_until_185p",
            source="stage_boundary",
            safe_next_step="Prepare local drafts only; create Gmail drafts after explicit future approval.",
        ),
        LiveConnectorReadinessItem(
            name="Gmail send",
            status="disabled",
            reason="gmail_send_not_authorized",
            source="safety_boundary",
            safe_next_step="Never send email from 181P.",
        ),
        LiveConnectorReadinessItem(
            name="Calendar writes",
            status="disabled",
            reason="calendar_writes_not_authorized",
            source="safety_boundary",
            safe_next_step="Use read-only Calendar context only.",
        ),
        LiveConnectorReadinessItem(
            name="External writes",
            status="disabled",
            reason="external_writes_not_authorized",
            source="safety_boundary",
            safe_next_step="Keep all outputs local or Telegram owner-requested replies only.",
        ),
    )


def _gmail_reason(gmail_metadata, gmail_readonly) -> str:
    if gmail_readonly is not None and gmail_readonly.ready:
        return gmail_readonly.reason
    if gmail_metadata is not None and gmail_metadata.ready:
        return gmail_metadata.reason
    if gmail_readonly is not None:
        return gmail_readonly.reason
    if gmail_metadata is not None:
        return gmail_metadata.reason
    return "gmail_readiness_missing"


def _overall_status(items: tuple[LiveConnectorReadinessItem, ...]) -> str:
    if any(item.status == "blocked" for item in items):
        return "blocked"
    if any(item.status == "connected" for item in items):
        return "partially_connected"
    return "not_connected"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.live_connector_readiness_check")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    report = build_live_connector_readiness_report()
    if args.as_json:
        print(json.dumps(asdict(report), sort_keys=True, indent=2))
    else:
        print(render_live_connector_readiness_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
