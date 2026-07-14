from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base


def generate_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Text, primary_key=True, default=generate_id)
    telegram_user_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(Text, nullable=False)
    username = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class Robot(Base):
    __tablename__ = "robots"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    name = Column(Text, default="Roboticxs", nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    source_channel = Column(Text, default="telegram", nullable=False)
    kind = Column(Text, default="GENERAL_TASK", nullable=False)
    input_text = Column(Text, nullable=False)
    scope_decision = Column(Text, nullable=False)
    task_class = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(Text, primary_key=True, default=generate_id)
    task_id = Column(Text, index=True, nullable=False)
    status = Column(Text, default="completed", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class SkillManifest(Base):
    __tablename__ = "skill_manifests"

    id = Column(Text, primary_key=True, default=generate_id)
    skill_id = Column(Text, unique=True, index=True, nullable=False)
    display_name = Column(Text, nullable=False)
    content_json = Column(Text, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class SafetyDecision(Base):
    __tablename__ = "safety_decisions"

    id = Column(Text, primary_key=True, default=generate_id)
    task_id = Column(Text, index=True, nullable=False)
    action_class = Column(Text, nullable=False)
    decision = Column(Text, nullable=False)
    reason_code = Column(Text, nullable=False)
    user_message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class ModelRouteDecision(Base):
    __tablename__ = "model_route_decisions"

    id = Column(Text, primary_key=True, default=generate_id)
    task_id = Column(Text, index=True, nullable=False)
    task_class = Column(Text, nullable=False)
    provider = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    routing_mode = Column(Text, nullable=False)
    estimated_input_tokens = Column(Integer, nullable=False)
    estimated_output_tokens = Column(Integer, nullable=False)
    estimated_cost_usd = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class TokenUsageEvent(Base):
    __tablename__ = "token_usage_events"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    task_id = Column(Text, index=True, nullable=False)
    provider = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    estimated_cost_usd = Column(Float, nullable=False)
    status = Column(Text, default="estimated", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class BudgetPolicy(Base):
    __tablename__ = "budget_policies"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    limit_amount = Column(Float, nullable=False)
    warn_threshold_percent = Column(Integer, nullable=False, default=80)
    block_threshold_percent = Column(Integer, nullable=False, default=100)
    status = Column(Text, nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class ProposedMemory(Base):
    __tablename__ = "proposed_memories"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    task_id = Column(Text, index=True, nullable=False)
    memory_type = Column(Text, nullable=False)
    proposed_content = Column(Text, nullable=False)
    source_text = Column(Text, nullable=False)
    status = Column(Text, default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=True)


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    memory_type = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    display_label = Column(Text, nullable=False, default="Memory")
    source = Column(Text, nullable=False)
    status = Column(Text, default="ACTIVE", nullable=False)
    importance = Column(Text, default="normal", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "robot_id",
            "source_channel",
            "source_message_id",
            name="uq_conversation_turn_source_message",
        ),
    )

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    source_channel = Column(Text, nullable=False, default="telegram")
    source_message_id = Column(Text, nullable=False)
    user_text = Column(Text, nullable=False)
    assistant_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class HelperDiscoverySession(Base):
    __tablename__ = "helper_discovery_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "robot_id", name="uq_helper_discovery_user_robot"),
    )

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    status = Column(Text, nullable=False, default="WAITING_CONSENT")
    current_step = Column(Integer, nullable=False, default=0)
    answers_json = Column(Text, nullable=False, default="{}")
    summary = Column(Text, nullable=True)
    proposal_id = Column(Text, nullable=True)
    consented_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class HelperProcessingConsent(Base):
    __tablename__ = "helper_processing_consents"
    __table_args__ = (
        UniqueConstraint("user_id", "robot_id", name="uq_helper_processing_consent_user_robot"),
    )

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    provider = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class HelperContextInvite(Base):
    __tablename__ = "helper_context_invites"

    id = Column(Text, primary_key=True, default=generate_id)
    source_user_id = Column(Text, index=True, nullable=False)
    target_user_id = Column(Text, index=True, nullable=False)
    context_text = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="PENDING")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class DocumentTask(Base):
    __tablename__ = "document_tasks"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    task_id = Column(Text, index=True, nullable=False)
    review_type = Column(Text, nullable=False)
    source_kind = Column(Text, nullable=False, default="TEXT_SIMULATED")
    source_text_preview = Column(Text, nullable=False)
    source_text_hash = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="DRAFTED")
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class FileIntakeAttempt(Base):
    __tablename__ = "file_intake_attempts"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    task_id = Column(Text, index=True, nullable=False)
    source_channel = Column(Text, nullable=False, default="telegram")
    telegram_file_id = Column(Text, nullable=False)
    telegram_file_unique_id = Column(Text, nullable=True)
    file_name = Column(Text, nullable=True)
    mime_type = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    status = Column(Text, nullable=False, default="METADATA_RECEIVED")
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class FileRetrievalAttempt(Base):
    __tablename__ = "file_retrieval_attempts"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    task_id = Column(Text, index=True, nullable=False)
    file_intake_id = Column(Text, index=True, nullable=False)
    request_kind = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="REQUESTED_NOT_ENABLED")
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class FileRetrievalEnablementRequest(Base):
    __tablename__ = "file_retrieval_enablement_requests"

    id = Column(Text, primary_key=True, default=generate_id)
    user_id = Column(Text, index=True, nullable=False)
    robot_id = Column(Text, index=True, nullable=False)
    task_id = Column(Text, index=True, nullable=False)
    status = Column(Text, nullable=False, default="REQUESTED_DISABLED")
    reason_code = Column(Text, nullable=False, default="FILE_RETRIEVAL_DISABLED_BY_POLICY")
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
