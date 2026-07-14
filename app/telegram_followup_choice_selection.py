from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, uuid5

from app.telegram_followup_choice_surface import PASSIVE_BUTTON_LABELS_BY_OPTION_KIND, TELEGRAM_FOLLOWUP_CHOICE_SURFACE_STAGE, TelegramFollowUpChoiceSurfaceRecord


TELEGRAM_FOLLOWUP_CHOICE_SELECTION_STAGE = "110P"
SELECTION_STATUSES = frozenset({"selected_pending_authorization", "cancelled_no_action", "duplicate", "blocked"})
ALLOWED_SELECTION_OPTION_KINDS = frozenset(
    {
        "deeper_summary",
        "extract_questions",
        "human_review_checklist",
        "compare_prior_version",
        "cancel_followup",
    }
)
OPTION_FLAG_TO_REJECTION_REASON = {
    "implies_execution": "rejected_execution_implying_followup_option",
    "implies_memory_mutation": "rejected_memory_mutating_followup_option",
    "implies_external_send": "rejected_external_send_implying_followup_option",
    "implies_model_call": "rejected_model_call_implying_followup_option",
    "implies_tool_call": "rejected_tool_call_implying_followup_option",
    "implies_delegation_creation": "rejected_delegation_creating_followup_option",
    "implies_action_packet_creation": "rejected_action_packet_creating_followup_option",
    "implies_approval_creation": "rejected_approval_creating_followup_option",
}


@dataclass(frozen=True, slots=True)
class TelegramFollowUpChoiceSelectionPayload:
    choice_surface_id: str
    draft_plan_id: str
    selected_option_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    requests_execution: bool = False


@dataclass(frozen=True, slots=True)
class TelegramFollowUpChoiceSelectionRecord:
    selection_id: str
    choice_surface_id: str
    draft_plan_id: str
    selected_option_id: str
    selected_option_kind: str
    followup_intent_id: str
    acknowledgement_id: str
    delivery_id: str
    source_surface_id: str
    inbox_record_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    status: str
    response_text: str
    lineage_summary: dict[str, object]
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in SELECTION_STATUSES:
            raise ValueError("Unsupported Telegram follow-up choice selection status.")


@dataclass(frozen=True, slots=True)
class TelegramFollowUpChoiceSelectionResponseEnvelope:
    channel: str
    telegram_chat_id: str
    text: str
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("110P only supports local Telegram-compatible response envelopes.")
        if self.send_allowed is not False:
            raise ValueError("110P response envelopes must keep send_allowed false.")


@dataclass(slots=True)
class TelegramFollowUpChoiceSelectionRegistry:
    selections_by_id: dict[str, TelegramFollowUpChoiceSelectionRecord] = field(default_factory=dict)

    def get_selection(self, selection_id: str) -> TelegramFollowUpChoiceSelectionRecord | None:
        return self.selections_by_id.get(selection_id)

    def store(self, record: TelegramFollowUpChoiceSelectionRecord) -> TelegramFollowUpChoiceSelectionRecord:
        self.selections_by_id[record.selection_id] = record
        return record

    def list_selections(self) -> tuple[TelegramFollowUpChoiceSelectionRecord, ...]:
        return tuple(self.selections_by_id[key] for key in sorted(self.selections_by_id))

    def get_active_for_choice_surface(self, choice_surface_id: str) -> TelegramFollowUpChoiceSelectionRecord | None:
        for record in self.list_selections():
            if record.choice_surface_id == choice_surface_id and record.status in {
                "selected_pending_authorization",
                "cancelled_no_action",
                "duplicate",
            }:
                return record
        return None


