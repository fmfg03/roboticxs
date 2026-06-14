from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_DOC = REPO_ROOT / "docs/reference/ROBOTICXS_COMMAND_SURFACE_POLICY_v0_1.md"


def test_command_surface_policy_doc_exists_and_is_docs_only_90p():
    text = POLICY_DOC.read_text()

    assert POLICY_DOC.is_file()
    assert "Status: 90P implemented pending review." in text
    for non_claim in [
        "no live command routing",
        "no runtime gateway changes",
        "no production enforcement code",
        "no MCP/plugin activation",
        "no arbitrary tool enablement",
        "no model-provider switching implementation",
        "no UI",
        "no 92P or later authorization",
    ]:
        assert non_claim in text


def test_policy_classes_are_complete_and_unknown_defaults_blocked():
    text = POLICY_DOC.read_text()

    for policy_class in [
        "`EXPOSE`",
        "`WRAP`",
        "`OPERATOR_ONLY`",
        "`BLOCK_CONSUMER`",
        "`UNKNOWN_UNVERIFIED`",
    ]:
        assert policy_class in text

    assert "Unknown commands default to blocked consumer exposure." in text
    assert "Any unverified raw Hermes command" in text


def test_initial_policy_matrix_contains_required_classes():
    text = POLICY_DOC.read_text()

    for exposed in [
        "| `help` | `EXPOSE` |",
        "| `status` | `EXPOSE` |",
        "| `usage` | `EXPOSE` |",
        "| `approve` | `EXPOSE` |",
        "| `deny` | `EXPOSE` |",
        "| `routines list` | `EXPOSE` |",
        "| `skills list` | `EXPOSE` |",
        "| `memory review` | `EXPOSE` |",
        "| `stop` | `EXPOSE` |",
    ]:
        assert exposed in text

    for wrapped in [
        "| `/cron` | `WRAP` |",
        "| `/skills` | `WRAP` |",
        "| `/bundles` | `WRAP` |",
        "| `/model` | `WRAP` |",
        "| `/handoff` | `WRAP` |",
        "| `/personality` | `WRAP` |",
        "| `/sessions` | `WRAP` |",
        "| `/resume` | `WRAP` |",
    ]:
        assert wrapped in text

    for operator_only in [
        "| `/config` | `OPERATOR_ONLY` |",
        "| `/reload` | `OPERATOR_ONLY` |",
        "| `/reload-mcp` | `OPERATOR_ONLY` |",
        "| `/plugins` | `OPERATOR_ONLY` |",
        "| Browser connect controls | `OPERATOR_ONLY` |",
        "| `/toolsets` | `OPERATOR_ONLY` |",
        "| `/debug` | `OPERATOR_ONLY` |",
        "| `/profile` | `OPERATOR_ONLY` |",
        "| `/platforms` | `OPERATOR_ONLY` |",
        "| `/gateway` | `OPERATOR_ONLY` |",
        "| `/codex-runtime` | `OPERATOR_ONLY` |",
        "| `/branch` | `OPERATOR_ONLY` |",
        "| `/rollback` | `OPERATOR_ONLY` |",
    ]:
        assert operator_only in text


def test_raw_command_exposure_requires_full_mapping_and_authority_boundaries():
    text = POLICY_DOC.read_text()

    for invariant in [
        "user intent",
        "allowed plan",
        "authority boundary",
        "cost policy",
        "audit log",
        "safe fallback",
        "Consumer users see Roboticxs product language, not Hermes operator language.",
        "Hermes capability does not equal Roboticxs permission.",
        "Zaubern-lite remains action authority.",
        "Cost Governor remains spend and wake authority.",
        "Memory Center remains canonical memory.",
    ]:
        assert invariant in text
