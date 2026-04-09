from __future__ import annotations

from typing import Any

from core.agents.trend_hunter import run_trend_hunter
from core.compliance_config import get_market_by_code
from utils.tavily_client import search_viral_video_benchmarks


def explore_trends(
    *,
    topic: str | None,
    target_country: str,
    target_platform: str,
    distribution_mode: str,
    product_category: str,
    target_languages: list[str],
) -> dict[str, Any]:
    market = get_market_by_code(target_country.upper())
    country_label = (market or {}).get("label", target_country.upper())
    base_state = {
        "topic": topic or "",
        "target_country": target_country,
        "target_platform": target_platform,
        "distribution_mode": distribution_mode,
        "product_category": product_category,
        "target_languages": target_languages,
    }

    trend_result: dict[str, Any] = {
        "trend_query": "",
        "trend_data": "",
        "trend_sources": [],
    }
    if topic:
        trend_result = run_trend_hunter(base_state)

    benchmarks: list[dict[str, Any]] = []
    benchmarks_error = ""
    try:
        benchmarks = search_viral_video_benchmarks(
            platform=target_platform,
            country_label=country_label,
            days=3,
            max_results=4,
        )
    except Exception as exc:
        benchmarks_error = str(exc)

    return {
        "filters": {
            "topic": topic,
            "target_country": target_country,
            "target_platform": target_platform,
            "distribution_mode": distribution_mode,
            "product_category": product_category,
            "target_languages": target_languages,
        },
        "trend_hunter": trend_result,
        "benchmarks": benchmarks,
        "benchmarks_error": benchmarks_error,
    }
