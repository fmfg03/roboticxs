from __future__ import annotations

from dataclasses import dataclass, field, replace
from uuid import NAMESPACE_URL, uuid5

from app.followup_intent_review import FOLLOWUP_SOURCE_ACTION, FollowUpIntentReviewRecord


FOLLOWUP_DRAFT_PLANNER_STAGE = "108P"
FOLLOWUP_DRAFT_PLAN_STATUSES = frozenset({"drafted", "duplicate", "blocked"})
FOLLOWUP_DRAFT_OPTION_KINDS = frozenset(
    {
        "deeper_summary",
        "extract_questions",
        "human_review_checklist",
        "compare_prior_version",
        "review_failure_reason",
        "cancel_followup",
    }
)
@dataclass(frozen=True, slots=True)
class FollowUpDraftOption:
    option_id: str
    label: str
    description: str
    option_kind: str
    local_only: bool
    creates_authority: bool

    def __post_init__(self) -> None:
        if self.option_kind not in FOLLOWUP_DRAFT_OPTION_KINDS:
            raise ValueError("Unsupported follow-up draft option kind.")
        if self.local_only is not True:
            raise ValueError("108P options must remain local-only.")
        if self.creates_authority is not False:
            raise ValueError("108P options must not create authority.")


@dataclass(frozen=True, slots=True)
class FollowUpDraftPlanRecord:
    draft_plan_id: str
    followup_intent_id: str
    acknowledgement_id: str
    delivery_id: str
    surface_id: str
    inbox_record_id: str
    owner_id: str
    robot_id: str
    telegram_chat_id: str
    status: str
    title: str
    summary: str
    options: tuple[FollowUpDraftOption, ...]
    lineage_summary: dict[str, object]
    rejection_reason: str | None

    def __post_init__(self) -> None:
        if self.status not in FOLLOWUP_DRAFT_PLAN_STATUSES:
            raise ValueError("Unsupported follow-up draft plan status.")


@dataclass(frozen=True, slots=True)
class FollowUpDraftPlanResponseEnvelope:
    channel: str
    telegram_chat_id: str
    text: str
    option_labels: tuple[str, ...]
    send_allowed: bool

    def __post_init__(self) -> None:
        if self.channel != "telegram":
            raise ValueError("108P only supports local Telegram-compatible response envelopes.")
        if self.send_allowed is not False:
            raise ValueError("108P response envelopes must not authorize sending.")


@dataclass(slots=True)
class FollowUpDraftPlanRegistry:
    plans_by_id: dict[str, FollowUpDraftPlanRecord] = field(default_factory=dict)

    def get_plan(self, draft_plan_id: str) -> FollowUpDraftPlanRecord | None:
        return self.plans_by_id.get(draft_plan_id)

    def store(self, record: FollowUpDraftPlanRecord) -> FollowUpDraftPlanRecord:
        self.plans_by_id[record.draft_plan_id] = record
        return record

    def list_plans(self) -> tuple[FollowUpDraftPlanRecord, ...]:
        return tuple(self.plans_by_id[key] for key in sorted(self.plans_by_id))

    def list_drafted(self) -> tuple[FollowUpDraftPlanRecord, ...]:
        return tuple(record for record in self.list_plans() if record.status == "drafted")

    def list_blocked(self) -> tuple[FollowUpDraftPlanRecord, ...]:
        return tuple(record for record in self.list_plans() if record.status == "blocked")


def create_followup_draft_plan(
    *,
    followup_intent_record: object,
    registry: FollowUpDraftPlanRegistry,
) -> FollowUpDraftPlanRecord:
    if not isinstance(followup_intent_record, FollowUpIntentReviewRecord):
        blocked = _blocked_unknown_source(followup_intent_record=followup_intent_record)
        return registry.store(blocked)

    draft_plan_id = _draft_plan_id(followup_intent_record=followup_intent_record)
    existing = registry.get_plan(draft_plan_id)
    if existing is not None:
        return replace(existing, status="duplicate", rejection_reason="duplicate_followup_draft_plan")

    rejection_reason = _validate_followup_intent_record(followup_intent_record=followup_intent_record)
    if rejection_reason is not None:
        return registry.store(
            _blocked_record(
                followup_intent_record=followup_intent_record,
                rejection_reason=rejection_reason,
            )
        )

    options = _draft_options(followup_intent_record=followup_intent_record)
    summary = _draft_summary(followup_intent_record=followup_intent_record, options=options)
    return registry.store(
        FollowUpDraftPlanRecord(
            draft_plan_id=draft_plan_id,
            followup_intent_id=followup_intent_record.followup_intent_id,
            acknowledgement_id=followup_intent_record.acknowledgement_id,
            delivery_id=followup_intent_record.delivery_id,
            surface_id=followup_intent_record.surface_id,
            inbox_record_id=followup_intent_record.inbox_record_id,
            owner_id=followup_intent_record.owner_id,
            robot_id=followup_intent_record.robot_id,
            telegram_chat_id=followup_intent_record.telegram_chat_id,
            status="drafted",
            title=_draft_title(followup_intent_record=followup_intent_record),
            summary=summary,
            options=options,
            lineage_summary=_draft_lineage_summary(followup_intent_record=followup_intent_record),
            rejection_reason=None,
        )
    )


