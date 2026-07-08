from __future__ import annotations

from dataclasses import dataclass


PILOT_SAFETY_INCIDENT_LOG_STAGE = "219P"
PILOT_SAFETY_INCIDENT_LOG_STATUS = "local_pilot_safety_log_v0"
PILOT_SAFETY_INCIDENT_TYPES = (
    "attempted_gmail_send",
    "attempted_calendar_write",
    "owner_mismatch",
    "robot_mismatch",
    "stale_approval_blocked",
    "missing_consent",
    "source_scope_mismatch",
    "connector_scope_mismatch",
    "secret_like_output_blocked",
    "destructive_action_blocked",
)
PILOT_SAFETY_SEVERITIES = ("info", "low", "medium", "high", "critical")


@dataclass(frozen=True, slots=True)
class PilotSafetyIncident:
    incident_id: str
    incident_type: str
    owner_id: str
    robot_id: str
    pilot_user_id: str
    severity: str
    command: str
    item_id: str
    reason: str
    source_trace_id: str
    created_at: str
    status: str

    def __post_init__(self) -> None:
        if self.incident_type not in PILOT_SAFETY_INCIDENT_TYPES:
            raise ValueError("219P pilot safety incident type is unsupported.")
        if self.severity not in PILOT_SAFETY_SEVERITIES:
            raise ValueError("219P pilot safety severity is unsupported.")
        if not all(
            (
                self.incident_id,
                self.owner_id,
                self.robot_id,
                self.pilot_user_id,
                self.command,
                self.item_id,
                self.reason,
                self.source_trace_id,
                self.created_at,
                self.status,
            )
        ):
            raise ValueError("219P pilot safety incidents require full identity and trace fields.")
        if self.status not in {"blocked", "recorded", "reviewed"}:
            raise ValueError("219P pilot safety incident status is unsupported.")


@dataclass(frozen=True, slots=True)
class PilotSafetyIncidentLog:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    incidents: tuple[PilotSafetyIncident, ...]
    total_incidents: int
    blocked_incidents: int
    top_incident_types: tuple[tuple[str, int], ...]
    local_log_only: bool
    external_ticket_created: bool
    crm_write_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    whatsapp_allowed: bool
    destructive_action_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != PILOT_SAFETY_INCIDENT_LOG_STAGE:
            raise ValueError("219P pilot safety logs must identify the 219P stage.")
        if self.status != PILOT_SAFETY_INCIDENT_LOG_STATUS:
            raise ValueError("219P pilot safety logs must use the safety log status.")
        if self.total_incidents != len(self.incidents):
            raise ValueError("219P pilot safety log counts must match incidents.")
        if self.blocked_incidents != sum(1 for incident in self.incidents if incident.status == "blocked"):
            raise ValueError("219P pilot safety blocked count must match incidents.")
        if any(
            (
                not self.local_log_only,
                self.external_ticket_created,
                self.crm_write_allowed,
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.whatsapp_allowed,
                self.destructive_action_allowed,
            )
        ):
            raise ValueError("219P pilot safety logs must not expand external authority.")
        if not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("219P pilot safety logs must be redacted and approval-preserving.")


def build_pilot_safety_incident(
    *,
    owner_id: str,
    robot_id: str,
    pilot_user_id: str,
    incident_type: str,
    command: str,
    item_id: str,
    reason: str,
    severity: str = "medium",
    source_trace_id: str | None = None,
    created_at: str = "2026-07-08T00:00:00Z",
    status: str = "blocked",
) -> PilotSafetyIncident:
    normalized_type = incident_type.strip()
    normalized_item = item_id.strip() or "pilot-unspecified"
    return PilotSafetyIncident(
        incident_id=f"safety-{normalized_type}-{normalized_item}".replace(" ", "-"),
        incident_type=normalized_type,
        owner_id=owner_id,
        robot_id=robot_id,
        pilot_user_id=pilot_user_id.strip() or "unknown-pilot-user",
        severity=severity.strip().lower() or "medium",
        command=command.strip() or "unknown-command",
        item_id=normalized_item,
        reason=_redact_reason(reason),
        source_trace_id=(source_trace_id or "source_trace_not_provided").strip() or "source_trace_not_provided",
        created_at=created_at,
        status=status,
    )


def build_pilot_safety_incident_log(
    *,
    owner_id: str,
    robot_id: str,
    incidents: tuple[PilotSafetyIncident, ...] = (),
) -> PilotSafetyIncidentLog:
    scoped_incidents = tuple(incident for incident in incidents if incident.owner_id == owner_id and incident.robot_id == robot_id)
    return PilotSafetyIncidentLog(
        stage=PILOT_SAFETY_INCIDENT_LOG_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=PILOT_SAFETY_INCIDENT_LOG_STATUS,
        incidents=scoped_incidents,
        total_incidents=len(scoped_incidents),
        blocked_incidents=sum(1 for incident in scoped_incidents if incident.status == "blocked"),
        top_incident_types=_top_types(scoped_incidents),
        local_log_only=True,
        external_ticket_created=False,
        crm_write_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        whatsapp_allowed=False,
        destructive_action_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_pilot_safety_incident_log(log: PilotSafetyIncidentLog) -> str:
    lines = [
        "Pilot Safety Incident Log",
        "",
        f"Stage: {log.stage}",
        f"Status: {log.status}",
        f"Owner: {log.owner_id}",
        f"Robot: {log.robot_id}",
        f"Incidents: {log.total_incidents}",
        f"Blocked incidents: {log.blocked_incidents}",
        f"Health: {_health(log)}",
        "",
        "Tracked incident types:",
        *[f"- {incident_type}" for incident_type in PILOT_SAFETY_INCIDENT_TYPES],
    ]
    if log.top_incident_types:
        lines.extend(["", "Top incident types:"])
        lines.extend(f"- {incident_type}: {count}" for incident_type, count in log.top_incident_types)
    if log.incidents:
        lines.extend(["", "Incidents:"])
        for incident in log.incidents:
            lines.extend(
                [
                    f"- {incident.incident_id}",
                    f"  Type: {incident.incident_type}",
                    f"  Severity: {incident.severity}",
                    f"  Command: {incident.command}",
                    f"  Item: {incident.item_id}",
                    f"  Reason: {incident.reason}",
                    f"  Source trace: {incident.source_trace_id}",
                    f"  Status: {incident.status}",
                ]
            )
    lines.extend(
        [
            "",
            "Local log only: yes",
            "External ticket: no",
            "CRM write: disabled",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "WhatsApp: disabled",
            "Destructive actions: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )
    return "\n".join(lines)


def _top_types(incidents: tuple[PilotSafetyIncident, ...]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for incident in incidents:
        counts[incident.incident_type] = counts.get(incident.incident_type, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3])


def _health(log: PilotSafetyIncidentLog) -> str:
    if not log.incidents:
        return "no_local_incidents"
    if any(incident.severity in {"high", "critical"} for incident in log.incidents):
        return "needs_operator_review"
    return "recorded_local"


def _redact_reason(reason: str) -> str:
    redacted = reason.strip() or "reason_not_provided"
    for marker in ("authorization", "bearer", "token", "secret", "client_secret", "refresh_token", "access_token"):
        redacted = redacted.replace(marker, "[redacted]")
        redacted = redacted.replace(marker.upper(), "[redacted]")
    return redacted
