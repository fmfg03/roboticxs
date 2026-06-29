from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.token_usage_cost_meter import build_usage_task_run_record
from app.usage_cost_ledger import (
    USAGE_COST_LEDGER_STAGE,
    UsageCostLedgerEntry,
    build_usage_cost_ledger_entry,
    build_usage_cost_ledger_entry_from_168p_record,
    render_usage_cost_ledger_summary,
    summarize_usage_cost_ledger,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/USAGE_COST_LEDGER_188P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def ledger_entry(**overrides) -> UsageCostLedgerEntry:
    values = {
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "task_id": "prep-188p",
        "command": "/prep",
        "task_class": "meeting_prep",
        "provider": "local_fixture",
        "model": "balanced_standard_v1",
        "model_mode": "balanced",
        "input_tokens": 1200,
        "output_tokens": 360,
        "estimated_cost_usd": 0.001896,
        "latency_ms": 125,
        "status": "completed",
        "created_at": "2026-06-26T12:00:00+00:00",
    }
    values.update(overrides)
    return build_usage_cost_ledger_entry(**values)


def test_188p_builds_local_usage_cost_ledger_entry_without_authority_expansion():
    entry = ledger_entry()

    assert entry.stage == USAGE_COST_LEDGER_STAGE
    assert entry.owner_id == "local-owner"
    assert entry.robot_id == "roboticxs-dev"
    assert entry.task_id == "prep-188p"
    assert entry.command == "/prep"
    assert entry.task_class == "meeting_prep"
    assert entry.provider == "local_fixture"
    assert entry.model == "balanced_standard_v1"
    assert entry.model_mode == "balanced"
    assert entry.input_tokens == 1200
    assert entry.output_tokens == 360
    assert entry.estimated_cost_usd == 0.001896
    assert entry.latency_ms == 125
    assert entry.status == "completed"
    assert entry.local_estimate_only is True
    assert entry.live_billing_checked is False
    assert entry.provider_call_made is False
    assert entry.connector_activation_allowed is False
    assert entry.external_write_allowed is False
    assert entry.persistence_authorized is False


def test_188p_failed_entry_requires_failure_reason_and_rejects_invalid_values():
    failed = ledger_entry(
        task_id="gmail-188p",
        command="/gmail_thread",
        task_class="gmail_context",
        status="failed",
        failure_reason="missing_auth_config",
    )

    assert failed.status == "failed"
    assert failed.failure_reason == "missing_auth_config"
    with pytest.raises(ValueError, match="must include a failure reason"):
        ledger_entry(status="failed", failure_reason=None)
    with pytest.raises(ValueError, match="non-negative"):
        ledger_entry(input_tokens=-1)
    with pytest.raises(ValueError, match="estimated cost must be non-negative"):
        ledger_entry(estimated_cost_usd=-0.01)


def test_188p_ledger_entry_rejects_authority_expansion():
    entry = ledger_entry()

    with pytest.raises(ValueError, match="must not expand billing"):
        UsageCostLedgerEntry(**{**asdict(entry), "provider_call_made": True})
    with pytest.raises(ValueError, match="must remain local estimates"):
        UsageCostLedgerEntry(**{**asdict(entry), "local_estimate_only": False})


def test_188p_builds_ledger_entry_from_168p_usage_record():
    record = build_usage_task_run_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        task_id="doc-168p",
        task_class="document_review",
        provider="local_fixture",
        model="advanced_reasoning_v1",
        model_mode="balanced",
        input_tokens=2000,
        output_tokens=700,
        estimated_cost_usd=0.00621,
        latency_ms=240,
        status="completed",
        created_at="2026-06-26T13:00:00+00:00",
    )

    entry = build_usage_cost_ledger_entry_from_168p_record(command="/document", record=record)

    assert entry.stage == USAGE_COST_LEDGER_STAGE
    assert entry.task_id == "doc-168p"
    assert entry.command == "/document"
    assert entry.task_class == "document_review"
    assert entry.input_tokens == 2000
    assert entry.output_tokens == 700
    assert entry.estimated_cost_usd == 0.00621
    assert entry.source == "168p:local_meter"
    assert entry.provider_call_made is False


