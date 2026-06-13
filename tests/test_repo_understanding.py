from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import get_args

from app.repo_understanding import (
    FILE_CATEGORY_REGISTRY,
    SOURCE_REPO_REGISTER,
    RepoFileCategory,
    RepoUnderstandingBudgetClass,
    RepoUnderstandingDecision,
    RepoUnderstandingOutputShape,
    RepoUnderstandingPacket,
    RepoUnderstandingPacketType,
    RepoUnderstandingRequest,
    build_repo_understanding_packet,
    classify_repo_understanding_request,
    infer_file_categories,
    infer_repo_budget_class,
)


DOC_PATH = Path(__file__).resolve().parents[1] / "docs/reference/REPO_UNDERSTANDING_FACTORY_SKILL_v0_1.md"
ROADMAP_PATH = Path(__file__).resolve().parents[1] / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "packet_type",
    "repo_decision",
    "repo_scope",
    "requested_focus",
    "file_categories",
    "source_repo_references",
    "budget_class",
    "requires_budget_confirmation",
    "requires_user_confirmation",
    "local_files_only",
    "code_execution_authorized",
    "dependency_install_authorized",
    "repo_clone_authorized",
    "mcp_server_authorized",
    "external_tool_authorized",
    "network_access_authorized",
    "persistent_index_authorized",
    "security_certification_authorized",
    "correctness_claim_authorized",
    "raw_source_archive_authorized",
    "recommended_output_shape",
    "summary_claim_level",
    "uncertainty_required",
    "next_questions",
    "blocked_reason",
    "future_stage_required",
    "created_at",
}


def request(**overrides) -> RepoUnderstandingRequest:
    values = {
        "raw_text": "Map this repo before we touch it.",
        "repo_scope": "local_repo",
        "requested_focus": "repo_overview",
    }
    values.update(overrides)
    return RepoUnderstandingRequest(**values)


def source_by_id(source_id: str) -> dict[str, str | bool]:
    return {entry["source_id"]: entry for entry in SOURCE_REPO_REGISTER}[source_id]


def test_repo_understanding_taxonomies_are_explicit():
    assert set(get_args(RepoUnderstandingPacketType)) == {
        "REPO_OVERVIEW_PACKET",
        "FILE_SCOPE_PACKET",
        "SYMBOL_MAP_PLAN",
        "DEPENDENCY_MAP_PLAN",
        "TEST_MAP_PACKET",
        "DOCS_MAP_PACKET",
        "RISK_MAP_PACKET",
        "FACTORY_HANDOFF_PACKET",
        "BLOCKED_CODE_EXECUTION_REQUEST",
        "BLOCKED_DEPENDENCY_INSTALL_REQUEST",
        "BLOCKED_REPO_CLONE_REQUEST",
        "BLOCKED_EXTERNAL_TOOL_REQUEST",
    }
    assert set(get_args(RepoUnderstandingDecision)) == {
        "PREPARE_REPO_UNDERSTANDING_PACKET",
        "PREPARE_FILE_SCOPE_PACKET",
        "PREPARE_SYMBOL_MAP_PLAN",
        "PREPARE_DEPENDENCY_MAP_PLAN",
        "PREPARE_TEST_MAP_PACKET",
        "PREPARE_RISK_MAP_PACKET",
        "ASK_CLARIFICATION",
        "REQUIRE_BUDGET_CONFIRMATION",
        "BLOCK_CODE_EXECUTION",
        "BLOCK_DEPENDENCY_INSTALL",
        "BLOCK_REPO_CLONE",
        "BLOCK_EXTERNAL_TOOL",
        "DEFER_TO_FUTURE_INDEXER_STAGE",
    }
    assert set(get_args(RepoFileCategory)) == {
        "APP_CODE",
        "TEST_CODE",
        "CONFIG",
        "DOCS",
        "SCRIPT",
        "MIGRATION",
        "SCHEMA",
        "LOCKFILE",
        "DEPENDENCY_MANIFEST",
        "CI_PIPELINE",
        "AGENT_INSTRUCTION",
        "SECRET_OR_CREDENTIAL_LIKE",
        "GENERATED_OR_VENDOR",
        "UNKNOWN",
    }
    assert set(get_args(RepoUnderstandingBudgetClass)) == {
        "REPO_UNDERSTANDING_LIGHT",
        "REPO_UNDERSTANDING_STANDARD",
        "REPO_UNDERSTANDING_LARGE",
        "REPO_UNDERSTANDING_MULTI_AGENT_DEFERRED",
        "REPO_INDEXER_DEFERRED",
    }
    assert set(get_args(RepoUnderstandingOutputShape)) == {
        "REPO_MAP",
        "FILE_SCOPE_PLAN",
        "SYMBOL_MAP_PLAN_OUTPUT",
        "DEPENDENCY_MAP_PLAN_OUTPUT",
        "TEST_MAP",
        "DOCS_MAP",
        "RISK_MAP",
        "FACTORY_HANDOFF",
        "QUESTION_LIST",
        "BLOCKED_NOTICE",
    }


