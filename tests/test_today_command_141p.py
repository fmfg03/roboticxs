from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pytest

from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.memory_center_projection import MemoryCenterItem
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)
from app.today_command import (
    TODAY_COMMAND_STAGE,
    TodayCommandRecord,
    build_today_command_record,
    render_today_command,
    run_today_command,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/today_command.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
REFERENCE_PATH = REPO_ROOT / "docs/reference/TODAY_COMMAND_141P_v0_1.md"


@dataclass(frozen=True, slots=True)
class PendingProposalFixture:
    proposal_id: str = "proposal-today-1"
    owner_id: str = "local-owner"
    robot_id: str = "roboticxs-dev"
    proposal_type: str = "memory_preference"
    proposed_memory_text: str = "Francisco prefers morning meeting prep."
    confidence: str = "medium"
    review_reason: str = "Explicitly stated in a local planning thread."
    source_stage: str = "141P"
    status: str = "pending_user_review"


class FakeCalendarHttpClient:
    def __init__(self, payload: dict | None = None) -> None:
        self.payload = payload or {
            "items": [
                {
                    "id": "evt-client-demo",
                    "summary": "Client demo prep meeting",
                    "start": {"dateTime": "2026-06-25T10:00:00-06:00"},
                    "end": {"dateTime": "2026-06-25T10:30:00-06:00"},
                    "location": "Google Meet",
                    "description": "Review proposal context and prepare open questions.",
                    "organizer": {"email": "owner@example.com"},
                    "attendees": [{"email": "client@example.com"}],
                    "htmlLink": "https://calendar.google.com/event?eid=1",
                }
            ]
        }
        self.calls: list[dict[str, object]] = []

    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str],
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.payload


def event(**overrides) -> CalendarEventSnapshot:
    values = {
        "event_id": "evt-client-demo",
        "summary": "Client demo prep meeting",
        "start": "2026-06-25T10:00:00-06:00",
        "end": "2026-06-25T10:30:00-06:00",
        "all_day": False,
        "location": "Google Meet",
        "description_preview": "Review proposal context and prepare open questions.",
        "organizer_email": "owner@example.com",
        "attendee_count": 3,
        "html_link": "https://calendar.google.com/event?eid=1",
        "source": "google_calendar_readonly",
    }
    values.update(overrides)
    return CalendarEventSnapshot(**values)


def calendar_result(*events: CalendarEventSnapshot, ok: bool = True, error_code: str | None = None) -> CalendarReadResult:
    return CalendarReadResult(
        ok=ok,
        calendar_id="primary",
        window_start="2026-06-24T10:00:00-06:00",
        window_end="2026-07-01T10:00:00-06:00",
        events=events,
        read_only=True,
        external_writes=False,
        memory_mutation=False,
        error_code=error_code,
        error_message=error_code,
    )


def suggestion_scan(*events: CalendarEventSnapshot, ok: bool = True, error_code: str | None = None):
    context_scan = build_calendar_context_scan_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_result=calendar_result(*events, ok=ok, error_code=error_code),
    )
    return build_proactive_meeting_suggestion_scan(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        context_scan=context_scan,
    )


def active_memory(**overrides) -> MemoryCenterItem:
    values = {
        "item_id": "mem-today-1",
        "owner_id": "local-owner",
        "robot_id": "roboticxs-dev",
        "memory_kind": "preference",
        "status": "active",
        "scopes": ("telegram", "general"),
        "sensitivity": "ordinary",
        "allowed_uses": ("telegram_context",),
        "skill_ids": (),
        "content": "Francisco likes compact daily briefings.",
        "bounded_summary": "Francisco likes compact daily briefings.",
        "source": "local_fixture",
    }
    values.update(overrides)
    return MemoryCenterItem(**values)


def memory_snapshot(*items: MemoryCenterItem, pending: tuple[object, ...] = ()):
    return build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=items,
            pending_memory_proposals=pending,
        ),
    )


