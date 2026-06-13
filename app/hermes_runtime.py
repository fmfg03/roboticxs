from __future__ import annotations

from dataclasses import dataclass, field


HERMES_UPSTREAM_REPOSITORY = "https://github.com/NousResearch/hermes-agent"
HERMES_UPSTREAM_OWNER = "NousResearch"
HERMES_PROJECT_NAME = "Hermes Agent"
HERMES_SOURCE_STATUS = "EXTERNAL_UPSTREAM_SOURCE"
ROBOTICXS_APPROVAL_STATUS = "FOUNDATION_REFERENCE_ONLY"


@dataclass(frozen=True, slots=True)
class HermesRuntimeStatus:
    runtime_name: str
    status: str
    upstream_repository: str
    compatibility_status: str
    orchestrator_available: bool
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HermesRuntimeRequest:
    user_id: str
    channel: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HermesRuntimeResponse:
    status: str
    text: str
    task_id: str | None
    safety_decision: str | None
    metadata: dict[str, str] = field(default_factory=dict)


def get_hermes_runtime_status() -> HermesRuntimeStatus:
    return HermesRuntimeStatus(
        runtime_name="Roboticxs Hermes-compatible runtime foundation",
        status="available",
        upstream_repository=HERMES_UPSTREAM_REPOSITORY,
        compatibility_status=ROBOTICXS_APPROVAL_STATUS,
        orchestrator_available=False,
        metadata={
            "upstream_owner": HERMES_UPSTREAM_OWNER,
            "project_name": HERMES_PROJECT_NAME,
            "source_status": HERMES_SOURCE_STATUS,
            "dispatch_mode": "deterministic_local_foundation",
            "telegram_implemented": "false",
            "memory_writes_enabled": "false",
            "retrieval_enabled": "false",
            "connectors_enabled": "false",
        },
    )


def dispatch_hermes_runtime_request(request: HermesRuntimeRequest) -> HermesRuntimeResponse:
    if not request.text.strip():
        return HermesRuntimeResponse(
            status="rejected",
            text="Hermes runtime foundation requires non-empty text input.",
            task_id=None,
            safety_decision=None,
            metadata={
                "runtime": "hermes_compatible_foundation",
                "channel": request.channel,
                "telegram_required": "false",
                "side_effects": "none",
            },
        )

    return HermesRuntimeResponse(
        status="ok",
        text="Hermes runtime foundation is available. Telegram/channel integration is not implemented yet.",
        task_id=None,
        safety_decision=None,
        metadata={
            "runtime": "hermes_compatible_foundation",
            "user_id": request.user_id,
            "channel": request.channel,
            "upstream_repository": HERMES_UPSTREAM_REPOSITORY,
            "orchestrator_adapter": "not_called_side_effect_boundary",
            "telegram_required": "false",
            "network_required": "false",
            "memory_write": "false",
            "proposed_memory_write": "false",
            "retrieval": "false",
            "connector": "false",
            "shell_execution": "false",
        },
    )