def test_source_repo_register_contains_required_repos_and_urls():
    assert {entry["source_id"] for entry in SOURCE_REPO_REGISTER} == {
        "understand_anything_source_repo",
        "codegraph_source_repo",
    }
    assert source_by_id("understand_anything_source_repo")["repo_url"] == "https://github.com/Lum1104/Understand-Anything"
    assert source_by_id("codegraph_source_repo")["repo_url"] == "https://github.com/colbymchenry/codegraph"


def test_understand_anything_source_repo_is_reference_only():
    source = source_by_id("understand_anything_source_repo")

    assert source["role"] == "architecture_reference_only"
    assert source["allowed_use_in_73P"] == "research_reference_only"
    assert source["dependency_authorized"] is False
    assert source["code_vendor_authorized"] is False
    assert source["repo_clone_authorized"] is False
    assert source["plugin_install_authorized"] is False
    assert source["dashboard_runtime_authorized"] is False
    assert source["multi_agent_runtime_authorized"] is False
    assert source["external_api_authorized"] is False


def test_codegraph_source_repo_is_reference_only():
    source = source_by_id("codegraph_source_repo")

    assert source["role"] == "architecture_reference_only"
    assert source["allowed_use_in_73P"] == "research_reference_only"
    assert source["dependency_authorized"] is False
    assert source["code_vendor_authorized"] is False
    assert source["repo_clone_authorized"] is False
    assert source["mcp_server_authorized"] is False
    assert source["tree_sitter_runtime_authorized"] is False
    assert source["sqlite_index_authorized"] is False
    assert source["external_api_authorized"] is False


def test_packet_contains_required_fields_and_source_refs():
    packet = build_repo_understanding_packet(request())

    assert isinstance(packet, RepoUnderstandingPacket)
    assert {field.name for field in fields(packet)} == REQUIRED_PACKET_FIELDS
    assert packet.packet_id.startswith("repo_understanding_")
    assert packet.source_repo_references == ("understand_anything_source_repo", "codegraph_source_repo")


def test_all_packets_disable_authority_flags_and_are_local_files_only():
    scenarios = [
        request(),
        request(run_code_requested=True),
        request(install_dependency_requested=True),
        request(repo_clone_requested=True),
        request(external_tool_requested=True),
        request(mcp_server_requested=True),
        request(persistent_index_requested=True),
        request(large_repo_requested=True),
    ]

    for scenario in scenarios:
        packet = build_repo_understanding_packet(scenario)
        assert packet.local_files_only is True
        assert packet.code_execution_authorized is False
        assert packet.dependency_install_authorized is False
        assert packet.repo_clone_authorized is False
        assert packet.mcp_server_authorized is False
        assert packet.external_tool_authorized is False
        assert packet.network_access_authorized is False
        assert packet.persistent_index_authorized is False
        assert packet.security_certification_authorized is False
        assert packet.correctness_claim_authorized is False
        assert packet.raw_source_archive_authorized is False


def test_unsafe_requests_block():
    cases = [
        (request(run_code_requested=True), "BLOCK_CODE_EXECUTION", "BLOCKED_CODE_EXECUTION_REQUEST"),
        (request(security_certification_requested=True), "BLOCK_CODE_EXECUTION", "BLOCKED_CODE_EXECUTION_REQUEST"),
        (request(correctness_claim_requested=True), "BLOCK_CODE_EXECUTION", "BLOCKED_CODE_EXECUTION_REQUEST"),
        (request(install_dependency_requested=True), "BLOCK_DEPENDENCY_INSTALL", "BLOCKED_DEPENDENCY_INSTALL_REQUEST"),
        (request(repo_clone_requested=True), "BLOCK_REPO_CLONE", "BLOCKED_REPO_CLONE_REQUEST"),
        (request(external_tool_requested=True), "BLOCK_EXTERNAL_TOOL", "BLOCKED_EXTERNAL_TOOL_REQUEST"),
        (request(mcp_server_requested=True), "BLOCK_EXTERNAL_TOOL", "BLOCKED_EXTERNAL_TOOL_REQUEST"),
        (request(network_access_requested=True), "BLOCK_EXTERNAL_TOOL", "BLOCKED_EXTERNAL_TOOL_REQUEST"),
    ]

    for scenario, decision, packet_type in cases:
        packet = build_repo_understanding_packet(scenario)
        assert packet.repo_decision == decision
        assert packet.packet_type == packet_type
        assert packet.recommended_output_shape == "BLOCKED_NOTICE"
        assert packet.blocked_reason


def test_persistent_index_request_defers_to_future_stage():
    packet = build_repo_understanding_packet(request(persistent_index_requested=True))

    assert packet.repo_decision == "DEFER_TO_FUTURE_INDEXER_STAGE"
    assert packet.packet_type == "FACTORY_HANDOFF_PACKET"
    assert packet.budget_class == "REPO_INDEXER_DEFERRED"
    assert packet.requires_budget_confirmation is True
    assert packet.future_stage_required == "future_indexer_stage_if_full_graph_needed"
    assert packet.persistent_index_authorized is False


