from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.cost_governor import build_task_cost_request, default_budget_policy, evaluate_cost_preflight
from app.token_usage_cost_meter import (
    TOKEN_USAGE_COST_METER_STAGE,
    UsageTaskRunRecord,
    build_usage_task_run_record,
    build_usage_task_run_record_from_cost_preflight,
    is_usage_cost_meter_command,
    render_usage_cost_summary,
    summarize_usage_costs,
)
from app.usage_reporting import is_token_usage_command


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/TOKEN_USAGE_COST_METER_168P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def test_168p_builds_local_estimated_usage_task_run_record_without_provider_or_billing_authority():
    record = build_usage_task_run_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        task_id="task-168p",
        task_class="meeting_prep",
        provider="local_fixture",
        model="balanced_standard_v1",
        model_mode="balanced",
        input_tokens=1200,
        output_tokens=360,
        estimated_cost_usd=0.001896,
        latency_ms=125,
        created_at="2026-06-26T12:00:00+00:00",
    )

    assert record.stage == TOKEN_USAGE_COST_METER_STAGE
    assert record.status == "estimated"
    assert record.input_tokens == 1200
    assert record.output_tokens == 360
    assert record.estimated_cost_usd == 0.001896
    assert record.latency_ms == 125
    assert record.local_estimate_only is True
    assert record.live_billing_checked is False
    assert record.provider_call_made is False
    assert record.connector_activation_allowed is False
    assert record.external_write_allowed is False
    assert record.persistence_authorized is False
    assert record.billing_reconciliation_authorized is False


def test_168p_derives_usage_record_from_existing_cost_preflight_result():
    request = build_task_cost_request(
        request_id="prep-168p",
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        text="prepare meeting notes in balanced mode",
    )
    result = evaluate_cost_preflight(
        request=request,
        budget_policy=default_budget_policy(owner_id="local-owner", robot_id="roboticxs-dev"),
    )

    record = build_usage_task_run_record_from_cost_preflight(
        request=request,
        result=result,
        latency_ms=88,
        created_at="2026-06-26T12:01:00+00:00",
    )

    assert record.task_id == "prep-168p"
    assert record.task_class == request.task_class
    assert record.input_tokens == result.token_estimate.estimated_input_tokens
    assert record.output_tokens == result.token_estimate.estimated_output_tokens
    assert record.estimated_cost_usd == round(result.estimated_cost_usd, 6)
    assert record.provider == result.route_decision.selected_provider_id
    assert record.model == result.route_decision.selected_model_id
    assert record.provider_call_made is False


def test_168p_summarizes_monthly_usage_by_owner_robot_and_month():
    records = (
        build_usage_task_run_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            task_id="today-1",
            task_class="daily_brief",
            provider="local_fixture",
            model="economy_basic_v1",
            model_mode="economy",
            input_tokens=200,
            output_tokens=80,
            estimated_cost_usd=0.000164,
            created_at="2026-06-01T10:00:00+00:00",
        ),
        build_usage_task_run_record(
            owner_id="local-owner",
            robot_id="roboticxs-dev",
            task_id="doc-1",
            task_class="document_review",
            provider="local_fixture",
            model="advanced_reasoning_v1",
            model_mode="balanced",
            input_tokens=1600,
            output_tokens=500,
            estimated_cost_usd=0.00507,
            created_at="2026-06-02T10:00:00+00:00",
        ),
        build_usage_task_run_record(
            owner_id="other-owner",
            robot_id="roboticxs-dev",
            task_id="other-1",
            task_class="daily_brief",
            provider="local_fixture",
            model="economy_basic_v1",
            model_mode="economy",
            input_tokens=999,
            output_tokens=999,
            estimated_cost_usd=9.99,
            created_at="2026-06-02T10:00:00+00:00",
        ),
    )

    summary = summarize_usage_costs(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        records=records,
        month="2026-06",
    )

    assert summary.total_tasks == 2
    assert summary.total_input_tokens == 1800
    assert summary.total_output_tokens == 580
    assert summary.total_tokens == 2380
    assert summary.total_estimated_cost_usd == 0.005234
    assert summary.most_expensive_task_id == "doc-1"
    assert summary.documents_reviewed == 1
    assert summary.model_mode_breakdown == (("balanced", 1), ("economy", 1))
    assert summary.task_class_breakdown == (("daily_brief", 1), ("document_review", 1))
    assert summary.live_billing_checked is False


def test_168p_render_usage_summary_is_customer_facing_and_boundary_clear():
    summary = summarize_usage_costs(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        records=(
            build_usage_task_run_record(
                owner_id="local-owner",
                robot_id="roboticxs-dev",
                task_id="prep-1",
                task_class="meeting_prep",
                provider="local_fixture",
                model="balanced_standard_v1",
                model_mode="balanced",
                input_tokens=100,
                output_tokens=50,
                estimated_cost_usd=0.00019,
                created_at="2026-06-03T10:00:00+00:00",
            ),
        ),
        month="2026-06",
    )

    rendered = render_usage_cost_summary(summary)

    assert "Usage this month" in rendered
    assert "Stage: 168P" in rendered
    assert "Tasks run: 1" in rendered
    assert "Estimated cost: $0.000190" in rendered
    assert "Most expensive task: prep-1 ($0.000190)" in rendered
    assert "Model mode:" in rendered
    assert "- balanced: 1" in rendered
    assert "Local estimated usage only. Not live billing or provider reconciliation." in rendered
    assert "Live billing: disabled" in rendered
    assert "Provider calls: disabled" in rendered
    assert "External writes: disabled" in rendered


def test_168p_usage_alias_maps_to_existing_token_usage_command():
    assert is_usage_cost_meter_command("/usage") is True
    assert is_usage_cost_meter_command("show usage") is True
    assert is_token_usage_command("/usage") is True


def test_168p_records_reject_authority_expansion_and_invalid_failures():
    valid = build_usage_task_run_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        task_id="task-168p",
        task_class="meeting_prep",
        provider="local_fixture",
        model="balanced_standard_v1",
        model_mode="balanced",
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=0.00019,
    )

    with pytest.raises(ValueError, match="must not expand billing"):
        UsageTaskRunRecord(**{**asdict(valid), "provider_call_made": True})

    with pytest.raises(ValueError, match="must include a failure reason"):
        UsageTaskRunRecord(**{**asdict(valid), "status": "failed", "failure_reason": None})


def test_168p_reference_and_roadmap_close_usage_meter_without_billing_authority():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "168P is Token Usage + Cost Meter v0 only." in reference
    assert "not live billing or provider reconciliation" in reference
    assert "does not authorize provider calls" in reference
    assert '"stage_id":"168P","stage_name":"Token Usage + Cost Meter v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "227P and later remain unauthorized" in roadmap
