from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

from app.followup_draft_planner import FOLLOWUP_DRAFT_PLANNER_STAGE, FollowUpDraftOption, FollowUpDraftPlanRecord
from app.telegram_async_result_delivery import TelegramAsyncResultTransport, TelegramOwnerBinding
from app.telegram_policy_chain import POLICY_CHAIN_STAGE


TELEGRAM_FOLLOWUP_CHOICE_SURFACE_STAGE = "109P"
CHOICE_SURFACE_STATUSES = frozenset({"rendered", "delivered", "duplicate", "blocked", "failed"})
PASSIVE_BUTTON_LABELS_BY_OPTION_KIND = {
    "deeper_summary": "Resumen mas profundo",
    "extract_questions": "Preguntas pendientes",
    "human_review_checklist": "Checklist de revision",
    "compare_prior_version": "Comparar version previa",
    "review_failure_reason": "Revisar fallo",
    "cancel_followup": "Cancelar",
}
PASSIVE_OPTION_FLAGS = (
    "implies_execution",
    "implies_memory_mutation",
    "implies_external_send",
    "implies_model_call",
    "implies_tool_call",
    "implies_delegation_creation",
    "implies_action_packet_creation",
    "implies_approval_creation",
    "binds_selection",
    "creates_selected_option_record",
)


@dataclass(frozen=True, slots=True)
class TelegramFollowUpChoiceSurfaceRecord:
    choice_surface_id: str
    draft_plan_id: str
    followup_intent_id: str
    acknowledgement_id: str
    delivery_id: str
    source_surface_id: str
    inbox_record_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    status: str
    text: str
    button_labels: tuple[str, ...]
    option_refs: tuple[str, ...]
    lineage_summary: dict[str, object]
    transport_receipt: dict | None
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in CHOICE_SURFACE_STATUSES:
            raise ValueError("Unsupported Telegram follow-up choice surface status.")


@dataclass(frozen=True, slots=True)
class TelegramFollowUpChoiceEnvelope:
    channel: str
    telegram_chat_id: str
    text: str
    button_labels: tuple[str, ...]
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("109P only supports Telegram choice envelopes.")
        if self.send_allowed is not False:
            raise ValueError("109P choice envelopes must keep send_allowed false.")


@dataclass(slots=True)
class TelegramFollowUpChoiceSurfaceRegistry:
    records_by_id: dict[str, TelegramFollowUpChoiceSurfaceRecord] = field(default_factory=dict)

    def get_record(self, choice_surface_id: str) -> TelegramFollowUpChoiceSurfaceRecord | None:
        return self.records_by_id.get(choice_surface_id)

    def store(self, record: TelegramFollowUpChoiceSurfaceRecord) -> TelegramFollowUpChoiceSurfaceRecord:
        self.records_by_id[record.choice_surface_id] = record
        return record

    def list_records(self) -> tuple[TelegramFollowUpChoiceSurfaceRecord, ...]:
        return tuple(self.records_by_id[key] for key in sorted(self.records_by_id))

    def list_active(self) -> tuple[TelegramFollowUpChoiceSurfaceRecord, ...]:
        return tuple(record for record in self.list_records() if record.status in {"rendered", "delivered"})


def create_telegram_followup_choice_surface(
    *,
    draft_plan_record: object,
    registry: TelegramFollowUpChoiceSurfaceRegistry,
) -> TelegramFollowUpChoiceSurfaceRecord:
    if not isinstance(draft_plan_record, FollowUpDraftPlanRecord):
        blocked = _blocked_unknown_source(draft_plan_record=draft_plan_record)
        return registry.store(blocked)

    choice_surface_id = _choice_surface_id(
        draft_plan_record=draft_plan_record,
        telegram_chat_id=draft_plan_record.telegram_chat_id,
    )
    existing = registry.get_record(choice_surface_id)
    if existing is not None:
        return replace(existing, status="duplicate", rejection_reason="duplicate_followup_choice_surface")

    rejection_reason = _validate_draft_plan_record(draft_plan_record=draft_plan_record)
    if rejection_reason is not None:
        return registry.store(_blocked_record(draft_plan_record=draft_plan_record, reason=rejection_reason))

    text = _render_choice_surface_text(draft_plan_record=draft_plan_record)
    button_labels = _button_labels(draft_plan_record=draft_plan_record)
    return registry.store(
        _record(
            draft_plan_record=draft_plan_record,
            telegram_chat_id=draft_plan_record.telegram_chat_id,
            text=text,
            button_labels=button_labels,
            status="rendered",
            transport_receipt=None,
            rejection_reason=None,
        )
    )


