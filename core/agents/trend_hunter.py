from __future__ import annotations

from typing import Any

from core.compliance_config import (
    canonicalize_language,
    canonicalize_platform,
    get_market_by_code,
)
from utils.tavily_client import tavily_search


PLATFORM_HINTS = {
    "tiktok": "short-form video trends, creator hooks, UGC style, viral editing patterns",
    "instagram": "reels trends, influencer hooks, product storytelling, visual-first angles",
    "youtube": "shorts trends, search-friendly hooks, retention patterns, creator talking points",
    "x": "conversation spikes, punchy talking points, meme angles, reply-driven hooks",
    "reddit": "community pain points, authentic proof points, discussion-led angles, objections",
    "discord": "community activation, launch messaging, event hooks, insider language",
    "douyin": "short-form hooks, high-retention editing, creator product demo formats",
}

MODE_HINTS = {
    "organic": "focus on audience interest, discoverability, creator-native storytelling",
    "branded_content": "focus on sponsor-safe hooks, creator-brand fit, disclosure-friendly formats",
    "paid_ads": "focus on ad-safe claims, conversion hooks, policy-sensitive wording",
}


def _compact_text(value: str | None, limit: int = 220) -> str:
    if not value:
        return ""
    collapsed = " ".join(str(value).split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _build_query(state: dict) -> tuple[str, str]:
    topic = str(state.get("topic", "")).strip()
    country_code = str(state.get("target_country", "US")).upper()
    platform = canonicalize_platform(state.get("target_platform", "tiktok"))
    distribution_mode = str(state.get("distribution_mode", "branded_content")).lower()
    product_category = str(state.get("product_category", "general")).lower().replace("_", " ")
    target_languages = state.get("target_languages", []) or []

    market = get_market_by_code(country_code)
    country_label = (market or {}).get("label", country_code)
    country_for_search = country_label.lower()

    normalized_languages = [
        canonicalize_language(str(item)) or str(item).lower()
        for item in target_languages
    ]
    language_hint = ", ".join(normalized_languages[:3]) if normalized_languages else "en"
    platform_hint = PLATFORM_HINTS.get(platform, "platform trends, hooks, creative angles")
    mode_hint = MODE_HINTS.get(distribution_mode, "campaign-safe messaging and creator-native angles")

    query = (
        f"{topic} {country_label} {platform} {product_category} social media trend "
        f"viral hooks creator insights audience pain points {platform_hint} {mode_hint} "
        f"content examples language {language_hint}"
    )
    return query, country_for_search


def _format_trend_data(state: dict, response: dict[str, Any], query: str) -> str:
    country_code = str(state.get("target_country", "US")).upper()
    platform = canonicalize_platform(state.get("target_platform", "tiktok"))
    results = response.get("results", []) or []
    answer = _compact_text(str(response.get("answer", "")).strip(), limit=420)

    lines = [
        "[Live Trend Intelligence]",
        f"- Market: {country_code}",
        f"- Platform: {platform}",
        f"- Search Query: {query}",
    ]
    if answer:
        lines.append(f"- Summary: {answer}")

    if results:
        lines.append("- Recent Signals:")
        for index, item in enumerate(results[:4], start=1):
            title = _compact_text(item.get("title", ""), limit=110) or f"Signal {index}"
            content = _compact_text(item.get("content", ""), limit=180)
            domain = item.get("url", "")
            score = item.get("score")
            score_suffix = f" (score: {score:.2f})" if isinstance(score, (int, float)) else ""
            signal_line = f"  {index}. {title}{score_suffix}"
            if content:
                signal_line += f" — {content}"
            if domain:
                signal_line += f" [{domain}]"
            lines.append(signal_line)
    else:
        lines.append("- Recent Signals: No reliable live search results were returned.")

    return "\n".join(lines)


def _fallback_trend_data(state: dict, query: str, reason: str) -> str:
    topic = str(state.get("topic", "")).strip() or "this topic"
    platform = canonicalize_platform(state.get("target_platform", "tiktok"))
    distribution_mode = str(state.get("distribution_mode", "branded_content")).lower()
    return "\n".join(
        [
            "[Trend Intelligence Fallback]",
            f"- Topic: {topic}",
            f"- Platform: {platform}",
            f"- Distribution Mode: {distribution_mode}",
            f"- Search Query Attempted: {query}",
            f"- Live Search Status: {reason}",
            "- Working Assumption: prioritize a fast hook in the first 3 seconds, explicit product payoff, audience pain point framing, and creator-native wording.",
        ]
    )


def run_trend_hunter(state: dict) -> dict:
    print("🤖 [Agent] Trend Hunter 执行中: 正在全网检索热点...")
    query, country_for_search = _build_query(state)

    try:
        response = tavily_search(
            query=query,
            country=country_for_search,
            days=30,
            max_results=5,
        )
        trend_data = _format_trend_data(state, response, query)
        trend_sources = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "score": item.get("score", ""),
                "content": _compact_text(item.get("content", ""), limit=240),
            }
            for item in (response.get("results", []) or [])[:5]
        ]
        print(f"✅ [Trend Hunter] Tavily 返回 {len(trend_sources)} 条实时结果。")
        return {
            "trend_query": query,
            "trend_data": trend_data,
            "trend_sources": trend_sources,
        }
    except Exception as exc:
        print(f"⚠️ [Trend Hunter] Tavily 搜索失败，回退到本地趋势模板: {exc}")
        return {
            "trend_query": query,
            "trend_data": _fallback_trend_data(state, query, str(exc)),
            "trend_sources": [],
        }