def build_followup_draft_plan_response_envelope(
    record: FollowUpDraftPlanRecord,
) -> FollowUpDraftPlanResponseEnvelope:
    return FollowUpDraftPlanResponseEnvelope(
        channel="telegram",
        telegram_chat_id=record.telegram_chat_id,
        text=record.summary,
        option_labels=tuple(option.label for option in record.options),
        send_allowed=False,
    )


def _validate_followup_intent_record(*, followup_intent_record: FollowUpIntentReviewRecord) -> str | None:
    if followup_intent_record.status != "pending_review":
        return f"rejected_followup_intent_status_{followup_intent_record.status}"
    if followup_intent_record.source_action != FOLLOWUP_SOURCE_ACTION:
        return "rejected_non_followup_intent_action"
    if not followup_intent_record.owner_id:
        return "rejected_missing_owner_id"
    if not followup_intent_record.robot_id:
        return "rejected_missing_robot_id"
    if not followup_intent_record.telegram_chat_id:
        return "rejected_missing_telegram_chat_id"
    if not followup_intent_record.acknowledgement_id:
        return "rejected_missing_acknowledgement_id"
    if not followup_intent_record.delivery_id:
        return "rejected_missing_delivery_id"
    if not followup_intent_record.surface_id:
        return "rejected_missing_surface_id"
    if not followup_intent_record.inbox_record_id:
        return "rejected_missing_inbox_record_id"

    lineage = followup_intent_record.lineage_summary
    if not lineage:
        return "rejected_missing_lineage_summary"
    if lineage.get("followup_stage") != "107P":
        return "rejected_unknown_followup_stage"
    if lineage.get("acknowledgement_stage") != "106P":
        return "rejected_unknown_acknowledgement_stage"
    if lineage.get("acknowledgement_id") != followup_intent_record.acknowledgement_id:
        return "rejected_acknowledgement_mismatch"
    if lineage.get("delivery_stage") != "105P":
        return "rejected_unknown_delivery_stage"
    if lineage.get("delivery_id") != followup_intent_record.delivery_id:
        return "rejected_delivery_mismatch"
    if lineage.get("surface_id") != followup_intent_record.surface_id:
        return "rejected_surface_mismatch"
    if lineage.get("inbox_record_id") != followup_intent_record.inbox_record_id:
        return "rejected_inbox_record_mismatch"
    if lineage.get("owner_id") != followup_intent_record.owner_id:
        return "rejected_owner_mismatch"
    if lineage.get("robot_id") != followup_intent_record.robot_id:
        return "rejected_robot_mismatch"
    if lineage.get("telegram_chat_id") != followup_intent_record.telegram_chat_id:
        return "rejected_chat_mismatch"
    upstream_lineage = lineage.get("upstream_lineage")
    if not isinstance(upstream_lineage, dict):
        return "rejected_missing_upstream_lineage"
    if upstream_lineage.get("surface_stage") != "104P":
        return "rejected_missing_104p_surface_lineage"
    if upstream_lineage.get("surface_id") != followup_intent_record.surface_id:
        return "rejected_surface_mismatch"
    if upstream_lineage.get("inbox_record_id") != followup_intent_record.inbox_record_id:
        return "rejected_inbox_record_mismatch"
    if upstream_lineage.get("owner_id") != followup_intent_record.owner_id:
        return "rejected_owner_mismatch"
    if upstream_lineage.get("robot_id") != followup_intent_record.robot_id:
        return "rejected_robot_mismatch"
    nested_lineage = upstream_lineage.get("upstream_lineage")
    if not isinstance(nested_lineage, dict):
        return "rejected_missing_103p_inbox_lineage"
    if nested_lineage.get("inbox_stage") != "103P":
        return "rejected_missing_103p_inbox_lineage"
    if nested_lineage.get("inbox_record_id") != followup_intent_record.inbox_record_id:
        return "rejected_inbox_record_mismatch"
    if _execution_authority_detected(nested_lineage):
        return "rejected_execution_authority_signal"
    return None


