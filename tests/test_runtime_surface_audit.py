from __future__ import annotations

import inspect
import json
from pathlib import Path
import re

from app.command_registry import REGISTERED_COMMAND_ROUTES
from app.orchestrator import process_telegram_message


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs/reference/RUNTIME_SURFACE_AUDIT_v0_1.md"
INVENTORY_PATTERN = re.compile(
    r"```json runtime-surface-inventory\n(?P<inventory>.+?)\n```",
    re.DOTALL,
)
REQUIRED_FIELDS = {
    "surface_id",
    "route_source",
    "route_name",
    "priority",
    "matcher_kind",
    "commands_or_patterns",
    "handler_or_flow",
    "effect_boundary",
    "evidence",
    "classification",
    "recommendation",
    "test_refs",
}
ALLOWED_EVIDENCE = {"implemented", "tested", "documented", "inferred"}
ALLOWED_CLASSIFICATIONS = {
    "RUNTIME_CONTRACT",
    "FREEZE_CANDIDATE",
    "EXPERIMENTAL",
    "LEGACY_CANDIDATE",
    "INTERNAL_DEV_ONLY",
    "AMBIGUOUS_REVIEW_REQUIRED",
    "BLOCKED",
}
ALLOWED_RECOMMENDATIONS = {
    "preserve",
    "freeze",
    "review_in_63P",
    "candidate_for_deprecation_later",
    "investigate",
}
OUTSIDE_REGISTRY_SURFACE_IDS = {
    "telegram.attachment_intake",
    "memory_proposal.explicit_intent",
    "fallback.general_task",
}
EXPECTED_OUTSIDE_REGISTRY_HANDLERS = {
    "telegram.attachment_intake": "process_file_intake",
    "memory_proposal.explicit_intent": "process_memory_proposal",
    "fallback.general_task": "process_general_task",
}
EXPECTED_REGISTERED_SURFACE_IDS = {
    "action_approval_packet": "approval.action_approval_packet",
    "web_preflight": "web.preflight",
    "capability_catalog": "capability.catalog",
    "capability_query": "capability.query",
    "attention_summary": "attention.summary",
    "robot_folder": "robot_folder.summary",
    "super_familiar": "super_familiar.prepare",
    "usage_spend": "usage.spend",
    "usage_tokens": "usage.tokens",
    "budget_status": "budget.status",
    "budget_policy_reset": "budget.reset",
    "file_listing": "file_control.list_received",
    "pending_file_retrievals": "retrieval_control.pending_attempts",
    "pending_file_retrieval_enablement_requests": "retrieval_control.pending_enablement_requests",
    "file_retrieval_enablement_request_history": "retrieval_control.enablement_request_history",
    "file_retrieval_control_summary": "retrieval_control.summary",
    "file_retrieval_control_report": "retrieval_control.report",
    "file_retrieval_policy_status": "retrieval_control.policy_status",
    "file_retrieval_enablement_request": "retrieval_control.request_enablement",
    "budget_limit_update": "budget.set_limit",
    "budget_warn_threshold_update": "budget.set_warn_threshold",
    "budget_block_threshold_update": "budget.set_block_threshold",
    "file_retrieval_enablement_resolution": "retrieval_control.resolve_enablement_request",
    "file_forget": "file_control.forget",
    "file_retrieval_cancel": "retrieval_control.cancel_attempt",
    "file_retrieval_preflight": "retrieval_control.preflight",
    "document_listing": "document_history.list",
    "document_forget": "document_history.forget",
    "document_review": "document_review.prepare",
    "memory_listing": "memory_control.what_do_you_remember",
    "memory_control_help": "memory_control.help",
    "pending_memory_review": "memory_control.pending_proposals",
    "memory_forget": "memory_control.forget",
    "memory_decision": "memory_control.proposal_decision",
}


def load_inventory() -> list[dict]:
    match = INVENTORY_PATTERN.search(AUDIT_PATH.read_text())
    assert match is not None, "Runtime surface audit must contain its structured inventory."
    return json.loads(match.group("inventory"))


