from __future__ import annotations

from dataclasses import dataclass


FRIENDLY_USER_ONBOARDING_PACK_STAGE = "211P"
FRIENDLY_USER_ONBOARDING_PACK_STATUS = "friendly_user_onboarding_pack_v0"


@dataclass(frozen=True, slots=True)
class FriendlyUserOnboardingPack:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    user_limit: str
    setup_checklist: tuple[str, ...]
    allowed_commands: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    privacy_source_explanation: tuple[str, ...]
    memory_approval_explanation: tuple[str, ...]
    daily_usage_script: tuple[str, ...]
    feedback_commands: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    local_pack_only: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != FRIENDLY_USER_ONBOARDING_PACK_STAGE:
            raise ValueError("211P friendly onboarding packs must identify the 211P stage.")
        if self.status != FRIENDLY_USER_ONBOARDING_PACK_STATUS:
            raise ValueError("211P friendly onboarding packs must use the onboarding status.")
        if self.user_limit != "1-3 friendly users":
            raise ValueError("211P friendly onboarding is limited to 1-3 users.")
        if not all(
            (
                self.setup_checklist,
                self.allowed_commands,
                self.blocked_actions,
                self.privacy_source_explanation,
                self.memory_approval_explanation,
                self.daily_usage_script,
                self.feedback_commands,
                self.stop_conditions,
            )
        ):
            raise ValueError("211P friendly onboarding packs require all onboarding sections.")
        if not self.local_pack_only:
            raise ValueError("211P friendly onboarding packs must remain local pack only.")
        if any(
            (
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("211P friendly onboarding must not expand external write authority.")
        if not self.secrets_redacted:
            raise ValueError("211P friendly onboarding packs must be redacted.")


def build_friendly_user_onboarding_pack(*, owner_id: str, robot_id: str) -> FriendlyUserOnboardingPack:
    return FriendlyUserOnboardingPack(
        stage=FRIENDLY_USER_ONBOARDING_PACK_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FRIENDLY_USER_ONBOARDING_PACK_STATUS,
        user_limit="1-3 friendly users",
        setup_checklist=(
            "Confirm Telegram owner access and friendly-user expectation.",
            "Run /setup and /checkup before the first session.",
            "Run /pilot_pack and /live_smoke once with the founder present.",
            "Confirm connectors show real data or explicit fallback status.",
            "Confirm the user understands no Gmail send or Calendar write will occur.",
        ),
        allowed_commands=(
            "/help",
            "/setup",
            "/daily_brief",
            "/prep",
            "/suggestions",
            "/approvals",
            "/drafts",
            "/memory",
            "/memory_review",
            "/usage",
            "/pilot_metrics",
            "/feedback <tag> <item_id> [comment]",
        ),
        blocked_actions=(
            "Gmail send/modify/archive/delete",
            "Calendar create/update/delete",
            "CRM writes",
            "WhatsApp",
            "destructive external actions",
            "autonomous background actions",
            "secret or token disclosure",
        ),
        privacy_source_explanation=(
            "Outputs should show source trace or explicit fallback when source context is missing.",
            "Connector failures must be visible instead of presented as live facts.",
            "Receipts and Telegram replies must not include secrets.",
        ),
        memory_approval_explanation=(
            "Memory proposals are not facts until approved.",
            "Memory correction commands create local receipts for wrong, stale, duplicate, merge, or never-use signals.",
            "Memory Store and Memory Center mutation remain disabled in this pack.",
        ),
        daily_usage_script=(
            "/founder_loop",
            "/daily_brief",
            "/prep",
            "/suggestions",
            "/approvals",
            "/drafts",
            "/usage",
            "/pilot_metrics",
        ),
        feedback_commands=(
            "/feedback useful <item_id>",
            "/feedback wrong <item_id>",
            "/feedback noisy <item_id>",
            "/feedback stale <item_id>",
            "/feedback missing_source <item_id>",
            "/feedback too_verbose <item_id>",
        ),
        stop_conditions=(
            "Any output claims live data without source or fallback.",
            "Any command attempts Gmail send, Calendar write, CRM write, or WhatsApp.",
            "Any approval bypass or owner gate mismatch.",
            "Any secret appears in a reply, receipt, doc, or log.",
            "The user cannot tell the next safe action from the card.",
        ),
        local_pack_only=True,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
    )


def render_friendly_user_onboarding_pack(pack: FriendlyUserOnboardingPack) -> str:
    sections = [
        ("Friendly User Onboarding Pack", (f"Stage: {pack.stage}", f"Status: {pack.status}", f"User limit: {pack.user_limit}")),
        ("Setup checklist", pack.setup_checklist),
        ("Allowed commands", pack.allowed_commands),
        ("Blocked actions", pack.blocked_actions),
        ("Privacy and source trace", pack.privacy_source_explanation),
        ("Memory approval", pack.memory_approval_explanation),
        ("Daily usage script", pack.daily_usage_script),
        ("Feedback commands", pack.feedback_commands),
        ("Stop conditions", pack.stop_conditions),
        (
            "Safety",
            (
                "Gmail send: disabled",
                "Calendar writes: disabled",
                "CRM writes: disabled",
                "WhatsApp: disabled",
                "External writes: disabled",
                "Secrets: redacted",
            ),
        ),
    ]
    rendered: list[str] = []
    for title, lines in sections:
        rendered.append(title)
        rendered.extend(f"- {line}" for line in lines)
        rendered.append("")
    return "\n".join(rendered).rstrip()