def bind_telegram_followup_choice_selection(
    *,
    choice_surface_record: object,
    payload: TelegramFollowUpChoiceSelectionPayload,
    registry: TelegramFollowUpChoiceSelectionRegistry,
) -> TelegramFollowUpChoiceSelectionRecord:
    if not isinstance(payload, TelegramFollowUpChoiceSelectionPayload):
        raise TypeError("110P selection binding requires a deterministic TelegramFollowUpChoiceSelectionPayload.")

    selection_id = _selection_id(payload=payload)
    existing = registry.get_selection(selection_id)
    if existing is not None:
        return existing

    if not isinstance(choice_surface_record, TelegramFollowUpChoiceSurfaceRecord):
        return registry.store(
            _blocked_record(
                selection_id=selection_id,
                payload=payload,
                rejection_reason="rejected_unknown_choice_surface_record",
                choice_surface_record=None,
                selected_option_kind="",
            )
        )

    active = registry.get_active_for_choice_surface(choice_surface_record.choice_surface_id)
    if active is not None and active.selected_option_id != payload.selected_option_id:
        return registry.store(
            _blocked_record(
                selection_id=selection_id,
                payload=payload,
                rejection_reason="rejected_selection_replacement_not_authorized",
                choice_surface_record=choice_surface_record,
                selected_option_kind=_infer_option_kind(choice_surface_record=choice_surface_record, selected_option_id=payload.selected_option_id) or "",
            )
        )

    rejection_reason, selected_option_kind = _validate_selection_binding(
        choice_surface_record=choice_surface_record,
        payload=payload,
    )
    if rejection_reason is not None:
        return registry.store(
            _blocked_record(
                selection_id=selection_id,
                payload=payload,
                rejection_reason=rejection_reason,
                choice_surface_record=choice_surface_record,
                selected_option_kind=selected_option_kind,
            )
        )

    assert selected_option_kind
    status = "cancelled_no_action" if selected_option_kind == "cancel_followup" else "selected_pending_authorization"
    return registry.store(
        TelegramFollowUpChoiceSelectionRecord(
            selection_id=selection_id,
            choice_surface_id=choice_surface_record.choice_surface_id,
            draft_plan_id=choice_surface_record.draft_plan_id,
            selected_option_id=payload.selected_option_id,
            selected_option_kind=selected_option_kind,
            followup_intent_id=choice_surface_record.followup_intent_id,
            acknowledgement_id=choice_surface_record.acknowledgement_id,
            delivery_id=choice_surface_record.delivery_id,
            source_surface_id=choice_surface_record.source_surface_id,
            inbox_record_id=choice_surface_record.inbox_record_id,
            owner_id=choice_surface_record.owner_id,
            robot_id=choice_surface_record.robot_id,
            telegram_chat_id=choice_surface_record.telegram_chat_id,
            status=status,
            response_text=_response_text(selected_option_kind=selected_option_kind),
            lineage_summary=_lineage_summary(
                choice_surface_record=choice_surface_record,
                selected_option_id=payload.selected_option_id,
                selected_option_kind=selected_option_kind,
                status=status,
            ),
            rejection_reason=None,
        )
    )


def build_followup_choice_selection_response_envelope(
    record: TelegramFollowUpChoiceSelectionRecord,
) -> TelegramFollowUpChoiceSelectionResponseEnvelope:
    return TelegramFollowUpChoiceSelectionResponseEnvelope(
        channel="telegram",
        telegram_chat_id=record.telegram_chat_id,
        text=record.response_text,
        send_allowed=False,
    )


def _validate_selection_binding(
    *,
    choice_surface_record: TelegramFollowUpChoiceSurfaceRecord,
    payload: TelegramFollowUpChoiceSelectionPayload,
) -> tuple[str | None, str]:
    if choice_surface_record.status == "blocked":
        return "rejected_blocked_choice_surface_record", ""
    if choice_surface_record.status == "failed":
        return "rejected_failed_choice_surface_record", ""
    if choice_surface_record.status == "duplicate":
        return "rejected_duplicate_only_choice_surface_record", ""
    if choice_surface_record.status not in {"rendered", "delivered"}:
        return f"rejected_non_bindable_choice_surface_status_{choice_surface_record.status}", ""
    if payload.choice_surface_id != choice_surface_record.choice_surface_id:
        return "rejected_choice_surface_mismatch", ""
    if payload.draft_plan_id != choice_surface_record.draft_plan_id:
        return "rejected_draft_plan_mismatch", ""
    if payload.owner_id != choice_surface_record.owner_id:
        return "rejected_owner_mismatch", ""
    if payload.robot_id != choice_surface_record.robot_id:
        return "rejected_robot_mismatch", ""
    if payload.telegram_chat_id != choice_surface_record.telegram_chat_id:
        return "rejected_chat_mismatch", ""
    if payload.requests_execution:
        return "rejected_execution_approval_requested", ""

    inferred_option_kind = _infer_option_kind(
        choice_surface_record=choice_surface_record,
        selected_option_id=payload.selected_option_id,
    )
    if payload.selected_option_id not in choice_surface_record.option_refs:
        if inferred_option_kind:
            return "rejected_option_surface_mismatch", inferred_option_kind
        return "rejected_unknown_selected_option_id", ""

    option_metadata = _option_metadata(
        choice_surface_record=choice_surface_record,
        selected_option_id=payload.selected_option_id,
    )
    if option_metadata is None:
        return "rejected_missing_source_draft_option_lineage", inferred_option_kind or ""

    selected_option_kind = str(option_metadata.get("option_kind") or inferred_option_kind or "")
    if selected_option_kind not in ALLOWED_SELECTION_OPTION_KINDS:
        return "rejected_unsupported_followup_option_kind", selected_option_kind
    if option_metadata.get("local_only") is not True:
        return "rejected_non_local_followup_option", selected_option_kind
    if option_metadata.get("creates_authority") is not False:
        return "rejected_authority_creating_followup_option", selected_option_kind
    for flag, rejection_reason in OPTION_FLAG_TO_REJECTION_REASON.items():
        if bool(option_metadata.get(flag)):
            return rejection_reason, selected_option_kind
    return None, selected_option_kind


