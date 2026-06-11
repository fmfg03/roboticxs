from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import get_args

from app.research_radar import (
    DEFAULT_FRESHNESS_WINDOW,
    SOURCE_CATEGORY_REGISTRY,
    SOURCE_REPO_REGISTRY,
    ResearchBudgetClass,
    ResearchDownstreamDecision,
    ResearchFreshnessWindow,
    ResearchOutputShape,
    ResearchRadarDecision,
    ResearchRadarPacket,
    ResearchRadarPacketType,
    ResearchRadarRequest,
    ResearchSourceCategory,
    ResearchSourceQuality,
    ResearchSourceRisk,
    build_research_radar_packet,
    classify_research_radar_request,
    infer_budget_class,
    infer_source_categories,
)


DOC_PATH = Path(__file__).resolve().parents[1] / "docs/reference/RESEARCH_RADAR_LAST30DAYS_SKILL_v0_1.md"
ROADMAP_PATH = Path(__file__).resolve().parents[1] / "docs/roadmap/ROBOTICXS_CANONICAL_ROADMAP_v0_1.md"

REQUIRED_PACKET_FIELDS = {
    "packet_id",
    "packet_type",
    "research_decision",
    "topic",
    "freshness_window",
    "source_categories",
    "source_quality_requirements",
    "source_risk_labels",
    "budget_class",
    "requires_budget_confirmation",
    "requires_user_confirmation",
    "live_access_authorized",
    "scraping_authorized",
    "background_monitoring_authorized",
    "external_action_authorized",
    "connector_authorized",
    "memory_write_authorized",
    "raw_content_storage_authorized",
    "summary_claim_level",
    "uncertainty_required",
    "recommended_output_shape",
    "downstream_decision",
    "blocked_reason",
    "future_stage_required",
    "created_at",
}


def request(**overrides) -> ResearchRadarRequest:
    values = {
        "raw_text": "What changed in the last 30 days about agentic AI governance?",
        "topic": "agentic AI governance",
    }
    values.update(overrides)
    return ResearchRadarRequest(**values)


def test_research_radar_taxonomies_are_explicit():
    assert set(get_args(ResearchRadarPacketType)) == {
        "RECENT_SIGNAL_RESEARCH",
        "CONTENT_BRIEF_RESEARCH",
        "COMPETITOR_SIGNAL_RESEARCH",
        "PRODUCT_TREND_RESEARCH",
        "MARKET_NOISE_CHECK",
        "CUSTOMER_LANGUAGE_RESEARCH",
        "TECH_REPO_RESEARCH",
        "POLICY_OR_REGULATION_RESEARCH",
        "BLOCKED_MONITORING_REQUEST",
        "BLOCKED_SCRAPING_REQUEST",
        "BLOCKED_EXTERNAL_ACTION_REQUEST",
    }
    assert set(get_args(ResearchRadarDecision)) == {
        "PREPARE_RESEARCH_PACKET",
        "PREPARE_CONTENT_BRIEF_PACKET",
        "PREPARE_SOURCE_PLAN_ONLY",
        "ASK_CLARIFICATION",
        "REQUIRE_BUDGET_CONFIRMATION",
        "BLOCK_BACKGROUND_MONITORING",
        "BLOCK_UNAPPROVED_SCRAPING",
        "BLOCK_EXTERNAL_ACTION",
        "DEFER_TO_FUTURE_CONNECTOR_STAGE",
    }
    assert set(get_args(ResearchFreshnessWindow)) == {
        "LAST_7_DAYS",
        "LAST_14_DAYS",
        "LAST_30_DAYS",
        "LAST_60_DAYS",
        "CUSTOM_RANGE_REQUIRES_CONFIRMATION",
    }
    assert set(get_args(ResearchSourceCategory)) == {
        "WEB_SEARCH_RESULTS",
        "OFFICIAL_SOURCE",
        "GITHUB_REPOSITORY",
        "REDDIT_PUBLIC_DISCUSSION",
        "X_PUBLIC_DISCUSSION",
        "YOUTUBE_PUBLIC_CONTENT",
        "HACKER_NEWS_DISCUSSION",
        "POLYMARKET_PUBLIC_MARKET",
        "NEWS_ARTICLE",
        "BLOG_POST",
        "PAPER_OR_PREPRINT",
        "COMPANY_DOCS",
        "USER_PROVIDED_SOURCES",
    }
    assert set(get_args(ResearchSourceQuality)) == {
        "PRIMARY",
        "OFFICIAL",
        "HIGH_SIGNAL",
        "SOCIAL_SIGNAL",
        "LOW_SIGNAL",
        "UNKNOWN",
    }
    assert set(get_args(ResearchSourceRisk)) == {
        "LOW",
        "MEDIUM",
        "HIGH",
        "NOISY",
        "UNVERIFIED",
        "POTENTIALLY_MANIPULATED",
    }
    assert set(get_args(ResearchBudgetClass)) == {
        "RESEARCH_LIGHT",
        "RESEARCH_STANDARD",
        "RESEARCH_DEEP",
        "RESEARCH_SOCIAL_MULTI_SOURCE",
        "RESEARCH_LONG_CONTEXT",
        "RESEARCH_BLOCKED_BACKGROUND",
    }
    assert set(get_args(ResearchOutputShape)) == {
        "SOURCE_PLAN",
        "RECENT_SIGNAL_SUMMARY",
        "CONTENT_BRIEF",
        "STRATEGY_NOTE",
        "QUESTION_LIST",
        "RESEARCH_PROMPT",
        "NO_ACTION_NOTICE",
        "BLOCKED_NOTICE",
    }
    assert set(get_args(ResearchDownstreamDecision)) == {
        "NO_ACTION",
        "ASK_USER_FOR_SCOPE",
        "PREPARE_RESEARCH_PLAN",
        "PREPARE_CONTENT_BRIEF_STRUCTURE",
        "PREPARE_MEMORY_CANDIDATE_REVIEW",
        "PREPARE_STRATEGY_REVIEW",
        "DEFER_TO_CONNECTOR_RESEARCH_STAGE",
        "BLOCKED",
    }


