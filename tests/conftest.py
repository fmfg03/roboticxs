from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.main import create_app
from app.models import (
    BudgetPolicy,
    DocumentTask,
    FileIntakeAttempt,
    FileRetrievalEnablementRequest,
    FileRetrievalAttempt,
    MemoryItem,
    ModelRouteDecision,
    ProposedMemory,
    Robot,
    SafetyDecision,
    SkillManifest,
    Task,
    TaskRun,
    TokenUsageEvent,
    User,
)


@pytest.fixture
async def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        test_client.app = app
        yield test_client


@pytest.fixture
def db_counts(client):
    def _counts():
        with client.app.state.db.session() as session:
            return {
                "users": session.scalar(select(func.count()).select_from(User)),
                "robots": session.scalar(select(func.count()).select_from(Robot)),
                "tasks": session.scalar(select(func.count()).select_from(Task)),
                "task_runs": session.scalar(select(func.count()).select_from(TaskRun)),
                "skills": session.scalar(select(func.count()).select_from(SkillManifest)),
                "safety": session.scalar(select(func.count()).select_from(SafetyDecision)),
                "routes": session.scalar(select(func.count()).select_from(ModelRouteDecision)),
                "tokens": session.scalar(select(func.count()).select_from(TokenUsageEvent)),
                "proposals": session.scalar(select(func.count()).select_from(ProposedMemory)),
                "memories": session.scalar(select(func.count()).select_from(MemoryItem)),
                "documents": session.scalar(select(func.count()).select_from(DocumentTask)),
                "file_intakes": session.scalar(select(func.count()).select_from(FileIntakeAttempt)),
                "file_retrieval_attempts": session.scalar(select(func.count()).select_from(FileRetrievalAttempt)),
                "file_retrieval_enablement_requests": session.scalar(select(func.count()).select_from(FileRetrievalEnablementRequest)),
                "budget_policies": session.scalar(select(func.count()).select_from(BudgetPolicy)),
            }

    return _counts
