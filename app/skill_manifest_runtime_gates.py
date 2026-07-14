from __future__ import annotations

from dataclasses import asdict, dataclass
import re


SKILL_MANIFEST_RUNTIME_GATES_STAGE = "189P"
SKILL_RUNTIME_DECISIONS = ("ANSWER", "CLARIFY", "REDIRECT", "OFFER_UPGRADE", "REFUSE_SCOPE", "BLOCK")
SKILL_RUNTIME_MANIFEST_IDS = (
    "basic",
    "setup",
    "daily_brief",
    "meetings",
    "documents",
    "memory",
    "gmail_drafts",
    "usage",
)
SENSITIVE_REQUEST_PATTERN = re.compile(
    r"\b("
    r"send\s+(?:email|message)|schedule|reschedule|cancel\s+meeting|delete|destroy|deploy|"
    r"pay|payment|refund|sign|signature|legal advice|accept terms|medical|diagnos(?:e|is)|"
    r"dosage|tax advice|investment|financial decision|change password|credential|permission"
    r")\b",
    re.IGNORECASE,
)
ACTION_CLASS_BY_COMMAND = {
    "/start": "READ",
    "/help": "READ",
    "/status": "READ",
    "/checkup": "READ",
    "/setup": "READ",
    "/miss": "SUMMARIZE",
    "/today": "SUMMARIZE",
    "/daily_brief": "SUMMARIZE",
    "/demo": "READ",
    "/pilot": "READ",
    "/pilot_pack": "READ",
    "/pilot_audit": "READ",
    "/live_smoke": "READ",
    "/pilot_metrics": "READ",
    "/friendly_onboarding": "READ",
    "/friendly_pilot": "READ",
    "/pilot_users": "READ",
    "/pilot_user": "READ",
    "/pilot_health": "READ",
    "/pilot_invite": "READ",
    "/pilot_consent": "READ",
    "/pilot_provision": "CLASSIFY",
    "/pilot_allowlist": "READ",
    "/pilot_boundary": "READ",
    "/pilot_runbook": "READ",
    "/report_issue": "CLASSIFY",
    "/report_bug": "CLASSIFY",
    "/report_confusing": "CLASSIFY",
    "/report_wrong": "CLASSIFY",
    "/report_missing": "CLASSIFY",
    "/report_slow": "CLASSIFY",
    "/pilot_safety": "READ",
    "/pilot_weekly_report": "READ",
    "/end_pilot": "CLASSIFY",
    "/export_pilot_data": "READ",
    "/delete_pilot_memory": "CLASSIFY",
    "/disable_pilot_connectors": "CLASSIFY",
    "/pilot_launch": "READ",
    "/pilot_activate": "CLASSIFY",
    "/pilot_review": "READ",
    "/pilot_learnings": "READ",
    "/paid_pilot_gate": "READ",
    "/founder_loop": "READ",
    "/feedback": "CLASSIFY",
    "/feedback_ledger": "READ",
    "/founder_outcome": "CLASSIFY",
    "/suggestion_quality": "READ",
    "/prep_quality": "READ",
    "/gmail_thread": "READ",
    "/loops": "READ",
    "/inbox": "READ",
    "/inbox_done": "CLASSIFY",
    "/inbox_dismiss": "CLASSIFY",
    "/prep": "SUMMARIZE",
    "/brief": "SUMMARIZE",
    "/suggest_brief": "SUMMARIZE",
    "/suggestions": "READ",
    "/suggestion_dismiss": "CLASSIFY",
    "/suggestion_snooze": "CLASSIFY",
    "/suggestion_memory": "DRAFT",
    "/suggestion_draft": "DRAFT",
    "/suggestion_followup": "DRAFT",
    "/drafts": "READ",
    "/draft_approve": "CLASSIFY",
    "/draft_reject": "CLASSIFY",
    "/draft_edit": "DRAFT",
    "/draft_revise": "DRAFT",
    "/draft_expire": "CLASSIFY",
    "/export_text": "DRAFT",
    "/export_email": "WRITE_EXTERNAL_RECORD",
    "/export_file": "DRAFT",
    "/usage": "READ",
    "/memory_review": "READ",
    "/memory_approve": "CLASSIFY",
    "/memory_reject": "CLASSIFY",
    "/memory_edit": "DRAFT",
    "/memory_forget": "CLASSIFY",
    "/memory_wrong": "CLASSIFY",
    "/memory_stale": "CLASSIFY",
    "/memory_duplicate": "CLASSIFY",
    "/memory_merge": "CLASSIFY",
    "/memory_never_use": "CLASSIFY",
    "/memory": "READ",
    "/memory_limits": "READ",
    "/memory_pending": "READ",
    "/document": "SUMMARIZE",
}
COMMAND_SKILL_MAP = {
    "/start": "basic",
    "/help": "basic",
    "/status": "setup",
    "/checkup": "setup",
    "/setup": "setup",
    "/miss": "daily_brief",
    "/today": "daily_brief",
    "/daily_brief": "daily_brief",
    "/demo": "basic",
    "/pilot": "basic",
    "/pilot_pack": "basic",
    "/pilot_audit": "basic",
    "/live_smoke": "basic",
    "/pilot_metrics": "basic",
    "/friendly_onboarding": "basic",
    "/friendly_pilot": "basic",
    "/pilot_users": "basic",
    "/pilot_user": "basic",
    "/pilot_health": "basic",
    "/pilot_invite": "basic",
    "/pilot_consent": "basic",
    "/pilot_provision": "basic",
    "/pilot_allowlist": "basic",
    "/pilot_boundary": "basic",
    "/pilot_runbook": "basic",
    "/report_issue": "basic",
    "/report_bug": "basic",
    "/report_confusing": "basic",
    "/report_wrong": "basic",
    "/report_missing": "basic",
    "/report_slow": "basic",
    "/pilot_safety": "basic",
    "/pilot_weekly_report": "basic",
    "/end_pilot": "basic",
    "/export_pilot_data": "basic",
    "/delete_pilot_memory": "basic",
    "/disable_pilot_connectors": "basic",
    "/pilot_launch": "basic",
    "/pilot_activate": "basic",
    "/pilot_review": "basic",
    "/pilot_learnings": "basic",
    "/paid_pilot_gate": "basic",
    "/founder_loop": "basic",
    "/feedback": "basic",
    "/feedback_ledger": "basic",
    "/founder_outcome": "basic",
    "/suggestion_quality": "meetings",
    "/prep_quality": "meetings",
    "/gmail_thread": "daily_brief",
    "/loops": "daily_brief",
    "/inbox": "basic",
    "/inbox_done": "basic",
    "/inbox_dismiss": "basic",
    "/prep": "meetings",
    "/brief": "meetings",
    "/suggest_brief": "meetings",
    "/suggestions": "meetings",
    "/suggestion_dismiss": "meetings",
    "/suggestion_snooze": "meetings",
    "/suggestion_memory": "memory",
    "/suggestion_draft": "gmail_drafts",
    "/suggestion_followup": "meetings",
    "/drafts": "gmail_drafts",
    "/draft_approve": "gmail_drafts",
    "/draft_reject": "gmail_drafts",
    "/draft_edit": "gmail_drafts",
    "/draft_revise": "gmail_drafts",
    "/draft_expire": "gmail_drafts",
    "/export_text": "gmail_drafts",
    "/export_email": "gmail_drafts",
    "/export_file": "gmail_drafts",
    "/usage": "usage",
    "/memory_review": "memory",
    "/memory_approve": "memory",
    "/memory_reject": "memory",
    "/memory_edit": "memory",
    "/memory_forget": "memory",
    "/memory_wrong": "memory",
    "/memory_stale": "memory",
    "/memory_duplicate": "memory",
    "/memory_merge": "memory",
    "/memory_never_use": "memory",
    "/memory": "memory",
    "/memory_limits": "memory",
    "/memory_pending": "memory",
    "/document": "documents",
}
COMMANDS_REQUIRING_TARGET = {
    "/gmail_thread",
    "/feedback",
    "/founder_outcome",
    "/prep",
    "/inbox_done",
    "/inbox_dismiss",
    "/suggestion_dismiss",
    "/suggestion_snooze",
    "/suggestion_memory",
    "/suggestion_draft",
    "/suggestion_followup",
    "/draft_approve",
    "/draft_reject",
    "/draft_edit",
    "/draft_revise",
    "/draft_expire",
    "/export_text",
    "/export_email",
    "/export_file",
    "/memory_approve",
    "/memory_reject",
    "/memory_edit",
    "/memory_forget",
    "/memory_wrong",
    "/memory_stale",
    "/memory_duplicate",
    "/memory_merge",
    "/memory_never_use",
    "/pilot_user",
}
BLOCKED_ACTION_CLASSES = {
    "PAY",
    "REFUND",
    "DELETE",
    "CONFIGURE",
    "RELEASE",
    "LEGAL_ACCEPTANCE",
    "EMPLOYMENT_DECISION",
    "MEDICAL_DECISION",
    "FINANCIAL_DECISION",
    "TAX_DECISION",
    "IDENTITY_CHANGE",
}