def _execution_authority_detected(nested_lineage: dict[str, object]) -> bool:
    event = nested_lineage.get("completion_event")
    if isinstance(event, dict):
        if any(bool(event.get(key)) for key in ("tool_authority_granted", "provider_call_authorized", "external_effect_authorized")):
            return True
    return False


def _draft_options(
    *,
    followup_intent_record: FollowUpIntentReviewRecord,
) -> tuple[FollowUpDraftOption, ...]:
    result_status = _result_status(followup_intent_record=followup_intent_record)
    option_kinds = ("deeper_summary", "extract_questions", "human_review_checklist", "cancel_followup")
    if result_status == "failed":
        option_kinds = ("review_failure_reason", "human_review_checklist", "cancel_followup")
    elif _has_prior_artifact_hint(followup_intent_record=followup_intent_record):
        option_kinds = (
            "deeper_summary",
            "extract_questions",
            "human_review_checklist",
            "compare_prior_version",
            "cancel_followup",
        )
    return tuple(_build_option(followup_intent_record=followup_intent_record, option_kind=option_kind) for option_kind in option_kinds)


def _build_option(
    *,
    followup_intent_record: FollowUpIntentReviewRecord,
    option_kind: str,
) -> FollowUpDraftOption:
    labels = {
        "deeper_summary": "Preparar un resumen mas profundo.",
        "extract_questions": "Extraer preguntas pendientes.",
        "human_review_checklist": "Crear una checklist de revision humana.",
        "compare_prior_version": "Comparar contra una version previa si existe.",
        "review_failure_reason": "Revisar por que fallo el resultado.",
        "cancel_followup": "Cancelar seguimiento.",
    }
    descriptions = {
        "deeper_summary": "Mantener el seguimiento en modo local y proponer un resumen mas detallado para revision humana.",
        "extract_questions": "Preparar solo preguntas abiertas detectables desde el resultado ya resumido.",
        "human_review_checklist": "Ordenar una lista de verificacion humana sin ejecutar ninguna accion.",
        "compare_prior_version": "Proponer una comparacion solo si existe evidencia local de una version previa.",
        "review_failure_reason": "Preparar una lectura local del fallo sin reintentar ni delegar trabajo.",
        "cancel_followup": "Cerrar esta solicitud sin ejecutar seguimiento.",
    }
    return FollowUpDraftOption(
        option_id=_stable_id(
            "followup_draft_option",
            followup_intent_record.followup_intent_id,
            followup_intent_record.acknowledgement_id,
            option_kind,
        ),
        label=labels[option_kind],
        description=descriptions[option_kind],
        option_kind=option_kind,
        local_only=True,
        creates_authority=False,
    )


def _draft_title(*, followup_intent_record: FollowUpIntentReviewRecord) -> str:
    if _result_status(followup_intent_record=followup_intent_record) == "failed":
        return "Opciones de seguimiento para un resultado no disponible"
    return "Opciones de seguimiento preparadas localmente"


def _draft_summary(
    *,
    followup_intent_record: FollowUpIntentReviewRecord,
    options: tuple[FollowUpDraftOption, ...],
) -> str:
    task_label = _task_label(followup_intent_record=followup_intent_record)
    status = _result_status(followup_intent_record=followup_intent_record)
    lines = ["Tengo estas opciones de seguimiento:", ""]
    for index, option in enumerate(options, start=1):
        lines.append(f"{index}. {option.label}")
    lines.extend(
        [
            "",
            f"Contexto: {task_label}.",
            f"Estado origen: {status}.",
            "Todavia no ejecute nada. Elige una opcion para continuar.",
        ]
    )
    return "\n".join(lines)


def _draft_lineage_summary(
    *,
    followup_intent_record: FollowUpIntentReviewRecord,
) -> dict[str, object]:
    upstream_lineage = followup_intent_record.lineage_summary.get("upstream_lineage")
    return {
        "planner_stage": FOLLOWUP_DRAFT_PLANNER_STAGE,
        "followup_stage": followup_intent_record.lineage_summary.get("followup_stage"),
        "followup_intent_id": followup_intent_record.followup_intent_id,
        "acknowledgement_stage": followup_intent_record.lineage_summary.get("acknowledgement_stage"),
        "acknowledgement_id": followup_intent_record.acknowledgement_id,
        "delivery_stage": followup_intent_record.lineage_summary.get("delivery_stage"),
        "delivery_id": followup_intent_record.delivery_id,
        "surface_id": followup_intent_record.surface_id,
        "inbox_record_id": followup_intent_record.inbox_record_id,
        "owner_id": followup_intent_record.owner_id,
        "robot_id": followup_intent_record.robot_id,
        "telegram_chat_id": followup_intent_record.telegram_chat_id,
        "source_action": followup_intent_record.source_action,
        "upstream_lineage": _copy_dict(upstream_lineage),
    }


