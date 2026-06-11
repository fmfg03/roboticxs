from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


ResearchRadarPacketType = Literal[
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
]

ResearchRadarDecision = Literal[
    "PREPARE_RESEARCH_PACKET",
    "PREPARE_CONTENT_BRIEF_PACKET",
    "PREPARE_SOURCE_PLAN_ONLY",
    "ASK_CLARIFICATION",
    "REQUIRE_BUDGET_CONFIRMATION",
    "BLOCK_BACKGROUND_MONITORING",
    "BLOCK_UNAPPROVED_SCRAPING",
    "BLOCK_EXTERNAL_ACTION",
    "DEFER_TO_FUTURE_CONNECTOR_STAGE",
]

ResearchFreshnessWindow = Literal[
    "LAST_7_DAYS",
    "LAST_14_DAYS",
    "LAST_30_DAYS",
    "LAST_60_DAYS",
    "CUSTOM_RANGE_REQUIRES_CONFIRMATION",
]

ResearchSourceCategory = Literal[
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
]

ResearchSourceQuality = Literal[
    "PRIMARY",
    "OFFICIAL",
    "HIGH_SIGNAL",
    "SOCIAL_SIGNAL",
    "LOW_SIGNAL",
    "UNKNOWN",
]

ResearchSourceRisk = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "NOISY",
    "UNVERIFIED",
    "POTENTIALLY_MANIPULATED",
]

ResearchBudgetClass = Literal[
    "RESEARCH_LIGHT",
    "RESEARCH_STANDARD",
    "RESEARCH_DEEP",
    "RESEARCH_SOCIAL_MULTI_SOURCE",
    "RESEARCH_LONG_CONTEXT",
    "RESEARCH_BLOCKED_BACKGROUND",
]

ResearchOutputShape = Literal[
    "SOURCE_PLAN",
    "RECENT_SIGNAL_SUMMARY",
    "CONTENT_BRIEF",
    "STRATEGY_NOTE",
    "QUESTION_LIST",
    "RESEARCH_PROMPT",
    "NO_ACTION_NOTICE",
    "BLOCKED_NOTICE",
]

ResearchDownstreamDecision = Literal[
    "NO_ACTION",
    "ASK_USER_FOR_SCOPE",
    "PREPARE_RESEARCH_PLAN",
    "PREPARE_CONTENT_BRIEF_STRUCTURE",
    "PREPARE_MEMORY_CANDIDATE_REVIEW",
    "PREPARE_STRATEGY_REVIEW",
    "DEFER_TO_CONNECTOR_RESEARCH_STAGE",
    "BLOCKED",
]


DEFAULT_FRESHNESS_WINDOW: ResearchFreshnessWindow = "LAST_30_DAYS"
ALLOWED_FRESHNESS_WINDOWS = frozenset(
    {"LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS", "LAST_60_DAYS", "CUSTOM_RANGE_REQUIRES_CONFIRMATION"}
)
SOCIAL_OR_MARKET_SOURCE_CATEGORIES = frozenset(
    {
        "REDDIT_PUBLIC_DISCUSSION",
        "X_PUBLIC_DISCUSSION",
        "YOUTUBE_PUBLIC_CONTENT",
        "HACKER_NEWS_DISCUSSION",
        "POLYMARKET_PUBLIC_MARKET",
    }
)


