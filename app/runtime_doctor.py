from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
import sys
import time
from pathlib import Path

from app.google_oauth_workspace import (
    DEFAULT_GOOGLE_OAUTH_CLIENT_SECRETS_FILE,
    DEFAULT_GOOGLE_OAUTH_TOKEN_FILE,
    GOOGLE_CALENDAR_READONLY_SCOPE,
    GOOGLE_GMAIL_METADATA_SCOPE,
    GOOGLE_GMAIL_READONLY_SCOPE,
    GOOGLE_OAUTH_WORKSPACE_STAGE,
)
from app.hermes_runtime_bootstrap import (
    DEFAULT_GENERATED_AT,
    ROADMAP_CLOSED_THROUGH,
    load_hermes_runtime_config_from_env,
)


RUNTIME_DOCTOR_STAGE = "149P"
NEXT_STAGE = "161P"
NEXT_STAGE_LABEL = "161P+ remains unauthorized."
DIRECT_GOOGLE_TOKEN_ENV_KEYS = (
    "ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN",
    "ROBOTICXS_GOOGLE_OAUTH_ACCESS_TOKEN",
)
ENV_CHECK_KEYS = (
    "ROBOTICXS_RUNTIME_MODE",
    "ROBOTICXS_ROBOT_ID",
    "ROBOTICXS_OWNER_ID",
    "ROBOTICXS_OWNER_DISPLAY_NAME",
    "ROBOTICXS_LOCAL_STATE_DIR",
    "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE",
    "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE",
    "ROBOTICXS_GOOGLE_CALENDAR_ID",
    "ROBOTICXS_GOOGLE_CALENDAR_TIMEZONE",
    *DIRECT_GOOGLE_TOKEN_ENV_KEYS,
)
SECRETISH_ENV_KEYS = frozenset(DIRECT_GOOGLE_TOKEN_ENV_KEYS)
NO_AUTHORITY_FLAGS = (
    "calendar_writes",
    "gmail_writes",
    "telegram_live_sends",
    "connector_activation",
    "oauth_url_generation",
    "oauth_token_exchange",
    "oauth_token_refresh",
    "model_calls",
    "tool_execution",
    "workers",
    "memory_center_mutation",
    "persistence",
    "scheduler",
    "billing",
    "deployment",
    "push_merge_pr",
)


@dataclass(frozen=True, slots=True)
class RuntimeDoctorEnvCheck:
    name: str
    status: str
    reason: str


@dataclass(frozen=True, slots=True)
class RuntimeDoctorPathCheck:
    name: str
    path: str
    exists: bool
    readable: bool
    json_valid: bool
    shape_status: str
    reason: str


@dataclass(frozen=True, slots=True)
class RuntimeDoctorServiceReadiness:
    service: str
    ready: bool
    reason: str
    required_scopes: tuple[str, ...]
    available_scopes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeDoctorBoundaryStatus:
    calendar_writes: bool
    gmail_writes: bool
    telegram_live_sends: bool
    connector_activation: bool
    oauth_url_generation: bool
    oauth_token_exchange: bool
    oauth_token_refresh: bool
    model_calls: bool
    tool_execution: bool
    workers: bool
    memory_center_mutation: bool
    persistence: bool
    scheduler: bool
    billing: bool
    deployment: bool
    push_merge_pr: bool


@dataclass(frozen=True, slots=True)
class RuntimeDoctorStatus:
    stage: str
    runtime_online: bool
    runtime_mode: str
    robot_id: str
    owner_id: str
    roadmap_closed_through: str
    next_stage_authorized: bool
    next_stage: str
    env_checks: tuple[RuntimeDoctorEnvCheck, ...]
    path_checks: tuple[RuntimeDoctorPathCheck, ...]
    service_readiness: tuple[RuntimeDoctorServiceReadiness, ...]
    boundary_status: RuntimeDoctorBoundaryStatus
    overall_status: str
    generated_at: str


@dataclass(frozen=True, slots=True)
class RuntimeDoctorReport:
    status: RuntimeDoctorStatus
    rendered_text: str


def _configured_env_status(name: str, source: dict[str, str]) -> RuntimeDoctorEnvCheck:
    value = source.get(name, "")
    if not value.strip():
        return RuntimeDoctorEnvCheck(name=name, status="missing", reason="env_not_configured")
    if name in SECRETISH_ENV_KEYS:
        return RuntimeDoctorEnvCheck(name=name, status="configured_redacted", reason="secret_value_present_but_not_rendered")
    return RuntimeDoctorEnvCheck(name=name, status="configured", reason="value_present")


def _resolve_path(source: dict[str, str], env_key: str, default_path: str) -> str:
    configured = source.get(env_key, "").strip()
    return configured or default_path


