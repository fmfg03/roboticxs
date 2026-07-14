from __future__ import annotations

from dataclasses import dataclass


CUSTOMER_PILOT_READINESS_PACK_STAGE = "199P"
CUSTOMER_PILOT_READINESS_PACK_STATUS = "ready_for_controlled_1_to_3_user_pilot"


@dataclass(frozen=True, slots=True)
class CustomerPilotReadinessPack:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    setup_checklist: tuple[str, ...]
    supported_commands: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    demo_script: tuple[str, ...]
    failure_modes: tuple[str, ...]
    source_trace_examples: tuple[str, ...]
    usage_report: tuple[str, ...]
    safety_receipts: tuple[str, ...]
    onboarding_copy: tuple[str, ...]
    target_pilot_users: str
    local_pack_only: bool
    external_write_allowed: bool
    gmail_send_allowed: bool
    gmail_modify_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    secrets_redacted: bool
    approval_gate_preserved: bool

    def __post_init__(self) -> None:
        if self.stage != CUSTOMER_PILOT_READINESS_PACK_STAGE:
            raise ValueError("199P pilot readiness packs must identify the 199P stage.")
        if self.status != CUSTOMER_PILOT_READINESS_PACK_STATUS:
            raise ValueError("199P pilot readiness packs must use the controlled pilot status.")
        required_sections = (
            self.setup_checklist,
            self.supported_commands,
            self.blocked_actions,
            self.demo_script,
            self.failure_modes,
            self.source_trace_examples,
            self.usage_report,
            self.safety_receipts,
            self.onboarding_copy,
        )
        if any(not section for section in required_sections):
            raise ValueError("199P pilot readiness packs require every pilot section.")
        if self.target_pilot_users != "1-3":
            raise ValueError("199P pilot readiness target must stay controlled at 1-3 users.")
        if not self.local_pack_only or not self.secrets_redacted or not self.approval_gate_preserved:
            raise ValueError("199P pilot readiness must remain local, redacted, and approval-preserving.")
        if any(
            (
                self.external_write_allowed,
                self.gmail_send_allowed,
                self.gmail_modify_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
            )
        ):
            raise ValueError("199P pilot readiness must not expand external action authority.")


def build_customer_pilot_readiness_pack(*, owner_id: str, robot_id: str) -> CustomerPilotReadinessPack:
    return CustomerPilotReadinessPack(
        stage=CUSTOMER_PILOT_READINESS_PACK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=CUSTOMER_PILOT_READINESS_PACK_STATUS,
        setup_checklist=(
            "Confirm Telegram owner id and robot id.",
            "Run /status and /checkup before the pilot session.",
            "Confirm Calendar and Gmail are read-only where connected.",
            "Prepare one real meeting, one read-only Gmail thread, and one approved memory.",
            "Confirm Gmail draft creation is draft-only and never send.",
            "Review blocked actions with the pilot user before starting.",
        ),
        supported_commands=(
            "/start",
            "/menu",
            "/status",
            "/checkup",
            "/today",
            "/daily_brief",
            "/prep",
            "/suggestions",
            "/drafts",
            "/approvals",
            "/usage",
            "/memory",
            "/document",
            "/pilot",
            "/pilot_pack",
        ),
        blocked_actions=(
            "Gmail send/archive/delete/label/modify",
            "Calendar create/update/delete",
            "CRM writes or lead handoff",
            "WhatsApp send or sync",
            "External destructive actions",
            "Secrets or tokens in logs, receipts, tests, or Telegram replies",
            "Unapproved memory mutation",
        ),
        demo_script=(
            "Open /start and confirm the product shell is owner-gated.",
            "Run /status or /checkup to show source readiness and blocked actions.",
            "Run /today or /daily_brief to show context and source trace.",
            "Run /prep to show prioritized Calendar, Gmail, Memory, and Document context.",
            "Run /suggestions, create a draft, and review /drafts.",
            "Approve the draft and materialize Gmail draft/export only after confirmation.",
            "Run /usage to show local estimated usage and routing cost visibility.",
            "Run /pilot to show the end-to-end controlled pilot receipt.",
        ),
        failure_modes=(
            "Missing credentials: show setup needed, do not fake live access.",
            "Expired or stale approval: block approval and ask for regeneration.",
            "Missing source trace: block external materialization.",
            "Owner mismatch: refuse command.",
            "Premium or expensive route: require explicit confirmation.",
            "Connector write request outside approved draft path: block.",
        ),
        source_trace_examples=(
            "calendar:event:readonly -> prep context",
            "gmail:thread:readonly -> draft source basis",
            "memory:approved -> personalization basis",
            "document:review -> suggested downstream actions",
            "usage:ledger -> estimated cost receipt",
        ),
        usage_report=(
            "Show mode as Economy, Balanced, or Premium.",
            "Show estimated tokens and estimated cost before expensive tasks.",
            "Record provider/model estimate and command in the local ledger.",
            "Label estimates as local and not live billing.",
        ),
        safety_receipts=(
            "Approval gate preserved for sensitive actions.",
            "Gmail send remains blocked.",
            "Calendar writes remain blocked.",
            "CRM and WhatsApp remain blocked.",
            "Source trace required where applicable.",
            "Secrets redacted in all customer-visible output.",
        ),
        onboarding_copy=(
            "Roboticxs is your personal robot with memory, context, and approval gates.",
            "It helps prepare, draft, remember, and explain sources.",
            "It does not send, schedule, delete, or mutate important external systems without explicit approved authority.",
            "Use the pilot to validate usefulness, trust, speed, output quality, and cost visibility.",
        ),
        target_pilot_users="1-3",
        local_pack_only=True,
        external_write_allowed=False,
        gmail_send_allowed=False,
        gmail_modify_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        secrets_redacted=True,
        approval_gate_preserved=True,
    )


def render_customer_pilot_readiness_pack(pack: CustomerPilotReadinessPack) -> str:
    return "\n".join(
        [
            "Customer Pilot Readiness Pack",
            "",
            f"Stage: {pack.stage}",
            f"Status: {pack.status}",
            f"Pilot users: {pack.target_pilot_users}",
            "",
            "Setup checklist:",
            *_bullets(pack.setup_checklist),
            "",
            "Supported commands:",
            *_bullets(pack.supported_commands),
            "",
            "Blocked actions:",
            *_bullets(pack.blocked_actions),
            "",
            "Demo script:",
            *_numbered(pack.demo_script),
            "",
            "Failure modes:",
            *_bullets(pack.failure_modes),
            "",
            "Source trace examples:",
            *_bullets(pack.source_trace_examples),
            "",
            "Usage report:",
            *_bullets(pack.usage_report),
            "",
            "Safety receipts:",
            *_bullets(pack.safety_receipts),
            "",
            "Onboarding copy:",
            *_bullets(pack.onboarding_copy),
            "",
            "Gmail send: disabled",
            "Calendar writes: disabled",
            "CRM writes: disabled",
            "WhatsApp: disabled",
            "External writes: disabled",
            "Approval gate: preserved",
            "Secrets: redacted",
        ]
    )


def _bullets(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items]


def _numbered(items: tuple[str, ...]) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)]
