from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


RepoUnderstandingPacketType = Literal[
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
]

RepoUnderstandingDecision = Literal[
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
]

RepoFileCategory = Literal[
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
]

RepoUnderstandingBudgetClass = Literal[
    "REPO_UNDERSTANDING_LIGHT",
    "REPO_UNDERSTANDING_STANDARD",
    "REPO_UNDERSTANDING_LARGE",
    "REPO_UNDERSTANDING_MULTI_AGENT_DEFERRED",
    "REPO_INDEXER_DEFERRED",
]

RepoUnderstandingOutputShape = Literal[
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
]


SOURCE_REPO_REGISTER: tuple[dict[str, str | bool], ...] = (
    {
        "source_id": "understand_anything_source_repo",
        "repo_name": "Understand Anything",
        "repo_url": "https://github.com/Lum1104/Understand-Anything",
        "project_site": "https://understand-anything.com/",
        "project_origin": "Egonex / Understand Anything",
        "role": "architecture_reference_only",
        "allowed_use_in_73P": "research_reference_only",
        "dependency_authorized": False,
        "code_vendor_authorized": False,
        "repo_clone_authorized": False,
        "plugin_install_authorized": False,
        "dashboard_runtime_authorized": False,
        "multi_agent_runtime_authorized": False,
        "external_api_authorized": False,
        "external_runtime_authorized": False,
        "mcp_server_authorized": False,
        "persistent_index_authorized": False,
        "network_access_authorized": False,
        "notes": "Architecture reference only; no install, vendoring, clone, dashboard, or multi-agent runtime.",
    },
    {
        "source_id": "codegraph_source_repo",
        "repo_name": "codegraph",
        "repo_url": "https://github.com/colbymchenry/codegraph",
        "role": "architecture_reference_only",
        "allowed_use_in_73P": "research_reference_only",
        "dependency_authorized": False,
        "code_vendor_authorized": False,
        "repo_clone_authorized": False,
        "mcp_server_authorized": False,
        "tree_sitter_runtime_authorized": False,
        "sqlite_index_authorized": False,
        "external_api_authorized": False,
        "external_runtime_authorized": False,
        "persistent_index_authorized": False,
        "network_access_authorized": False,
        "notes": "Architecture reference only; no MCP, tree-sitter runtime, SQLite index, or external tooling.",
    },
)

FILE_CATEGORY_REGISTRY: tuple[dict[str, str | bool], ...] = (
    {"file_category": "APP_CODE", "allowed_in_73P": True, "deep_summary_by_default": True, "risk_label": "MEDIUM"},
    {"file_category": "TEST_CODE", "allowed_in_73P": True, "deep_summary_by_default": True, "risk_label": "MEDIUM"},
    {"file_category": "CONFIG", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "HIGH"},
    {"file_category": "DOCS", "allowed_in_73P": True, "deep_summary_by_default": True, "risk_label": "LOW"},
    {"file_category": "SCRIPT", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "HIGH"},
    {"file_category": "MIGRATION", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "HIGH"},
    {"file_category": "SCHEMA", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "HIGH"},
    {"file_category": "LOCKFILE", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "LOW"},
    {"file_category": "DEPENDENCY_MANIFEST", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "HIGH"},
    {"file_category": "CI_PIPELINE", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "HIGH"},
    {"file_category": "AGENT_INSTRUCTION", "allowed_in_73P": True, "deep_summary_by_default": True, "risk_label": "HIGH"},
    {"file_category": "SECRET_OR_CREDENTIAL_LIKE", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "HIGH"},
    {"file_category": "GENERATED_OR_VENDOR", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "LOW"},
    {"file_category": "UNKNOWN", "allowed_in_73P": True, "deep_summary_by_default": False, "risk_label": "UNKNOWN"},
)