def build_telegram_followup_choice_envelope(
    record: TelegramFollowUpChoiceSurfaceRecord,
) -> TelegramFollowUpChoiceEnvelope:
    return TelegramFollowUpChoiceEnvelope(
        channel="telegram",
        telegram_chat_id=record.telegram_chat_id,
        text=record.text,
        button_labels=record.button_labels,
        send_allowed=False,
    )


def deliver_telegram_followup_choice_surface(
    *,
    draft_plan_record: object,
    owner_binding: TelegramOwnerBinding | None,
    transport: TelegramAsyncResultTransport,
    registry: TelegramFollowUpChoiceSurfaceRegistry,
    telegram_chat_id: str | None = None,
) -> TelegramFollowUpChoiceSurfaceRecord:
    created = create_telegram_followup_choice_surface(
        draft_plan_record=draft_plan_record,
        registry=registry,
    )
    if created.status == "blocked":
        return created
    if created.status == "duplicate":
        existing = registry.get_record(created.choice_surface_id)
        if existing is not None:
            return existing

    base_record = registry.get_record(created.choice_surface_id)
    if base_record is None:
        raise KeyError(f"Missing 109P choice surface record: {created.choice_surface_id}")
    if base_record.status == "delivered":
        return base_record

    envelope = build_telegram_followup_choice_envelope(base_record)
    reason = _validate_delivery_request(
        record=base_record,
        envelope=envelope,
        owner_binding=owner_binding,
        telegram_chat_id=telegram_chat_id,
    )
    if reason is not None:
        blocked = replace(base_record, status="blocked", rejection_reason=reason)
        return registry.store(blocked)

    assert owner_binding is not None
    target_chat_id = owner_binding.telegram_chat_id if telegram_chat_id is None else telegram_chat_id

    try:
        receipt = transport.deliver(target_chat_id, envelope.text, envelope.button_labels)
    except Exception:
        failed = replace(
            base_record,
            telegram_chat_id=target_chat_id,
            status="failed",
            transport_receipt=None,
            rejection_reason="transport_delivery_failed",
        )
        return registry.store(failed)

    delivered = replace(
        base_record,
        telegram_chat_id=target_chat_id,
        status="delivered",
        transport_receipt=receipt,
        rejection_reason=None,
    )
    return registry.store(delivered)


def _validate_draft_plan_record(*, draft_plan_record: FollowUpDraftPlanRecord) -> str | None:
    if draft_plan_record.status != "drafted":
        return f"rejected_non_drafted_plan_status_{draft_plan_record.status}"
    if not draft_plan_record.owner_id:
        return "rejected_missing_owner_id"
    if not draft_plan_record.robot_id:
        return "rejected_missing_robot_id"
    if not draft_plan_record.telegram_chat_id:
        return "rejected_missing_telegram_chat_id"
    if not draft_plan_record.followup_intent_id:
        return "rejected_missing_followup_intent_id"
    if not draft_plan_record.acknowledgement_id:
        return "rejected_missing_acknowledgement_id"
    if not draft_plan_record.delivery_id:
        return "rejected_missing_delivery_id"
    if not draft_plan_record.surface_id:
        return "rejected_missing_surface_id"
    if not draft_plan_record.inbox_record_id:
        return "rejected_missing_inbox_record_id"
    if not draft_plan_record.options:
        return "rejected_missing_followup_options"
    for option in draft_plan_record.options:
        if getattr(option, "local_only", False) is not True:
            return "rejected_non_local_followup_option"
        if getattr(option, "creates_authority", False) is not False:
            return "rejected_authority_creating_followup_option"
        for forbidden_flag in PASSIVE_OPTION_FLAGS:
            if getattr(option, forbidden_flag, False):
                if forbidden_flag == "implies_execution":
                    return "rejected_execution_implying_followup_option"
                return f"rejected_forbidden_followup_option_{forbidden_flag}"
        option_kind = getattr(option, "option_kind", None)
        if option_kind not in PASSIVE_BUTTON_LABELS_BY_OPTION_KIND:
            return "rejected_unknown_followup_option_kind"

    lineage = draft_plan_record.lineage_summary
    if not lineage:
        return "rejected_missing_lineage_summary"
    if lineage.get("planner_stage") != FOLLOWUP_DRAFT_PLANNER_STAGE:
        return "rejected_unknown_planner_stage"
    if lineage.get("followup_stage") != "107P":
        return "rejected_unknown_followup_stage"
    if lineage.get("followup_intent_id") != draft_plan_record.followup_intent_id:
        return "rejected_followup_intent_mismatch"
    if lineage.get("acknowledgement_stage") != "106P":
        return "rejected_unknown_acknowledgement_stage"
    if lineage.get("acknowledgement_id") != draft_plan_record.acknowledgement_id:
        return "rejected_acknowledgement_mismatch"
    if lineage.get("delivery_stage") != "105P":
        return "rejected_unknown_delivery_stage"
    if lineage.get("delivery_id") != draft_plan_record.delivery_id:
        return "rejected_delivery_mismatch"
    if lineage.get("surface_id") != draft_plan_record.surface_id:
        return "rejected_surface_mismatch"
    if lineage.get("inbox_record_id") != draft_plan_record.inbox_record_id:
        return "rejected_inbox_record_mismatch"
    if lineage.get("owner_id") != draft_plan_record.owner_id:
        return "rejected_owner_mismatch"
    if lineage.get("robot_id") != draft_plan_record.robot_id:
        return "rejected_robot_mismatch"
    if lineage.get("telegram_chat_id") != draft_plan_record.telegram_chat_id:
        return "rejected_chat_mismatch"
    upstream_lineage = lineage.get("upstream_lineage")
    if not isinstance(upstream_lineage, dict):
        return "rejected_missing_upstream_lineage"
    if upstream_lineage.get("surface_stage") != "104P":
        return "rejected_missing_104p_surface_lineage"
    if upstream_lineage.get("surface_id") != draft_plan_record.surface_id:
        return "rejected_surface_mismatch"
    nested_lineage = upstream_lineage.get("upstream_lineage")
    if not isinstance(nested_lineage, dict):
        return "rejected_missing_103p_inbox_lineage"
    if nested_lineage.get("inbox_stage") != "103P":
        return "rejected_missing_103p_inbox_lineage"
    if nested_lineage.get("inbox_record_id") != draft_plan_record.inbox_record_id:
        return "rejected_inbox_record_mismatch"
    return None


