from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import importlib.util
import json
import os
import sys


HERMES_RUNTIME_BOOTSTRAP_STAGE = "129P"
ROADMAP_CLOSED_THROUGH = "202P"
NEXT_STAGE = "203P"
NEXT_STAGE_LABEL = "203P+ remains unauthorized."
DEFAULT_RUNTIME_MODE = "local-dev"
DEFAULT_ROBOT_ID = "roboticxs-dev"
DEFAULT_OWNER_ID = "local-owner"
DEFAULT_OWNER_DISPLAY_NAME = "Local Owner"
DEFAULT_LOCAL_STATE_DIR = ".roboticxs_state"
DEFAULT_GENERATED_AT = "2026-06-21T00:00:00Z"
FEATURE_MODULES = (
    ("runnable_telegram_robot_mvp", "app.runnable_telegram_robot_mvp", False),
    ("daily_brief_what_did_i_miss", "app.daily_brief_what_did_i_miss", False),
    ("meeting_brief_demo_flow", "app.meeting_brief_demo_flow", False),
    ("document_review_demo_flow", "app.document_review_demo_flow", False),
    ("google_calendar_readonly_connector", "app.google_calendar_readonly_connector", False),
    ("calendar_context_scan", "app.calendar_context_scan", False),
    ("proactive_meeting_suggestion", "app.proactive_meeting_suggestion", False),
    ("suggested_meeting_brief_request", "app.suggested_meeting_brief_request", False),
    ("today_command", "app.today_command", False),
    ("open_loops_command", "app.open_loops_command", False),
    ("meeting_prep_pack", "app.meeting_prep_pack", False),
    ("meeting_prep_pack_v1", "app.meeting_prep_pack_v1", False),
    ("brief_memory_proposal", "app.brief_memory_proposal", False),
    ("brief_memory_approval", "app.brief_memory_approval", False),
    ("personal_admin_inbox", "app.personal_admin_inbox", False),
    ("inbox_item_decision", "app.inbox_item_decision", False),
    ("roboticxs_loop_handoff", "app.roboticxs_loop_handoff", False),
    ("roboticxs_loop_cli", "app.roboticxs_loop_cli", False),
    ("runtime_doctor", "app.runtime_doctor", False),
    ("telegram_demo_loop", "app.telegram_demo_loop", False),
    ("telegram_document_intake_stub", "app.telegram_document_intake_stub", False),
    ("customer_mvp_baseline", "app.customer_mvp_baseline", False),
    ("customer_mvp_demo_pack_v1", "app.customer_mvp_demo_pack_v1", False),
    ("live_connector_readiness_check", "app.live_connector_readiness_check", False),
    ("calendar_context_binding_v1", "app.calendar_context_binding_v1", False),
    ("gmail_context_binding_v1", "app.gmail_context_binding_v1", False),
    ("source_trace_receipts", "app.source_trace_receipts", False),
    ("approved_gmail_draft_creation", "app.approved_gmail_draft_creation", False),
    ("memory_source_forget_receipts", "app.memory_source_forget_receipts", False),
    ("usage_cost_ledger", "app.usage_cost_ledger", False),
    ("skill_manifest_runtime_gates", "app.skill_manifest_runtime_gates", False),
    ("controlled_live_pilot_baseline", "app.controlled_live_pilot_baseline", False),
    ("premium_telegram_ux_shell", "app.premium_telegram_ux_shell", False),
    ("fast_path_cache", "app.fast_path_cache", False),
    ("smart_context_ranking", "app.smart_context_ranking", False),
    ("proactive_priority_engine", "app.proactive_priority_engine", False),
    ("draft_quality_engine", "app.draft_quality_engine", False),
    ("memory_intelligence", "app.memory_intelligence", False),
    ("document_to_action_flow", "app.document_to_action_flow", False),
    ("cost_aware_model_routing_v1", "app.cost_aware_model_routing_v1", False),
    ("customer_pilot_readiness_pack", "app.customer_pilot_readiness_pack", False),
    ("customer_pilot_audit_gate", "app.customer_pilot_audit_gate", False),
    ("live_smoke_script", "app.live_smoke_script", False),
    ("founder_daily_use_loop", "app.founder_daily_use_loop", False),
    ("setup_capability_status_component", "app.setup_capability_status_component", False),
    ("calendar_backed_today_prep", "app.calendar_backed_today_prep", False),
    ("gmail_readonly_context_scan", "app.gmail_readonly_context_scan", False),
    ("gmail_thread_drilldown", "app.gmail_thread_drilldown", False),
    ("context_scan_proposed_memory", "app.context_scan_proposed_memory", False),
    ("memory_store", "app.memory_store", False),
    ("document_review_pack", "app.document_review_pack", False),
    ("document_review_pack_v1", "app.document_review_pack_v1", False),
    ("action_boundary_confirmation_gate", "app.action_boundary_confirmation_gate", False),
    ("token_usage_cost_meter", "app.token_usage_cost_meter", False),
    ("model_router_runtime", "app.model_router_runtime", False),
    ("proactive_suggestion_loop", "app.proactive_suggestion_loop", False),
    ("suggestion_inbox", "app.suggestion_inbox", False),
    ("suggestion_decision_flow", "app.suggestion_decision_flow", False),
    ("action_draft_queue", "app.action_draft_queue", False),
    ("user_confirmation_runtime", "app.user_confirmation_runtime", False),
    ("approved_output_export", "app.approved_output_export", False),
    ("memory_approval_telegram_flow", "app.memory_approval_telegram_flow", False),
    ("cross_source_daily_brief", "app.cross_source_daily_brief", False),
    ("demo_result_delivery_surface", "app.demo_result_delivery_surface", False),
    ("skill_pack_activation_surface", "app.skill_pack_activation_surface", False),
    ("memory_center_writeback", "app.memory_center_writeback", False),
    ("telegram_memory_center_commands", "app.telegram_memory_center_commands", False),
    ("proactive_opportunity_detection", "app.proactive_opportunity_detection", False),
    ("proactive_telegram_suggestion", "app.proactive_telegram_suggestion", False),
    ("proactive_suggestion_adapter", "app.proactive_suggestion_adapter", False),
    ("proactive_delegation_adapter", "app.proactive_delegation_adapter", False),
    ("proactive_execution_skeleton", "app.proactive_execution_skeleton", False),
)
REQUIRED_BOOTSTRAP_MODULES = (
    ("hermes_runtime_bootstrap", "app.hermes_runtime_bootstrap", True),
    ("hermes_os_contract", "app.hermes_os_contract", True),
)


