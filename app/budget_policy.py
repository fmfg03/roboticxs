from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

from sqlalchemy import select

from app.models import BudgetPolicy as BudgetPolicyModel
from app.usage_reporting import UsageSummary


BUDGET_STATUS_COMMAND = "show budget status"
RESET_BUDGET_POLICY_COMMAND = "reset budget policy"
RESTORE_DEFAULT_BUDGET_POLICY_COMMAND = "restore default budget policy"
SET_BUDGET_LIMIT_PATTERN = re.compile(r"^set budget limit(?:\s+(.+))?$", re.IGNORECASE)
SET_BUDGET_WARN_THRESHOLD_PATTERN = re.compile(r"^set budget warn threshold(?:\s+(.+))?$", re.IGNORECASE)
SET_BUDGET_BLOCK_THRESHOLD_PATTERN = re.compile(r"^set budget block threshold(?:\s+(.+))?$", re.IGNORECASE)
DEFAULT_BUDGET_LIMIT_USD = 0.0016
DEFAULT_WARN_THRESHOLD_PERCENT = 80
DEFAULT_BLOCK_THRESHOLD_PERCENT = 100


@dataclass(slots=True)
class BudgetPolicyConfig:
    budget_limit_usd: float
    warn_threshold_percent: int
    block_threshold_percent: int


@dataclass(slots=True)
class BudgetPosture:
    budget_limit_usd: float
    warn_threshold_percent: int
    block_threshold_percent: int
    current_estimated_spend_usd: float
    projected_estimated_spend_usd: float
    remaining_estimated_budget_usd: float
    usage_percentage: float
    status: str


def is_budget_status_command(text: str) -> bool:
    return text.strip().lower() == BUDGET_STATUS_COMMAND


def is_budget_policy_reset_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {RESET_BUDGET_POLICY_COMMAND, RESTORE_DEFAULT_BUDGET_POLICY_COMMAND}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_set_budget_limit_command(text: str) -> str | None:
    return _parse_single_argument_command(text, SET_BUDGET_LIMIT_PATTERN)


def parse_set_budget_warn_threshold_command(text: str) -> str | None:
    return _parse_single_argument_command(text, SET_BUDGET_WARN_THRESHOLD_PATTERN)


def parse_set_budget_block_threshold_command(text: str) -> str | None:
    return _parse_single_argument_command(text, SET_BUDGET_BLOCK_THRESHOLD_PATTERN)


