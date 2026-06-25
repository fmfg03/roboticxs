from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.calendar_context_scan import build_calendar_context_scan_record
from app.context_scan_proposed_memory import (
    CONTEXT_SCAN_PROPOSED_MEMORY_STAGE,
    ContextScanProposedMemoryRecord,
    build_context_scan_proposed_memory_record,
    main,
    render_context_scan_proposed_memory_record,
)
from app.gmail_readonly_context_scan import GmailReadonlyConfig, read_gmail_context
from tests.test_calendar_context_scan_137p import calendar_result, event
from tests.test_gmail_readonly_context_scan_163p import FakeGmailReadonlyHttpClient


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "docs/reference/CONTEXT_SCAN_PROPOSED_MEMORY_164P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def calendar_scan():
    return build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(event()),
    )


def gmail_scan():
    return read_gmail_context(
        config=GmailReadonlyConfig(
            access_token="token-164p",
            query="newer_than:30d",
            max_results=5,
            timeout_seconds=30,
        ),
        http_client=FakeGmailReadonlyHttpClient(),
    )


def test_164p_builds_pending_memory_candidates_from_calendar_and_gmail_without_writes():
    record = build_context_scan_proposed_memory_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_scan=calendar_scan(),
        gmail_scan=gmail_scan(),
    )

    assert record.stage == CONTEXT_SCAN_PROPOSED_MEMORY_STAGE
    assert record.status == "completed_with_candidates"
    assert record.source_stages == ("137P", "163P")
    assert len(record.candidates) == 6
    assert {candidate.source_stage for candidate in record.candidates} == {"137P", "163P"}
    assert {candidate.source_type for candidate in record.candidates} == {
        "calendar_context_candidate",
        "gmail_context_signal",
    }
    assert all(candidate.status == "pending_owner_review" for candidate in record.candidates)
    assert all(candidate.treated_as_fact is False for candidate in record.candidates)
    assert all(candidate.approval_command == f"/memory_approve {candidate.candidate_id}" for candidate in record.candidates)
    assert all(candidate.rejection_command == f"/memory_reject {candidate.candidate_id}" for candidate in record.candidates)
    assert all(candidate.edit_command == f"/memory_edit {candidate.candidate_id}" for candidate in record.candidates)
    assert record.read_only is True
    assert record.owner_review_required is True
    assert record.memory_write_allowed is False
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False
    assert record.approval_decision_created is False
    assert record.calendar_write_allowed is False
    assert record.gmail_send_allowed is False
    assert record.gmail_modify_allowed is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False


def test_164p_candidate_ids_are_deterministic_for_same_scan_inputs():
    first = build_context_scan_proposed_memory_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_scan=calendar_scan(),
        gmail_scan=gmail_scan(),
    )
    second = build_context_scan_proposed_memory_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_scan=calendar_scan(),
        gmail_scan=gmail_scan(),
    )

    assert tuple(candidate.candidate_id for candidate in first.candidates) == tuple(
        candidate.candidate_id for candidate in second.candidates
    )


def test_164p_empty_source_scans_create_empty_review_record():
    empty_calendar_scan = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(
            event(
                event_id="evt-focus",
                summary="Focus block",
                description_preview=None,
                attendee_count=0,
                location=None,
            )
        ),
    )

    record = build_context_scan_proposed_memory_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_scan=empty_calendar_scan,
    )

    assert record.status == "empty"
    assert record.candidates == ()
    assert record.memory_center_mutated is False
    assert record.proposed_memory_written is False


def test_164p_missing_sources_are_rejected():
    with pytest.raises(ValueError, match="rejected_missing_context_scan_source"):
        build_context_scan_proposed_memory_record(owner_id="local-owner", robot_id="roboticxs-dev")


def test_164p_render_marks_candidates_as_review_only_not_facts():
    record = build_context_scan_proposed_memory_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_scan=calendar_scan(),
        gmail_scan=gmail_scan(),
    )

    rendered = render_context_scan_proposed_memory_record(record)

    assert "Context-Derived Memory Proposals" in rendered
    assert "Stage: 164P" in rendered
    assert "Owner review required: true" in rendered
    assert "Treated as facts: false" in rendered
    assert "Memory Center mutation: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Approval decisions: disabled in 164P" in rendered
    assert "Gmail send/modify: disabled" in rendered
    assert "pending owner review" in rendered
    assert "does not remember them as facts yet" in rendered
    assert "No memory was written." in rendered


def test_164p_record_rejects_authority_expansion():
    valid = build_context_scan_proposed_memory_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_scan=calendar_scan(),
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        ContextScanProposedMemoryRecord(**{**asdict(valid), "proposed_memory_written": True})


def test_164p_cli_json_output_is_empty_and_safe(capsys):
    exit_code = main(["--json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"stage": "164P"' in captured.out
    assert '"status": "empty"' in captured.out
    assert '"memory_center_mutated": false' in captured.out
    assert '"external_write_allowed": false' in captured.out


def test_164p_reference_and_roadmap_close_context_proposals_without_memory_mutation():
    reference = REFERENCE_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "164P is context-derived proposed memory candidates only." in reference
    assert "does not authorize Memory Center mutation" in reference
    assert "ProposedMemory writes" in reference
    assert '"stage_id":"164P","stage_name":"Context Scan -> Proposed Memories v0","status":"CLOSED_COMMITTED"' in roadmap
    assert "170P and later remain unauthorized" in roadmap