def _validate_delivery_request(
    *,
    record: TelegramFollowUpChoiceSurfaceRecord,
    envelope: TelegramFollowUpChoiceEnvelope,
    owner_binding: TelegramOwnerBinding | None,
    telegram_chat_id: str | None,
) -> str | None:
    if record.status not in {"rendered", "delivered"}:
        return "rejected_non_deliverable_choice_surface_status"
    if envelope.channel != "telegram":
        return "rejected_non_telegram_channel"
    if envelope.send_allowed is not False:
        return "rejected_send_allowed_envelope"
    if owner_binding is None:
        return "rejected_unknown_telegram_binding"
    if owner_binding.channel != "telegram":
        return "rejected_non_telegram_binding"
    if owner_binding.enabled is not True:
        return "rejected_disabled_telegram_binding"
    if owner_binding.owner_id != record.owner_id:
        return "rejected_owner_mismatch"
    if owner_binding.robot_id != record.robot_id:
        return "rejected_robot_mismatch"
    if not owner_binding.telegram_chat_id:
        return "rejected_unknown_telegram_recipient"
    if telegram_chat_id is not None and telegram_chat_id != owner_binding.telegram_chat_id:
        return "rejected_third_party_recipient"
    return None


def _render_choice_surface_text(*, draft_plan_record: FollowUpDraftPlanRecord) -> str:
    lines = ["Tengo estas opciones de seguimiento:", ""]
    for index, option in enumerate(draft_plan_record.options, start=1):
        lines.append(f"{index}. {option.label}")
    lines.extend(["", "Todavia no ejecute nada. Elige una opcion para continuar."])
    return "\n".join(lines)


def _button_labels(*, draft_plan_record: FollowUpDraftPlanRecord) -> tuple[str, ...]:
    return tuple(PASSIVE_BUTTON_LABELS_BY_OPTION_KIND[option.option_kind] for option in draft_plan_record.options)


def _blocked_record(
    *,
    draft_plan_record: FollowUpDraftPlanRecord,
    reason: str,
) -> TelegramFollowUpChoiceSurfaceRecord:
    return _record(
        draft_plan_record=draft_plan_record,
        telegram_chat_id=draft_plan_record.telegram_chat_id,
        text="No pude preparar opciones de seguimiento para Telegram en esta version.",
        button_labels=(),
        status="blocked",
        transport_receipt=None,
        rejection_reason=reason,
    )