SOURCE_CATEGORY_REGISTRY: tuple[dict[str, str | bool], ...] = (
    {
        "source_category": "WEB_SEARCH_RESULTS",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": False,
        "source_quality_default": "UNKNOWN",
        "source_risk_default": "MEDIUM",
        "notes": "Planning category only; no live web search is authorized in 72P.",
    },
    {
        "source_category": "OFFICIAL_SOURCE",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": False,
        "source_quality_default": "OFFICIAL",
        "source_risk_default": "LOW",
        "notes": "Official sources are higher-quality planning targets, not live-access authority.",
    },
    {
        "source_category": "GITHUB_REPOSITORY",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": False,
        "source_quality_default": "HIGH_SIGNAL",
        "source_risk_default": "MEDIUM",
        "notes": "Repository signals require later live-access authorization before inspection.",
    },
    {
        "source_category": "REDDIT_PUBLIC_DISCUSSION",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": True,
        "source_quality_default": "SOCIAL_SIGNAL",
        "source_risk_default": "NOISY",
        "notes": "Social discussion is signal, not fact.",
    },
    {
        "source_category": "X_PUBLIC_DISCUSSION",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": True,
        "source_quality_default": "SOCIAL_SIGNAL",
        "source_risk_default": "NOISY",
        "notes": "X discussion is noisy public signal, not proof.",
    },
    {
        "source_category": "YOUTUBE_PUBLIC_CONTENT",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": True,
        "source_quality_default": "SOCIAL_SIGNAL",
        "source_risk_default": "NOISY",
        "notes": "Video/community signal requires later explicit access authority.",
    },
    {
        "source_category": "HACKER_NEWS_DISCUSSION",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": True,
        "source_quality_default": "SOCIAL_SIGNAL",
        "source_risk_default": "NOISY",
        "notes": "Discussion signal is not source-of-truth evidence.",
    },
    {
        "source_category": "POLYMARKET_PUBLIC_MARKET",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": True,
        "source_quality_default": "SOCIAL_SIGNAL",
        "source_risk_default": "POTENTIALLY_MANIPULATED",
        "notes": "Market odds are not truth and may be manipulated.",
    },
    {
        "source_category": "NEWS_ARTICLE",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": False,
        "source_quality_default": "HIGH_SIGNAL",
        "source_risk_default": "MEDIUM",
        "notes": "News articles require source comparison and publication-date checks.",
    },
    {
        "source_category": "BLOG_POST",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": False,
        "source_quality_default": "LOW_SIGNAL",
        "source_risk_default": "UNVERIFIED",
        "notes": "Blog posts are not primary by default.",
    },
    {
        "source_category": "PAPER_OR_PREPRINT",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": False,
        "source_quality_default": "PRIMARY",
        "source_risk_default": "MEDIUM",
        "notes": "Papers/preprints still require recency and venue/context review.",
    },
    {
        "source_category": "COMPANY_DOCS",
        "allowed_in_72P": True,
        "requires_live_access": True,
        "requires_user_confirmation": False,
        "source_quality_default": "OFFICIAL",
        "source_risk_default": "MEDIUM",
        "notes": "Company docs are official for company claims only.",
    },
    {
        "source_category": "USER_PROVIDED_SOURCES",
        "allowed_in_72P": True,
        "requires_live_access": False,
        "requires_user_confirmation": False,
        "source_quality_default": "HIGH_SIGNAL",
        "source_risk_default": "MEDIUM",
        "notes": "User-provided sources must be labeled as user-provided.",
    },
)

