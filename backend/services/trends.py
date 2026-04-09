from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable
from urllib.parse import urlparse

from backend.db import fetch_trend_snapshot, upsert_trend_snapshot
from core.agents.trend_hunter import run_trend_hunter
from core.compliance_config import get_market_by_code
from utils.tavily_client import search_viral_video_benchmarks, tavily_search


INDUSTRY_LABELS = {
    "technology": "科技行业",
    "video": "视频行业",
    "marketing": "营销行业",
}
INDUSTRY_QUERY_TEMPLATES = {
    "technology": (
        "{country_label} technology AI creator economy consumer tech platform update "
        "{platform} short video trend {topic_hint} last 7 days"
    ),
    "video": (
        "{country_label} short-form video industry creator monetization platform update "
        "{platform} video commerce retention trend {topic_hint} last 7 days"
    ),
    "marketing": (
        "{country_label} influencer marketing creator partnership paid social brand campaign "
        "{platform} social commerce trend {topic_hint} last 7 days"
    ),
}


def _compact_text(value: str | None, limit: int = 220) -> str:
    if not value:
        return ""
    collapsed = " ".join(str(value).split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _build_scope_key(filters: dict[str, Any]) -> str:
    return json.dumps(filters, ensure_ascii=False, sort_keys=True)


def _module_response(
    *,
    module_name: str,
    scope_key: str,
    filters: dict[str, Any],
    refresh: bool,
    loader: Callable[[], dict[str, Any]],
    empty_payload: dict[str, Any],
) -> dict[str, Any]:
    cached_snapshot = fetch_trend_snapshot(module_name, scope_key)

    if cached_snapshot and not refresh:
        return {
            **empty_payload,
            **cached_snapshot["payload"],
            "from_cache": True,
            "stale": False,
            "cached_at": cached_snapshot["updated_at"],
        }

    try:
        payload = loader()
        saved_snapshot = upsert_trend_snapshot(
            module_name=module_name,
            scope_key=scope_key,
            filters=filters,
            payload=payload,
        )
        return {
            **empty_payload,
            **payload,
            "from_cache": False,
            "stale": False,
            "cached_at": saved_snapshot["updated_at"],
        }
    except Exception as exc:
        if cached_snapshot:
            return {
                **empty_payload,
                **cached_snapshot["payload"],
                "error": str(exc),
                "from_cache": True,
                "stale": True,
                "cached_at": cached_snapshot["updated_at"],
            }
        return {
            **empty_payload,
            "error": str(exc),
            "from_cache": False,
            "stale": False,
            "cached_at": "",
        }


def _build_industry_query(
    category_key: str,
    *,
    country_label: str,
    target_platform: str,
    topic: str | None,
) -> str:
    topic_hint = _compact_text(topic, limit=80) if topic else "creator economy"
    template = INDUSTRY_QUERY_TEMPLATES[category_key]
    return template.format(
        country_label=country_label,
        platform=target_platform,
        topic_hint=topic_hint,
    )


def _build_topic_brief(
    *,
    base_state: dict[str, Any],
    refresh_token: str,
) -> dict[str, Any]:
    if not str(base_state.get("topic", "")).strip():
        return {
            "trend_query": "",
            "trend_data": "未填写主题时，这里只展示行业情报与热点视频缓存。",
            "trend_sources": [],
        }
    return run_trend_hunter(base_state, cache_buster=refresh_token)


def _search_industry_category(
    category_key: str,
    *,
    country_label: str,
    country_for_search: str,
    target_platform: str,
    topic: str | None,
    refresh_token: str,
) -> dict[str, Any]:
    query = _build_industry_query(
        category_key,
        country_label=country_label,
        target_platform=target_platform,
        topic=topic,
    )
    response = tavily_search(
        query=query,
        country=country_for_search,
        days=7,
        max_results=4,
        include_answer="advanced",
        include_images=False,
        search_depth="advanced",
        cache_buster=refresh_token,
    )

    articles = []
    for item in (response.get("results", []) or [])[:4]:
        url = str(item.get("url", "") or "")
        articles.append(
            {
                "title": _compact_text(item.get("title", ""), limit=96) or INDUSTRY_LABELS[category_key],
                "url": url,
                "summary": _compact_text(item.get("content", ""), limit=180),
                "source": urlparse(url).netloc or "web",
                "score": item.get("score", 0.0) or 0.0,
            }
        )

    summary = _compact_text(str(response.get("answer", "") or ""), limit=340)
    if not summary and articles:
        summary = " ".join(article["summary"] for article in articles[:2] if article["summary"]).strip()

    return {
        "key": category_key,
        "label": INDUSTRY_LABELS[category_key],
        "query": query,
        "summary": summary,
        "articles": articles,
    }


def explore_trends(
    *,
    topic: str | None,
    target_country: str,
    target_platform: str,
    distribution_mode: str,
    product_category: str,
    target_languages: list[str],
    refresh_videos: bool = False,
    refresh_industry: bool = False,
) -> dict[str, Any]:
    market = get_market_by_code(target_country.upper())
    country_label = (market or {}).get("label", target_country.upper())
    country_for_search = country_label.lower()
    normalized_filters = {
        "topic": topic or "",
        "target_country": target_country,
        "target_platform": target_platform,
        "distribution_mode": distribution_mode,
        "product_category": product_category,
        "target_languages": target_languages,
    }
    refresh_token = datetime.utcnow().isoformat()
    base_state = {
        "topic": topic or "",
        "target_country": target_country,
        "target_platform": target_platform,
        "distribution_mode": distribution_mode,
        "product_category": product_category,
        "target_languages": target_languages,
    }

    videos_scope_key = _build_scope_key(
        {
            **normalized_filters,
            "module": "videos",
        }
    )
    industry_scope_key = _build_scope_key(
        {
            **normalized_filters,
            "module": "industry",
        }
    )

    videos = _module_response(
        module_name="videos",
        scope_key=videos_scope_key,
        filters=normalized_filters,
        refresh=refresh_videos,
        empty_payload={"items": [], "error": ""},
        loader=lambda: {
            "items": search_viral_video_benchmarks(
                platform=target_platform,
                country_label=country_label,
                days=3,
                max_results=6,
                topic=topic or "",
                product_category=product_category,
                distribution_mode=distribution_mode,
                cache_buster=refresh_token,
            ),
            "error": "",
        },
    )

    industry = _module_response(
        module_name="industry",
        scope_key=industry_scope_key,
        filters=normalized_filters,
        refresh=refresh_industry,
        empty_payload={
            "topic_brief": {
                "trend_query": "",
                "trend_data": "",
                "trend_sources": [],
            },
            "categories": [],
            "error": "",
        },
        loader=lambda: {
            "topic_brief": _build_topic_brief(
                base_state=base_state,
                refresh_token=refresh_token,
            ),
            "categories": [
                _search_industry_category(
                    category_key,
                    country_label=country_label,
                    country_for_search=country_for_search,
                    target_platform=target_platform,
                    topic=topic,
                    refresh_token=refresh_token,
                )
                for category_key in ("technology", "video", "marketing")
            ],
            "error": "",
        },
    )

    return {
        "filters": normalized_filters,
        "videos": videos,
        "industry": industry,
        "trend_hunter": industry.get("topic_brief", {}),
        "benchmarks": videos.get("items", []),
        "benchmarks_error": videos.get("error", ""),
    }