@dataclass(frozen=True, slots=True)
class SkillRuntimeManifest:
    stage: str
    skill_id: str
    display_name: str
    status: str
    package: str
    commands: tuple[str, ...]
    allowed_action_classes: tuple[str, ...]
    confirmation_required: tuple[str, ...]
    blocked_action_classes: tuple[str, ...]
    blocked_topics: tuple[str, ...]
    upgrade_paths: tuple[str, ...]
    safe_fallback: str

    def __post_init__(self) -> None:
        if self.stage != SKILL_MANIFEST_RUNTIME_GATES_STAGE:
            raise ValueError("189P skill runtime manifests must identify the 189P stage.")
        if self.skill_id not in SKILL_RUNTIME_MANIFEST_IDS:
            raise ValueError("rejected_unknown_skill_runtime_manifest")
        if self.status not in {"active", "available_with_confirmation", "draft_only"}:
            raise ValueError("rejected_invalid_skill_runtime_status")
        if not self.commands:
            raise ValueError("rejected_skill_manifest_without_commands")
        if not self.allowed_action_classes:
            raise ValueError("rejected_skill_manifest_without_allowed_actions")
        if not self.safe_fallback.strip():
            raise ValueError("rejected_skill_manifest_without_safe_fallback")


@dataclass(frozen=True, slots=True)
class SkillRuntimeGateRequest:
    owner_id: str
    robot_id: str
    command: str
    raw_text: str = ""
    active_skill_id: str | None = None
    requested_action_class: str | None = None
    requested_package: str | None = None