SOURCE_REPO_REGISTRY: tuple[dict[str, str | bool], ...] = (
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


@dataclass(frozen=True, slots=True)
class ResearchRadarRequest:
    raw_text: str
    topic: str
    requested_freshness_window: ResearchFreshnessWindow = DEFAULT_FRESHNESS_WINDOW
    requested_sources: tuple[ResearchSourceCategory, ...] = ()
    background_monitoring_requested: bool = False
    scraping_requested: bool = False
    external_action_requested: bool = False
    connector_required: bool = False
    deep_research_requested: bool = False
    social_multi_source_requested: bool = False
    long_context_requested: bool = False
    content_brief_requested: bool = False
    competitor_research_requested: bool = False
    policy_or_regulation_requested: bool = False
    tech_repo_research_requested: bool = False
    user_provided_sources_present: bool = False
    source_event_ref: str | None = None
    user_id: str | None = None
    robot_id: str = "local_robot"
    budget_mode: str = "LOCAL_DEFAULT"
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.requested_freshness_window not in ALLOWED_FRESHNESS_WINDOWS:
            raise ValueError(f"Unknown research freshness window: {self.requested_freshness_window}.")


@dataclass(frozen=True, slots=True)
class ResearchRadarPacket:
    packet_id: str
    packet_type: ResearchRadarPacketType
    research_decision: ResearchRadarDecision
    topic: str
    freshness_window: ResearchFreshnessWindow
    source_categories: tuple[ResearchSourceCategory, ...]
    source_quality_requirements: dict[ResearchSourceCategory, ResearchSourceQuality]
    source_risk_labels: dict[ResearchSourceCategory, ResearchSourceRisk]
    budget_class: ResearchBudgetClass
    requires_budget_confirmation: bool
    requires_user_confirmation: bool
    live_access_authorized: bool
    scraping_authorized: bool
    background_monitoring_authorized: bool
    external_action_authorized: bool
    connector_authorized: bool
    memory_write_authorized: bool
    raw_content_storage_authorized: bool
    summary_claim_level: str
    uncertainty_required: bool
    recommended_output_shape: ResearchOutputShape
    downstream_decision: ResearchDownstreamDecision
    blocked_reason: str | None
    future_stage_required: str | None
    created_at: str

    def __post_init__(self) -> None:
        if self.live_access_authorized:
            raise ValueError("72P cannot authorize live access.")
        if self.scraping_authorized:
            raise ValueError("72P cannot authorize scraping.")
        if self.background_monitoring_authorized:
            raise ValueError("72P cannot authorize background monitoring.")
        if self.external_action_authorized:
            raise ValueError("72P cannot authorize external action.")
        if self.connector_authorized:
            raise ValueError("72P cannot authorize connectors.")
        if self.memory_write_authorized:
            raise ValueError("72P cannot authorize memory writes.")
        if self.raw_content_storage_authorized:
            raise ValueError("72P cannot authorize raw content storage.")


def build_research_radar_packet(request: ResearchRadarRequest) -> ResearchRadarPacket:
    decision = classify_research_radar_request(request)
    source_categories = tuple(infer_source_categories(request))
    budget_class = infer_budget_class(request)

    return ResearchRadarPacket(
        packet_id=f"research_radar_{uuid4().hex}",
        packet_type=infer_research_packet_type(request),
        research_decision=decision,
        topic=request.topic.strip(),
        freshness_window=request.requested_freshness_window or DEFAULT_FRESHNESS_WINDOW,
        source_categories=source_categories,
        source_quality_requirements=_source_quality_requirements(source_categories),
        source_risk_labels=_source_risk_labels(source_categories),
        budget_class=budget_class,
        requires_budget_confirmation=_requires_budget_confirmation(budget_class),
        requires_user_confirmation=_requires_user_confirmation(request, budget_class),
        live_access_authorized=False,
        scraping_authorized=False,
        background_monitoring_authorized=False,
        external_action_authorized=False,
        connector_authorized=False,
        memory_write_authorized=False,
        raw_content_storage_authorized=False,
        summary_claim_level=_summary_claim_level(source_categories, decision),
        uncertainty_required=True,
        recommended_output_shape=_output_shape_for_decision(decision),
        downstream_decision=_downstream_decision_for_decision(decision),
        blocked_reason=_blocked_reason_for_decision(decision),
        future_stage_required=_future_stage_for_decision(decision),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def classify_research_radar_request(request: ResearchRadarRequest) -> ResearchRadarDecision:
    if request.external_action_requested:
        return "BLOCK_EXTERNAL_ACTION"
    if request.background_monitoring_requested:
        return "BLOCK_BACKGROUND_MONITORING"
    if request.scraping_requested:
        return "BLOCK_UNAPPROVED_SCRAPING"
    if request.connector_required:
        return "DEFER_TO_FUTURE_CONNECTOR_STAGE"
    if request.deep_research_requested or request.social_multi_source_requested or request.long_context_requested:
        return "REQUIRE_BUDGET_CONFIRMATION"
    if not request.topic.strip():
        return "ASK_CLARIFICATION"
    if request.content_brief_requested:
        return "PREPARE_CONTENT_BRIEF_PACKET"
    if not request.raw_text.strip():
        return "PREPARE_SOURCE_PLAN_ONLY"
    return "PREPARE_RESEARCH_PACKET"


def infer_research_packet_type(request: ResearchRadarRequest) -> ResearchRadarPacketType:
    if request.external_action_requested:
        return "BLOCKED_EXTERNAL_ACTION_REQUEST"
    if request.background_monitoring_requested:
        return "BLOCKED_MONITORING_REQUEST"
    if request.scraping_requested:
        return "BLOCKED_SCRAPING_REQUEST"
    if request.content_brief_requested:
        return "CONTENT_BRIEF_RESEARCH"
    if request.competitor_research_requested:
        return "COMPETITOR_SIGNAL_RESEARCH"
    if request.policy_or_regulation_requested:
        return "POLICY_OR_REGULATION_RESEARCH"
    if request.tech_repo_research_requested:
        return "TECH_REPO_RESEARCH"
    if request.social_multi_source_requested:
        return "RECENT_SIGNAL_RESEARCH"
    return "RECENT_SIGNAL_RESEARCH"


def infer_source_categories(request: ResearchRadarRequest) -> list[ResearchSourceCategory]:
    if request.requested_sources:
        categories = list(request.requested_sources)
    elif request.content_brief_requested:
        categories = [
            "WEB_SEARCH_RESULTS",
            "NEWS_ARTICLE",
            "BLOG_POST",
            "REDDIT_PUBLIC_DISCUSSION",
            "X_PUBLIC_DISCUSSION",
            "YOUTUBE_PUBLIC_CONTENT",
        ]
    elif request.tech_repo_research_requested:
        categories = ["GITHUB_REPOSITORY", "WEB_SEARCH_RESULTS", "BLOG_POST", "HACKER_NEWS_DISCUSSION"]
    elif request.policy_or_regulation_requested:
        categories = ["OFFICIAL_SOURCE", "NEWS_ARTICLE", "PAPER_OR_PREPRINT", "WEB_SEARCH_RESULTS"]
    elif request.competitor_research_requested:
        categories = ["COMPANY_DOCS", "WEB_SEARCH_RESULTS", "NEWS_ARTICLE", "BLOG_POST"]
    else:
        categories = ["WEB_SEARCH_RESULTS", "NEWS_ARTICLE", "BLOG_POST"]

    if request.social_multi_source_requested:
        categories.extend(["REDDIT_PUBLIC_DISCUSSION", "X_PUBLIC_DISCUSSION", "YOUTUBE_PUBLIC_CONTENT"])
    if request.user_provided_sources_present and "USER_PROVIDED_SOURCES" not in categories:
        categories.append("USER_PROVIDED_SOURCES")
    return _dedupe_categories(categories)


def infer_budget_class(request: ResearchRadarRequest) -> ResearchBudgetClass:
    if request.background_monitoring_requested:
        return "RESEARCH_BLOCKED_BACKGROUND"
    if request.long_context_requested:
        return "RESEARCH_LONG_CONTEXT"
    if request.social_multi_source_requested:
        return "RESEARCH_SOCIAL_MULTI_SOURCE"
    if request.deep_research_requested:
        return "RESEARCH_DEEP"
    if request.content_brief_requested:
        return "RESEARCH_STANDARD"
    if request.requested_freshness_window == "LAST_60_DAYS":
        return "RESEARCH_STANDARD"
    return "RESEARCH_LIGHT"


def _source_quality_requirements(
    categories: tuple[ResearchSourceCategory, ...],
) -> dict[ResearchSourceCategory, ResearchSourceQuality]:
    return {
        category: _registry_value(category, "source_quality_default")  # type: ignore[return-value]
        for category in categories
    }


def _source_risk_labels(
    categories: tuple[ResearchSourceCategory, ...],
) -> dict[ResearchSourceCategory, ResearchSourceRisk]:
    return {
        category: _registry_value(category, "source_risk_default")  # type: ignore[return-value]
        for category in categories
    }


def _registry_value(category: ResearchSourceCategory, key: str) -> str:
    for entry in SOURCE_CATEGORY_REGISTRY:
        if entry["source_category"] == category:
            return str(entry[key])
    return "UNKNOWN"


def _requires_budget_confirmation(budget_class: ResearchBudgetClass) -> bool:
    return budget_class in {"RESEARCH_DEEP", "RESEARCH_SOCIAL_MULTI_SOURCE", "RESEARCH_LONG_CONTEXT"}


def _requires_user_confirmation(request: ResearchRadarRequest, budget_class: ResearchBudgetClass) -> bool:
    return request.requested_freshness_window == "CUSTOM_RANGE_REQUIRES_CONFIRMATION" or _requires_budget_confirmation(
        budget_class
    )


def _summary_claim_level(
    categories: tuple[ResearchSourceCategory, ...],
    decision: ResearchRadarDecision,
) -> str:
    if decision.startswith("BLOCK_"):
        return "blocked_notice_only"
    if any(category in SOCIAL_OR_MARKET_SOURCE_CATEGORIES for category in categories):
        return "signals_not_facts"
    return "plan_only_no_findings"


def _output_shape_for_decision(decision: ResearchRadarDecision) -> ResearchOutputShape:
    if decision.startswith("BLOCK_"):
        return "BLOCKED_NOTICE"
    outputs: dict[ResearchRadarDecision, ResearchOutputShape] = {
        "ASK_CLARIFICATION": "QUESTION_LIST",
        "PREPARE_CONTENT_BRIEF_PACKET": "CONTENT_BRIEF",
        "PREPARE_RESEARCH_PACKET": "RECENT_SIGNAL_SUMMARY",
        "PREPARE_SOURCE_PLAN_ONLY": "SOURCE_PLAN",
        "REQUIRE_BUDGET_CONFIRMATION": "RESEARCH_PROMPT",
        "DEFER_TO_FUTURE_CONNECTOR_STAGE": "RESEARCH_PROMPT",
        "BLOCK_BACKGROUND_MONITORING": "BLOCKED_NOTICE",
        "BLOCK_UNAPPROVED_SCRAPING": "BLOCKED_NOTICE",
        "BLOCK_EXTERNAL_ACTION": "BLOCKED_NOTICE",
    }
    return outputs[decision]


def _downstream_decision_for_decision(decision: ResearchRadarDecision) -> ResearchDownstreamDecision:
    downstream: dict[ResearchRadarDecision, ResearchDownstreamDecision] = {
        "PREPARE_RESEARCH_PACKET": "PREPARE_RESEARCH_PLAN",
        "PREPARE_CONTENT_BRIEF_PACKET": "PREPARE_CONTENT_BRIEF_STRUCTURE",
        "PREPARE_SOURCE_PLAN_ONLY": "PREPARE_RESEARCH_PLAN",
        "ASK_CLARIFICATION": "ASK_USER_FOR_SCOPE",
        "REQUIRE_BUDGET_CONFIRMATION": "ASK_USER_FOR_SCOPE",
        "DEFER_TO_FUTURE_CONNECTOR_STAGE": "DEFER_TO_CONNECTOR_RESEARCH_STAGE",
        "BLOCK_BACKGROUND_MONITORING": "BLOCKED",
        "BLOCK_UNAPPROVED_SCRAPING": "BLOCKED",
        "BLOCK_EXTERNAL_ACTION": "BLOCKED",
    }
    return downstream[decision]


def _blocked_reason_for_decision(decision: ResearchRadarDecision) -> str | None:
    reasons: dict[ResearchRadarDecision, str] = {
        "BLOCK_BACKGROUND_MONITORING": "Background monitoring is outside 72P.",
        "BLOCK_UNAPPROVED_SCRAPING": "Live scraping and raw content collection are not authorized in 72P.",
        "BLOCK_EXTERNAL_ACTION": "External actions, alerts, publishing, or third-party sends are outside 72P.",
    }
    return reasons.get(decision)


def _future_stage_for_decision(decision: ResearchRadarDecision) -> str | None:
    if decision == "DEFER_TO_FUTURE_CONNECTOR_STAGE":
        return "future_connector_research_stage"
    if decision == "BLOCK_UNAPPROVED_SCRAPING":
        return "future_live_research_or_connector_stage"
    if decision == "BLOCK_EXTERNAL_ACTION":
        return "future_explicit_external_action_authority"
    if decision == "BLOCK_BACKGROUND_MONITORING":
        return "future_explicit_monitoring_authority"
    return None


def _dedupe_categories(categories: list[ResearchSourceCategory]) -> list[ResearchSourceCategory]:
    deduped: list[ResearchSourceCategory] = []
    for category in categories:
        if category not in deduped:
            deduped.append(category)
    return deduped