def test_188p_summary_filters_owner_robot_month_and_counts_breakdowns():
    entries = (
        ledger_entry(task_id="prep-1", command="/prep", estimated_cost_usd=0.001, created_at="2026-06-01T10:00:00+00:00"),
        ledger_entry(
            task_id="doc-1",
            command="/document",
            task_class="document_review",
            model_mode="premium",
            estimated_cost_usd=0.005,
            input_tokens=2000,
            output_tokens=900,
            created_at="2026-06-02T10:00:00+00:00",
        ),
        ledger_entry(
            task_id="fail-1",
            command="/gmail_thread",
            task_class="gmail_context",
            status="failed",
            failure_reason="missing_access_token",
            estimated_cost_usd=0.0,
            created_at="2026-06-03T10:00:00+00:00",
        ),
        ledger_entry(owner_id="other-owner", task_id="other", estimated_cost_usd=9.99),
        ledger_entry(task_id="old", estimated_cost_usd=9.99, created_at="2026-05-01T10:00:00+00:00"),
    )

    summary = summarize_usage_cost_ledger(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        entries=entries,
        month="2026-06",
    )

    assert summary.total_tasks == 3
    assert summary.total_estimated_cost_usd == 0.006
    assert summary.total_input_tokens == 4400
    assert summary.total_output_tokens == 1620
    assert summary.total_tokens == 6020
    assert summary.most_expensive_task_id == "doc-1"
    assert summary.documents_reviewed == 1
    assert summary.failed_tasks == 1
    assert summary.command_breakdown == (("/document", 1), ("/gmail_thread", 1), ("/prep", 1))
    assert summary.task_class_breakdown == (("document_review", 1), ("gmail_context", 1), ("meeting_prep", 1))
    assert summary.model_mode_breakdown == (("balanced", 2), ("premium", 1))
    assert summary.status_breakdown == (("completed", 2), ("failed", 1))


def test_188p_render_summary_and_empty_state_are_customer_facing_and_boundary_clear():
    summary = summarize_usage_cost_ledger(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        entries=(ledger_entry(),),
        month="2026-06",
    )
    empty = summarize_usage_cost_ledger(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        entries=(),
        month="2026-06",
    )

    rendered = render_usage_cost_ledger_summary(summary)
    empty_rendered = render_usage_cost_ledger_summary(empty)

    assert "Usage & Cost Ledger" in rendered
    assert "Stage: 188P" in rendered
    assert "Tasks run: 1" in rendered
    assert "Estimated cost: $0.001896" in rendered
    assert "Most expensive task: prep-188p ($0.001896)" in rendered
    assert "Commands:" in rendered
    assert "- /prep: 1" in rendered
    assert "Local estimated usage ledger only. Not live billing or provider reconciliation." in rendered
    assert "Live billing: disabled" in rendered
    assert "Provider calls: disabled" in rendered
    assert "Persistence: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "No local usage records yet." in empty_rendered
    assert "Run product flows with injected local ledger entries to see usage here." in empty_rendered


def test_188p_redacts_secret_like_text_fields_before_rendering():
    entry = ledger_entry(
        task_id="token-task-188p",
        command="/usage",
        provider="Bearer secret-token-188p",
        model="client_secret_model",
        failure_reason="access_token secret-token-188p",
        status="failed",
    )
    summary = summarize_usage_cost_ledger(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        entries=(entry,),
        month="2026-06",
    )
    rendered = render_usage_cost_ledger_summary(summary)

    assert entry.task_id == "[redacted]"
    assert entry.provider == "[redacted]"
    assert entry.model == "[redacted]"
    assert entry.failure_reason == "[redacted]"
    assert "secret-token-188p" not in rendered
    assert "Bearer" not in rendered
    assert "client_secret" not in rendered


def test_188p_reference_and_roadmap_close_usage_cost_ledger_without_billing_authority():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "188P is Usage & Cost Ledger v0 only." in reference
    assert "not live billing or provider reconciliation" in reference
    assert "does not authorize provider calls" in reference
    assert '"stage_id":"188P","stage_name":"Usage & Cost Ledger v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "210P and later remain unauthorized" in roadmap