@dataclass(frozen=True, slots=True)
class RepoUnderstandingRequest:
    raw_text: str
    repo_scope: str = "local_repo"
    requested_focus: str = "repo_overview"
    file_paths: tuple[str, ...] = ()
    run_code_requested: bool = False
    install_dependency_requested: bool = False
    repo_clone_requested: bool = False
    external_tool_requested: bool = False
    mcp_server_requested: bool = False
    persistent_index_requested: bool = False
    network_access_requested: bool = False
    security_certification_requested: bool = False
    correctness_claim_requested: bool = False
    large_repo_requested: bool = False
    multi_agent_requested: bool = False
    symbol_map_requested: bool = False
    dependency_map_requested: bool = False
    test_map_requested: bool = False
    risk_map_requested: bool = False
    docs_map_requested: bool = False
    source_event_ref: str | None = None
    user_id: str | None = None
    robot_id: str = "local_robot"
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class RepoUnderstandingPacket:
    packet_id: str
    packet_type: RepoUnderstandingPacketType
    repo_decision: RepoUnderstandingDecision
    repo_scope: str
    requested_focus: str
    file_categories: tuple[RepoFileCategory, ...]
    source_repo_references: tuple[str, ...]
    budget_class: RepoUnderstandingBudgetClass
    requires_budget_confirmation: bool
    requires_user_confirmation: bool
    local_files_only: bool
    code_execution_authorized: bool
    dependency_install_authorized: bool
    repo_clone_authorized: bool
    mcp_server_authorized: bool
    external_tool_authorized: bool
    network_access_authorized: bool
    persistent_index_authorized: bool
    security_certification_authorized: bool
    correctness_claim_authorized: bool
    raw_source_archive_authorized: bool
    recommended_output_shape: RepoUnderstandingOutputShape
    summary_claim_level: str
    uncertainty_required: bool
    next_questions: tuple[str, ...]
    blocked_reason: str | None
    future_stage_required: str | None
    created_at: str

    def __post_init__(self) -> None:
        if not self.local_files_only:
            raise ValueError("73P packets must be local-files-only.")
        for field_name in (
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
        ):
            if getattr(self, field_name):
                raise ValueError(f"73P cannot authorize {field_name}.")