def test_packet_contains_required_fields():
    packet = build_research_radar_packet(request())

    assert isinstance(packet, ResearchRadarPacket)
    assert {field.name for field in fields(packet)} == REQUIRED_PACKET_FIELDS
    assert packet.packet_id.startswith("research_radar_")


def test_all_packets_disable_authority_flags():
    scenarios = [
        request(),
        request(background_monitoring_requested=True),
        request(scraping_requested=True),
        request(external_action_requested=True),
        request(connector_required=True),
        request(deep_research_requested=True),
        request(content_brief_requested=True),
    ]

    for scenario in scenarios:
        packet = build_research_radar_packet(scenario)
        assert packet.live_access_authorized is False
        assert packet.scraping_authorized is False
        assert packet.background_monitoring_authorized is False
        assert packet.external_action_authorized is False
        assert packet.connector_authorized is False
        assert packet.memory_write_authorized is False
        assert packet.raw_content_storage_authorized is False


def test_default_freshness_window_is_last_30_days():
    packet = build_research_radar_packet(request())

    assert DEFAULT_FRESHNESS_WINDOW == "LAST_30_DAYS"
    assert packet.freshness_window == "LAST_30_DAYS"


def test_background_monitoring_blocks():
    packet = build_research_radar_packet(
        request(raw_text="Monitor Reddit and X every day and alert me.", background_monitoring_requested=True)
    )

    assert packet.packet_type == "BLOCKED_MONITORING_REQUEST"
    assert packet.research_decision == "BLOCK_BACKGROUND_MONITORING"
    assert packet.budget_class == "RESEARCH_BLOCKED_BACKGROUND"
    assert packet.blocked_reason == "Background monitoring is outside 72P."
    assert packet.recommended_output_shape == "BLOCKED_NOTICE"


def test_scraping_request_blocks():
    packet = build_research_radar_packet(
        request(raw_text="Scrape X, Reddit, and YouTube posts.", scraping_requested=True)
    )

    assert packet.packet_type == "BLOCKED_SCRAPING_REQUEST"
    assert packet.research_decision == "BLOCK_UNAPPROVED_SCRAPING"
    assert packet.blocked_reason == "Live scraping and raw content collection are not authorized in 72P."


def test_external_action_request_blocks():
    packet = build_research_radar_packet(
        request(raw_text="Research this and publish a post automatically.", external_action_requested=True)
    )

    assert packet.packet_type == "BLOCKED_EXTERNAL_ACTION_REQUEST"
    assert packet.research_decision == "BLOCK_EXTERNAL_ACTION"
    assert packet.downstream_decision == "BLOCKED"
    assert packet.external_action_authorized is False


def test_connector_required_request_defers():
    packet = build_research_radar_packet(request(connector_required=True))

    assert classify_research_radar_request(request(connector_required=True)) == "DEFER_TO_FUTURE_CONNECTOR_STAGE"
    assert packet.research_decision == "DEFER_TO_FUTURE_CONNECTOR_STAGE"
    assert packet.downstream_decision == "DEFER_TO_CONNECTOR_RESEARCH_STAGE"
    assert packet.future_stage_required == "future_connector_research_stage"