@dataclass(frozen=True, slots=True)
class HermesRuntimeFeatureFlagSet:
    telegram_enabled: bool
    connectors_enabled: bool
    model_calls_enabled: bool
    tools_enabled: bool
    workers_enabled: bool
    external_writes_enabled: bool
    memory_mutation_enabled: bool


@dataclass(frozen=True, slots=True)
class HermesRuntimeConfig:
    runtime_mode: str
    robot_id: str
    owner_id: str
    owner_display_name: str
    local_state_dir: str
    feature_flags: HermesRuntimeFeatureFlagSet


@dataclass(frozen=True, slots=True)
class HermesRuntimeModuleCheck:
    feature_name: str
    module_path: str
    required: bool
    available: bool
    reason: str


@dataclass(frozen=True, slots=True)
class HermesRuntimeBootstrapStatus:
    runtime_online: bool
    runtime_mode: str
    robot_id: str
    owner_id: str
    owner_display_name: str
    roadmap_closed_through: str
    next_stage_authorized: bool
    next_stage: str
    telegram_enabled: bool
    connectors_enabled: bool
    model_calls_enabled: bool
    tools_enabled: bool
    workers_enabled: bool
    external_writes_enabled: bool
    memory_mutation_enabled: bool
    local_state_dir: str
    available_local_features: tuple[str, ...]
    unavailable_features: tuple[str, ...]
    module_check_results: tuple[HermesRuntimeModuleCheck, ...]
    generated_at: str


@dataclass(frozen=True, slots=True)
class HermesRuntimeBootstrapReport:
    status: HermesRuntimeBootstrapStatus
    rendered_text: str