def build_repo_understanding_packet(request: RepoUnderstandingRequest) -> RepoUnderstandingPacket:
    decision = classify_repo_understanding_request(request)
    budget_class = infer_repo_budget_class(request)

    return RepoUnderstandingPacket(
        packet_id=f"repo_understanding_{uuid4().hex}",
        packet_type=infer_repo_packet_type(request),
        repo_decision=decision,
        repo_scope=request.repo_scope.strip(),
        requested_focus=request.requested_focus.strip(),
        file_categories=tuple(infer_file_categories(list(request.file_paths))),
        source_repo_references=tuple(str(entry["source_id"]) for entry in SOURCE_REPO_REGISTER),
        budget_class=budget_class,
        requires_budget_confirmation=_requires_budget_confirmation(budget_class),
        requires_user_confirmation=_requires_user_confirmation(decision, budget_class),
        local_files_only=True,
        code_execution_authorized=False,
        dependency_install_authorized=False,
        repo_clone_authorized=False,
        mcp_server_authorized=False,
        external_tool_authorized=False,
        network_access_authorized=False,
        persistent_index_authorized=False,
        security_certification_authorized=False,
        correctness_claim_authorized=False,
        raw_source_archive_authorized=False,
        recommended_output_shape=_output_shape_for_decision(decision),
        summary_claim_level=_summary_claim_level(decision),
        uncertainty_required=True,
        next_questions=_next_questions_for_decision(decision, request),
        blocked_reason=_blocked_reason_for_decision(decision),
        future_stage_required=_future_stage_for_decision(decision),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def classify_repo_understanding_request(request: RepoUnderstandingRequest) -> RepoUnderstandingDecision:
    if request.run_code_requested or request.security_certification_requested or request.correctness_claim_requested:
        return "BLOCK_CODE_EXECUTION"
    if request.install_dependency_requested:
        return "BLOCK_DEPENDENCY_INSTALL"
    if request.repo_clone_requested:
        return "BLOCK_REPO_CLONE"
    if request.external_tool_requested or request.mcp_server_requested or request.network_access_requested:
        return "BLOCK_EXTERNAL_TOOL"
    if request.large_repo_requested or request.multi_agent_requested:
        return "REQUIRE_BUDGET_CONFIRMATION"
    if not request.repo_scope.strip() and not request.requested_focus.strip():
        return "ASK_CLARIFICATION"
    if request.symbol_map_requested:
        return "PREPARE_SYMBOL_MAP_PLAN"
    if request.dependency_map_requested:
        return "PREPARE_DEPENDENCY_MAP_PLAN"
    if request.test_map_requested:
        return "PREPARE_TEST_MAP_PACKET"
    if request.risk_map_requested:
        return "PREPARE_RISK_MAP_PACKET"
    if request.docs_map_requested:
        return "PREPARE_FILE_SCOPE_PACKET"
    if request.persistent_index_requested:
        return "DEFER_TO_FUTURE_INDEXER_STAGE"
    return "PREPARE_REPO_UNDERSTANDING_PACKET"


def infer_repo_packet_type(request: RepoUnderstandingRequest) -> RepoUnderstandingPacketType:
    decision = classify_repo_understanding_request(request)
    mapping: dict[RepoUnderstandingDecision, RepoUnderstandingPacketType] = {
        "BLOCK_CODE_EXECUTION": "BLOCKED_CODE_EXECUTION_REQUEST",
        "BLOCK_DEPENDENCY_INSTALL": "BLOCKED_DEPENDENCY_INSTALL_REQUEST",
        "BLOCK_REPO_CLONE": "BLOCKED_REPO_CLONE_REQUEST",
        "BLOCK_EXTERNAL_TOOL": "BLOCKED_EXTERNAL_TOOL_REQUEST",
        "PREPARE_SYMBOL_MAP_PLAN": "SYMBOL_MAP_PLAN",
        "PREPARE_DEPENDENCY_MAP_PLAN": "DEPENDENCY_MAP_PLAN",
        "PREPARE_TEST_MAP_PACKET": "TEST_MAP_PACKET",
        "PREPARE_RISK_MAP_PACKET": "RISK_MAP_PACKET",
        "PREPARE_FILE_SCOPE_PACKET": "FILE_SCOPE_PACKET",
        "PREPARE_REPO_UNDERSTANDING_PACKET": "REPO_OVERVIEW_PACKET",
        "DEFER_TO_FUTURE_INDEXER_STAGE": "FACTORY_HANDOFF_PACKET",
        "REQUIRE_BUDGET_CONFIRMATION": "FACTORY_HANDOFF_PACKET",
        "ASK_CLARIFICATION": "FILE_SCOPE_PACKET",
    }
    return mapping[decision]


def infer_file_categories(file_paths: list[str]) -> list[RepoFileCategory]:
    if not file_paths:
        return ["UNKNOWN"]

    categories: list[RepoFileCategory] = []
    for path in file_paths:
        categories.append(_category_for_path(path))
    return _dedupe_categories(categories)


def infer_repo_budget_class(request: RepoUnderstandingRequest) -> RepoUnderstandingBudgetClass:
    if request.persistent_index_requested:
        return "REPO_INDEXER_DEFERRED"
    if request.multi_agent_requested:
        return "REPO_UNDERSTANDING_MULTI_AGENT_DEFERRED"
    if request.large_repo_requested:
        return "REPO_UNDERSTANDING_LARGE"
    if any(
        (
            request.symbol_map_requested,
            request.dependency_map_requested,
            request.test_map_requested,
            request.risk_map_requested,
            request.docs_map_requested,
        )
    ):
        return "REPO_UNDERSTANDING_STANDARD"
    return "REPO_UNDERSTANDING_LIGHT"


def _category_for_path(path: str) -> RepoFileCategory:
    normalized = path.replace("\\", "/").lower().strip()
    name = normalized.rsplit("/", 1)[-1]

    if _is_secret_like(normalized):
        return "SECRET_OR_CREDENTIAL_LIKE"
    if normalized.startswith(("node_modules/", "vendor/", "dist/", "build/")) or "/node_modules/" in normalized or "/vendor/" in normalized:
        return "GENERATED_OR_VENDOR"
    if normalized.startswith(("tests/", "test/")) or name.startswith("test_") or ".test." in name:
        return "TEST_CODE"
    if name in {"agents.md", "claude.md", "skill.md"}:
        return "AGENT_INSTRUCTION"
    if normalized.startswith(".github/workflows/") or name == ".gitlab-ci.yml":
        return "CI_PIPELINE"
    if normalized.startswith("docs/") or name in {"readme.md", "readme"} or name.endswith(".md"):
        return "DOCS"
    if name in {"package-lock.json", "poetry.lock", "pnpm-lock.yaml", "yarn.lock"}:
        return "LOCKFILE"
    if name in {"package.json", "pyproject.toml", "cargo.toml", "go.mod"} or name.startswith("requirements") and name.endswith(".txt"):
        return "DEPENDENCY_MANIFEST"
    if normalized.startswith(("migrations/", "alembic/")) or name.endswith(".sql"):
        return "MIGRATION"
    if name.startswith("schema.") or name == "models.py":
        return "SCHEMA"
    if normalized.startswith("scripts/") or name.endswith((".sh", ".bash", ".zsh")):
        return "SCRIPT"
    if name in {".env.example", "config.toml", "settings.py"} or normalized.startswith(("config/", ".config/")):
        return "CONFIG"
    if name.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
        return "APP_CODE"
    return "UNKNOWN"


def _is_secret_like(normalized_path: str) -> bool:
    name = normalized_path.rsplit("/", 1)[-1]
    if name == ".env" or name.endswith(".pem") or name in {"id_rsa", "id_dsa", "id_ed25519"}:
        return True
    return any(marker in normalized_path for marker in ("secret", "credential", "token"))


def _requires_budget_confirmation(budget_class: RepoUnderstandingBudgetClass) -> bool:
    return budget_class in {
        "REPO_UNDERSTANDING_LARGE",
        "REPO_UNDERSTANDING_MULTI_AGENT_DEFERRED",
        "REPO_INDEXER_DEFERRED",
    }


def _requires_user_confirmation(
    decision: RepoUnderstandingDecision,
    budget_class: RepoUnderstandingBudgetClass,
) -> bool:
    return decision.startswith("BLOCK_") or _requires_budget_confirmation(budget_class)


def _output_shape_for_decision(decision: RepoUnderstandingDecision) -> RepoUnderstandingOutputShape:
    if decision.startswith("BLOCK_"):
        return "BLOCKED_NOTICE"
    mapping: dict[RepoUnderstandingDecision, RepoUnderstandingOutputShape] = {
        "ASK_CLARIFICATION": "QUESTION_LIST",
        "REQUIRE_BUDGET_CONFIRMATION": "QUESTION_LIST",
        "PREPARE_SYMBOL_MAP_PLAN": "SYMBOL_MAP_PLAN_OUTPUT",
        "PREPARE_DEPENDENCY_MAP_PLAN": "DEPENDENCY_MAP_PLAN_OUTPUT",
        "PREPARE_TEST_MAP_PACKET": "TEST_MAP",
        "PREPARE_RISK_MAP_PACKET": "RISK_MAP",
        "PREPARE_FILE_SCOPE_PACKET": "FILE_SCOPE_PLAN",
        "PREPARE_REPO_UNDERSTANDING_PACKET": "REPO_MAP",
        "DEFER_TO_FUTURE_INDEXER_STAGE": "FACTORY_HANDOFF",
        "BLOCK_CODE_EXECUTION": "BLOCKED_NOTICE",
        "BLOCK_DEPENDENCY_INSTALL": "BLOCKED_NOTICE",
        "BLOCK_REPO_CLONE": "BLOCKED_NOTICE",
        "BLOCK_EXTERNAL_TOOL": "BLOCKED_NOTICE",
    }
    return mapping[decision]


def _summary_claim_level(decision: RepoUnderstandingDecision) -> str:
    if decision.startswith("BLOCK_"):
        return "blocked_notice_only"
    if decision == "DEFER_TO_FUTURE_INDEXER_STAGE":
        return "handoff_plan_only_no_index"
    return "map_or_plan_only_no_correctness_claim"


def _next_questions_for_decision(
    decision: RepoUnderstandingDecision,
    request: RepoUnderstandingRequest,
) -> tuple[str, ...]:
    if decision == "ASK_CLARIFICATION":
        return ("Which local repo path, file family, or feature area should the packet map first?",)
    if decision == "REQUIRE_BUDGET_CONFIRMATION":
        return ("Should this large or multi-agent repo-understanding request proceed under an explicit budget cap?",)
    if decision == "DEFER_TO_FUTURE_INDEXER_STAGE":
        return ("Is a future approved indexer/MCP stage required, or is a review-only plan enough?",)
    if decision.startswith("BLOCK_"):
        return ("Can the request be reframed as local review-only packet preparation?",)
    if request.file_paths:
        return ("Which flagged files should receive deeper read-only inspection next?",)
    return ("Which subsystem, file family, or risk area should be inspected next?",)


def _blocked_reason_for_decision(decision: RepoUnderstandingDecision) -> str | None:
    reasons: dict[RepoUnderstandingDecision, str] = {
        "BLOCK_CODE_EXECUTION": "73P does not execute code or certify safety/correctness.",
        "BLOCK_DEPENDENCY_INSTALL": "73P does not install dependencies or external repo-understanding tools.",
        "BLOCK_REPO_CLONE": "73P does not clone repositories or acquire hidden sources.",
        "BLOCK_EXTERNAL_TOOL": "73P documents external tools as reference-only and does not start MCP, network, or external runtimes.",
    }
    return reasons.get(decision)


def _future_stage_for_decision(decision: RepoUnderstandingDecision) -> str | None:
    if decision == "DEFER_TO_FUTURE_INDEXER_STAGE":
        return "future_indexer_stage_if_full_graph_needed"
    if decision == "BLOCK_EXTERNAL_TOOL":
        return "future_explicit_external_tool_or_mcp_stage"
    if decision == "BLOCK_DEPENDENCY_INSTALL":
        return "future_explicit_dependency_install_authority"
    if decision == "BLOCK_REPO_CLONE":
        return "future_explicit_repo_acquisition_authority"
    if decision == "BLOCK_CODE_EXECUTION":
        return "future_explicit_execution_or_validation_stage"
    return None


def _dedupe_categories(categories: list[RepoFileCategory]) -> list[RepoFileCategory]:
    deduped: list[RepoFileCategory] = []
    for category in categories:
        if category not in deduped:
            deduped.append(category)
    return deduped
