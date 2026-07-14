from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import NAMESPACE_URL, uuid5

from app.async_delegation_authority import (
    AsyncDelegationAuthorityState,
    AsyncDelegationCompletionEvent,
    record_async_delegation_completion,
    record_async_delegation_failure,
)


ASYNC_DELEGATION_INBOX_STAGE = "103P"
ACCEPTED_EVENT_STATUSES = frozenset({"completed", "failed"})
INBOX_RECORD_STATUSES = frozenset({"accepted", "duplicate", "quarantined"})


@dataclass(frozen=True, slots=True)
class AsyncDelegationInboxRecord:
    inbox_record_id: str
    event_id: str
    handle_id: str | None
    owner_id: str | None
    robot_id: str | None
    request_id: str | None
    event_kind: str
    status: str
    reason: str | None
    bound_completion_event: dict[str, object] | None
    rejection_evidence: dict[str, object] | None
    created_at: str

    def __post_init__(self) -> None:
        if self.status not in INBOX_RECORD_STATUSES:
            raise ValueError("Inbox record status must be accepted, duplicate, or quarantined.")


@dataclass(frozen=True, slots=True)
class AsyncDelegationRegistry:
    authority_states: tuple[AsyncDelegationAuthorityState, ...]
    local_only: bool = True
    non_dispatching: bool = True
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        seen_handles: set[str] = set()
        for state in self.authority_states:
            handle = state.handle
            if handle is None:
                continue
            if handle.handle_id in seen_handles:
                raise ValueError("AsyncDelegationRegistry handle ids must be unique.")
            seen_handles.add(handle.handle_id)

    def get_by_handle_id(self, handle_id: str) -> AsyncDelegationAuthorityState | None:
        for state in self.authority_states:
            if state.handle is not None and state.handle.handle_id == handle_id:
                return state
        return None

    def replace_state(self, original: AsyncDelegationAuthorityState, updated: AsyncDelegationAuthorityState) -> AsyncDelegationRegistry:
        replaced = tuple(updated if state == original else state for state in self.authority_states)
        return replace(self, authority_states=replaced)


@dataclass(frozen=True, slots=True)
class AsyncDelegationInboxReceipt:
    record: AsyncDelegationInboxRecord
    inbox: AsyncDelegationCompletionInbox
    registry: AsyncDelegationRegistry


@dataclass(frozen=True, slots=True)
class AsyncDelegationCompletionInbox:
    records: tuple[AsyncDelegationInboxRecord, ...] = ()
    local_only: bool = True
    non_dispatching: bool = True
    execution_authorized: bool = False
    provider_call_authorized: bool = False
    external_effect_authorized: bool = False

    def receive_event(
        self,
        *,
        event: AsyncDelegationCompletionEvent,
        registry: AsyncDelegationRegistry,
    ) -> AsyncDelegationInboxReceipt:
        existing = self.get_record(event.event_id)
        if existing is not None:
            duplicate_record = self._duplicate_record_for(existing)
            duplicate_existing = self._find_duplicate_record(duplicate_record.event_id)
            if duplicate_existing is not None:
                return AsyncDelegationInboxReceipt(record=duplicate_existing, inbox=self, registry=registry)
            updated_inbox = replace(self, records=self.records + (duplicate_record,))
            return AsyncDelegationInboxReceipt(record=duplicate_record, inbox=updated_inbox, registry=registry)

        authority_state = registry.get_by_handle_id(event.handle_id)
        if authority_state is None:
            record = self._quarantined_record(
                event=event,
                reason="rejected_unknown_handle",
                rejection_evidence={"reason_code": "rejected_unknown_handle"},
            )
            return AsyncDelegationInboxReceipt(record=record, inbox=replace(self, records=self.records + (record,)), registry=registry)
        if event.completion_status not in ACCEPTED_EVENT_STATUSES:
            record = self._quarantined_record(
                event=event,
                reason="rejected_unsupported_inbox_event_kind",
                rejection_evidence={"reason_code": "rejected_unsupported_inbox_event_kind"},
            )
            return AsyncDelegationInboxReceipt(record=record, inbox=replace(self, records=self.records + (record,)), registry=registry)

        updated_state = _apply_event(authority_state=authority_state, event=event)
        accepted = updated_state.packet.state in {"completed", "failed"} and updated_state.trace_records[-1].decision in {
            "record_completion",
            "record_failure",
        }
        registry_after = registry.replace_state(authority_state, updated_state)
        if accepted:
            record = self._accepted_record(event=event)
            return AsyncDelegationInboxReceipt(
                record=record,
                inbox=replace(self, records=self.records + (record,)),
                registry=registry_after,
            )

        record = self._quarantined_record(
            event=event,
            reason=updated_state.trace_records[-1].reason_code,
            rejection_evidence={
                "reason_code": updated_state.trace_records[-1].reason_code,
                "trace_id": updated_state.trace_records[-1].trace_id,
                "packet_state": updated_state.packet.state,
                "handle_status": None if updated_state.handle is None else updated_state.handle.status,
            },
        )
        return AsyncDelegationInboxReceipt(
            record=record,
            inbox=replace(self, records=self.records + (record,)),
            registry=registry_after,
        )

    def list_records(self) -> tuple[AsyncDelegationInboxRecord, ...]:
        return self.records

    def list_quarantined(self) -> tuple[AsyncDelegationInboxRecord, ...]:
        return tuple(record for record in self.records if record.status == "quarantined")

    def get_record(self, event_id: str) -> AsyncDelegationInboxRecord | None:
        for record in self.records:
            if record.event_id == event_id and record.status != "duplicate":
                return record
        return None

    def _find_duplicate_record(self, event_id: str) -> AsyncDelegationInboxRecord | None:
        for record in self.records:
            if record.event_id == event_id and record.status == "duplicate":
                return record
        return None

    def _accepted_record(self, *, event: AsyncDelegationCompletionEvent) -> AsyncDelegationInboxRecord:
        return AsyncDelegationInboxRecord(
            inbox_record_id=_stable_id("async_inbox_record", event.event_id, "accepted"),
            event_id=event.event_id,
            handle_id=event.handle_id,
            owner_id=event.owner_id,
            robot_id=event.robot_id,
            request_id=_event_request_id(event),
            event_kind=event.completion_status,
            status="accepted",
            reason=event.reason_code,
            bound_completion_event=_serialize_completion_event(event),
            rejection_evidence=None,
            created_at=_created_marker(len(self.records) + 1),
        )

    def _quarantined_record(
        self,
        *,
        event: AsyncDelegationCompletionEvent,
        reason: str,
        rejection_evidence: dict[str, object],
    ) -> AsyncDelegationInboxRecord:
        return AsyncDelegationInboxRecord(
            inbox_record_id=_stable_id("async_inbox_record", event.event_id, "quarantined"),
            event_id=event.event_id,
            handle_id=event.handle_id,
            owner_id=event.owner_id,
            robot_id=event.robot_id,
            request_id=_event_request_id(event),
            event_kind=event.completion_status,
            status="quarantined",
            reason=reason,
            bound_completion_event=None,
            rejection_evidence=rejection_evidence,
            created_at=_created_marker(len(self.records) + 1),
        )

    def _duplicate_record_for(self, record: AsyncDelegationInboxRecord) -> AsyncDelegationInboxRecord:
        return AsyncDelegationInboxRecord(
            inbox_record_id=_stable_id("async_inbox_record", record.event_id, "duplicate"),
            event_id=record.event_id,
            handle_id=record.handle_id,
            owner_id=record.owner_id,
            robot_id=record.robot_id,
            request_id=record.request_id,
            event_kind=record.event_kind,
            status="duplicate",
            reason=f"duplicate_of_{record.status}",
            bound_completion_event=record.bound_completion_event,
            rejection_evidence=record.rejection_evidence,
            created_at=_created_marker(len(self.records) + 1),
        )