@dataclass(frozen=True, slots=True)
class SkillRuntimeGateDecision:
    stage: str
    owner_id: str
    robot_id: str
    command: str
    skill_id: str
    decision: str
    reason_code: str
    safe_user_message: str
    active_skill_id: str | None
    target_skill_id: str | None
    action_class: str
    requires_confirmation: bool
    confirmation_required_actions: tuple[str, ...]
    blocked: bool
    upgrade_path: str
    safe_fallback: str
    execution_authorized: bool
    external_write_allowed: bool
    connector_activation_allowed: bool
    model_call_allowed: bool
    tool_call_allowed: bool
    memory_center_mutation_allowed: bool
    calendar_write_allowed: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != SKILL_MANIFEST_RUNTIME_GATES_STAGE:
            raise ValueError("189P skill runtime decisions must identify the 189P stage.")
        if self.decision not in SKILL_RUNTIME_DECISIONS:
            raise ValueError("rejected_unknown_skill_runtime_decision")
        if any(
            (
                self.execution_authorized,
                self.external_write_allowed,
                self.connector_activation_allowed,
                self.model_call_allowed,
                self.tool_call_allowed,
                self.memory_center_mutation_allowed,
                self.calendar_write_allowed,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
            )
        ):
            raise ValueError("189P skill runtime gates must not authorize execution.")
        if self.decision == "BLOCK" and not self.blocked:
            raise ValueError("189P blocked skill runtime decisions must be marked blocked.")


