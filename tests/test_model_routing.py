from __future__ import annotations

import json

from app.config import Settings
from app.model_catalog import MODEL_CATALOG
from app.model_router import classify_task, estimate_route


def settings() -> Settings:
    return Settings(database_url="sqlite:////tmp/test.db", default_provider="openai", default_model="stub", default_routing_mode="economy")


def test_general_task_route_classification_is_explicit():
    task_class = classify_task("Help me prepare for my meeting tomorrow", "ANSWER", "GENERAL_TASK")
    route = estimate_route(
        text="Help me prepare for my meeting tomorrow",
        task_id="t1",
        task_family="GENERAL_TASK",
        task_class=task_class,
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert route["task_class"] == "REASONING"
    assert reason["task_family"] == "GENERAL_TASK"
    assert reason["task_class"] == "REASONING"


def test_memory_proposal_route_classification_is_explicit():
    route = estimate_route(
        text="remember that I prefer short direct answers",
        task_id="t2",
        task_family="MEMORY_PROPOSAL",
        task_class="EXTRACTION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert route["task_class"] == "EXTRACTION"
    assert reason["task_family"] == "MEMORY_PROPOSAL"


def test_memory_decision_route_classification_is_explicit():
    route = estimate_route(
        text="APPROVE",
        task_id="t3",
        task_family="MEMORY_DECISION",
        task_class="SIMPLE_CLASSIFICATION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert route["task_class"] == "SIMPLE_CLASSIFICATION"
    assert reason["task_family"] == "MEMORY_DECISION"


def test_memory_control_route_classification_is_explicit():
    route = estimate_route(
        text="what do you remember",
        task_id="t4",
        task_family="MEMORY_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert reason["task_family"] == "MEMORY_CONTROL"
    assert route["routing_mode"] == "economy"


def test_document_review_route_classification_is_explicit():
    route = estimate_route(
        text="review document: contract requires signatures and penalties",
        task_id="t5",
        task_family="DOCUMENT_REVIEW",
        task_class="SENSITIVE_REVIEW",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert reason["task_family"] == "DOCUMENT_REVIEW"
    assert route["routing_mode"] == "premium"
    assert reason["budget_policy_result"] in {"WARN", "ALLOW"}


def test_document_control_route_classification_is_explicit():
    route = estimate_route(
        text="what documents did you review",
        task_id="t6",
        task_family="DOCUMENT_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert reason["task_family"] == "DOCUMENT_CONTROL"


def test_file_intake_route_classification_is_explicit():
    route = estimate_route(
        text="telegram_document_metadata: nda.pdf (application/pdf, 48291 bytes)",
        task_id="t7",
        task_family="FILE_INTAKE",
        task_class="EXTRACTION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert reason["task_family"] == "FILE_INTAKE"
    assert route["provider"] == "stub-openai"


def test_file_control_route_classification_is_explicit():
    route = estimate_route(
        text="what files did you receive",
        task_id="t8",
        task_family="FILE_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert reason["task_family"] == "FILE_CONTROL"


def test_file_retrieval_preflight_route_classification_is_explicit():
    route = estimate_route(
        text="retrieve file 123e4567-e89b-12d3-a456-426614174000",
        task_id="t8b",
        task_family="FILE_RETRIEVAL_PREFLIGHT",
        task_class="SIMPLE_CLASSIFICATION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert reason["task_family"] == "FILE_RETRIEVAL_PREFLIGHT"
    assert route["routing_mode"] == "economy"


def test_file_retrieval_control_route_classification_is_explicit():
    route = estimate_route(
        text="what file retrievals are pending",
        task_id="t8c",
        task_family="FILE_RETRIEVAL_CONTROL",
        task_class="SIMPLE_CLASSIFICATION",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert reason["task_family"] == "FILE_RETRIEVAL_CONTROL"
    assert route["routing_mode"] == "economy"


def test_route_reason_metadata_is_structured_json():
    route = estimate_route(
        text="review document: tell me if this contract is legally enforceable",
        task_id="t9",
        task_family="DOCUMENT_REVIEW",
        task_class="SENSITIVE_REVIEW",
        settings=settings(),
    )
    reason = json.loads(route["reason"])
    assert sorted(reason.keys()) == sorted(
        [
            "budget_policy_result",
            "context_size_class",
            "estimated_cost_basis",
            "requires_sensitive_boundary",
            "requires_tool_execution",
            "selected_mode",
            "selected_model",
            "selected_provider",
            "sensitivity_level",
            "task_class",
            "task_family",
        ]
    )


def test_cost_estimate_is_deterministic_and_local():
    route = estimate_route(
        text="summarize document: short memo",
        task_id="t10",
        task_family="DOCUMENT_REVIEW",
        task_class="EXTRACTION",
        settings=settings(),
    )
    assert route["estimated_cost_usd"] > 0
    assert route["estimated_cost_usd"] < 0.01


def test_local_model_catalog_has_expected_tiers():
    tiers = {entry.tier for entry in MODEL_CATALOG}
    assert tiers == {"economy", "balanced", "premium"}