def create_async_delegation_registry(*authority_states: AsyncDelegationAuthorityState) -> AsyncDelegationRegistry:
    return AsyncDelegationRegistry(authority_states=tuple(authority_states))


def replay_async_delegation_inbox(
    *,
    events: tuple[AsyncDelegationCompletionEvent, ...],
    clean_registry: AsyncDelegationRegistry,
) -> AsyncDelegationInboxReceipt:
    inbox = AsyncDelegationCompletionInbox()
    registry = clean_registry
    receipt: AsyncDelegationInboxReceipt | None = None
    for event in events:
        receipt = inbox.receive_event(event=event, registry=registry)
        inbox = receipt.inbox
        registry = receipt.registry
    if receipt is None:
        raise ValueError("Replay requires at least one event.")
    return receipt


def _apply_event(
    *,
    authority_state: AsyncDelegationAuthorityState,
    event: AsyncDelegationCompletionEvent,
) -> AsyncDelegationAuthorityState:
    if event.completion_status == "completed":
        return record_async_delegation_completion(authority_state=authority_state, event=event)
    if event.completion_status == "failed":
        return record_async_delegation_failure(authority_state=authority_state, event=event)
    raise ValueError("Inbox only accepts completed or failed async delegation events.")


def _event_request_id(event: AsyncDelegationCompletionEvent) -> str | None:
    request_id = event.cost_preflight_evidence.get("request_id")
    return None if request_id is None else str(request_id)


def _serialize_completion_event(event: AsyncDelegationCompletionEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "handle_id": event.handle_id,
        "delegation_id": event.delegation_id,
        "owner_id": event.owner_id,
        "robot_id": event.robot_id,
        "actor_id": event.actor_id,
        "source_stage": event.source_stage,
        "original_request_evidence": _dict_copy(event.original_request_evidence),
        "cost_preflight_evidence": _dict_copy(event.cost_preflight_evidence),
        "approval_evidence": None if event.approval_evidence is None else _dict_copy(event.approval_evidence),
        "completion_status": event.completion_status,
        "completion_payload_summary": _dict_copy(event.completion_payload_summary),
        "reason_code": event.reason_code,
        "authority_expanded": event.authority_expanded,
        "memory_access_expanded": event.memory_access_expanded,
        "tool_authority_granted": event.tool_authority_granted,
        "provider_call_authorized": event.provider_call_authorized,
        "external_effect_authorized": event.external_effect_authorized,
        "execution_authorized": event.execution_authorized,
        "live_dispatch_authorized": event.live_dispatch_authorized,
    }


def _dict_copy(value: dict[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    copied: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(item, dict):
            copied[key] = _dict_copy(item)
        elif isinstance(item, list):
            copied[key] = list(item)
        elif isinstance(item, tuple):
            copied[key] = list(item)
        else:
            copied[key] = item
    return copied


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}_" + uuid5(NAMESPACE_URL, "|".join("" if part is None else str(part) for part in parts)).hex[:12]


def _created_marker(index: int) -> str:
    return f"inbox_seq_{index:04d}"
