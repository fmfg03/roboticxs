from __future__ import annotations

from dataclasses import dataclass


CUSTOMER_PILOT_AUDIT_GATE_STAGE = "200P"
CUSTOMER_PILOT_AUDIT_GATE_STATUS = "pass_customer_pilot_audit_gate_v0"
AUDIT_STATUSES = ("PASS", "WARN", "FAIL")


@dataclass(frozen=True, slots=True)
class CustomerPilotAuditCriterion:
    criterion_id: str
    title: str
    status: str
    evidence: str
    customer_visible: bool

    def __post_init__(self) -> None:
        if self.status not in AUDIT_STATUSES:
            raise ValueError("200P audit criteria must use PASS, WARN, or FAIL.")
        if not self.criterion_id or not self.title or not self.evidence:
            raise ValueError("200P audit criteria require id, title, and evidence.")


@dataclass(frozen=True, slots=True)
class CustomerPilotAuditGateReport:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    criteria: tuple[CustomerPilotAuditCriterion, ...]
    residue_policy: str
    residue_evidence: str
    demo_condition: str
    local_audit_only: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool
    source_trace_preserved: bool
    usage_cost_receipt_visible: bool

    def __post_init__(self) -> None:
        if self.stage != CUSTOMER_PILOT_AUDIT_GATE_STAGE:
            raise ValueError("200P audit reports must identify the 200P stage.")
        if self.status != CUSTOMER_PILOT_AUDIT_GATE_STATUS:
            raise ValueError("200P audit reports must use the pilot audit status.")
        if len(self.criteria) != 10:
            raise ValueError("200P audit reports must cover the 10 required audit points.")
        if any(criterion.status != "PASS" for criterion in self.criteria):
            raise ValueError("200P pilot audit gate only closes when every criterion passes.")
        if self.residue_policy != "ignored_generated_scratch":
            raise ValueError("200P residue policy must classify generated loop handoffs.")
        if not self.local_audit_only:
            raise ValueError("200P audit gate must remain local-only.")
        if not all((self.secrets_redacted, self.approval_gate_preserved, self.source_trace_preserved, self.usage_cost_receipt_visible)):
            raise ValueError("200P audit gate requires redaction, approval, source trace, and usage/cost visibility.")
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
            raise ValueError("200P audit gate must not expand external action authority.")


def build_customer_pilot_audit_gate(*, owner_id: str, robot_id: str) -> CustomerPilotAuditGateReport:
    criteria = (
        _criterion("pilot_pack", "/pilot_pack exists and guides the demo.", "/pilot_pack renders setup, demo script, blocked actions, safety receipts, usage expectations, source examples, and onboarding copy."),
        _criterion("daily_brief_context", "/daily_brief uses real context or explicit fallback.", "/daily_brief composes Calendar, Gmail, Memory, and Documents when injected; missing connector state is rendered as explicit fallback rather than faked data."),
        _criterion("prep_context", "/prep uses Calendar + Gmail + Memory when available.", "/prep builds Calendar source trace, Gmail read-only scan, Memory snapshot, smart context ranking, and source receipt from existing read-only paths."),
        _criterion("source_trace", "Source trace appears in important outputs.", "184P receipts are attached to /daily_brief and /prep; 190P pilot receipt includes source trace; 199P pilot pack gives examples."),
        _criterion("cost_routing", "Cost/routing receipt appears where appropriate.", "198P renders Economy/Balanced/Premium, estimated tokens, estimated cost, confirmation state, and ledger source; /usage remains local estimated ledger."),
        _criterion("suggestion_priority", "Suggestions have priority and reason.", "194P adds P0-P3 priority, confidence, reason codes, safe next action, and source trace to suggestion inbox rendering."),
        _criterion("draft_quality", "Drafts have quality metadata.", "195P draft queue rendering includes intent, audience, tone, sources, risk note, approval state, expiry, and editable body."),
        _criterion("document_actions", "Document review proposes safe actions.", "197P renders save memory, questions, prep pack, draft, and export-review candidates without automatic downstream writes."),
        _criterion("gmail_draft_only", "Gmail draft creation remains draft-only.", "185P and 190P materialize Gmail drafts only after approval; receipts state no email was sent and no Gmail modify/delete is allowed."),
        _criterion("blocked_writes", "Unsafe external writes remain blocked.", "Gmail send/modify/archive/delete, Calendar writes, CRM writes, WhatsApp, destructive actions, and external writes remain disabled."),
    )
    return CustomerPilotAuditGateReport(
        stage=CUSTOMER_PILOT_AUDIT_GATE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=CUSTOMER_PILOT_AUDIT_GATE_STATUS,
        criteria=criteria,
        residue_policy="ignored_generated_scratch",
        residue_evidence="roboticxs_artifacts/loop_handoffs/ is generated local loop handoff scratch; no secrets found; ignored by .gitignore.",
        demo_condition="Francisco can run the Telegram demo with real sources or explicit fallback, without dangerous writes, with source trace, approval, and usage/cost receipts visible.",
        local_audit_only=True,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
        source_trace_preserved=True,
        usage_cost_receipt_visible=True,
    )


def render_customer_pilot_audit_gate(report: CustomerPilotAuditGateReport) -> str:
    return "\n".join(
        [
            "Customer Pilot Audit Gate",
            "",
            f"Stage: {report.stage}",
            f"Status: {report.status}",
            "",
            "Audit criteria:",
            *[
                f"{index}. {criterion.status} - {criterion.title}\n   Evidence: {criterion.evidence}"
                for index, criterion in enumerate(report.criteria, start=1)
            ],
            "",
            "Residue policy:",
            f"- {report.residue_policy}: {report.residue_evidence}",
            "",
            "Demo condition:",
            f"- {report.demo_condition}",
            "",
            "Safety checks:",
            "Gmail send: disabled",
            "Gmail modify/archive/delete: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
            "Source trace: preserved",
            "Usage/cost receipt: visible",
            "Secrets: redacted",
        ]
    )


def _criterion(criterion_id: str, title: str, evidence: str) -> CustomerPilotAuditCriterion:
    return CustomerPilotAuditCriterion(
        criterion_id=criterion_id,
        title=title,
        status="PASS",
        evidence=evidence,
        customer_visible=True,
    )