def test_empty_topic_asks_clarification():
    packet = build_research_radar_packet(request(topic=""))

    assert packet.research_decision == "ASK_CLARIFICATION"
    assert packet.recommended_output_shape == "QUESTION_LIST"
    assert packet.downstream_decision == "ASK_USER_FOR_SCOPE"


def test_deep_social_and_long_context_research_require_budget_confirmation():
    scenarios = [
        (request(deep_research_requested=True), "RESEARCH_DEEP"),
        (request(social_multi_source_requested=True), "RESEARCH_SOCIAL_MULTI_SOURCE"),
        (request(long_context_requested=True), "RESEARCH_LONG_CONTEXT"),
    ]

    for scenario, budget_class in scenarios:
        packet = build_research_radar_packet(scenario)
        assert packet.research_decision == "REQUIRE_BUDGET_CONFIRMATION"
        assert packet.budget_class == budget_class
        assert packet.requires_budget_confirmation is True
        assert packet.requires_user_confirmation is True
        assert packet.recommended_output_shape == "RESEARCH_PROMPT"


def test_content_brief_request_maps_to_content_brief_packet():
    packet = build_research_radar_packet(
        request(raw_text="Research the last 30 days for a post about AI SEO.", content_brief_requested=True)
    )

    assert packet.packet_type == "CONTENT_BRIEF_RESEARCH"
    assert packet.research_decision == "PREPARE_CONTENT_BRIEF_PACKET"
    assert packet.recommended_output_shape == "CONTENT_BRIEF"
    assert packet.downstream_decision == "PREPARE_CONTENT_BRIEF_STRUCTURE"
    assert {"WEB_SEARCH_RESULTS", "NEWS_ARTICLE", "BLOG_POST", "REDDIT_PUBLIC_DISCUSSION", "X_PUBLIC_DISCUSSION", "YOUTUBE_PUBLIC_CONTENT"}.issubset(packet.source_categories)


def test_tech_repo_request_includes_github_source_category():
    packet = build_research_radar_packet(request(tech_repo_research_requested=True))

    assert packet.packet_type == "TECH_REPO_RESEARCH"
    assert "GITHUB_REPOSITORY" in packet.source_categories
    assert "HACKER_NEWS_DISCUSSION" in packet.source_categories
    assert infer_budget_class(request(tech_repo_research_requested=True)) == "RESEARCH_LIGHT"


def test_policy_or_regulation_request_includes_official_sources():
    packet = build_research_radar_packet(request(policy_or_regulation_requested=True))

    assert packet.packet_type == "POLICY_OR_REGULATION_RESEARCH"
    assert "OFFICIAL_SOURCE" in packet.source_categories
    assert "PAPER_OR_PREPRINT" in packet.source_categories


def test_social_source_categories_are_noisy_social_signal():
    packet = build_research_radar_packet(
        request(social_multi_source_requested=True, requested_sources=("REDDIT_PUBLIC_DISCUSSION", "X_PUBLIC_DISCUSSION"))
    )

    assert packet.source_quality_requirements["REDDIT_PUBLIC_DISCUSSION"] == "SOCIAL_SIGNAL"
    assert packet.source_quality_requirements["X_PUBLIC_DISCUSSION"] == "SOCIAL_SIGNAL"
    assert packet.source_risk_labels["REDDIT_PUBLIC_DISCUSSION"] == "NOISY"
    assert packet.source_risk_labels["X_PUBLIC_DISCUSSION"] == "NOISY"
    assert packet.summary_claim_level == "signals_not_facts"


def test_polymarket_is_potentially_manipulated_signal():
    packet = build_research_radar_packet(
        request(requested_sources=("POLYMARKET_PUBLIC_MARKET",))
    )

    assert packet.source_quality_requirements["POLYMARKET_PUBLIC_MARKET"] == "SOCIAL_SIGNAL"
    assert packet.source_risk_labels["POLYMARKET_PUBLIC_MARKET"] == "POTENTIALLY_MANIPULATED"


def test_official_and_user_provided_sources_are_higher_quality():
    packet = build_research_radar_packet(
        request(policy_or_regulation_requested=True, user_provided_sources_present=True)
    )

    assert packet.source_quality_requirements["OFFICIAL_SOURCE"] == "OFFICIAL"
    assert packet.source_risk_labels["OFFICIAL_SOURCE"] == "LOW"
    assert "USER_PROVIDED_SOURCES" in packet.source_categories
    assert packet.source_quality_requirements["USER_PROVIDED_SOURCES"] == "HIGH_SIGNAL"
    assert packet.source_risk_labels["USER_PROVIDED_SOURCES"] == "MEDIUM"


