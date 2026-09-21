from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_V01 = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
ROADMAP_V02 = REPO_ROOT / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_2.md"

CLASSIFICATIONS = {
    "KEEP",
    "DELETE",
    "ABSORBED_BY_NANOBOT",
    "ROBOTICXS_FEATURE",
    "ZAUBERN_BOUNDARY",
}


def load_json_block(block_name: str):
    text = ROADMAP_V02.read_text()
    match = re.search(
        rf"```json {re.escape(block_name)}\n(?P<payload>.+?)\n```",
        text,
        re.DOTALL,
    )
    assert match is not None, f"Missing {block_name} JSON block."
    return json.loads(match.group("payload"))


def test_v02_preserves_v01_as_historical_evidence_without_editing_it():
    assert ROADMAP_V01.is_file()
    authority = load_json_block("canonical-roadmap-v0-2-authority")
    assert authority["previous_canon"] == "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"
    assert authority["previous_canon_preserved"] is True
    assert authority["historical_terminal_stage"] == "226P"

    changed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", str(ROADMAP_V01.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    assert changed == []


def test_v02_classification_never_grants_execution_or_dependency_authority():
    text = ROADMAP_V02.read_text()
    authority = load_json_block("canonical-roadmap-v0-2-authority")

    assert "classification != authorization" in text
    assert "ABSORBED_BY_NANOBOT != dependency_adopted" in text
    assert authority["classification_is_authorization"] is False
    assert authority["absorbed_by_nanobot_is_dependency_adopted"] is False
    assert authority["next_implementation_stage_authorized"] is False
    assert "nanobot_dependency" in authority["forbidden_effects"]
    assert "next_feature_implementation" in authority["forbidden_effects"]


def test_future_candidates_use_only_the_five_approved_classifications():
    candidates = load_json_block("future-roadmap-classification-registry")
    classifications = {candidate["classification"] for candidate in candidates}

    assert classifications <= CLASSIFICATIONS
    assert classifications == {
        "DELETE",
        "ABSORBED_BY_NANOBOT",
        "ROBOTICXS_FEATURE",
        "ZAUBERN_BOUNDARY",
    }
    assert all("reason" in candidate for candidate in candidates)
    assert all("user_observable_outcome" in candidate for candidate in candidates)

    deleted = [candidate for candidate in candidates if candidate["classification"] == "DELETE"]
    assert deleted
    assert "Do not delete or alter code, commits, documents, tests, or historical evidence." in ROADMAP_V02.read_text()


def test_absorbed_candidates_have_pinned_concrete_upstream_evidence_and_no_adoption():
    evidence_records = load_json_block("upstream-capability-evidence-records")
    records_by_id = {record["record_id"]: record for record in evidence_records}
    candidates = load_json_block("future-roadmap-classification-registry")
    absorbed = [candidate for candidate in candidates if candidate["classification"] == "ABSORBED_BY_NANOBOT"]

    assert absorbed
    for candidate in absorbed:
        record = records_by_id[candidate["upstream_evidence_record_id"]]
        assert record["upstream_repository"] == "https://github.com/HKUDS/nanobot"
        assert record["observed_commit"] == "7cede64f078f4435053f4a33964ea719ce582684"
        assert record["reviewed_sources"]
        assert record["capabilities_observed"]
        assert record["sufficiency_assessment"]
        assert record["residual_gap"]
        assert record["dependency_adopted"] is False
        assert record["adoption_authorized"] is False


def test_runtime_freeze_requires_a_documented_blocker_record_and_product_queue_is_not_executable():
    text = ROADMAP_V02.read_text()
    blocker = load_json_block("runtime-blocker-record-schema")
    queue = load_json_block("product-planning-queue")

    assert blocker["packet_type"] == "RuntimeBlockerRecord"
    assert blocker["human_decision_required"] is True
    assert blocker["alternatives_evaluated"] == ["plugin", "adapter", "extension"]
    assert blocker["why_alternatives_do_not_suffice"] == "string"
    assert [item["priority"] for item in queue] == list(range(1, 10))
    assert queue[0]["name"] == "Que se me paso"
    assert all(item["observable_outcome"] for item in queue)
    assert "No entry is `NEXT_ELIGIBLE`" in text