def _parse_single_argument_command(text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.match(text.strip())
    if match is None:
        return None
    raw_amount = match.group(1)
    return raw_amount.strip() if raw_amount is not None else ""


def parse_budget_amount(raw_amount: str) -> Decimal | None:
    cleaned = raw_amount.strip()
    if not cleaned:
        return None
    if not re.fullmatch(r"\$?-?\d+(?:\.\d+)?", cleaned):
        return None
    normalized = cleaned[1:] if cleaned.startswith("$") else cleaned
    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None
    if amount <= 0:
        return None
    return amount


def parse_budget_threshold_percent(raw_percent: str) -> int | None:
    cleaned = raw_percent.strip()
    if not cleaned:
        return None
    if not re.fullmatch(r"-?\d+%?", cleaned):
        return None
    normalized = cleaned[:-1] if cleaned.endswith("%") else cleaned
    try:
        threshold = int(normalized)
    except ValueError:
        return None
    if threshold <= 0 or threshold > 100:
        return None
    return threshold


def upsert_budget_limit_policy(*, session, user_id: str, robot_id: str, limit_amount: Decimal) -> BudgetPolicyModel:
    policy = _get_or_create_budget_policy(session=session, user_id=user_id, robot_id=robot_id)
    policy.limit_amount = float(limit_amount)
    policy.updated_at = now_utc()
    session.flush()
    return policy


def upsert_budget_warn_threshold_policy(*, session, user_id: str, robot_id: str, warn_threshold_percent: int) -> BudgetPolicyModel | None:
    current_policy = get_budget_policy(session=session, user_id=user_id, robot_id=robot_id)
    if warn_threshold_percent >= current_policy.block_threshold_percent:
        return None
    policy = _get_or_create_budget_policy(session=session, user_id=user_id, robot_id=robot_id)
    policy.warn_threshold_percent = warn_threshold_percent
    policy.updated_at = now_utc()
    session.flush()
    return policy


def upsert_budget_block_threshold_policy(*, session, user_id: str, robot_id: str, block_threshold_percent: int) -> BudgetPolicyModel | None:
    current_policy = get_budget_policy(session=session, user_id=user_id, robot_id=robot_id)
    if block_threshold_percent <= current_policy.warn_threshold_percent:
        return None
    policy = _get_or_create_budget_policy(session=session, user_id=user_id, robot_id=robot_id)
    policy.block_threshold_percent = block_threshold_percent
    policy.updated_at = now_utc()
    session.flush()
    return policy


def _get_or_create_budget_policy(*, session, user_id: str, robot_id: str) -> BudgetPolicyModel:
    policy = session.scalar(
        select(BudgetPolicyModel).where(
            BudgetPolicyModel.user_id == user_id,
            BudgetPolicyModel.robot_id == robot_id,
            BudgetPolicyModel.status == "ACTIVE",
        )
    )
    if policy is None:
        policy = BudgetPolicyModel(
            user_id=user_id,
            robot_id=robot_id,
            limit_amount=DEFAULT_BUDGET_LIMIT_USD,
            warn_threshold_percent=DEFAULT_WARN_THRESHOLD_PERCENT,
            block_threshold_percent=DEFAULT_BLOCK_THRESHOLD_PERCENT,
            status="ACTIVE",
        )
        session.add(policy)
        session.flush()
    return policy


def reset_budget_policy(*, session, user_id: str, robot_id: str) -> BudgetPolicyModel | None:
    policy = session.scalar(
        select(BudgetPolicyModel).where(
            BudgetPolicyModel.user_id == user_id,
            BudgetPolicyModel.robot_id == robot_id,
            BudgetPolicyModel.status == "ACTIVE",
        )
    )
    if policy is None:
        return None
    policy.status = "INACTIVE"
    policy.updated_at = now_utc()
    session.flush()
    return policy


def get_budget_policy(*, session, user_id: str, robot_id: str) -> BudgetPolicyConfig:
    policy = session.scalar(
        select(BudgetPolicyModel).where(
            BudgetPolicyModel.user_id == user_id,
            BudgetPolicyModel.robot_id == robot_id,
            BudgetPolicyModel.status == "ACTIVE",
        )
    )
    if policy is not None:
        return BudgetPolicyConfig(
            budget_limit_usd=policy.limit_amount,
            warn_threshold_percent=policy.warn_threshold_percent,
            block_threshold_percent=policy.block_threshold_percent,
        )
    return BudgetPolicyConfig(
        budget_limit_usd=DEFAULT_BUDGET_LIMIT_USD,
        warn_threshold_percent=DEFAULT_WARN_THRESHOLD_PERCENT,
        block_threshold_percent=DEFAULT_BLOCK_THRESHOLD_PERCENT,
    )


def evaluate_budget_posture(
    *,
    summary: UsageSummary,
    estimated_route_cost_usd: float,
    policy: BudgetPolicyConfig,
) -> BudgetPosture:
    current_spend = round(summary.total_estimated_cost_usd, 6)
    projected_spend = round(current_spend + estimated_route_cost_usd, 6)
    remaining_budget = round(policy.budget_limit_usd - current_spend, 6)
    usage_percentage = 0.0 if policy.budget_limit_usd <= 0 else round((current_spend / policy.budget_limit_usd) * 100, 2)
    projected_percentage = 0.0 if policy.budget_limit_usd <= 0 else round((projected_spend / policy.budget_limit_usd) * 100, 2)

    status = "ALLOW"
    if projected_percentage >= policy.block_threshold_percent:
        status = "BLOCK"
    elif projected_percentage >= policy.warn_threshold_percent:
        status = "WARN"

    return BudgetPosture(
        budget_limit_usd=policy.budget_limit_usd,
        warn_threshold_percent=policy.warn_threshold_percent,
        block_threshold_percent=policy.block_threshold_percent,
        current_estimated_spend_usd=current_spend,
        projected_estimated_spend_usd=projected_spend,
        remaining_estimated_budget_usd=remaining_budget,
        usage_percentage=usage_percentage,
        status=status,
    )
