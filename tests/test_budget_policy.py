from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import BudgetPolicy, DocumentTask, FileIntakeAttempt, MemoryItem, ProposedMemory
from tests.test_document_review import LONG_DOCUMENT, build_update
from tests.test_file_intake import build_document_update


HIGH_COST_TEXT = "Help me prepare for my meeting tomorrow " + ("long context " * 240)


async def seed_costly_usage(client, *, user_id: int = 123456, name: str = "Francisco", turns: int = 1):
    for _ in range(turns):
        response = await client.post("/api/telegram/webhook", json=build_update(HIGH_COST_TEXT, user_id=user_id, name=name))
        assert response.status_code == 200


@pytest.mark.anyio
async def test_show_budget_status_empty_default_state(client):
    response = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget status: ALLOW." in reply
    assert "Local budget limit:" in reply
    assert "Warn threshold: 80%." in reply
    assert "Block threshold: 100%." in reply
    assert "Current local estimated spend: $0.000000." in reply
    assert "This is based on local estimates only, not live billing or provider reconciliation." in reply


@pytest.mark.anyio
async def test_budget_status_uses_seeded_local_usage(client):
    await seed_costly_usage(client, turns=1)

    response = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget status: WARN." in reply
    assert "Current local estimated spend:" in reply
    assert "Remaining local estimated budget:" in reply
    assert "Usage:" in reply


@pytest.mark.anyio
async def test_warn_threshold_allows_normal_task_with_warning(client):
    await seed_costly_usage(client, turns=1)

    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "ANSWER"
    assert "Budget warning: WARN." in body["reply"]["text"]


@pytest.mark.anyio
async def test_block_threshold_blocks_normal_task_locally(client):
    await seed_costly_usage(client, turns=2)

    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "BLOCK"
    assert body["safety_decision"] == "BLOCK"
    assert "local estimated budget threshold has been reached" in body["reply"]["text"].lower()