def _response_text(*, selected_option_kind: str) -> str:
    if selected_option_kind == "cancel_followup":
        return "Listo. Cancele el seguimiento. No ejecute ninguna accion."
    label = PASSIVE_BUTTON_LABELS_BY_OPTION_KIND[selected_option_kind]
    return f"Registre tu seleccion: {label}. Todavia no ejecute nada."


def _lineage_summary(
    *,
    choice_surface_record: TelegramFollowUpChoiceSurfaceRecord,
    selected_option_id: str,
    selected_option_kind: str,
    status: str,
) -> dict[str, object]:
    return {
        "selection_stage": TELEGRAM_FOLLOWUP_CHOICE_SELECTION_STAGE,
        "selection_status": status,
        "choice_surface_stage": choice_surface_record.lineage_summary.get("choice_surface_stage", TELEGRAM_FOLLOWUP_CHOICE_SURFACE_STAGE),
        "choice_surface_id": choice_surface_record.choice_surface_id,
        "draft_planner_stage": choice_surface_record.lineage_summary.get("draft_planner_stage"),
        "draft_plan_id": choice_surface_record.draft_plan_id,
        "followup_stage": choice_surface_record.lineage_summary.get("followup_stage"),
        "followup_intent_id": choice_surface_record.followup_intent_id,
        "acknowledgement_stage": choice_surface_record.lineage_summary.get("acknowledgement_stage"),
        "acknowledgement_id": choice_surface_record.acknowledgement_id,
        "delivery_stage": choice_surface_record.lineage_summary.get("delivery_stage"),
        "delivery_id": choice_surface_record.delivery_id,
        "source_surface_stage": choice_surface_record.lineage_summary.get("source_surface_stage"),
        "source_surface_id": choice_surface_record.source_surface_id,
        "inbox_stage": choice_surface_record.lineage_summary.get("inbox_stage"),
        "inbox_record_id": choice_surface_record.inbox_record_id,
        "telegram_policy_boundary_stage": choice_surface_record.lineage_summary.get("telegram_policy_boundary_stage"),
        "owner_id": choice_surface_record.owner_id,
        "robot_id": choice_surface_record.robot_id,
        "telegram_chat_id": choice_surface_record.telegram_chat_id,
        "selected_option_id": selected_option_id,
        "selected_option_kind": selected_option_kind,
        "upstream_lineage": choice_surface_record.lineage_summary,
    }


