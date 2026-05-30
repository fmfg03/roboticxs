from __future__ import annotations

import json

from app.config import Settings
from app.model_catalog import MODEL_CATALOG, ModelCatalogEntry


def classify_task(text: str, scope_decision: str, task_family: str = "GENERAL_TASK") -> str:
    family_mapping = {
        "MEMORY_PROPOSAL": "EXTRACTION",
        "MEMORY_DECISION": "SIMPLE_CLASSIFICATION",
        "MEMORY_CONTROL": "SIMPLE_CLASSIFICATION",
        "DOCUMENT_CONTROL": "SIMPLE_CLASSIFICATION",
        "FILE_INTAKE": "EXTRACTION",
        "FILE_CONTROL": "SIMPLE_CLASSIFICATION",
        "FILE_RETRIEVAL_PREFLIGHT": "SIMPLE_CLASSIFICATION",
        "FILE_RETRIEVAL_CONTROL": "SIMPLE_CLASSIFICATION",
        "USAGE_REPORT": "SIMPLE_CLASSIFICATION",
        "BUDGET_CONTROL": "SIMPLE_CLASSIFICATION",
    }
    if task_family in family_mapping:
        return family_mapping[task_family]

    normalized = text.lower()
    if scope_decision == "REFUSE_SCOPE":
        return "SENSITIVE_REVIEW"
    if any(term in normalized for term in ["tool", "steps", "plan the process"]):
        return "TOOL_PLANNING"
    if any(term in normalized for term in ["summary", "summarize", "extract", "list", "field"]):
        return "EXTRACTION"
    if any(term in normalized for term in ["draft", "write", "reply"]):
        return "DRAFTING"
    if len(normalized) > 1500:
        return "LONG_CONTEXT"
    return "REASONING"


def estimate_route(
    *,
    text: str,
    task_id: str,
    task_family: str,
    task_class: str,
    settings: Settings,
) -> dict[str, str | int | float]:
    estimated_input_tokens = max(1, len(text) // 4)
    estimated_output_tokens = max(32, min(256, estimated_input_tokens // 2))
    context_size_class = classify_context_size(estimated_input_tokens)
    sensitivity_level = classify_sensitivity_level(task_class)
    selected_mode = select_routing_mode(
        task_family=task_family,
        task_class=task_class,
        context_size_class=context_size_class,
        default_mode=settings.default_routing_mode,
    )
    catalog_entry = select_catalog_entry(task_class=task_class, selected_mode=selected_mode)
    estimated_cost_usd = estimate_cost(
        entry=catalog_entry,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
    )
    budget_policy_result = evaluate_budget_policy(
        estimated_cost_usd=estimated_cost_usd,
        selected_mode=selected_mode,
        context_size_class=context_size_class,
    )
    reason_metadata = {
        "budget_policy_result": budget_policy_result,
        "context_size_class": context_size_class,
        "estimated_cost_basis": "local_catalog_stub",
        "requires_sensitive_boundary": sensitivity_level in {"medium", "high"},
        "requires_tool_execution": task_class == "TOOL_PLANNING",
        "selected_mode": selected_mode,
        "selected_model": catalog_entry.model,
        "selected_provider": catalog_entry.provider,
        "sensitivity_level": sensitivity_level,
        "task_class": task_class,
        "task_family": task_family,
    }
    return {
        "task_id": task_id,
        "task_class": task_class,
        "provider": catalog_entry.provider,
        "model": catalog_entry.model,
        "routing_mode": catalog_entry.routing_mode,
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "estimated_cost_usd": estimated_cost_usd,
        "reason": json.dumps(reason_metadata, sort_keys=True),
    }


def classify_context_size(estimated_input_tokens: int) -> str:
    if estimated_input_tokens >= 4000:
        return "long"
    if estimated_input_tokens >= 1000:
        return "medium"
    return "short"


def classify_sensitivity_level(task_class: str) -> str:
    if task_class == "SENSITIVE_REVIEW":
        return "high"
    if task_class in {"REASONING", "TOOL_PLANNING", "LONG_CONTEXT"}:
        return "medium"
    return "low"


def select_routing_mode(*, task_family: str, task_class: str, context_size_class: str, default_mode: str) -> str:
    if task_class == "SENSITIVE_REVIEW":
        return "premium"
    if task_class in {"REASONING", "TOOL_PLANNING"}:
        return "balanced" if default_mode == "economy" else default_mode
    if task_class == "LONG_CONTEXT":
        return "balanced"
    if task_family in {"FILE_CONTROL", "FILE_RETRIEVAL_PREFLIGHT", "FILE_RETRIEVAL_CONTROL", "DOCUMENT_CONTROL", "MEMORY_CONTROL", "MEMORY_DECISION", "USAGE_REPORT", "BUDGET_CONTROL"}:
        return "economy"
    return default_mode


def select_catalog_entry(*, task_class: str, selected_mode: str) -> ModelCatalogEntry:
    for entry in MODEL_CATALOG:
        if entry.routing_mode == selected_mode and task_class in entry.supported_task_classes:
            return entry
    for entry in MODEL_CATALOG:
        if task_class in entry.supported_task_classes:
            return entry
    return MODEL_CATALOG[1]


def estimate_cost(*, entry: ModelCatalogEntry, estimated_input_tokens: int, estimated_output_tokens: int) -> float:
    input_cost = (estimated_input_tokens / 1_000_000) * entry.input_cost_per_million_tokens_usd
    output_cost = (estimated_output_tokens / 1_000_000) * entry.output_cost_per_million_tokens_usd
    return round(input_cost + output_cost, 6)


def evaluate_budget_policy(*, estimated_cost_usd: float, selected_mode: str, context_size_class: str) -> str:
    if estimated_cost_usd >= 1.0:
        return "BLOCK"
    if estimated_cost_usd >= 0.05 or selected_mode == "premium" or context_size_class == "long":
        return "WARN"
    return "ALLOW"