@pytest.mark.anyio
async def test_budget_status_is_scoped_by_user_and_robot(client):
    await seed_costly_usage(client, user_id=123456, name="Francisco", turns=2)

    response = await client.post("/api/telegram/webhook", json=build_update("show budget status", user_id=777, name="Alicia"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget status: ALLOW." in reply
    assert "Current local estimated spend: $0.000000." in reply


@pytest.mark.anyio
async def test_usage_and_budget_commands_remain_available_when_budget_is_blocked(client):
    await seed_costly_usage(client, turns=2)

    spend = await client.post("/api/telegram/webhook", json=build_update("what did you spend"))
    assert spend.status_code == 200
    assert "Local estimated spend summary:" in spend.json()["reply"]["text"]

    usage = await client.post("/api/telegram/webhook", json=build_update("show token usage"))
    assert usage.status_code == 200
    assert "Local token usage summary:" in usage.json()["reply"]["text"]

    budget = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert budget.status_code == 200
    assert "Budget status: BLOCK." in budget.json()["reply"]["text"]


@pytest.mark.anyio
async def test_budget_status_turns_create_runtime_records_without_new_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    assert after["file_intakes"] == before["file_intakes"]


@pytest.mark.anyio
async def test_budget_status_does_not_create_file_intake_records(client):
    response = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        assert session.query(FileIntakeAttempt).count() == 0


@pytest.mark.anyio
async def test_set_budget_limit_persists_policy_for_same_user_robot(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget limit updated for this robot: $0.010000 local estimated spend." in reply
    after = db_counts()
    assert after["budget_policies"] == before["budget_policies"] + 1
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    with client.app.state.db.session() as session:
        policy = session.scalar(select(BudgetPolicy).order_by(BudgetPolicy.created_at.desc()))
        assert policy is not None
        assert policy.limit_amount == 0.01
        assert policy.warn_threshold_percent == 80
        assert policy.block_threshold_percent == 100
        assert policy.status == "ACTIVE"


@pytest.mark.anyio
async def test_set_budget_limit_dollar_amount_parses_correctly(client):
    response = await client.post("/api/telegram/webhook", json=build_update("set budget limit $1.50"))
    assert response.status_code == 200
    with client.app.state.db.session() as session:
        policy = session.scalar(select(BudgetPolicy).order_by(BudgetPolicy.created_at.desc()))
        assert policy is not None
        assert policy.limit_amount == 1.5


@pytest.mark.anyio
async def test_set_budget_limit_invalid_missing_amount_does_not_create_policy(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("set budget limit"))
    assert response.status_code == 200
    assert "could not set the budget limit" in response.json()["reply"]["text"].lower()
    after = db_counts()
    assert after["budget_policies"] == before["budget_policies"]
    assert after["tasks"] == before["tasks"] + 1


@pytest.mark.anyio
async def test_set_budget_limit_rejects_zero_negative_nonnumeric_and_malformed_values(client, db_counts):
    invalid_commands = [
        "set budget limit 0",
        "set budget limit -1",
        "set budget limit abc",
        "set budget limit $-1",
        "set budget limit 1.2.3",
    ]
    before = db_counts()
    for command in invalid_commands:
        response = await client.post("/api/telegram/webhook", json=build_update(command))
        assert response.status_code == 200
        assert "could not set the budget limit" in response.json()["reply"]["text"].lower()
    after = db_counts()
    assert after["budget_policies"] == before["budget_policies"]


@pytest.mark.anyio
async def test_show_budget_status_reflects_configured_limit(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    response = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Local budget limit: $0.010000." in reply


@pytest.mark.anyio
async def test_set_budget_warn_threshold_persists_for_same_user_robot(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 70"))
    assert response.status_code == 200
    assert "Budget warn threshold updated for this robot: 70%." in response.json()["reply"]["text"]
    after = db_counts()
    assert after["budget_policies"] == before["budget_policies"] + 1
    with client.app.state.db.session() as session:
        policy = session.scalar(select(BudgetPolicy).order_by(BudgetPolicy.created_at.desc()))
        assert policy is not None
        assert policy.limit_amount == 0.0016
        assert policy.warn_threshold_percent == 70
        assert policy.block_threshold_percent == 100


@pytest.mark.anyio
async def test_set_budget_block_threshold_persists_for_same_user_robot(client):
    response = await client.post("/api/telegram/webhook", json=build_update("set budget block threshold 95%"))
    assert response.status_code == 200
    assert "Budget block threshold updated for this robot: 95%." in response.json()["reply"]["text"]
    with client.app.state.db.session() as session:
        policy = session.scalar(select(BudgetPolicy).order_by(BudgetPolicy.created_at.desc()))
        assert policy is not None
        assert policy.warn_threshold_percent == 80
        assert policy.block_threshold_percent == 95


@pytest.mark.anyio
async def test_set_budget_warn_threshold_rejects_invalid_and_contradictory_values(client, db_counts):
    invalid_commands = [
        "set budget warn threshold",
        "set budget warn threshold 0",
        "set budget warn threshold -1",
        "set budget warn threshold abc",
        "set budget warn threshold 1.5",
        "set budget warn threshold 100",
        "set budget warn threshold 101",
    ]
    before = db_counts()
    for command in invalid_commands:
        response = await client.post("/api/telegram/webhook", json=build_update(command))
        assert response.status_code == 200
        assert "could not set the budget warn threshold" in response.json()["reply"]["text"].lower()
    after = db_counts()
    assert after["budget_policies"] == before["budget_policies"]


@pytest.mark.anyio
async def test_set_budget_block_threshold_rejects_invalid_and_contradictory_values(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 85"))
    invalid_commands = [
        "set budget block threshold",
        "set budget block threshold 0",
        "set budget block threshold -1",
        "set budget block threshold abc",
        "set budget block threshold 1.5",
        "set budget block threshold 101",
        "set budget block threshold 85",
        "set budget block threshold 80",
    ]
    before = db_counts()
    for command in invalid_commands:
        response = await client.post("/api/telegram/webhook", json=build_update(command))
        assert response.status_code == 200
        assert "could not set the budget block threshold" in response.json()["reply"]["text"].lower()
    after = db_counts()
    assert after["budget_policies"] == before["budget_policies"]


@pytest.mark.anyio
async def test_show_budget_status_reflects_configured_thresholds(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 70"))
    await client.post("/api/telegram/webhook", json=build_update("set budget block threshold 95"))
    response = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Warn threshold: 70%." in reply
    assert "Block threshold: 95%." in reply


@pytest.mark.anyio
async def test_reset_budget_policy_restores_default_fallback(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 70"))
    await client.post("/api/telegram/webhook", json=build_update("set budget block threshold 95"))

    reset = await client.post("/api/telegram/webhook", json=build_update("reset budget policy"))
    assert reset.status_code == 200
    assert "Budget policy reset for this robot." in reset.json()["reply"]["text"]

    response = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Local budget limit: $0.001600." in reply
    assert "Warn threshold: 80%." in reply
    assert "Block threshold: 100%." in reply

    with client.app.state.db.session() as session:
        policy = session.scalar(select(BudgetPolicy).order_by(BudgetPolicy.created_at.desc()))
        assert policy is not None
        assert policy.status == "INACTIVE"


@pytest.mark.anyio
async def test_restore_default_budget_policy_alias_works(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    response = await client.post("/api/telegram/webhook", json=build_update("restore default budget policy"))
    assert response.status_code == 200
    assert "Budget policy reset for this robot." in response.json()["reply"]["text"]
    status = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert "Local budget limit: $0.001600." in status.json()["reply"]["text"]


@pytest.mark.anyio
async def test_configured_budget_limit_changes_guardrail_behavior(client):
    await seed_costly_usage(client, turns=1)
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))

    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    assert "Budget warning: WARN." not in response.json()["reply"]["text"]
    assert response.json()["scope_decision"] == "ANSWER"


@pytest.mark.anyio
async def test_set_budget_limit_is_scoped_by_user_and_robot(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01", user_id=123456, name="Francisco"))
    response = await client.post("/api/telegram/webhook", json=build_update("show budget status", user_id=777, name="Alicia"))
    assert response.status_code == 200
    assert "Local budget limit: $0.001600." in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_budget_threshold_configuration_is_scoped_by_user_and_robot(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 70", user_id=123456, name="Francisco"))
    await client.post("/api/telegram/webhook", json=build_update("set budget block threshold 95", user_id=123456, name="Francisco"))
    response = await client.post("/api/telegram/webhook", json=build_update("show budget status", user_id=777, name="Alicia"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Warn threshold: 80%." in reply
    assert "Block threshold: 100%." in reply


@pytest.mark.anyio
async def test_reset_budget_policy_is_scoped_by_user_and_robot(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01", user_id=123456, name="Francisco"))
    response = await client.post("/api/telegram/webhook", json=build_update("reset budget policy", user_id=777, name="Alicia"))
    assert response.status_code == 200
    status = await client.post("/api/telegram/webhook", json=build_update("show budget status", user_id=123456, name="Francisco"))
    assert "Local budget limit: $0.010000." in status.json()["reply"]["text"]


@pytest.mark.anyio
async def test_set_budget_limit_remains_available_while_budget_is_blocked(client):
    await seed_costly_usage(client, turns=2)
    response = await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    assert response.status_code == 200
    assert "Budget limit updated for this robot" in response.json()["reply"]["text"]
    with client.app.state.db.session() as session:
        policy = session.scalar(select(BudgetPolicy).order_by(BudgetPolicy.created_at.desc()))
        assert policy is not None
        assert policy.limit_amount == 0.01


@pytest.mark.anyio
async def test_budget_threshold_commands_remain_available_while_budget_is_blocked(client):
    await seed_costly_usage(client, turns=2)
    warn_response = await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 70"))
    block_response = await client.post("/api/telegram/webhook", json=build_update("set budget block threshold 95"))
    assert warn_response.status_code == 200
    assert block_response.status_code == 200
    assert "Budget warn threshold updated for this robot: 70%." in warn_response.json()["reply"]["text"]
    assert "Budget block threshold updated for this robot: 95%." in block_response.json()["reply"]["text"]
    with client.app.state.db.session() as session:
        policy = session.scalar(select(BudgetPolicy).order_by(BudgetPolicy.created_at.desc()))
        assert policy is not None
        assert policy.warn_threshold_percent == 70
        assert policy.block_threshold_percent == 95


@pytest.mark.anyio
async def test_reset_budget_policy_remains_available_while_budget_is_blocked(client):
    await seed_costly_usage(client, turns=2)
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    response = await client.post("/api/telegram/webhook", json=build_update("reset budget policy"))
    assert response.status_code == 200
    assert "Budget policy reset for this robot." in response.json()["reply"]["text"]
    status = await client.post("/api/telegram/webhook", json=build_update("show budget status"))
    assert "Local budget limit: $0.001600." in status.json()["reply"]["text"]


@pytest.mark.anyio
async def test_set_budget_limit_does_not_create_document_memory_or_file_artifacts(client, db_counts):
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    assert response.status_code == 200
    after = db_counts()
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    assert after["file_intakes"] == before["file_intakes"]


@pytest.mark.anyio
async def test_budget_threshold_commands_do_not_create_document_memory_or_file_artifacts(client, db_counts):
    before = db_counts()
    warn_response = await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 70"))
    block_response = await client.post("/api/telegram/webhook", json=build_update("set budget block threshold 95"))
    assert warn_response.status_code == 200
    assert block_response.status_code == 200
    after = db_counts()
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    assert after["file_intakes"] == before["file_intakes"]


@pytest.mark.anyio
async def test_reset_budget_policy_does_not_create_document_memory_or_file_artifacts(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("reset budget policy"))
    assert response.status_code == 200
    after = db_counts()
    assert after["documents"] == before["documents"]
    assert after["memories"] == before["memories"]
    assert after["proposals"] == before["proposals"]
    assert after["file_intakes"] == before["file_intakes"]


@pytest.mark.anyio
async def test_reset_budget_policy_turn_creates_runtime_records(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("set budget limit 0.01"))
    before = db_counts()
    response = await client.post("/api/telegram/webhook", json=build_update("reset budget policy"))
    assert response.status_code == 200
    after = db_counts()
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    assert after["budget_policies"] == before["budget_policies"]


@pytest.mark.anyio
async def test_configured_warn_threshold_changes_guardrail_behavior(client):
    await client.post("/api/telegram/webhook", json=build_update("set budget warn threshold 1"))
    response = await client.post("/api/telegram/webhook", json=build_update(HIGH_COST_TEXT))
    assert response.status_code == 200
    assert "Budget warning: WARN." in response.json()["reply"]["text"]


@pytest.mark.anyio
async def test_configured_block_threshold_changes_guardrail_behavior(client):
    await seed_costly_usage(client, turns=1)
    await client.post("/api/telegram/webhook", json=build_update("set budget block threshold 90"))
    response = await client.post("/api/telegram/webhook", json=build_update("Help me prepare for my meeting tomorrow"))
    assert response.status_code == 200
    assert response.json()["scope_decision"] == "BLOCK"
    assert response.json()["safety_decision"] == "BLOCK"


@pytest.mark.anyio
async def test_warn_threshold_allows_document_review_with_warning(client):
    await seed_costly_usage(client, turns=1)

    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget warning: WARN." in reply
    assert "Summary:" in reply


@pytest.mark.anyio
async def test_block_threshold_blocks_document_review_without_document_task(client, db_counts):
    await seed_costly_usage(client, turns=2)
    before = db_counts()

    response = await client.post("/api/telegram/webhook", json=build_update(f"review document: {LONG_DOCUMENT}"))
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "BLOCK"
    assert body["safety_decision"] == "BLOCK"
    after = db_counts()
    assert after["documents"] == before["documents"]
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_warn_threshold_allows_memory_proposal_with_warning(client):
    await seed_costly_usage(client, turns=1)

    response = await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget warning: WARN." in reply
    assert "Reply APPROVE to save it or REJECT to discard it." in reply


@pytest.mark.anyio
async def test_block_threshold_blocks_memory_proposal_without_proposal(client, db_counts):
    await seed_costly_usage(client, turns=2)
    before = db_counts()

    response = await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "BLOCK"
    assert body["safety_decision"] == "BLOCK"
    after = db_counts()
    assert after["proposals"] == before["proposals"]
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1


@pytest.mark.anyio
async def test_warn_threshold_allows_memory_decision_with_warning(client):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    await seed_costly_usage(client, turns=1)

    response = await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget warning: WARN." in reply
    assert "Saved to your robot memory." in reply

    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        memory = session.scalar(select(MemoryItem).order_by(MemoryItem.created_at.desc()))
        assert proposal is not None and proposal.status == "APPROVED"
        assert memory is not None and memory.status == "ACTIVE"


@pytest.mark.anyio
async def test_block_threshold_blocks_memory_decision_without_mutating_pending(client, db_counts):
    await client.post("/api/telegram/webhook", json=build_update("Remember that I prefer short direct answers."))
    await seed_costly_usage(client, turns=2)
    before = db_counts()

    response = await client.post("/api/telegram/webhook", json=build_update("APPROVE"))
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "BLOCK"
    assert body["safety_decision"] == "BLOCK"
    after = db_counts()
    assert after["memories"] == before["memories"]
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1
    with client.app.state.db.session() as session:
        proposal = session.scalar(select(ProposedMemory).order_by(ProposedMemory.created_at.desc()))
        assert proposal is not None
        assert proposal.status == "PENDING"


@pytest.mark.anyio
async def test_warn_threshold_allows_file_intake_with_warning(client):
    await seed_costly_usage(client, turns=1)

    response = await client.post("/api/telegram/webhook", json=build_document_update())
    assert response.status_code == 200
    reply = response.json()["reply"]["text"]
    assert "Budget warning: WARN." in reply
    assert "received the file metadata" in reply.lower()


@pytest.mark.anyio
async def test_block_threshold_blocks_file_intake_without_file_record(client, db_counts):
    await seed_costly_usage(client, turns=2)
    before = db_counts()

    response = await client.post("/api/telegram/webhook", json=build_document_update())
    assert response.status_code == 200
    body = response.json()
    assert body["scope_decision"] == "BLOCK"
    assert body["safety_decision"] == "BLOCK"
    after = db_counts()
    assert after["file_intakes"] == before["file_intakes"]
    assert after["tasks"] == before["tasks"] + 1
    assert after["task_runs"] == before["task_runs"] + 1
    assert after["safety"] == before["safety"] + 1
    assert after["routes"] == before["routes"] + 1
    assert after["tokens"] == before["tokens"] + 1


def test_file_intake_model_still_has_no_raw_content_fields():
    columns = {column.name for column in FileIntakeAttempt.__table__.columns}
    assert "raw_bytes" not in columns
    assert "file_bytes" not in columns
    assert "downloaded_file_path" not in columns
    assert "full_text" not in columns
    assert "extracted_text" not in columns
    assert "ocr_text" not in columns