def build_default_skill_runtime_manifests() -> tuple[SkillRuntimeManifest, ...]:
    manifests = (
        _manifest(
            "basic",
            "Basic",
            "basic",
            ("/start", "/help", "/demo", "/pilot", "/pilot_metrics", "/pilot_weekly_report", "/pilot_launch", "/pilot_activate", "/pilot_review", "/pilot_learnings", "/paid_pilot_gate", "/friendly_onboarding", "/friendly_pilot", "/pilot_users", "/pilot_user", "/pilot_health", "/pilot_invite", "/pilot_consent", "/pilot_provision", "/pilot_allowlist", "/pilot_boundary", "/pilot_runbook", "/report_issue", "/report_bug", "/report_confusing", "/report_wrong", "/report_missing", "/report_slow", "/pilot_safety", "/end_pilot", "/export_pilot_data", "/delete_pilot_memory", "/disable_pilot_connectors", "/inbox", "/inbox_done", "/inbox_dismiss"),
            ("READ", "CLASSIFY", "SUMMARIZE"),
            safe_fallback="I can show the Roboticxs menu, local demo, and task inbox boundaries without external action.",
        ),
        _manifest(
            "setup",
            "Setup",
            "basic",
            ("/status", "/checkup", "/setup"),
            ("READ", "CLASSIFY"),
            safe_fallback="I can show local setup and capability status without printing secrets or activating connectors.",
        ),
        _manifest(
            "daily_brief",
            "Daily Brief",
            "basic",
            ("/miss", "/today", "/daily_brief", "/gmail_thread", "/loops"),
            ("READ", "SEARCH_APPROVED_CONTEXT", "SUMMARIZE"),
            safe_fallback="I can prepare read-only daily brief context from approved local sources.",
        ),
        _manifest(
            "meetings",
            "Meetings",
            "pro",
            ("/prep", "/brief", "/suggest_brief", "/suggestions", "/suggestion_dismiss", "/suggestion_snooze", "/suggestion_followup"),
            ("READ", "SEARCH_APPROVED_CONTEXT", "SUMMARIZE", "DRAFT", "CLASSIFY"),
            upgrade_paths=("Documents Pack for document-linked prep.", "Gmail Drafts for approved draft creation."),
            safe_fallback="I can prepare meeting context and suggested next steps, but I will not send messages or update calendars.",
        ),
        _manifest(
            "documents",
            "Documents",
            "documents",
            ("/document",),
            ("READ", "SUMMARIZE", "DRAFT"),
            upgrade_paths=("Documents Pack enables deeper document review when configured."),
            safe_fallback="I can summarize supplied document text in draft-only mode without legal, tax, medical, or signature advice.",
        ),
        _manifest(
            "memory",
            "Memory",
            "basic",
            ("/memory", "/memory_review", "/memory_pending", "/memory_limits", "/memory_approve", "/memory_reject", "/memory_edit", "/memory_forget", "/memory_wrong", "/memory_stale", "/memory_duplicate", "/memory_merge", "/memory_never_use", "/suggestion_memory"),
            ("READ", "CLASSIFY", "DRAFT"),
            safe_fallback="I can show memory proposals and local owner decision receipts; approved memory authority remains separate.",
        ),
        _manifest(
            "gmail_drafts",
            "Gmail Drafts",
            "pro",
            ("/drafts", "/draft_approve", "/draft_reject", "/draft_edit", "/draft_expire", "/export_text", "/export_email", "/export_file", "/suggestion_draft"),
            ("READ", "DRAFT", "CLASSIFY", "WRITE_EXTERNAL_RECORD"),
            confirmation_required=("WRITE_EXTERNAL_RECORD", "SEND_NOTIFY"),
            upgrade_paths=("Gmail Drafts can create drafts after explicit approval; sending remains blocked."),
            safe_fallback="I can prepare or create approved Gmail drafts only when a prior confirmation receipt exists; I cannot send email.",
        ),
        _manifest(
            "usage",
            "Usage",
            "basic",
            ("/usage",),
            ("READ", "SUMMARIZE"),
            safe_fallback="I can show local estimated usage and cost ledger summaries only.",
        ),
    )
    return manifests


def manifests_by_skill_id(
    manifests: tuple[SkillRuntimeManifest, ...] | None = None,
) -> dict[str, SkillRuntimeManifest]:
    return {manifest.skill_id: manifest for manifest in (manifests or build_default_skill_runtime_manifests())}


def map_command_to_skill(command: str) -> str | None:
    return COMMAND_SKILL_MAP.get(_normalize_command(command))