def _read_json_shape(path: Path) -> tuple[bool, dict | None, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, None, "file_missing"
    except PermissionError:
        return False, None, "file_not_readable"
    except OSError:
        return False, None, "file_not_readable"
    except json.JSONDecodeError:
        return False, None, "invalid_json"
    if not isinstance(payload, dict):
        return False, None, "json_root_not_object"
    return True, payload, "json_object"


def _text_present(payload: dict, key: str) -> bool:
    value = payload.get(key)
    return isinstance(value, str) and bool(value.strip())


def _tuple_scopes(payload: dict | None) -> tuple[str, ...]:
    if payload is None:
        return ()
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        return ()
    return tuple(scope.strip() for scope in scopes if isinstance(scope, str) and scope.strip())


def _check_oauth_client_file(path: str) -> RuntimeDoctorPathCheck:
    candidate = Path(path)
    exists = candidate.exists()
    json_valid, payload, reason = _read_json_shape(candidate)
    if not exists:
        return RuntimeDoctorPathCheck("google_oauth_client_secrets", path, False, False, False, "missing", "client_secrets_file_missing")
    if not json_valid or payload is None:
        return RuntimeDoctorPathCheck("google_oauth_client_secrets", path, True, reason != "file_not_readable", False, "blocked", reason)
    installed = payload.get("installed")
    if not isinstance(installed, dict):
        return RuntimeDoctorPathCheck("google_oauth_client_secrets", path, True, True, True, "blocked", "rejected_google_oauth_client_must_be_installed_app")
    if not _text_present(installed, "client_id"):
        return RuntimeDoctorPathCheck("google_oauth_client_secrets", path, True, True, True, "blocked", "rejected_missing_google_oauth_client_id")
    redirect_uris = installed.get("redirect_uris")
    if not isinstance(redirect_uris, list) or not any(isinstance(uri, str) and uri.strip() for uri in redirect_uris):
        return RuntimeDoctorPathCheck("google_oauth_client_secrets", path, True, True, True, "warning", "google_oauth_redirect_uris_missing")
    return RuntimeDoctorPathCheck("google_oauth_client_secrets", path, True, True, True, "ready", "installed_app_client_shape_valid_secret_redacted")


def _check_oauth_token_file(path: str) -> RuntimeDoctorPathCheck:
    candidate = Path(path)
    exists = candidate.exists()
    json_valid, payload, reason = _read_json_shape(candidate)
    if not exists:
        return RuntimeDoctorPathCheck("google_workspace_token", path, False, False, False, "missing", "workspace_token_file_missing")
    if not json_valid or payload is None:
        return RuntimeDoctorPathCheck("google_workspace_token", path, True, reason != "file_not_readable", False, "blocked", reason)
    if payload.get("stage") != GOOGLE_OAUTH_WORKSPACE_STAGE:
        return RuntimeDoctorPathCheck("google_workspace_token", path, True, True, True, "blocked", "rejected_invalid_google_oauth_stage")
    if not _text_present(payload, "client_id"):
        return RuntimeDoctorPathCheck("google_workspace_token", path, True, True, True, "blocked", "rejected_missing_google_oauth_client_id")
    if not _text_present(payload, "access_token"):
        return RuntimeDoctorPathCheck("google_workspace_token", path, True, True, True, "blocked", "rejected_missing_google_oauth_access_token")
    if not _tuple_scopes(payload):
        return RuntimeDoctorPathCheck("google_workspace_token", path, True, True, True, "warning", "google_oauth_scopes_missing")
    expires_at = payload.get("expires_at")
    if isinstance(expires_at, int) and expires_at <= int(time.time()):
        return RuntimeDoctorPathCheck("google_workspace_token", path, True, True, True, "warning", "google_oauth_token_expired_no_refresh_attempted")
    return RuntimeDoctorPathCheck("google_workspace_token", path, True, True, True, "ready", "workspace_token_shape_valid_tokens_redacted")


def _build_service_readiness(*, token_payload: dict | None, direct_token_configured: bool) -> tuple[RuntimeDoctorServiceReadiness, ...]:
    available_scopes = _tuple_scopes(token_payload)
    oauth_ready = token_payload is not None and bool(available_scopes)
    calendar_ready = direct_token_configured or GOOGLE_CALENDAR_READONLY_SCOPE in available_scopes
    gmail_metadata_ready = GOOGLE_GMAIL_METADATA_SCOPE in available_scopes
    gmail_readonly_ready = GOOGLE_GMAIL_READONLY_SCOPE in available_scopes
    return (
        RuntimeDoctorServiceReadiness("oauth_workspace", oauth_ready, "token_scope_shape_present" if oauth_ready else "workspace_token_scope_shape_missing", (), available_scopes),
        RuntimeDoctorServiceReadiness("calendar_readonly", calendar_ready, "direct_token_configured_redacted" if direct_token_configured else "calendar_readonly_scope_present" if calendar_ready else "calendar_readonly_scope_missing", (GOOGLE_CALENDAR_READONLY_SCOPE,), available_scopes),
        RuntimeDoctorServiceReadiness("gmail_metadata", gmail_metadata_ready, "gmail_metadata_scope_present" if gmail_metadata_ready else "gmail_metadata_scope_missing", (GOOGLE_GMAIL_METADATA_SCOPE,), available_scopes),
        RuntimeDoctorServiceReadiness("gmail_readonly", gmail_readonly_ready, "gmail_readonly_scope_present" if gmail_readonly_ready else "gmail_readonly_scope_missing", (GOOGLE_GMAIL_READONLY_SCOPE,), available_scopes),
    )


def _build_boundary_status() -> RuntimeDoctorBoundaryStatus:
    return RuntimeDoctorBoundaryStatus(**{name: False for name in NO_AUTHORITY_FLAGS})


def _overall_status(path_checks: tuple[RuntimeDoctorPathCheck, ...], service_readiness: tuple[RuntimeDoctorServiceReadiness, ...]) -> str:
    if any(check.shape_status == "blocked" for check in path_checks):
        return "blocked"
    if any(check.shape_status in {"missing", "warning"} for check in path_checks):
        return "warning"
    if not any(service.ready for service in service_readiness):
        return "warning"
    return "ready"


def build_runtime_doctor_status(*, env: dict[str, str] | None = None, generated_at: str = DEFAULT_GENERATED_AT) -> RuntimeDoctorStatus:
    source = os.environ if env is None else env
    runtime_config = load_hermes_runtime_config_from_env(env=source)
    env_checks = tuple(_configured_env_status(name, source) for name in ENV_CHECK_KEYS)
    client_path = _resolve_path(source, "ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE", DEFAULT_GOOGLE_OAUTH_CLIENT_SECRETS_FILE)
    token_path = _resolve_path(source, "ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE", DEFAULT_GOOGLE_OAUTH_TOKEN_FILE)
    path_checks = (_check_oauth_client_file(client_path), _check_oauth_token_file(token_path))
    _, token_payload, _ = _read_json_shape(Path(token_path))
    direct_token_configured = any(source.get(name, "").strip() for name in DIRECT_GOOGLE_TOKEN_ENV_KEYS)
    service_readiness = _build_service_readiness(token_payload=token_payload, direct_token_configured=direct_token_configured)
    return RuntimeDoctorStatus(
        stage=RUNTIME_DOCTOR_STAGE,
        runtime_online=True,
        runtime_mode=runtime_config.runtime_mode,
        robot_id=runtime_config.robot_id,
        owner_id=runtime_config.owner_id,
        roadmap_closed_through=ROADMAP_CLOSED_THROUGH,
        next_stage_authorized=False,
        next_stage=NEXT_STAGE,
        env_checks=env_checks,
        path_checks=path_checks,
        service_readiness=service_readiness,
        boundary_status=_build_boundary_status(),
        overall_status=_overall_status(path_checks, service_readiness),
        generated_at=generated_at,
    )


def render_runtime_doctor_report(*, status: RuntimeDoctorStatus, output_format: str = "text") -> RuntimeDoctorReport:
    if output_format not in {"text", "json"}:
        raise ValueError("rejected_invalid_output_format")
    if output_format == "json":
        rendered_text = json.dumps(
            {
                **asdict(status),
                "env_checks": [asdict(check) for check in status.env_checks],
                "path_checks": [asdict(check) for check in status.path_checks],
                "service_readiness": [asdict(readiness) for readiness in status.service_readiness],
                "boundary_status": asdict(status.boundary_status),
            },
            sort_keys=True,
            indent=2,
        )
        return RuntimeDoctorReport(status=status, rendered_text=rendered_text)

    lines = [
        "Runtime Doctor: local read-only",
        f"Stage: {status.stage}",
        f"Overall status: {status.overall_status}",
        f"Roadmap Closed Through: {status.roadmap_closed_through}",
        f"Next authorized stage: {NEXT_STAGE_LABEL}",
        f"Robot: {status.robot_id}",
        f"Owner: {status.owner_id}",
        f"Mode: {status.runtime_mode}",
        "Environment checks:",
    ]
    lines.extend(f"- {check.name}: {check.status} ({check.reason})" for check in status.env_checks)
    lines.append("Path checks:")
    lines.extend(f"- {check.name}: {check.shape_status} ({check.reason}) at {check.path}" for check in status.path_checks)
    lines.append("Service readiness:")
    lines.extend(f"- {readiness.service}: {'ready' if readiness.ready else 'not ready'} ({readiness.reason})" for readiness in status.service_readiness)
    lines.append("Boundary status:")
    for name, value in asdict(status.boundary_status).items():
        lines.append(f"- {name}: {'enabled' if value else 'disabled'}")
    lines.append(f"Generated At: {status.generated_at}")
    return RuntimeDoctorReport(status=status, rendered_text="\n".join(lines))


def run_runtime_doctor(*, env: dict[str, str] | None = None, output_format: str = "text", generated_at: str = DEFAULT_GENERATED_AT) -> RuntimeDoctorReport:
    status = build_runtime_doctor_status(env=env, generated_at=generated_at)
    return render_runtime_doctor_report(status=status, output_format=output_format)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.runtime_doctor")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--text", action="store_true", dest="as_text")
    args = parser.parse_args(argv)
    output_format = "json" if args.as_json and not args.as_text else "text"
    try:
        report = run_runtime_doctor(output_format=output_format)
    except ValueError as exc:
        print(f"Runtime Doctor: unavailable\nReason: {exc}", file=sys.stderr)
        return 1
    print(report.rendered_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