def _blocked_record(
    *,
    followup_intent_record: FollowUpIntentReviewRecord,
    rejection_reason: str,
) -> FollowUpDraftPlanRecord:
    return FollowUpDraftPlanRecord(
        draft_plan_id=_draft_plan_id(followup_intent_record=followup_intent_record),
        followup_intent_id=followup_intent_record.followup_intent_id,
        acknowledgement_id=followup_intent_record.acknowledgement_id,
        delivery_id=followup_intent_record.delivery_id,
        surface_id=followup_intent_record.surface_id,
        inbox_record_id=followup_intent_record.inbox_record_id,
        owner_id=followup_intent_record.owner_id,
        robot_id=followup_intent_record.robot_id,
        telegram_chat_id=followup_intent_record.telegram_chat_id,
        status="blocked",
        title="Seguimiento no disponible",
        summary="No pude preparar opciones de seguimiento en esta version.",
        options=(),
        lineage_summary=_draft_lineage_summary(followup_intent_record=followup_intent_record),
        rejection_reason=rejection_reason,
    )


def _blocked_unknown_source(*, followup_intent_record: object) -> FollowUpDraftPlanRecord:
    source_type = type(followup_intent_record).__name__
    return FollowUpDraftPlanRecord(
        draft_plan_id=_stable_id("followup_draft_plan", "unknown", source_type),
        followup_intent_id="",
        acknowledgement_id="",
        delivery_id="",
        surface_id="",
        inbox_record_id="",
        owner_id="",
        robot_id="",
        telegram_chat_id="",
        status="blocked",
        title="Seguimiento no disponible",
        summary="No pude preparar opciones de seguimiento en esta version.",
        options=(),
        lineage_summary={"planner_stage": FOLLOWUP_DRAFT_PLANNER_STAGE, "source_type": source_type},
        rejection_reason="rejected_unknown_followup_intent_record",
    )


def _task_label(*, followup_intent_record: FollowUpIntentReviewRecord) -> str:
    surface_lineage = _surface_lineage(followup_intent_record=followup_intent_record)
    request_evidence = surface_lineage.get("request_evidence")
    if isinstance(request_evidence, dict):
        payload = request_evidence.get("request_payload")
        if isinstance(payload, dict):
            summary = payload.get("summary")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
        capability = request_evidence.get("requested_capability")
        if isinstance(capability, str) and capability.strip():
            return capability.strip()
    return "seguimiento local"


def _result_status(*, followup_intent_record: FollowUpIntentReviewRecord) -> str:
    surface_lineage = _surface_lineage(followup_intent_record=followup_intent_record)
    status = surface_lineage.get("completion_status")
    if status in {"completed", "failed"}:
        return str(status)
    return "completed"


def _has_prior_artifact_hint(*, followup_intent_record: FollowUpIntentReviewRecord) -> bool:
    surface_lineage = _surface_lineage(followup_intent_record=followup_intent_record)
    payload_summary = surface_lineage.get("completion_payload_summary")
    if not isinstance(payload_summary, dict):
        return False
    for key in ("prior_artifact_available", "prior_version_available", "comparison_available"):
        if payload_summary.get(key) is True:
            return True
    return False


def _surface_lineage(*, followup_intent_record: FollowUpIntentReviewRecord) -> dict[str, object]:
    delivery_lineage = followup_intent_record.lineage_summary.get("upstream_lineage")
    if not isinstance(delivery_lineage, dict):
        return {}
    surface_lineage = delivery_lineage.get("upstream_lineage")
    if not isinstance(surface_lineage, dict):
        return {}
    return surface_lineage


def _copy_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    copied: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(item, dict):
            copied[key] = _copy_dict(item)
        elif isinstance(item, list):
            copied[key] = list(item)
        else:
            copied[key] = item
    return copied


def _draft_plan_id(*, followup_intent_record: FollowUpIntentReviewRecord) -> str:
    return "followup_draft_plan_" + uuid5(
        NAMESPACE_URL,
        "|".join(
            [
                followup_intent_record.followup_intent_id,
                followup_intent_record.acknowledgement_id,
                followup_intent_record.delivery_id,
                followup_intent_record.surface_id,
                followup_intent_record.inbox_record_id,
                followup_intent_record.owner_id,
                followup_intent_record.robot_id,
                followup_intent_record.telegram_chat_id,
            ]
        ),
    ).hex[:12]


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(NAMESPACE_URL, "|".join("" if part is None else str(part) for part in parts)).hex[:12]