def classify_skill_runtime_gate(
    request: SkillRuntimeGateRequest,
    *,
    manifests: tuple[SkillRuntimeManifest, ...] | None = None,
) -> SkillRuntimeGateDecision:
    manifest_map = manifests_by_skill_id(manifests)
    command = _normalize_command(request.command)
    target_skill_id = map_command_to_skill(command)
    action_class = request.requested_action_class or ACTION_CLASS_BY_COMMAND.get(command, "READ")
    raw_text = request.raw_text or command

    if _is_blocked_request(raw_text=raw_text, action_class=action_class):
        return _decision(
            request=request,
            command=command,
            skill_id=target_skill_id or "basic",
            target_skill_id=target_skill_id,
            action_class=action_class,
            decision="BLOCK",
            reason_code="blocked_sensitive_or_destructive_request",
            manifest=manifest_map.get(target_skill_id or "basic"),
        )
    if request.requested_package and request.requested_package not in {manifest.package for manifest in manifest_map.values()}:
        return _decision(
            request=request,
            command=command,
            skill_id=target_skill_id or "basic",
            target_skill_id=target_skill_id,
            action_class=action_class,
            decision="OFFER_UPGRADE",
            reason_code="requested_package_not_enabled",
            manifest=manifest_map.get(target_skill_id or "basic"),
        )
    if target_skill_id is None:
        if _looks_like_upgrade_request(raw_text):
            return _decision(
                request=request,
                command=command,
                skill_id="basic",
                target_skill_id=None,
                action_class=action_class,
                decision="OFFER_UPGRADE",
                reason_code="known_paid_skill_not_enabled_for_command",
                manifest=manifest_map["basic"],
                upgrade_path="Ask to enable the relevant product skill before using this request.",
            )
        return _decision(
            request=request,
            command=command,
            skill_id="basic",
            target_skill_id=None,
            action_class=action_class,
            decision="REFUSE_SCOPE",
            reason_code="unknown_command_outside_runtime_manifest",
            manifest=manifest_map["basic"],
        )
    manifest = manifest_map[target_skill_id]
    if request.active_skill_id and request.active_skill_id != target_skill_id:
        return _decision(
            request=request,
            command=command,
            skill_id=request.active_skill_id,
            target_skill_id=target_skill_id,
            action_class=action_class,
            decision="REDIRECT",
            reason_code="command_belongs_to_enabled_target_skill",
            manifest=manifest,
        )
    if command in COMMANDS_REQUIRING_TARGET and not _has_argument(raw_text, command):
        return _decision(
            request=request,
            command=command,
            skill_id=target_skill_id,
            target_skill_id=target_skill_id,
            action_class=action_class,
            decision="CLARIFY",
            reason_code="command_requires_target_argument",
            manifest=manifest,
        )
    return _decision(
        request=request,
        command=command,
        skill_id=target_skill_id,
        target_skill_id=target_skill_id,
        action_class=action_class,
        decision="ANSWER",
        reason_code="command_allowed_by_skill_manifest",
        manifest=manifest,
    )


def classify_command_for_skill_gate(
    *,
    owner_id: str,
    robot_id: str,
    command: str,
    raw_text: str = "",
    active_skill_id: str | None = None,
) -> SkillRuntimeGateDecision:
    return classify_skill_runtime_gate(
        SkillRuntimeGateRequest(
            owner_id=owner_id,
            robot_id=robot_id,
            command=command,
            raw_text=raw_text,
            active_skill_id=active_skill_id,
        )
    )


def render_skill_runtime_gate_decision(record: SkillRuntimeGateDecision) -> str:
    return "\n".join(
        [
            "Skill Runtime Gate",
            f"Stage: {record.stage}",
            f"Decision: {record.decision}",
            f"Skill: {record.skill_id}",
            f"Action class: {record.action_class}",
            f"Reason: {record.reason_code}",
            record.safe_user_message,
            f"Requires confirmation: {str(record.requires_confirmation).lower()}",
            f"Blocked: {str(record.blocked).lower()}",
            "Execution authorized: false",
            "External writes: disabled",
            "Connector activation: disabled",
            "Model/tool calls: disabled",
            "Memory Center mutation: disabled",
            "Gmail send/modify: disabled",
        ]
    )


def render_skill_runtime_manifest_summary(
    manifests: tuple[SkillRuntimeManifest, ...] | None = None,
) -> tuple[str, ...]:
    return tuple(
        f"- {manifest.display_name}: {', '.join(manifest.commands)}"
        for manifest in (manifests or build_default_skill_runtime_manifests())
    )


def render_skill_runtime_boundary_lines() -> tuple[str, ...]:
    return (
        "Skill Manifest Runtime Gates: active",
        "Decisions: ANSWER, CLARIFY, REDIRECT, OFFER_UPGRADE, REFUSE_SCOPE, BLOCK",
        "External writes, connector activation, model/tool calls, Gmail send/modify, Calendar writes, and Memory Center mutation: disabled",
    )


def decision_to_dict(record: SkillRuntimeGateDecision) -> dict:
    return asdict(record)


