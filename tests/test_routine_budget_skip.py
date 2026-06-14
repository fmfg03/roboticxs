from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
COST_POLICY_PATH = REPO_ROOT / "docs/reference/ROBOTICXS_ROUTINE_COST_POLICY_v0_1.md"


def load_json_block(block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(COST_POLICY_PATH.read_text())
    assert match is not None, f"{COST_POLICY_PATH} must contain {block_name}."
    return json.loads(match.group("payload"))


def test_routine_budget_policy_is_required_and_blocks_before_model_router():
    text = COST_POLICY_PATH.read_text()
    policy = load_json_block("routine-budget-policy-v0")

    assert "Every recurring routine must declare a `RoutineBudgetPolicy`." in text
    assert "Every recurring routine must declare a wake policy." in text
    assert policy["on_budget_exceeded"] == "BLOCK_BUDGET"
    assert policy["requires_observable_budget_record"] is True
    assert "`BLOCK_BUDGET` means do not wake an agent, do not route a model" in text


def test_budget_skip_semantics_preserve_zero_token_paths():
    text = COST_POLICY_PATH.read_text()

    for required in [
        "`wakeAgent=false` is the zero-token path.",
        "The LLM should not run, Model Router should not run, and token usage should be zero.",
        "A skipped no-change run records zero expected tokens.",
        "A no-agent/script-only run records zero expected tokens.",
        "A budget-blocked run records zero expected tokens for agent/model usage.",
        "Script success is not spend approval.",
    ]:
        assert required in text
