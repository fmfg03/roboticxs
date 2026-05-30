from __future__ import annotations

from app.token_usage import build_token_usage_event


def test_token_usage_event_builder():
    event = build_token_usage_event(
        user_id="u1",
        robot_id="r1",
        task_id="t1",
        provider="openai",
        model="gpt-4o-mini",
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=0.01,
    )
    assert event["status"] == "estimated"
    assert event["input_tokens"] == 100
    assert event["estimated_cost_usd"] == 0.01