def test_map_requests_prepare_plans_only():
    cases = [
        (request(symbol_map_requested=True), "PREPARE_SYMBOL_MAP_PLAN", "SYMBOL_MAP_PLAN", "SYMBOL_MAP_PLAN_OUTPUT"),
        (request(dependency_map_requested=True), "PREPARE_DEPENDENCY_MAP_PLAN", "DEPENDENCY_MAP_PLAN", "DEPENDENCY_MAP_PLAN_OUTPUT"),
        (request(test_map_requested=True), "PREPARE_TEST_MAP_PACKET", "TEST_MAP_PACKET", "TEST_MAP"),
        (request(risk_map_requested=True), "PREPARE_RISK_MAP_PACKET", "RISK_MAP_PACKET", "RISK_MAP"),
        (request(docs_map_requested=True), "PREPARE_FILE_SCOPE_PACKET", "FILE_SCOPE_PACKET", "FILE_SCOPE_PLAN"),
    ]

    for scenario, decision, packet_type, output_shape in cases:
        packet = build_repo_understanding_packet(scenario)
        assert packet.repo_decision == decision
        assert packet.packet_type == packet_type
        assert packet.recommended_output_shape == output_shape
        assert packet.summary_claim_level == "map_or_plan_only_no_correctness_claim"


def test_large_and_multi_agent_requests_require_budget_confirmation():
    scenarios = [
        (request(large_repo_requested=True), "REPO_UNDERSTANDING_LARGE"),
        (request(multi_agent_requested=True), "REPO_UNDERSTANDING_MULTI_AGENT_DEFERRED"),
    ]

    for scenario, budget_class in scenarios:
        packet = build_repo_understanding_packet(scenario)
        assert packet.repo_decision == "REQUIRE_BUDGET_CONFIRMATION"
        assert packet.budget_class == budget_class
        assert packet.requires_budget_confirmation is True
        assert packet.requires_user_confirmation is True


def test_file_category_taxonomy_and_secret_flagging():
    assert {entry["file_category"] for entry in FILE_CATEGORY_REGISTRY} == set(get_args(RepoFileCategory))
    categories = infer_file_categories(
        [
            "app/repo_understanding.py",
            "tests/test_repo_understanding.py",
            "docs/reference/spec.md",
            "pyproject.toml",
            "AGENTS.md",
            ".github/workflows/ci.yml",
            "config/settings.toml",
            "storage/schema.sql",
            "migrations/001.sql",
            "scripts/run.sh",
            "package-lock.json",
            "vendor/generated.js",
            ".env",
        ]
    )

    assert categories == [
        "APP_CODE",
        "TEST_CODE",
        "DOCS",
        "DEPENDENCY_MANIFEST",
        "AGENT_INSTRUCTION",
        "CI_PIPELINE",
        "CONFIG",
        "MIGRATION",
        "SCRIPT",
        "LOCKFILE",
        "GENERATED_OR_VENDOR",
        "SECRET_OR_CREDENTIAL_LIKE",
    ]


def test_decision_precedence_is_deterministic():
    scenario = request(
        run_code_requested=True,
        install_dependency_requested=True,
        repo_clone_requested=True,
        external_tool_requested=True,
        large_repo_requested=True,
        symbol_map_requested=True,
    )

    assert classify_repo_understanding_request(scenario) == "BLOCK_CODE_EXECUTION"
    assert infer_repo_budget_class(request(symbol_map_requested=True)) == "REPO_UNDERSTANDING_STANDARD"


def test_docs_contain_required_non_claims_and_source_register():
    text = DOC_PATH.read_text()

    for required in [
        "Understand Anything and codegraph are architecture references only.",
        "repo-understanding-source-register",
        "https://github.com/Lum1104/Understand-Anything",
        "https://github.com/colbymchenry/codegraph",
        "Roboticxs Factory does not execute code in 73P.",
        "Roboticxs Factory does not install dependencies in 73P.",
        "Roboticxs Factory does not clone repositories in 73P.",
        "Roboticxs Factory does not start an MCP server in 73P.",
        "Roboticxs Factory does not vendor Understand Anything or codegraph in 73P.",
        "Roboticxs Factory does not create a persistent repo index in 73P.",
        "Roboticxs Factory does not certify security or correctness in 73P.",
        "Roboticxs Factory does not claim full codebase understanding in 73P.",
        "74P ECC Knowledge Compiler Factory Skill becomes the next eligible stage.",
    ]:
        assert required in text


def test_roadmap_marks_73p_completed_and_74p_next_after_closeout():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"73P","stage_name":"Understand-Anything + codegraph Factory Skill","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"commit":"same_commit_as_73P_closeout"' in text
    assert '"app/repo_understanding.py"' in text
    assert '"docs/reference/REPO_UNDERSTANDING_FACTORY_SKILL_v0_1.md"' in text
    assert '"tests/test_repo_understanding.py"' in text
    assert '"stage_id":"74P","stage_name":"ECC Knowledge Compiler Factory Skill","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"stage_id":"75P","stage_name":"Agent-Reach Research Parking Lot","status":"NEXT_ELIGIBLE"' in text
    assert '"after_commit_next_eligible":"75P"' in text
