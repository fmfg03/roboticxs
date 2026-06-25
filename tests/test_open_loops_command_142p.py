from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pytest

from app.calendar_context_scan import build_calendar_context_scan_record
from app.google_calendar_readonly_connector import CalendarEventSnapshot, CalendarReadResult
from app.open_loops_command import (
    OPEN_LOOPS_COMMAND_STAGE,
    OpenLoopsCommandRecord,
    build_open_loops_command_record,
    render_open_loops_command,
    run_open_loops_command,
)
from app.proactive_meeting_suggestion import build_proactive_meeting_suggestion_scan
from app.telegram_memory_center_commands import (
    TelegramMemoryCenterSourceBundle,
    build_memory_center_telegram_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "app/open_loops_command.py"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
REFERENCE_PATH = REPO_ROOT / "docs/reference/OPEN_LOOPS_COMMAND_142P_v0_1.md"


@dataclass(frozen=True, slots=True)
class PendingProposalFixture:
    proposal_id: str = "proposal-loop-1"
    owner_id: str = "local-owner"
    robot_id: str = "roboticxs-dev"
    proposal_type: str = "memory_preference"
    proposed_memory_text: str = "Francisco prefers compact loop reviews."
    confidence: str = "medium"
    review_reason: str = "Explicitly stated in a local planning thread."
    source_stage: str = "142P"
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


def memory_snapshot(pending: tuple[object, ...] = ()):
    return build_memory_center_telegram_snapshot(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=pending,
        ),
    )


def test_142p_builds_read_only_open_loops_from_pending_memory_and_suggestions():
    record = build_open_loops_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(event()),
        memory_snapshot=memory_snapshot(pending=(PendingProposalFixture(),)),
    )

    assert record.stage == OPEN_LOOPS_COMMAND_STAGE
    assert record.status == "completed_with_open_loops"
    assert record.calendar_status == "completed"
    assert record.memory_status == "pending"
    assert record.suggestion_status == "completed"
    assert any("pending review; not treated as fact" in line for line in record.pending_memory_lines)
    assert any("/brief" in line for line in record.meeting_suggestion_lines)
    assert record.read_only is True
    assert record.calendar_write_allowed is False
    assert record.memory_write_allowed is False
    assert record.proposed_memory_written is False
    assert record.followup_intent_created is False
    assert record.reminder_scheduled is False
    assert record.model_call_allowed is False
    assert record.tool_call_allowed is False
    assert record.worker_dispatch_allowed is False
    assert record.external_write_allowed is False
    assert record.proactive_send_allowed is False


def test_142p_fails_closed_for_unavailable_calendar_but_keeps_pending_memory_visible():
    record = build_open_loops_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(ok=False, error_code="missing_access_token"),
        memory_snapshot=memory_snapshot(pending=(PendingProposalFixture(),)),
    )

    assert record.status == "partial_calendar_unavailable"
    assert record.calendar_status == "blocked_calendar_unavailable"
    assert "Read-only Calendar context unavailable: missing_access_token." in record.calendar_lines
    assert any("pending review; not treated as fact" in line for line in record.pending_memory_lines)
    assert record.meeting_suggestion_lines == ("No meeting suggestion loop was generated because Calendar failed closed.",)


def test_142p_empty_state_when_no_local_loops_exist():
    record = build_open_loops_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(),
        memory_snapshot=memory_snapshot(),
    )

    assert record.status == "empty"
    assert record.pending_memory_lines == ("No pending memory proposals are visible in this local snapshot.",)
    assert record.meeting_suggestion_lines == ("No owner-requestable meeting brief suggestion loops are available right now.",)
    assert "No unresolved local loops were found." in record.next_steps


def test_142p_run_open_loops_uses_injected_sources_without_writes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN", "token-142p")
    calendar_client = FakeCalendarHttpClient()

    record = run_open_loops_command(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        calendar_http_client=calendar_client,
        memory_source_bundle=TelegramMemoryCenterSourceBundle(
            pending_memory_proposals=(PendingProposalFixture(),),
        ),
    )

    assert len(calendar_client.calls) == 1
    assert record.status == "completed_with_open_loops"
    assert record.external_write_allowed is False
    assert record.memory_write_allowed is False
    assert record.proposed_memory_written is False
    assert record.followup_intent_created is False


def test_142p_render_names_open_loop_sections_and_disabled_authority():
    record = build_open_loops_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(event()),
        memory_snapshot=memory_snapshot(pending=(PendingProposalFixture(),)),
    )

    rendered = render_open_loops_command(record)

    assert "Open Loops" in rendered
    assert "Stage: 142P" in rendered
    assert "Pending memory proposals:" in rendered
    assert "Meeting suggestions:" in rendered
    assert "Calendar:" in rendered
    assert "Suggested next steps:" in rendered
    assert "pending review; not treated as fact" in rendered
    assert "Calendar writes: disabled" in rendered
    assert "Memory writes: disabled" in rendered
    assert "ProposedMemory writes: disabled" in rendered
    assert "Follow-up intents: disabled" in rendered
    assert "Reminders/scheduler: disabled" in rendered
    assert "LLM/model calls: disabled" in rendered
    assert "Tools/workers: disabled" in rendered
    assert "External writes: disabled" in rendered
    assert "Proactive outbound: disabled" in rendered
    assert "No external action was taken." in rendered


def test_142p_rejects_authority_expansion():
    record = build_open_loops_command_record(
        owner_id="local-owner",
        robot_id="roboticxs-dev",
        suggestion_scan=suggestion_scan(event()),
        memory_snapshot=memory_snapshot(),
    )

    with pytest.raises(ValueError, match="must not expand authority"):
        OpenLoopsCommandRecord(**{**asdict(record), "followup_intent_created": True})


def test_142p_rejects_source_owner_robot_mismatch():
    scan = suggestion_scan(event())

    with pytest.raises(ValueError, match="rejected_open_loops_suggestion_owner_robot_mismatch"):
        build_open_loops_command_record(
            owner_id="different-owner",
            robot_id="roboticxs-dev",
            suggestion_scan=scan,
            memory_snapshot=memory_snapshot(),
        )


def test_142p_module_and_reference_preserve_scope_boundaries():
    module_text = MODULE_PATH.read_text()
    reference_text = REFERENCE_PATH.read_text()
    roadmap_text = ROADMAP_PATH.read_text()

    assert "run_proactive_meeting_suggestion_scan" in module_text
    assert "build_memory_center_telegram_snapshot" in module_text
    assert "followup_intent_created: bool" in module_text
    assert "reminder_scheduled: bool" in module_text
    assert "task database or persistence" in reference_text
    assert "`143P+` remains unauthorized" in reference_text
    assert '"stage_id":"142P","stage_name":"Open Loops Command v0","status":"CLOSED_COMMITTED"' in roadmap_text