def _blocked_record(
    *,
    selection_id: str,
    payload: TelegramFollowUpChoiceSelectionPayload,
    rejection_reason: str,
    choice_surface_record: TelegramFollowUpChoiceSurfaceRecord | None,
    selected_option_kind: str,
) -> TelegramFollowUpChoiceSelectionRecord:
    return TelegramFollowUpChoiceSelectionRecord(
        selection_id=selection_id,
        choice_surface_id=payload.choice_surface_id,
        draft_plan_id=payload.draft_plan_id,
        selected_option_id=payload.selected_option_id,
        selected_option_kind=selected_option_kind,
        followup_intent_id="" if choice_surface_record is None else choice_surface_record.followup_intent_id,
        acknowledgement_id="" if choice_surface_record is None else choice_surface_record.acknowledgement_id,
        delivery_id="" if choice_surface_record is None else choice_surface_record.delivery_id,
        source_surface_id="" if choice_surface_record is None else choice_surface_record.source_surface_id,
        inbox_record_id="" if choice_surface_record is None else choice_surface_record.inbox_record_id,
        owner_id=payload.owner_id,
        robot_id=payload.robot_id,
        telegram_chat_id=payload.telegram_chat_id,
        status="blocked",
        response_text="No pude registrar esa seleccion en esta version.",
        lineage_summary={
            "selection_stage": TELEGRAM_FOLLOWUP_CHOICE_SELECTION_STAGE,
            "choice_surface_id": payload.choice_surface_id,
            "draft_plan_id": payload.draft_plan_id,
            "selected_option_id": payload.selected_option_id,
            "selected_option_kind": selected_option_kind,
            "owner_id": payload.owner_id,
            "robot_id": payload.robot_id,
            "telegram_chat_id": payload.telegram_chat_id,
            "upstream_lineage": None if choice_surface_record is None else choice_surface_record.lineage_summary,
        },
        rejection_reason=rejection_reason,
    )


def _option_metadata(
    *,
    choice_surface_record: TelegramFollowUpChoiceSurfaceRecord,
    selected_option_id: str,
) -> dict[str, object] | None:
    metadata_by_ref = choice_surface_record.lineage_summary.get("option_metadata_by_ref")
    if isinstance(metadata_by_ref, dict):
        entry = metadata_by_ref.get(selected_option_id)
        if isinstance(entry, dict):
            return dict(entry)

    inferred_option_kind = _infer_option_kind(
        choice_surface_record=choice_surface_record,
        selected_option_id=selected_option_id,
    )
    if not inferred_option_kind:
        return None
    return {
        "option_id": selected_option_id,
        "option_kind": inferred_option_kind,
        "label": PASSIVE_BUTTON_LABELS_BY_OPTION_KIND.get(inferred_option_kind, ""),
        "local_only": True,
        "creates_authority": False,
        "implies_execution": False,
        "implies_memory_mutation": False,
        "implies_external_send": False,
        "implies_model_call": False,
        "implies_tool_call": False,
        "implies_delegation_creation": False,
        "implies_action_packet_creation": False,
        "implies_approval_creation": False,
    }


def _infer_option_kind(
    *,
    choice_surface_record: TelegramFollowUpChoiceSurfaceRecord,
    selected_option_id: str,
) -> str | None:
    metadata_by_ref = choice_surface_record.lineage_summary.get("option_metadata_by_ref")
    if isinstance(metadata_by_ref, dict):
        entry = metadata_by_ref.get(selected_option_id)
        if isinstance(entry, dict):
            option_kind = entry.get("option_kind")
            if isinstance(option_kind, str) and option_kind:
                return option_kind

    for option_kind in (
        "deeper_summary",
        "extract_questions",
        "human_review_checklist",
        "compare_prior_version",
        "review_failure_reason",
        "cancel_followup",
    ):
        if selected_option_id == _draft_option_id(
            followup_intent_id=choice_surface_record.followup_intent_id,
            acknowledgement_id=choice_surface_record.acknowledgement_id,
            option_kind=option_kind,
        ):
            return option_kind
    return None


def _draft_option_id(*, followup_intent_id: str, acknowledgement_id: str, option_kind: str) -> str:
    return "followup_draft_option_" + uuid5(
        NAMESPACE_URL,
        "|".join(str(part) for part in (followup_intent_id, acknowledgement_id, option_kind)),
    ).hex[:12]


def _selection_id(*, payload: TelegramFollowUpChoiceSelectionPayload) -> str:
    return "telegram_followup_choice_selection_" + uuid5(
        NAMESPACE_URL,
        "|".join(
            [
                payload.choice_surface_id,
                payload.draft_plan_id,
                payload.selected_option_id,
                payload.owner_id,
                payload.robot_id,
                payload.telegram_chat_id,
            ]
        ),
    ).hex[:12]