def _manifest(
    skill_id: str,
    display_name: str,
    package: str,
    commands: tuple[str, ...],
    allowed_action_classes: tuple[str, ...],
    *,
    confirmation_required: tuple[str, ...] = (),
    blocked_action_classes: tuple[str, ...] = (
        "PAY",
        "REFUND",
        "DELETE",
        "CONFIGURE",
        "RELEASE",
        "LEGAL_ACCEPTANCE",
        "MEDICAL_DECISION",
        "FINANCIAL_DECISION",
        "TAX_DECISION",
        "IDENTITY_CHANGE",
    ),
    blocked_topics: tuple[str, ...] = (
        "medical advice",
        "legal acceptance",
        "tax advice",
        "payments",
        "destructive actions",
        "production deploys",
    ),
    upgrade_paths: tuple[str, ...] = (),
    safe_fallback: str,
) -> SkillRuntimeManifest:
    return SkillRuntimeManifest(
        stage=SKILL_MANIFEST_RUNTIME_GATES_STAGE,
        skill_id=skill_id,
        display_name=display_name,
        status="available_with_confirmation" if confirmation_required else "active",
        package=package,
        commands=commands,
        allowed_action_classes=allowed_action_classes,
        confirmation_required=confirmation_required,
        blocked_action_classes=blocked_action_classes,
        blocked_topics=blocked_topics,
        upgrade_paths=upgrade_paths,
        safe_fallback=safe_fallback,
    )


def _decision(
    *,
    request: SkillRuntimeGateRequest,
    command: str,
    skill_id: str,
    target_skill_id: str | None,
    action_class: str,
    decision: str,
    reason_code: str,
    manifest: SkillRuntimeManifest | None,
    upgrade_path: str = "",
) -> SkillRuntimeGateDecision:
    requires_confirmation = bool(manifest and action_class in manifest.confirmation_required)
    safe_fallback = manifest.safe_fallback if manifest else "I can only help with enabled Roboticxs skills."
    return SkillRuntimeGateDecision(
        stage=SKILL_MANIFEST_RUNTIME_GATES_STAGE,
        owner_id=request.owner_id,
        robot_id=request.robot_id,
        command=command,
        skill_id=skill_id,
        decision=decision,
        reason_code=reason_code,
        safe_user_message=_safe_user_message(decision, manifest, target_skill_id),
        active_skill_id=request.active_skill_id,
        target_skill_id=target_skill_id,
        action_class=action_class,
        requires_confirmation=requires_confirmation,
        confirmation_required_actions=manifest.confirmation_required if manifest else (),
        blocked=decision == "BLOCK",
        upgrade_path=upgrade_path or _upgrade_path(manifest),
        safe_fallback=safe_fallback,
        execution_authorized=False,
        external_write_allowed=False,
        connector_activation_allowed=False,
        model_call_allowed=False,
        tool_call_allowed=False,
        memory_center_mutation_allowed=False,
        calendar_write_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
    )


def _normalize_command(command: str) -> str:
    normalized = (command or "").strip().split()[0] if command else ""
    return normalized if normalized.startswith("/") else f"/{normalized}" if normalized else ""


def _has_argument(raw_text: str, command: str) -> bool:
    text = (raw_text or "").strip()
    if not text:
        return False
    if not text.startswith(command):
        return False
    return bool(text[len(command) :].strip())


def _is_blocked_request(*, raw_text: str, action_class: str) -> bool:
    return action_class in BLOCKED_ACTION_CLASSES or bool(SENSITIVE_REQUEST_PATTERN.search(raw_text or ""))


def _looks_like_upgrade_request(raw_text: str) -> bool:
    return bool(re.search(r"\b(crm|marketing|sales|hr|finance|whatsapp|voice|browser)\b", raw_text or "", re.IGNORECASE))


def _upgrade_path(manifest: SkillRuntimeManifest | None) -> str:
    if manifest is None or not manifest.upgrade_paths:
        return ""
    return manifest.upgrade_paths[0]


def _safe_user_message(
    decision: str,
    manifest: SkillRuntimeManifest | None,
    target_skill_id: str | None,
) -> str:
    if decision == "ANSWER":
        return "This command is inside the active skill boundary. No external action is authorized by this gate."
    if decision == "CLARIFY":
        return "I need the missing target before I can prepare the local reply."
    if decision == "REDIRECT":
        return f"This belongs to the {target_skill_id or 'target'} skill. I can route the local reply there without executing anything."
    if decision == "OFFER_UPGRADE":
        return "That request belongs to a product skill or package that is not enabled here."
    if decision == "BLOCK":
        return "That request is blocked because it asks for a sensitive, destructive, professional, or external action."
    return manifest.safe_fallback if manifest else "That request is outside the enabled Roboticxs runtime skills."
