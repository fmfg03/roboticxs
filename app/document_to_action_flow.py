from __future__ import annotations

from dataclasses import dataclass


DOCUMENT_TO_ACTION_FLOW_STAGE = "197P"
ACTION_TYPES = ("save_memory", "create_questions", "prepare_prep_pack", "create_draft", "export_review")


@dataclass(frozen=True, slots=True)
class DocumentActionCandidate:
    action_type: str
    title: str
    summary: str
    approval_state: str
    source_trace: str
    safe_next_step: str

    def __post_init__(self) -> None:
        if self.action_type not in ACTION_TYPES:
            raise ValueError("197P document action type must be supported.")
        if not self.title or not self.summary or not self.source_trace:
            raise ValueError("197P document actions require title, summary, and source trace.")


@dataclass(frozen=True, slots=True)
class DocumentToActionFlowRecord:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    document_title: str
    actions: tuple[DocumentActionCandidate, ...]
    no_external_action_taken: bool
    memory_center_mutated: bool
    draft_created: bool
    export_created: bool
    calendar_write_allowed: bool
    gmail_write_allowed: bool
    model_call_allowed: bool
    professional_advice_provided: bool
    external_write_allowed: bool

    def __post_init__(self) -> None:
        if self.stage != DOCUMENT_TO_ACTION_FLOW_STAGE:
            raise ValueError("197P document-to-action records must identify the 197P stage.")
        if not self.no_external_action_taken:
            raise ValueError("197P document-to-action flow must not take action.")
        if any(
            (
                self.memory_center_mutated,
                self.draft_created,
                self.export_created,
                self.calendar_write_allowed,
                self.gmail_write_allowed,
                self.model_call_allowed,
                self.professional_advice_provided,
                self.external_write_allowed,
            )
        ):
            raise ValueError("197P document-to-action flow must not expand authority.")


def build_document_to_action_flow(record: object) -> DocumentToActionFlowRecord:
    actions: tuple[DocumentActionCandidate, ...] = ()
    status = str(getattr(record, "status", ""))
    document_title = str(getattr(record, "document_title", "Untitled document"))
    if status == "completed_document_review_pack_v1":
        trace = f"document:{getattr(record, 'source_stage', 'unknown')}:{document_title}"
        questions = tuple(str(question) for question in getattr(record, "questions_to_ask", ()))
        actions = (
            DocumentActionCandidate(
                "save_memory",
                "Save useful document context",
                "Create a pending memory candidate from approved document facts only.",
                "approval_required",
                trace,
                "Use memory approval flow before anything is remembered.",
            ),
            DocumentActionCandidate(
                "create_questions",
                "Create questions",
                "; ".join(questions[:3]) or "No questions available.",
                "draft_only",
                trace,
                "Review questions before using them in a meeting.",
            ),
            DocumentActionCandidate(
                "prepare_prep_pack",
                "Prepare prep pack",
                "Use document signals as local context for meeting prep.",
                "owner_request_required",
                trace,
                "Run /prep only when owner-requested.",
            ),
            DocumentActionCandidate(
                "create_draft",
                "Create draft",
                "Create a local draft candidate from the review, not an email send.",
                "approval_required",
                trace,
                "Review /drafts and approve explicitly before export.",
            ),
            DocumentActionCandidate(
                "export_review",
                "Export review",
                "Prepare a local export payload for the review.",
                "approval_required",
                trace,
                "Export only through approved output flow.",
            ),
        )
    return DocumentToActionFlowRecord(
        stage=DOCUMENT_TO_ACTION_FLOW_STAGE,
        owner_id=str(getattr(record, "owner_id", "")),
        robot_id=str(getattr(record, "robot_id", "")),
        status="actions_suggested" if actions else "blocked_no_document_actions",
        document_title=document_title,
        actions=actions,
        no_external_action_taken=True,
        memory_center_mutated=False,
        draft_created=False,
        export_created=False,
        calendar_write_allowed=False,
        gmail_write_allowed=False,
        model_call_allowed=False,
        professional_advice_provided=False,
        external_write_allowed=False,
    )


def render_document_to_action_flow(record: DocumentToActionFlowRecord) -> str:
    lines = [
        "Document Actions",
        "",
        f"Stage: {record.stage}",
        f"Status: {record.status}",
        f"Document: {record.document_title}",
        "",
        "Suggested actions:",
    ]
    if not record.actions:
        lines.append("- No downstream actions are available for this document review.")
    else:
        for action in record.actions:
            lines.append(f"- {action.action_type}: {action.title}")
            lines.append(f"  summary: {action.summary}")
            lines.append(f"  approval: {action.approval_state}")
            lines.append(f"  source: {action.source_trace}")
            lines.append(f"  next: {action.safe_next_step}")
    lines.extend(
        [
            "",
            "Boundaries:",
            "Memory Center mutation: disabled",
            "Draft creation: disabled",
            "Export creation: disabled",
            "Calendar writes: disabled",
            "Gmail writes: disabled",
            "Professional advice: disabled",
            "External writes: disabled",
            "",
            "No external action was taken.",
        ]
    )
    return "\n".join(lines)
