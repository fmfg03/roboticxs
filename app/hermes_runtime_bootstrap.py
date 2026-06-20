from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import importlib.util
import json
import os
import sys


HERMES_RUNTIME_BOOTSTRAP_STAGE = "129P"
ROADMAP_CLOSED_THROUGH = "128P"
NEXT_STAGE = "130P"
NEXT_STAGE_LABEL = "130P Runnable Telegram Robot MVP is unauthorized."
DEFAULT_RUNTIME_MODE = "local-dev"
DEFAULT_ROBOT_ID = "roboticxs-dev"
DEFAULT_OWNER_ID = "local-owner"
DEFAULT_OWNER_DISPLAY_NAME = "Local Owner"
DEFAULT_LOCAL_STATE_DIR = ".roboticxs_state"
DEFAULT_GENERATED_AT = "2026-06-21T00:00:00Z"
FEATURE_MODULES = (
    ("daily_brief_what_did_i_miss", "app.daily_brief_what_did_i_miss", False),
    ("meeting_brief_demo_flow", "app.meeting_brief_demo_flow", False),
    ("document_review_demo_flow", "app.document_review_demo_flow", False),
    ("demo_result_delivery_surface", "app.demo_result_delivery_surface", False),
    ("skill_pack_activation_surface", "app.skill_pack_activation_surface", False),
    ("memory_center_writeback", "app.memory_center_writeback", False),
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
            f"Roadmap: 95P-128P CLOSED_COMMITTED",
            f"Roadmap Closed Through: {status.roadmap_closed_through}",
            f"Telegram: {'enabled' if status.telegram_enabled else 'disabled'}",
            f"Connectors: {'enabled' if status.connectors_enabled else 'disabled'}",
            f"LLM/model calls: {'enabled' if status.model_calls_enabled else 'disabled'}",
            f"Tools: {'enabled' if status.tools_enabled else 'disabled'}",
            f"Workers: {'enabled' if status.workers_enabled else 'disabled'}",
            f"External writes: {'enabled' if status.external_writes_enabled else 'disabled'}",
            f"Memory Center: {'mutation enabled' if status.memory_mutation_enabled else 'local/read-only bootstrap check'}",
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
                "Meeting Brief Demo: available if local records exist",
                "Document Review Demo: available if local records exist",
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