def _env_bool(name: str, default: bool = False, env: dict[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    raw = source.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_hermes_runtime_config_from_env(env: dict[str, str] | None = None) -> HermesRuntimeConfig:
    source = os.environ if env is None else env
    return HermesRuntimeConfig(
        runtime_mode=source.get("ROBOTICXS_RUNTIME_MODE", DEFAULT_RUNTIME_MODE),
        robot_id=source.get("ROBOTICXS_ROBOT_ID", DEFAULT_ROBOT_ID),
        owner_id=source.get("ROBOTICXS_OWNER_ID", DEFAULT_OWNER_ID),
        owner_display_name=source.get("ROBOTICXS_OWNER_DISPLAY_NAME", DEFAULT_OWNER_DISPLAY_NAME),
        local_state_dir=source.get("ROBOTICXS_LOCAL_STATE_DIR", DEFAULT_LOCAL_STATE_DIR),
        feature_flags=HermesRuntimeFeatureFlagSet(
            telegram_enabled=_env_bool("ROBOTICXS_ENABLE_TELEGRAM", env=source),
            connectors_enabled=_env_bool("ROBOTICXS_ENABLE_CONNECTORS", env=source),
            model_calls_enabled=_env_bool("ROBOTICXS_ENABLE_MODEL_CALLS", env=source),
            tools_enabled=_env_bool("ROBOTICXS_ENABLE_TOOLS", env=source),
            workers_enabled=_env_bool("ROBOTICXS_ENABLE_WORKERS", env=source),
            external_writes_enabled=False,
            memory_mutation_enabled=False,
        ),
    )


def validate_hermes_runtime_config(config: HermesRuntimeConfig) -> HermesRuntimeConfig:
    if not config.runtime_mode:
        raise ValueError("rejected_missing_runtime_mode")
    if not config.robot_id:
        raise ValueError("rejected_missing_robot_id")
    if not config.owner_id:
        raise ValueError("rejected_missing_owner_id")
    if not config.owner_display_name:
        raise ValueError("rejected_missing_owner_display_name")
    if not config.local_state_dir:
        raise ValueError("rejected_missing_local_state_dir")
    if config.feature_flags.telegram_enabled:
        raise ValueError("rejected_telegram_enabled_in_129p")
    if config.feature_flags.connectors_enabled:
        raise ValueError("rejected_connectors_enabled_in_129p")
    if config.feature_flags.model_calls_enabled:
        raise ValueError("rejected_model_calls_enabled_in_129p")
    if config.feature_flags.tools_enabled:
        raise ValueError("rejected_tools_enabled_in_129p")
    if config.feature_flags.workers_enabled:
        raise ValueError("rejected_workers_enabled_in_129p")
    return config


def _check_module(feature_name: str, module_path: str, *, required: bool) -> HermesRuntimeModuleCheck:
    spec = importlib.util.find_spec(module_path)
    if spec is None:
        return HermesRuntimeModuleCheck(
            feature_name=feature_name,
            module_path=module_path,
            required=required,
            available=False,
            reason="module_not_found",
        )
    return HermesRuntimeModuleCheck(
        feature_name=feature_name,
        module_path=module_path,
        required=required,
        available=True,
        reason="import_spec_found",
    )


def build_hermes_runtime_bootstrap_status(
    *,
    config: HermesRuntimeConfig,
    generated_at: str = DEFAULT_GENERATED_AT,
    module_candidates: tuple[tuple[str, str, bool], ...] | None = None,
) -> HermesRuntimeBootstrapStatus:
    validated = validate_hermes_runtime_config(config)
    candidates = REQUIRED_BOOTSTRAP_MODULES + FEATURE_MODULES if module_candidates is None else module_candidates
    checks = tuple(_check_module(feature_name, module_path, required=required) for feature_name, module_path, required in candidates)
    missing_required = tuple(check.feature_name for check in checks if check.required and not check.available)
    if missing_required:
        raise ValueError(f"rejected_missing_required_module:{','.join(missing_required)}")
    available = tuple(check.feature_name for check in checks if check.available and not check.required)
    unavailable = tuple(check.feature_name for check in checks if not check.available and not check.required)
    return HermesRuntimeBootstrapStatus(
        runtime_online=True,
        runtime_mode=validated.runtime_mode,
        robot_id=validated.robot_id,
        owner_id=validated.owner_id,
        owner_display_name=validated.owner_display_name,
        roadmap_closed_through=ROADMAP_CLOSED_THROUGH,
        next_stage_authorized=False,
        next_stage=NEXT_STAGE,
        telegram_enabled=validated.feature_flags.telegram_enabled,
        connectors_enabled=validated.feature_flags.connectors_enabled,
        model_calls_enabled=validated.feature_flags.model_calls_enabled,
        tools_enabled=validated.feature_flags.tools_enabled,
        workers_enabled=validated.feature_flags.workers_enabled,
        external_writes_enabled=validated.feature_flags.external_writes_enabled,
        memory_mutation_enabled=validated.feature_flags.memory_mutation_enabled,
        local_state_dir=validated.local_state_dir,
        available_local_features=available,
        unavailable_features=unavailable,
        module_check_results=checks,
        generated_at=generated_at,
    )


def render_hermes_runtime_bootstrap_report(
    *,
    status: HermesRuntimeBootstrapStatus,
    output_format: str = "text",
) -> HermesRuntimeBootstrapReport:
    if output_format not in {"text", "json"}:
        raise ValueError("rejected_invalid_output_format")
    if output_format == "json":
        rendered_text = json.dumps(
            {
                **asdict(status),
                "module_check_results": [asdict(check) for check in status.module_check_results],
            },
            sort_keys=True,
            indent=2,
        )
    else:
        lines = [
            "Hermes Runtime: online",
            f"Robot: {status.robot_id}",
            f"Owner: {status.owner_id}",
            f"Owner Display Name: {status.owner_display_name}",
            f"Mode: {status.runtime_mode}",
            f"Roadmap: 95P-202P CLOSED_COMMITTED",
            f"Roadmap Closed Through: {status.roadmap_closed_through}",
            f"Telegram: {'enabled' if status.telegram_enabled else 'disabled'}",
            f"Connectors: {'enabled' if status.connectors_enabled else 'disabled'}",
            f"LLM/model calls: {'enabled' if status.model_calls_enabled else 'disabled'}",
            f"Tools: {'enabled' if status.tools_enabled else 'disabled'}",
            f"Workers: {'enabled' if status.workers_enabled else 'disabled'}",
            f"External writes: {'enabled' if status.external_writes_enabled else 'disabled'}",
            f"Memory Center: {'mutation enabled' if status.memory_mutation_enabled else 'local/read-only bootstrap check'}",
            "Telegram Memory Center Commands: available if Telegram env is configured",
            f"Local state dir: {status.local_state_dir}",
            "Available local features:",
        ]
        lines.extend(f"- {feature}" for feature in status.available_local_features)
        lines.append("Unavailable features:")
        if status.unavailable_features:
            lines.extend(f"- {feature}" for feature in status.unavailable_features)
        else:
            lines.append("- none")
        lines.append("Module checks:")
        lines.extend(
            f"- {check.feature_name}: {'available' if check.available else 'unavailable'} ({check.reason})"
            for check in status.module_check_results
        )
        lines.extend(
            [
                "Daily Brief: available if local records exist",
                "Telegram Robot MVP: available if env is configured",
                "Meeting Brief Demo: available if local records exist",
                "Document Review Demo: available if local records exist",
                "Google Calendar Read-Only Connector: available for local manual smoke runs",
                "Calendar Context Scan: available for local manual smoke runs",
                "Proactive Meeting Suggestion: available for owner-requested Telegram replies only",
                "Suggested Meeting Brief Request: available for owner-requested Telegram replies only",
                "Today Command: available for owner-requested Telegram replies only",
                "Today / Brief Product Flow: available for customer-facing daily and brief views only",
                "Setup & Capability Status: available for customer-facing /status readiness only",
                "Open Loops Command: available for owner-requested Telegram replies only",
                "Meeting Prep Pack: available for owner-requested Telegram replies only",
                "Meeting Prep Pack v1: available for owner-requested read-only meeting prep only",
                "Meeting Prep Pack Product Flow: available for customer-facing /prep output only",
                "Brief Memory Proposals: available as owner-reviewed candidates only",
                "Brief Memory Approval: available as local owner decision receipts only",
                "Memory Review Flow: available for customer-facing pending memory review and local receipts only",
                "First-Run Onboarding: available for customer-facing /start orientation only",
                "Telegram Demo Loop: available for local deterministic product demos only",
                "Telegram Document Intake Stub: available for draft-only document metadata replies only",
                "Telegram Product Copy Consolidation: available for shared customer-facing copy only",
                "Customer MVP Baseline: available for local customer MVP verification only",
                "Customer MVP Demo Pack v1: available for local end-to-end customer demo only",
                "Live Connector Readiness Check: available for owner-requested read-only readiness only",
                "Calendar Context Binding v1: available for owner-requested Calendar source trace only",
                "Gmail Context Binding v1: available for owner-requested Gmail source trace only",
                "Source Trace Receipts: available for owner-requested unified source receipts only",
                "Approved Gmail Draft Creation: available for owner-approved Gmail draft creation only",
                "Memory Source & Forget Receipts: available for local memory provenance and forget/edit receipts only",
                "Usage & Cost Ledger: available for local estimated usage reporting only",
                "Skill Manifest Runtime Gates: available for local command skill boundaries only",
                "Controlled Live Pilot Baseline: available for owner-requested controlled pilot receipts only",
                "Premium Telegram UX Shell: available for grouped customer-facing Telegram command surfaces only",
                "Fast Path Cache: available for local TTL cache hits on quick commands only",
                "Smart Context Ranking: available for read-only ranked context sections only",
                "Proactive Priority Engine: available for local suggestion priority labels only",
                "Draft Quality Engine: available for local draft review metadata only",
                "Memory Intelligence: available for local read-only memory findings only",
                "Document-to-Action Flow: available for local document action suggestions only",
                "Cost-Aware Model Routing v1: available for local mode and cost receipts only",
                "Customer Pilot Readiness Pack: available for local pilot setup packages only",
                "Customer Pilot Audit Gate: available for local pilot audit reports only",
                "Live Smoke Script: available for local manual smoke guides only",
                "Founder Daily Use Loop: available for local morning operating cards only",
                "Setup Capability Status Component: available for shared customer-facing setup copy only",
                "Calendar-Backed Today / Prep: available for read-only Calendar product context only",
                "Gmail Read-Only Context Scan: available for read-only Gmail context signals only",
                "Gmail Thread Drilldown: available for owner-requested read-only thread metadata only",
                "Context Scan Proposed Memories: available for local pending memory candidates only",
                "Memory Store: available for local approved memory items only",
                "Document Review Pack: available for local draft document review only",
                "Document Review Pack v1: available for local injected-text document review only",
                "Action Boundary Confirmation Gate: available for local action classification only",
                "Token Usage + Cost Meter: available for local estimated /usage reporting only",
                "Model Router Runtime: available for local mode selection only",
                "Proactive Suggestion Loop: available for local suggestions only",
                "Suggestion Inbox: available for owner-requested local suggestion review only",
                "Suggestion Decision Flow: available for owner-requested local decision receipts only",
                "Action Draft Queue: available for owner-requested local draft approval candidates only",
                "User Confirmation Runtime: available for owner-requested local confirmation receipts only",
                "Approved Output Export: available for owner-requested local export payloads only",
                "Memory Approval Telegram Flow: available for owner-requested local memory approval receipts only",
                "Cross-Source Daily Brief: available for owner-requested read-only daily brief only",
                "Personal Admin Inbox: available for owner-requested read-only inbox visibility only",
                "Inbox Item Decisions: available as local owner decision receipts only",
                "Task Inbox Flow: available for customer-facing task inbox visibility and local receipts only",
                "Factory Loop Handoff Harness: available for local non-authority loop evidence only",
                "Runtime Doctor: available for local read-only readiness diagnostics only",
                "Telegram Product Shell: available for customer-facing menu and setup status only",
                f"Next authorized stage: {NEXT_STAGE_LABEL}",
                f"Generated At: {status.generated_at}",
            ]
        )
        rendered_text = "\n".join(lines)
    return HermesRuntimeBootstrapReport(status=status, rendered_text=rendered_text)


def run_hermes_runtime_bootstrap(
    *,
    env: dict[str, str] | None = None,
    output_format: str = "text",
    generated_at: str = DEFAULT_GENERATED_AT,
    module_candidates: tuple[tuple[str, str, bool], ...] | None = None,
) -> HermesRuntimeBootstrapReport:
    config = load_hermes_runtime_config_from_env(env=env)
    status = build_hermes_runtime_bootstrap_status(
        config=config,
        generated_at=generated_at,
        module_candidates=module_candidates,
    )
    return render_hermes_runtime_bootstrap_report(status=status, output_format=output_format)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.hermes_runtime_bootstrap")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--text", action="store_true", dest="as_text")
    parser.add_argument("--check", action="store_true", dest="check_only")
    args = parser.parse_args(argv)
    output_format = "json" if args.as_json and not args.as_text else "text"
    try:
        report = run_hermes_runtime_bootstrap(output_format=output_format)
    except ValueError as exc:
        print(f"Hermes Runtime: offline\nReason: {exc}", file=sys.stderr)
        return 1
    print(report.rendered_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
