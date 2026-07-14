from __future__ import annotations

from dataclasses import dataclass


FRIENDLY_PILOT_OPERATOR_CONSOLE_STAGE = "213P"
FRIENDLY_PILOT_OPERATOR_CONSOLE_STATUS = "local_friendly_pilot_operator_console_v0"


@dataclass(frozen=True, slots=True)
class FriendlyPilotUserStatus:
    user_id: str
    user_alias: str
    role: str
    robot_status: str
    connector_readiness: str
    last_activity: str
    feedback_count: int
    blocked_actions: int
    unresolved_setup_issues: int
    usage_cost_snapshot: str

    def __post_init__(self) -> None:
        if not self.user_id or not self.user_alias:
            raise ValueError("213P pilot users require user id and alias.")
        if self.role not in {"owner_founder", "friendly_user"}:
            raise ValueError("213P pilot user role is unsupported.")
        if min(self.feedback_count, self.blocked_actions, self.unresolved_setup_issues) < 0:
            raise ValueError("213P pilot user counters must be non-negative.")


@dataclass(frozen=True, slots=True)
class FriendlyPilotOperatorConsole:
    stage: str
    owner_id: str
    robot_id: str
    status: str
    users: tuple[FriendlyPilotUserStatus, ...]
    selected_user_id: str | None
    local_console_only: bool
    web_console_created: bool
    provisioning_allowed: bool
    gmail_send_allowed: bool
    calendar_write_allowed: bool
    crm_write_allowed: bool
    whatsapp_allowed: bool
    external_write_allowed: bool
    secrets_redacted: bool

    def __post_init__(self) -> None:
        if self.stage != FRIENDLY_PILOT_OPERATOR_CONSOLE_STAGE:
            raise ValueError("213P operator consoles must identify the 213P stage.")
        if self.status != FRIENDLY_PILOT_OPERATOR_CONSOLE_STATUS:
            raise ValueError("213P operator consoles must use the console status.")
        if not self.local_console_only or self.web_console_created or self.provisioning_allowed:
            raise ValueError("213P operator console must remain local and non-provisioning.")
        if any(
            (
                self.gmail_send_allowed,
                self.calendar_write_allowed,
                self.crm_write_allowed,
                self.whatsapp_allowed,
                self.external_write_allowed,
            )
        ):
            raise ValueError("213P operator console must not expand external write authority.")
        if not self.secrets_redacted:
            raise ValueError("213P operator console must be redacted.")


def build_friendly_pilot_operator_console(
    *,
    owner_id: str,
    robot_id: str,
    users: tuple[FriendlyPilotUserStatus, ...] = (),
    selected_user_id: str | None = None,
) -> FriendlyPilotOperatorConsole:
    scoped_users = users or (
        FriendlyPilotUserStatus(
            user_id=owner_id,
            user_alias="Founder",
            role="owner_founder",
            robot_status="ready_local",
            connector_readiness="fallback_or_readonly",
            last_activity="not_recorded",
            feedback_count=0,
            blocked_actions=0,
            unresolved_setup_issues=0,
            usage_cost_snapshot="no_local_usage_yet",
        ),
    )
    selected = selected_user_id.strip() if selected_user_id else None
    if selected and all(user.user_id != selected for user in scoped_users):
        scoped_users = scoped_users + (
            FriendlyPilotUserStatus(
                user_id=selected,
                user_alias="Unknown pilot user",
                role="friendly_user",
                robot_status="not_found",
                connector_readiness="unknown",
                last_activity="not_recorded",
                feedback_count=0,
                blocked_actions=0,
                unresolved_setup_issues=1,
                usage_cost_snapshot="unavailable",
            ),
        )
    return FriendlyPilotOperatorConsole(
        stage=FRIENDLY_PILOT_OPERATOR_CONSOLE_STAGE,
        owner_id=owner_id,
        robot_id=robot_id,
        status=FRIENDLY_PILOT_OPERATOR_CONSOLE_STATUS,
        users=scoped_users,
        selected_user_id=selected,
        local_console_only=True,
        web_console_created=False,
        provisioning_allowed=False,
        gmail_send_allowed=False,
        calendar_write_allowed=False,
        crm_write_allowed=False,
        whatsapp_allowed=False,
        external_write_allowed=False,
        secrets_redacted=True,
    )


def render_pilot_users(console: FriendlyPilotOperatorConsole) -> str:
    lines = [
        "Friendly Pilot Users",
        "",
        f"Stage: {console.stage}",
        f"Status: {console.status}",
        f"Users: {len(console.users)}",
        "",
        "Pilot roster:",
    ]
    for user in console.users:
        lines.append(
            f"- {user.user_id} | {user.user_alias} | {user.role} | {user.robot_status} | "
            f"feedback={user.feedback_count} blocked={user.blocked_actions} setup_issues={user.unresolved_setup_issues}"
        )
    lines.extend(_safety_lines())
    return "\n".join(lines)


def render_pilot_user(console: FriendlyPilotOperatorConsole) -> str:
    selected = next((user for user in console.users if user.user_id == console.selected_user_id), console.users[0])
    lines = [
        "Friendly Pilot User",
        "",
        f"Stage: {console.stage}",
        f"Status: {console.status}",
        f"User id: {selected.user_id}",
        f"Alias: {selected.user_alias}",
        f"Role: {selected.role}",
        f"Robot status: {selected.robot_status}",
        f"Connector readiness: {selected.connector_readiness}",
        f"Last activity: {selected.last_activity}",
        f"Feedback count: {selected.feedback_count}",
        f"Blocked actions: {selected.blocked_actions}",
        f"Unresolved setup issues: {selected.unresolved_setup_issues}",
        f"Usage/cost snapshot: {selected.usage_cost_snapshot}",
    ]
    lines.extend(_safety_lines())
    return "\n".join(lines)


def render_pilot_health(console: FriendlyPilotOperatorConsole) -> str:
    blocked = sum(user.blocked_actions for user in console.users)
    setup_issues = sum(user.unresolved_setup_issues for user in console.users)
    feedback = sum(user.feedback_count for user in console.users)
    active = sum(1 for user in console.users if user.last_activity != "not_recorded")
    lines = [
        "Friendly Pilot Health",
        "",
        f"Stage: {console.stage}",
        f"Status: {console.status}",
        f"Users: {len(console.users)}",
        f"Active users: {active}",
        f"Feedback count: {feedback}",
        f"Blocked actions: {blocked}",
        f"Unresolved setup issues: {setup_issues}",
        f"Health: {_health_label(blocked=blocked, setup_issues=setup_issues)}",
    ]
    lines.extend(_safety_lines())
    return "\n".join(lines)


def _health_label(*, blocked: int, setup_issues: int) -> str:
    if blocked or setup_issues:
        return "needs_attention"
    return "ready_local"


def _safety_lines() -> list[str]:
    return [
        "",
        "Local console only: yes",
        "Web console: not created",
        "Provisioning: disabled",
        "Gmail send: disabled",
        "Calendar writes: disabled",
        "CRM writes: disabled",
        "WhatsApp: disabled",
        "External writes: disabled",
        "Secrets: redacted",
    ]
