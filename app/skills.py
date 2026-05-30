from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SkillManifest


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def load_skill_manifest_file(skill_name: str = "basic_assistant.json") -> dict[str, Any]:
    path = SKILLS_DIR / skill_name
    return json.loads(path.read_text())


def seed_skill_manifest(session: Session, skill_name: str = "basic_assistant.json") -> SkillManifest:
    manifest = load_skill_manifest_file(skill_name)
    existing = session.scalar(select(SkillManifest).where(SkillManifest.skill_id == manifest["skill_id"]))
    content_json = json.dumps(manifest, sort_keys=True)
    if existing:
        existing.display_name = manifest["display_name"]
        existing.content_json = content_json
        existing.active = True
        return existing

    seeded = SkillManifest(
        skill_id=manifest["skill_id"],
        display_name=manifest["display_name"],
        content_json=content_json,
        active=True,
    )
    session.add(seeded)
    session.flush()
    return seeded


def get_active_skill_manifest(session: Session) -> dict[str, Any]:
    record = session.scalar(select(SkillManifest).where(SkillManifest.active.is_(True)).limit(1))
    if record is None:
        record = seed_skill_manifest(session)
        session.flush()
    return json.loads(record.content_json)
