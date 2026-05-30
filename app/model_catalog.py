from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelCatalogEntry:
    tier: str
    provider: str
    model: str
    routing_mode: str
    supported_task_classes: tuple[str, ...]
    input_cost_per_million_tokens_usd: float
    output_cost_per_million_tokens_usd: float
    context_capacity_label: str


MODEL_CATALOG: tuple[ModelCatalogEntry, ...] = (
    ModelCatalogEntry(
        tier="economy",
        provider="stub-openai",
        model="gpt-economy-stub",
        routing_mode="economy",
        supported_task_classes=("SIMPLE_CLASSIFICATION", "EXTRACTION"),
        input_cost_per_million_tokens_usd=0.15,
        output_cost_per_million_tokens_usd=0.60,
        context_capacity_label="short",
    ),
    ModelCatalogEntry(
        tier="balanced",
        provider="stub-openai",
        model="gpt-balanced-stub",
        routing_mode="balanced",
        supported_task_classes=("DRAFTING", "REASONING", "TOOL_PLANNING", "EXTRACTION", "LONG_CONTEXT"),
        input_cost_per_million_tokens_usd=0.80,
        output_cost_per_million_tokens_usd=3.20,
        context_capacity_label="medium",
    ),
    ModelCatalogEntry(
        tier="premium",
        provider="stub-anthropic",
        model="claude-premium-stub",
        routing_mode="premium",
        supported_task_classes=("SENSITIVE_REVIEW", "REASONING", "LONG_CONTEXT", "TOOL_PLANNING", "DRAFTING"),
        input_cost_per_million_tokens_usd=3.00,
        output_cost_per_million_tokens_usd=15.00,
        context_capacity_label="long",
    ),
)