def test_source_category_taxonomy_exists_with_required_fields():
    required_fields = {
        "source_category",
        "allowed_in_72P",
        "requires_live_access",
        "requires_user_confirmation",
        "source_quality_default",
        "source_risk_default",
        "notes",
    }

    assert {entry["source_category"] for entry in SOURCE_CATEGORY_REGISTRY} == set(get_args(ResearchSourceCategory))
    for entry in SOURCE_CATEGORY_REGISTRY:
        assert set(entry) == required_fields
        assert entry["allowed_in_72P"] is True


def test_source_repo_register_keeps_last30days_as_reference_only():
    assert SOURCE_REPO_REGISTRY == (
        {
            "source_id": "last30days_skill_source_repo",
            "repo": "https://github.com/mvanhorn/last30days-skill",
            "owner": "mvanhorn",
            "role": "inspiration / architecture reference only",
            "allowed_use_in_72P": "research_reference_only",
            "dependency_authorized": False,
            "code_vendor_authorized": False,
            "live_scraping_authorized": False,
            "external_api_authorized": False,
            "reason": "72P defines Roboticxs' bounded research-radar packet contract before any live research or skill integration.",
        },
    )


def test_output_shape_is_plan_or_structure_only():
    for scenario in [
        request(),
        request(content_brief_requested=True),
        request(deep_research_requested=True),
        request(background_monitoring_requested=True),
    ]:
        packet = build_research_radar_packet(scenario)
        assert packet.recommended_output_shape in {
            "SOURCE_PLAN",
            "RECENT_SIGNAL_SUMMARY",
            "CONTENT_BRIEF",
            "QUESTION_LIST",
            "RESEARCH_PROMPT",
            "BLOCKED_NOTICE",
        }
        assert packet.live_access_authorized is False


def test_no_memory_write_authorized():
    packet = build_research_radar_packet(request())

    assert packet.memory_write_authorized is False
    assert packet.downstream_decision == "PREPARE_RESEARCH_PLAN"


def test_infer_source_categories_includes_user_provided_once():
    categories = infer_source_categories(
        request(
            requested_sources=("WEB_SEARCH_RESULTS", "USER_PROVIDED_SOURCES"),
            user_provided_sources_present=True,
        )
    )

    assert categories.count("USER_PROVIDED_SOURCES") == 1


def test_decision_precedence_is_deterministic():
    scenario = request(
        external_action_requested=True,
        background_monitoring_requested=True,
        scraping_requested=True,
        connector_required=True,
        deep_research_requested=True,
    )

    assert classify_research_radar_request(scenario) == "BLOCK_EXTERNAL_ACTION"


def test_docs_contain_required_non_claims():
    text = DOC_PATH.read_text()

    for required in [
        "Last30Days-style recent research",
        "local packet builder only",
        "Roboticxs does not scrape Reddit, X, YouTube, Hacker News, Polymarket, or the web in 72P.",
        "Roboticxs does not continuously monitor topics in 72P.",
        "Roboticxs does not call external research APIs in 72P.",
        "Roboticxs does not run browser automation in 72P.",
        "Roboticxs does not store raw source content in 72P.",
        "Roboticxs does not treat social engagement as truth.",
        "Roboticxs does not write research insights to memory automatically.",
        "Roboticxs does not send alerts automatically.",
        "Roboticxs does not activate connectors for Research Radar in 72P.",
        "Roboticxs does not vendor or depend on `mvanhorn/last30days-skill` in 72P.",
        "73P Understand-Anything + codegraph Factory Skill becomes the next eligible stage.",
    ]:
        assert required in text


def test_roadmap_marks_72p_completed_and_73p_next_after_closeout():
    text = ROADMAP_PATH.read_text()

    assert '"stage_id":"72P","stage_name":"Research Radar / Last30Days Skill","status":"COMPLETED_FIXED_BASELINE"' in text
    assert '"commit":"same_commit_as_72P_closeout"' in text
    assert '"app/research_radar.py"' in text
    assert '"docs/reference/RESEARCH_RADAR_LAST30DAYS_SKILL_v0_1.md"' in text
    assert '"tests/test_research_radar.py"' in text
    assert '"stage_id":"74P","stage_name":"ECC Knowledge Compiler Factory Skill","status":"NEXT_ELIGIBLE"' in text
    assert '"after_commit_next_eligible":"74P"' in text