def _blocked_unknown_source(*, draft_plan_record: object) -> TelegramFollowUpChoiceSurfaceRecord:
    source_type = type(draft_plan_record).__name__
    return TelegramFollowUpChoiceSurfaceRecord(
        choice_surface_id=_stable_id("telegram_followup_choice_surface", "unknown", source_type),
        draft_plan_id="",
        followup_intent_id="",
        acknowledgement_id="",
        delivery_id="",
        source_surface_id="",
        inbox_record_id="",
        owner_id="",
        robot_id="",
        telegram_chat_id="",
        status="blocked",
        text="No pude preparar opciones de seguimiento para Telegram en esta version.",
        button_labels=(),
        option_refs=(),
        lineage_summary={
            "choice_surface_stage": TELEGRAM_FOLLOWUP_CHOICE_SURFACE_STAGE,
            "source_type": source_type,
        },
        transport_receipt=None,
        rejection_reason="rejected_unknown_followup_draft_plan_record",
    )


def _record(
    *,
    draft_plan_record: FollowUpDraftPlanRecord,
    telegram_chat_id: str,
    text: str,
    button_labels: tuple[str, ...],
    status: str,
    transport_receipt: dict | None,
    rejection_reason: str | None,
) -> TelegramFollowUpChoiceSurfaceRecord:
    return TelegramFollowUpChoiceSurfaceRecord(
        choice_surface_id=_choice_surface_id(
            draft_plan_record=draft_plan_record,
            telegram_chat_id=telegram_chat_id,
        ),
        draft_plan_id=draft_plan_record.draft_plan_id,
        followup_intent_id=draft_plan_record.followup_intent_id,
        acknowledgement_id=draft_plan_record.acknowledgement_id,
        delivery_id=draft_plan_record.delivery_id,
        source_surface_id=draft_plan_record.surface_id,
        inbox_record_id=draft_plan_record.inbox_record_id,
        owner_id=draft_plan_record.owner_id,
        robot_id=draft_plan_record.robot_id,
        telegram_chat_id=telegram_chat_id,
        status=status,
        text=text,
        button_labels=button_labels,
        option_refs=tuple(getattr(option, "option_id", "") for option in draft_plan_record.options),
        lineage_summary={
            "choice_surface_stage": TELEGRAM_FOLLOWUP_CHOICE_SURFACE_STAGE,
            "draft_planner_stage": FOLLOWUP_DRAFT_PLANNER_STAGE,
            "followup_stage": draft_plan_record.lineage_summary.get("followup_stage"),
            "followup_intent_id": draft_plan_record.followup_intent_id,
            "acknowledgement_stage": draft_plan_record.lineage_summary.get("acknowledgement_stage"),
            "acknowledgement_id": draft_plan_record.acknowledgement_id,
            "delivery_stage": draft_plan_record.lineage_summary.get("delivery_stage"),
            "delivery_id": draft_plan_record.delivery_id,
            "source_surface_stage": "104P",
            "source_surface_id": draft_plan_record.surface_id,
            "inbox_stage": "103P",
            "inbox_record_id": draft_plan_record.inbox_record_id,
            "telegram_policy_boundary_stage": POLICY_CHAIN_STAGE,
            "owner_id": draft_plan_record.owner_id,
            "robot_id": draft_plan_record.robot_id,
            "telegram_chat_id": telegram_chat_id,
            "option_refs": tuple(getattr(option, "option_id", "") for option in draft_plan_record.options),
            "upstream_lineage": draft_plan_record.lineage_summary,
        },
        transport_receipt=transport_receipt,
        rejection_reason=rejection_reason,
    )


def _choice_surface_id(
    *,
    draft_plan_record: FollowUpDraftPlanRecord,
    telegram_chat_id: str,
) -> str:
    text_hash = sha256(_render_choice_surface_text(draft_plan_record=draft_plan_record).encode("utf-8")).hexdigest()[:16]
    return "telegram_followup_choice_surface_" + uuid5(
        NAMESPACE_URL,
        "|".join(
            [
                draft_plan_record.draft_plan_id,
                draft_plan_record.followup_intent_id,
                draft_plan_record.acknowledgement_id,
                draft_plan_record.delivery_id,
                draft_plan_record.surface_id,
                draft_plan_record.inbox_record_id,
                draft_plan_record.owner_id,
                draft_plan_record.robot_id,
                telegram_chat_id,
                ",".join(getattr(option, "option_id", "") for option in draft_plan_record.options),
                text_hash,
            ]
        ),
    ).hex[:12]


def _stable_id(*parts: str) -> str:
    return uuid5(NAMESPACE_URL, "|".join(parts)).hex[:12]
