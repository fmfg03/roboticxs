from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs/reference/RUNTIME_SURFACE_AUDIT_v0_1.md"
FREEZE_PATH = REPO_ROOT / "docs/reference/RETRIEVAL_CONTROL_FREEZE_v0_1.md"
REQUIRED_FREEZE_FIELDS = {
    "surface_id",
    "current_effect",
    "freeze_classification",
    "visible_status",
    "expansion_rule",
    "rename_status",
    "future_architecture_boundary",
    "test_evidence",
}
ALLOWED_FREEZE_CLASSIFICATIONS = {
    "PRESERVE_LOCAL_CONTROL_ONLY",
    "FROZEN_VISIBLE_NOT_EXPANDABLE",
    "DEFERRED_CONNECTOR_ARCHITECTURE",
}
ALLOWED_RENAME_STATUSES = {"NONE", "RENAME_LATER"}
REQUIRED_BLOCKED_V0_BEHAVIORS = {
    "telegram_getfile_calls",
    "file_download",
    "pdf_parsing",
    "ocr",
    "raw_byte_storage",
    "extracted_content_storage",
    "content_review_without_content_access",
    "browser_retrieval",
    "connector_activation",
    "credential_or_cookie_handling",
    "external_writes",
    "local_intent_or_approval_as_execution_authority",
}
REQUIRED_DEFERRED_CONNECTOR_REQUIREMENTS = {
    "connector_authorization_and_revocation",
    "credential_isolation",
    "explicit_user_confirmation_before_external_effects",
    "retrieval_execution_lifecycle",
    "content_retention_policy",
    "audit_receipts",
    "failure_and_retry_behavior",
    "provider_and_transport_boundaries",
    "authority_and_data_boundary_tests",
}
REQUIRED_APPROVAL_DENIALS = {
    "does_not_enable_retrieval",
    "does_not_change_configuration",
    "does_not_authorize_connector",
    "does_not_authorize_credentials",
    "does_not_execute_retrieval",
    "does_not_grant_external_authority",
}
REQUIRED_LIVE_RETRIEVAL_DENIALS = {
    "implementation_available",
    "execution_authorized",
    "connector_active",
    "credentials_available",
    "retrieval_will_execute",
}


def load_json_block(path: Path, block_name: str):
    pattern = re.compile(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        re.DOTALL,
    )
    match = pattern.search(path.read_text())
    assert match is not None, f"{path.name} must contain {block_name}."
    return json.loads(match.group("payload"))


def load_audited_retrieval_surfaces() -> list[dict]:
    inventory = load_json_block(AUDIT_PATH, "runtime-surface-inventory")
    return [
        surface
        for surface in inventory
        if surface["surface_id"].startswith("retrieval_control.")
    ]


def load_freeze_inventory() -> list[dict]:
    return load_json_block(FREEZE_PATH, "retrieval-control-freeze-inventory")


def test_freeze_inventory_covers_exactly_the_62p_retrieval_surfaces_once():
    audited_ids = [surface["surface_id"] for surface in load_audited_retrieval_surfaces()]
    frozen_ids = [surface["surface_id"] for surface in load_freeze_inventory()]

    assert len(frozen_ids) == len(set(frozen_ids))
    assert set(frozen_ids) == set(audited_ids)
    assert all(surface_id.startswith("retrieval_control.") for surface_id in frozen_ids)


def test_every_frozen_surface_has_the_approved_taxonomy_and_existing_test_evidence():
    for surface in load_freeze_inventory():
        assert set(surface) == REQUIRED_FREEZE_FIELDS
        assert surface["current_effect"]
        assert surface["freeze_classification"] in ALLOWED_FREEZE_CLASSIFICATIONS
        assert surface["rename_status"] in ALLOWED_RENAME_STATUSES
        assert surface["visible_status"]
        assert surface["expansion_rule"]
        assert surface["future_architecture_boundary"]
        assert surface["test_evidence"]
        for test_ref in surface["test_evidence"]:
            assert (REPO_ROOT / test_ref).is_file()


def test_existing_surfaces_are_local_control_or_frozen_visible_not_deferred():
    inventory = load_freeze_inventory()

    assert {
        surface["freeze_classification"]
        for surface in inventory
    } == {
        "PRESERVE_LOCAL_CONTROL_ONLY",
        "FROZEN_VISIBLE_NOT_EXPANDABLE",
    }
    assert all("BLOCKED_V0" not in surface.values() for surface in inventory)
    assert all(
        surface["rename_status"] in ALLOWED_RENAME_STATUSES
        for surface in inventory
    )


def test_expansion_rules_freeze_external_effects_and_visible_surface_growth():
    for surface in load_freeze_inventory():
        rule = surface["expansion_rule"].lower()
        boundary = surface["future_architecture_boundary"].lower()
        assert "no " in rule or "do not " in rule
        assert "connector" in boundary or "retrieval" in boundary or "execution" in boundary
        assert any(term in boundary for term in ("separate", "requires", "cannot", "must", "belongs"))

        if surface["freeze_classification"] == "FROZEN_VISIBLE_NOT_EXPANDABLE":
            assert "compatibility" in rule
        else:
            assert "local" in rule


def test_blocked_v0_behaviors_are_global_policy_not_surface_classifications():
    blocked_behaviors = load_json_block(FREEZE_PATH, "blocked-v0-behaviors")

    assert set(blocked_behaviors) == REQUIRED_BLOCKED_V0_BEHAVIORS
    assert "BLOCKED_V0" not in ALLOWED_FREEZE_CLASSIFICATIONS


def test_connector_architecture_is_deferred_with_required_authority_boundaries():
    requirements = load_json_block(FREEZE_PATH, "deferred-connector-requirements")

    assert set(requirements) == REQUIRED_DEFERRED_CONNECTOR_REQUIREMENTS
    assert all(
        surface["freeze_classification"] != "DEFERRED_CONNECTOR_ARCHITECTURE"
        for surface in load_freeze_inventory()
    )


def test_approval_intent_is_not_activation_authority():
    policy = load_json_block(FREEZE_PATH, "approval-intent-policy")

    assert policy["request_meaning"] == "local_intent_record_only"
    assert policy["approval_meaning"] == "local_approval_pending_future_policy_change_only"
    assert policy["approval_status"] == "APPROVED_PENDING_POLICY_CHANGE"
    assert set(policy["denied_implications"]) == REQUIRED_APPROVAL_DENIALS


def test_live_retrieval_enabled_is_only_a_policy_signal():
    policy = load_json_block(FREEZE_PATH, "live-retrieval-enabled-policy")

    assert policy["meaning"] == "policy_or_configuration_signal_only"
    assert policy["default"] is False
    assert set(policy["does_not_mean"]) == REQUIRED_LIVE_RETRIEVAL_DENIALS
    assert policy["runtime_change_authorized_by_63P"] is False