def test_141p_builds_read_only_today_record_from_calendar_suggestions_and_memory():
    record = build_today_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(event()),
        memory_snapshot=memory_snapshot(active_memory(), pending=(PendingProposalFixture(),)),
    )

    assert record.stage == TODAY_COMMAND_STAGE
    assert record.status == "completed"
    assert record.calendar_status == "completed"
    assert record.memory_status == "visible"
    assert record.suggestion_status == "completed"
    assert any("Client demo prep meeting" in line for line in record.calendar_lines)
    assert any("/brief" in line for line in record.suggestion_lines)
    assert "Approved visible memories: 1" in record.memory_lines
    assert "Pending memory proposals: 1" in record.memory_lines
    assert record.read_only is True
    assert record.calendar_write_allowed is False
    assert record.memory_write_allowed is False
    assert record.proposed_memory_written is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert record.proactive_send_allowed is False


def test_141p_fails_closed_for_unavailable_calendar_but_keeps_memory_visible():
    record = build_today_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(ok=False, error_code="missing_access_token"),
        memory_snapshot=memory_snapshot(active_memory()),
    )

    assert record.status == "partial_calendar_unavailable"
    assert record.calendar_status == "blocked_calendar_unavailable"
    assert "Read-only Calendar context unavailable: missing_access_token." in record.calendar_lines
    assert "Approved visible memories: 1" in record.memory_lines
    assert record.suggestion_lines == ("No meeting brief suggestions were generated because Calendar failed closed.",)


def test_141p_run_today_command_uses_injected_sources_without_writes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-141p")
    calendar_client = FakeCalendarHttpClient()

    record = run_today_command(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            approved_memory_items=(active_memory(),),
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert len(calendar_client.calls) == 1
    assert record.status == "completed"
    assert record.external_write_allowed is False
    assert record.memory_write_allowed is False
    assert record.proposed_memory_written is False
    assert record.proactive_send_allowed is False


def test_141p_render_names_today_sections_and_disabled_authority():
    record = build_today_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(event()),
        memory_snapshot=memory_snapshot(active_memory()),
    )

    rendered = render_today_command(record)

    assert "Today" in rendered
    assert "Stage: 141P" not in rendered
    assert "Meetings:" in rendered
    assert "Open loops:" in rendered
    assert "Things waiting for you:" in rendered
    assert "Brief options:" in rendered
    assert "Known memory:" in rendered
    assert "Suggested next action:" in rendered
    assert "Blocked / unavailable sources:" in rendered
    assert "Boundaries:" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Memory writes: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Model calls: disabled" in rendered
    assert "Tools: disabled" in rendered
    assert "Worker dispatch: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Proactive outbound: disabled" in rendered
    assert "No external action was taken." in rendered


def test_141p_rejects_authority_expansion():
    record = build_today_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(event()),
        memory_snapshot=memory_snapshot(),
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        TodayCommandRecord(**{**asdict(record), "model_call_allowed": True})


def test_141p_rejects_source_owner_robot_mismatch():
    scan = suggestion_scan(event())

    with pytest.raises(ValueError, match="rejected_today_suggestion_owner_robot_mismatch"):
        build_today_command_record(
            owner_id="different-owner",
            robot_id="roboticxs-dev",
            suggestion_scan=scan,
            memory_snapshot=memory_snapshot(),
        )


def test_141p_module_and_reference_preserve_scope_boundaries():
    module_text = MODULE_PATH.read_text()
    reference_text = REFERENCE_PATH.read_text()
    roadmap_text = ROADMAP_PATH.read_text()

    assert "run_proactive_meeting_suggestion_scan" in module_text
    assert "build_memory_center_telegram_snapshot" in module_text
    assert "proposed_memory_written: bool" in module_text
    assert "proactive_send_allowed: bool" in module_text
    assert "scheduler, cron, reminders" in reference_text
    assert "`143P+` remains unauthorized" in reference_text
    assert '"stage_id":"141P","stage_name":"Today Command v0","status":"CLOSED_COMMITTED"' in roadmap_text
