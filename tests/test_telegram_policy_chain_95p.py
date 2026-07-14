from __future__ import annotations

from pathlib import Path

import pytest

from app.models import MemoryItem, Robot, User
from app.telegram_policy_chain import (
    POLICY_CHAIN_WEBHOOK_PATH,
    run_telegram_policy_chain,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = REPO_ROOT / "app/telegram_policy_chain.py"
DOC_PATH = REPO_ROOT / "docs/reference/TELEGRAM_HERMES_POLICY_CHAIN_RUNTIME_SKELETON_95P_v0_1.md"
ROADMAP_PATH = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"


def build_update(text: str, user_id: int = 123456, chat_id: int = 123456) -> dict:
    return {
        "update_id": 95001,
        "message": {
            "message_id": 950,
            "date": 1710000000,
            "chat": {"id": chat_id, "type": "private"},
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Francisco",
                "username": "francisco",
            },
            "text": text,
        },
    }


@pytest.mark.anyio
async def test_policy_chain_webhook_runs_safe_text_through_all_policies_and_adapter(client):
    response = await client.post(POLICY_CHAIN_WEBHOOK_PATH, json=build_update("Draft a short meeting summary"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["stage"] == "95P"
    assert body["owner_id"] is not None
    assert body["robot_id"] is not None
    assert [step["policy"] for step in body["policy_trace"]] == [
        "command_surface_policy_90p",
        "skill_scope_policy_91p",
        "tool_authority_policy_92p",
    ]
    assert body["command_policy"]["decision"] == "PRODUCT_INTENT"
    assert body["skill_scope_policy"]["decision"] == "ANSWER"
    assert body["tool_authority_policy"]["decision"] == "ALLOW"
    assert body["memory_context"]["source_of_truth"] == "Roboticxs Memory Center"
    assert body["memory_context"]["tool_action_authorization"] is False
    assert body["hermes_adapter"]["called"] is True
    assert body["hermes_adapter"]["status"] == "local_stub_ok"
    assert body["local_response"] == {
        "network_call": False,
        "telegram_send": False,
        "live_hermes_gateway_started": False,
        "external_side_effect": False,
        "hermes_adapter_called": True,
        "action_packet_required": False,
    }


@pytest.mark.anyio
async def test_raw_hermes_operator_command_is_blocked_before_adapter(client):
    response = await client.post(POLICY_CHAIN_WEBHOOK_PATH, json=build_update("/gateway start"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error_code"] == "command_policy_blocked"
    assert body["command_policy"]["decision"] == "BLOCK_CONSUMER"
    assert body["skill_scope_policy"]["decision"] == "SKIPPED"
    assert body["tool_authority_policy"]["decision"] == "SKIPPED"
    assert body["hermes_adapter"]["called"] is False
    assert body["local_response"]["network_call"] is False
    assert body["local_response"]["live_hermes_gateway_started"] is False


@pytest.mark.anyio
async def test_external_send_request_produces_action_packet_and_stops_before_adapter(client):
    response = await client.post(
        POLICY_CHAIN_WEBHOOK_PATH,
        json=build_update("Send email to Ana with the final summary"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error_code"] == "action_packet_required"
    assert body["tool_authority_policy"]["decision"] == "ASK_CONFIRMATION"
    assert body["action_packet"]["packet_id"].startswith("ap_")
    assert body["action_packet"]["action_class"] == "SEND_EXTERNAL_MESSAGE"
    assert body["action_packet"]["external_effect_authorized"] is False
    assert body["action_packet"]["confirmation_command"] == f"/approve {body['action_packet']['packet_id']}"
    assert body["hermes_adapter"]["called"] is False
    assert body["local_response"]["telegram_send"] is False


@pytest.mark.anyio
async def test_cost_require_confirmation_emits_structured_non_authority_metadata(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=95077, first_name="Cost", username="cost")
        session.add(user)
        session.flush()
        robot = Robot(user_id=user.id, name="Cost Robot")
        session.add(robot)
        session.flush()
        owner_id = str(user.id)
        robot_id = str(robot.id)

    response = await client.post(
        POLICY_CHAIN_WEBHOOK_PATH,
        json=build_update("Premium research " + ("long context " * 700), user_id=95077, chat_id=95077),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error_code"] == "cost_confirmation_required"
    assert body["cost_preflight"]["decision"] == "require_confirmation"
    confirmation = body["cost_confirmation"]
    assert confirmation["confirmation_type"] == "cost_preflight"
    assert confirmation["request_id"] == body["cost_preflight"]["request_id"]
    assert confirmation["owner_id"] == owner_id
    assert confirmation["robot_id"] == robot_id
    assert confirmation["requester_actor_id"] == owner_id
    assert confirmation["task_class"] == "long_context"
    assert confirmation["routing_mode"] == "premium"
    assert confirmation["estimated_tokens"] == body["cost_preflight"]["token_estimate"]["estimated_total_tokens"]
    assert confirmation["estimated_cost_usd"] == body["cost_preflight"]["estimated_cost_usd"]
    assert confirmation["selected_model_id"] == body["cost_preflight"]["route_decision"]["selected_model_id"]
    assert confirmation["decision"] == "require_confirmation"
    assert confirmation["reason_code"] == body["cost_preflight"]["trace"][-1]["reason_code"]
    assert confirmation["task_cost_request"]["request_id"] == body["cost_preflight"]["request_id"]
    assert confirmation["task_cost_request"]["owner_id"] == owner_id
    assert confirmation["task_cost_request"]["robot_id"] == robot_id
    assert confirmation["task_cost_request"]["task_class"] == "long_context"
    assert confirmation["task_cost_request"]["routing_mode"] == "premium"
    assert confirmation["task_cost_request"]["requires_long_context"] is True
    assert confirmation["budget_policy"]["policy_id"] == "cost_governor_policy_100p_v0"
    assert confirmation["budget_policy"]["owner_id"] == owner_id
    assert confirmation["budget_policy"]["robot_id"] == robot_id
    assert confirmation["budget_policy"]["confirmation_cost_usd"] == 0.02
    assert confirmation["budget_policy"]["async_delegation_allowed"] is False
    assert confirmation["authority_expanded"] is False
    assert confirmation["external_effect_authorized"] is False
    assert confirmation["provider_call_authorized"] is False
    assert confirmation["execution_authorized"] is False
    assert body["action_packet"] is None
    assert body["hermes_adapter"]["called"] is False


@pytest.mark.anyio
async def test_blocked_payment_does_not_create_action_packet_or_reach_adapter(client):
    response = await client.post(POLICY_CHAIN_WEBHOOK_PATH, json=build_update("Please pay this invoice now"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error_code"] == "skill_scope_blocked"
    assert body["skill_scope_policy"]["decision"] == "BLOCK"
    assert body["action_packet"] is None
    assert body["hermes_adapter"]["called"] is False
    assert body["local_response"]["external_side_effect"] is False


@pytest.mark.anyio
async def test_bare_approval_is_blocked_but_specific_packet_reference_is_bound_locally(client):
    bare_response = await client.post(POLICY_CHAIN_WEBHOOK_PATH, json=build_update("/approve"))
    bare = bare_response.json()
    assert bare["error_code"] == "command_policy_blocked"
    assert bare["hermes_adapter"]["called"] is False

    specific_response = await client.post(POLICY_CHAIN_WEBHOOK_PATH, json=build_update("/approve ap_test123"))
    specific = specific_response.json()
    assert specific["ok"] is True
    assert specific["command_policy"]["metadata"]["action_packet_id"] == "ap_test123"
    assert specific["tool_authority_policy"]["decision"] == "DRAFT_ONLY"
    assert specific["hermes_adapter"]["called"] is True
    assert specific["local_response"]["external_side_effect"] is False


@pytest.mark.anyio
async def test_memory_projection_is_scoped_bounded_and_non_authority(client):
    with client.app.state.db.session() as session:
        user = User(telegram_user_id=777, first_name="Scoped", username="scoped")
        other = User(telegram_user_id=778, first_name="Other", username="other")
        session.add_all([user, other])
        session.flush()
        robot = Robot(user_id=user.id, name="Scoped Robot")
        other_robot = Robot(user_id=other.id, name="Other Robot")
        session.add_all([robot, other_robot])
        session.flush()
        session.add_all(
            [
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="WORK_PREFERENCE",
                    content="Prefers concise summaries.",
                    display_label="Preference",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="BOUNDARY_MEMORY",
                    content="Requires approval before external sends.",
                    display_label="Boundary",
                    source="telegram_text",
                    status="ACTIVE",
                ),
                MemoryItem(
                    user_id=user.id,
                    robot_id=robot.id,
                    memory_type="TASK_MEMORY",
                    content="Forgotten context must not be projected.",
                    display_label="Task",
                    source="telegram_text",
                    status="FORGOTTEN",
                ),
                MemoryItem(
                    user_id=other.id,
                    robot_id=other_robot.id,
                    memory_type="BOUNDARY_MEMORY",
                    content="Foreign memory must not be projected.",
                    display_label="Boundary",
                    source="telegram_text",
                    status="ACTIVE",
                ),
            ]
        )

    response = await client.post(
        POLICY_CHAIN_WEBHOOK_PATH,
        json=build_update("Draft my status update", user_id=777, chat_id=777),
    )
    body = response.json()
    projections = body["memory_context"]["projections"]

    assert [projection["memory_type"] for projection in projections] == [
        "BOUNDARY_MEMORY",
        "WORK_PREFERENCE",
    ]
    assert all("Foreign memory" not in projection["content"] for projection in projections)
    assert all("Forgotten context" not in projection["content"] for projection in projections)
    assert body["memory_context"]["tool_action_authorization"] is False
    assert body["memory_context"]["permission_expansion_authorized"] is False
    assert body["hermes_adapter"]["memory_projection_count"] == 2


def test_policy_chain_module_has_no_network_or_external_execution_imports():
    text = RUNTIME_PATH.read_text()

    for forbidden in [
        "import requests",
        "import httpx",
        "import urllib",
        "import socket",
        "import subprocess",
        "api.telegram.org",
        "setWebhook",
        "uvicorn.run",
        "smtp",
        "stripe",
    ]:
        assert forbidden not in text


def test_95p_reference_doc_and_roadmap_register_stage():
    doc = DOC_PATH.read_text()
    roadmap = ROADMAP_PATH.read_text()

    assert "Status: 95P implemented pending review." in doc
    assert "Telegram -> command policy -> skill scope policy -> tool authority policy -> memory projection policy -> Action Packet binding -> Hermes Gateway adapter stub -> local response" in doc
    assert "no live Telegram sends" in doc
    assert "no live Hermes Gateway startup" in doc
    assert "no external side effects" in doc
    assert '"stage_id":"95P","stage_name":"Telegram-Hermes Policy Chain Runtime Skeleton v0","status":"CLOSED_COMMITTED"' in roadmap