def test_registered_routes_are_audited_once_in_runtime_priority_order():
    registered_surfaces = [
        surface for surface in load_inventory() if surface["route_source"] == "command_registry"
    ]
    runtime_routes = list(REGISTERED_COMMAND_ROUTES)

    assert [surface["route_name"] for surface in registered_surfaces] == [
        route.name for route in runtime_routes
    ]
    assert [surface["priority"] for surface in registered_surfaces] == list(
        range(len(runtime_routes))
    )
    assert [surface["handler_or_flow"] for surface in registered_surfaces] == [
        route.handler.__name__ for route in runtime_routes
    ]


def test_surface_ids_are_unique_and_outside_registry_paths_are_explicit():
    inventory = load_inventory()
    surface_ids = [surface["surface_id"] for surface in inventory]
    registered_surface_ids = {
        surface["route_name"]: surface["surface_id"]
        for surface in inventory
        if surface["route_source"] == "command_registry"
    }

    assert len(surface_ids) == len(set(surface_ids))
    assert registered_surface_ids == EXPECTED_REGISTERED_SURFACE_IDS
    outside_registry = {
        surface["surface_id"]
        for surface in inventory
        if surface["route_source"] == "orchestrator"
    }
    assert outside_registry == OUTSIDE_REGISTRY_SURFACE_IDS
    assert {
        surface["surface_id"]: surface["handler_or_flow"]
        for surface in inventory
        if surface["route_source"] == "orchestrator"
    } == EXPECTED_OUTSIDE_REGISTRY_HANDLERS
    for surface in inventory:
        if surface["surface_id"] in OUTSIDE_REGISTRY_SURFACE_IDS:
            assert surface["route_name"] is None
            assert surface["priority"] is None


def test_outside_registry_handlers_remain_in_documented_orchestrator_order():
    source = inspect.getsource(process_telegram_message)
    handler_positions = [
        source.index(handler)
        for handler in EXPECTED_OUTSIDE_REGISTRY_HANDLERS.values()
    ]

    assert handler_positions == sorted(handler_positions)


def test_every_surface_has_structured_evidence_classification_and_recommendation():
    for surface in load_inventory():
        assert set(surface) == REQUIRED_FIELDS
        assert surface["surface_id"]
        assert surface["matcher_kind"]
        assert surface["commands_or_patterns"]
        assert surface["handler_or_flow"]
        assert surface["effect_boundary"]
        assert set(surface["evidence"]) <= ALLOWED_EVIDENCE
        assert surface["evidence"]
        assert surface["classification"] in ALLOWED_CLASSIFICATIONS
        assert surface["recommendation"] in ALLOWED_RECOMMENDATIONS
        assert surface["test_refs"]


def test_test_references_point_to_existing_test_files():
    for surface in load_inventory():
        for test_ref in surface["test_refs"]:
            path = REPO_ROOT / test_ref
            assert path.is_file(), f"{surface['surface_id']} references missing {test_ref}"
            assert path.name.startswith("test_")


def test_retrieval_control_is_only_recommended_for_stage_63p_review():
    retrieval_surfaces = [
        surface
        for surface in load_inventory()
        if surface["surface_id"].startswith("retrieval_control.")
    ]

    assert retrieval_surfaces
    assert {surface["classification"] for surface in retrieval_surfaces} == {
        "FREEZE_CANDIDATE"
    }
    assert {surface["recommendation"] for surface in retrieval_surfaces} == {
        "review_in_63P"
    }
    assert all(
        "no retrieval" in surface["effect_boundary"].lower()
        or "does not enable retrieval" in surface["effect_boundary"].lower()
        or "retrieval remains disabled" in surface["effect_boundary"].lower()
        or "does not change retrieval policy" in surface["effect_boundary"].lower()
        or "does not retrieve" in surface["effect_boundary"].lower()
        for surface in retrieval_surfaces
    )
