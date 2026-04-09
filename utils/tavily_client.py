from __future__ import annotations

import os
import re
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient


current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)


SUPPORTED_VIRAL_PLATFORMS = ("tiktok", "instagram", "x")
PLATFORM_DOMAINS = {
    "tiktok": ("tiktok.com",),
    "instagram": ("instagram.com",),
    "x": ("x.com", "twitter.com"),
}
PLATFORM_LABELS = {
    "tiktok": "TikTok",
    "instagram": "Instagram Reels",
    "x": "X",
}
VIRAL_QUERY_HINTS = {
    "tiktok": (
        "{country} {focus} TikTok viral video public creator post last {days} days",
        "{country} {focus} TikTok short video trending example public post",
    ),
    "instagram": (
        "{country} {focus} Instagram Reels viral creator video last {days} days",
        "{country} {focus} Instagram Reels high views creator example",
    ),
    "x": (
        "{country} {focus} X Twitter viral video creator post last {days} days",
        "{country} {focus} X Twitter trending clip high engagement",
    ),
}
PRODUCT_CATEGORY_HINTS = {
    "general": "creator storytelling",
    "beauty": "beauty skincare makeup creator review",
    "electronics": "tech gadget electronics creator review",
    "fashion": "fashion outfit styling creator review",
    "food_beverage": "food beverage snack drink creator review",
    "health_supplement": "health supplement wellness creator review",
}
DISTRIBUTION_QUERY_HINTS = {
    "organic": "organic creator trend audience engagement",
    "branded_content": "brand partnership creator sponsored style",
    "paid_ads": "performance creative paid social winning ad",
}
VIEW_PATTERNS = (
    re.compile(r"(\d+(?:\.\d+)?)\s*([mk])\s*(?:views?|plays?)", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?)\s*million\s*(?:views?|plays?)", re.IGNORECASE),
    re.compile(r"([1-9]\d{0,2}(?:,\d{3})+)\s*(?:views?|plays?)", re.IGNORECASE),
)
RELATIVE_DATE_PATTERN = re.compile(r"(\d+)\s*([dhw])\s*ago", re.IGNORECASE)
ISO_DATE_PATTERN = re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b")
SHORT_DATE_PATTERN = re.compile(r"[·•]\s*(\d{1,2})-(\d{1,2})\b")
LONG_DATE_PATTERNS = (
    re.compile(r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b"),
    re.compile(r"\b([A-Z][a-z]+ \d{1,2},\s*20\d{2})\b"),
)


def _mask_key(api_key: str) -> str:
    if len(api_key) <= 10:
        return "*" * len(api_key)
    return f"{api_key[:8]}...{api_key[-4:]}"


@lru_cache(maxsize=1)
def get_tavily_client() -> Optional[TavilyClient]:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        print("⚠️ [Tavily] TAVILY_API_KEY 未配置，Trend Hunter 将回退到本地占位趋势。")
        return None

    print(f"🔎 [Tavily] 使用 API Key: {_mask_key(api_key)}")
    return TavilyClient(api_key=api_key)


def _compact_text(value: str | None, limit: int = 180) -> str:
    if not value:
        return ""
    collapsed = " ".join(str(value).split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _normalize_focus_text(topic: str, product_category: str, distribution_mode: str) -> str:
    focus_parts: list[str] = []
    cleaned_topic = " ".join(topic.split()).strip()
    if cleaned_topic:
        focus_parts.append(cleaned_topic)

    category_hint = PRODUCT_CATEGORY_HINTS.get(
        product_category,
        product_category.replace("_", " ").strip(),
    ).strip()
    if category_hint:
        focus_parts.append(category_hint)

    mode_hint = DISTRIBUTION_QUERY_HINTS.get(distribution_mode, "").strip()
    if mode_hint:
        focus_parts.append(mode_hint)

    normalized = " ".join(part for part in focus_parts if part).strip()
    return normalized or "creator product storytelling"


def _infer_platform_from_url(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if "tiktok.com" in domain:
        return "tiktok"
    if "instagram.com" in domain:
        return "instagram"
    if "x.com" in domain or "twitter.com" in domain:
        return "x"
    return ""


def _extract_view_count(text: str) -> int | None:
    content = text or ""
    for pattern in VIEW_PATTERNS:
        match = pattern.search(content)
        if not match:
            continue
        groups = [group for group in match.groups() if group]
        if not groups:
            continue
        if len(groups) == 2 and groups[1].lower() in {"m", "k"}:
            value = float(groups[0])
            multiplier = 1_000_000 if groups[1].lower() == "m" else 1_000
            return int(value * multiplier)
        numeric_value = groups[0].replace(",", "")
        if "million" in match.group(0).lower():
            return int(float(numeric_value) * 1_000_000)
        return int(float(numeric_value))

    lowered = content.lower()
    if "million views" in lowered or "million plays" in lowered:
        return 1_000_000
    return None


def _format_view_count(view_count: int) -> str:
    if view_count >= 1_000_000:
        return f"{view_count / 1_000_000:.1f}M"
    if view_count >= 1_000:
        return f"{view_count / 1_000:.1f}K"
    return str(view_count)


def _extract_age_days(text: str) -> int | None:
    content = text or ""
    lowered = content.lower()
    now = datetime.now().date()

    relative_match = RELATIVE_DATE_PATTERN.search(lowered)
    if relative_match:
        quantity = int(relative_match.group(1))
        unit = relative_match.group(2).lower()
        if unit == "h":
            return 0
        if unit == "d":
            return quantity
        if unit == "w":
            return quantity * 7

    iso_match = ISO_DATE_PATTERN.search(content)
    if iso_match:
        try:
            published = datetime(
                int(iso_match.group(1)),
                int(iso_match.group(2)),
                int(iso_match.group(3)),
            ).date()
            return abs((now - published).days)
        except ValueError:
            pass

    for pattern in LONG_DATE_PATTERNS:
        long_match = pattern.search(content)
        if not long_match:
            continue
        try:
            published = datetime.strptime(long_match.group(1).replace("  ", " "), "%B %d, %Y").date()
            return abs((now - published).days)
        except ValueError:
            continue

    short_match = SHORT_DATE_PATTERN.search(content)
    if short_match:
        try:
            published = datetime(now.year, int(short_match.group(1)), int(short_match.group(2))).date()
            return abs((now - published).days)
        except ValueError:
            return None

    return None


def _build_viral_queries(
    platform: str,
    country_label: str,
    *,
    topic: str = "",
    product_category: str = "",
    distribution_mode: str = "",
    days: int = 3,
) -> tuple[str, ...]:
    country_hint = country_label.strip() or "global"
    focus_text = _normalize_focus_text(topic, product_category, distribution_mode)
    platform_hints = VIRAL_QUERY_HINTS.get(
        platform,
        ("{country} {focus} viral social video public post last {days} days",),
    )
    return tuple(
        platform_hint.format(country=country_hint, focus=focus_text, days=days)
        for platform_hint in platform_hints
    )


@lru_cache(maxsize=64)
def tavily_search(
    query: str,
    country: str = "",
    days: int = 30,
    max_results: int = 5,
    include_domains: tuple[str, ...] = (),
    include_answer: str | bool = "advanced",
    include_images: bool = False,
    search_depth: str = "basic",
    timeout: int = 45,
    cache_buster: str = "",
) -> dict[str, Any]:
    client = get_tavily_client()
    if client is None:
        raise RuntimeError("Tavily client is not configured.")

    _ = cache_buster

    search_kwargs = {
        "query": query,
        "topic": "general",
        "days": days,
        "max_results": max_results,
        "include_answer": include_answer,
        "include_images": include_images,
        "include_favicon": True,
        "search_depth": search_depth,
        "timeout": timeout,
    }
    if include_domains:
        search_kwargs["include_domains"] = list(include_domains)
    if country:
        search_kwargs["country"] = country

    last_exc: Exception | None = None
    response: dict[str, Any] | None = None
    for attempt in range(2):
        try:
            response = client.search(**search_kwargs)
            break
        except Exception as exc:
            last_exc = exc
            if attempt == 1:
                raise
            time.sleep(0.5)

    if response is None:
        raise RuntimeError(f"Tavily search failed: {last_exc}")

    results = response.get("results", []) or []
    if results or response.get("answer"):
        return response

    if search_kwargs["search_depth"] == "advanced":
        return response

    search_kwargs["search_depth"] = "advanced"
    return client.search(**search_kwargs)


def search_viral_video_benchmarks(
    platform: str = "",
    country_label: str = "",
    days: int = 3,
    max_results: int = 4,
    minimum_view_count: int = 100_000,
    topic: str = "",
    product_category: str = "",
    distribution_mode: str = "",
    cache_buster: str = "",
) -> list[dict[str, Any]]:
    requested_platforms = [platform] if platform in SUPPORTED_VIRAL_PLATFORMS else list(SUPPORTED_VIRAL_PLATFORMS)
    collected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    def _collect_for_platform(platform_name: str):
        for query in _build_viral_queries(
            platform_name,
            country_label,
            topic=topic,
            product_category=product_category,
            distribution_mode=distribution_mode,
            days=days,
        ):
            response = tavily_search(
                query=query,
                country=country_label.lower(),
                days=days,
                max_results=6,
                include_domains=PLATFORM_DOMAINS.get(platform_name, ()),
                include_answer=False,
                include_images=True,
                search_depth="advanced",
                cache_buster=cache_buster,
            )
            images = response.get("images", []) or []
            results = response.get("results", []) or []

            for index, item in enumerate(results):
                url = str(item.get("url", "") or "").strip()
                if not url or url in seen_urls:
                    continue

                text_blob = " ".join(
                    part for part in [item.get("title", ""), item.get("content", ""), item.get("raw_content", "")]
                    if part
                )
                age_days = _extract_age_days(text_blob)
                if age_days is not None and age_days > days:
                    continue
                view_count = _extract_view_count(text_blob)
                score = float(item.get("score", 0.0) or 0.0)
                if view_count is not None and view_count < minimum_view_count:
                    continue
                if view_count is None and score < 0.85:
                    continue

                inferred_platform = _infer_platform_from_url(url) or platform_name
                seen_urls.add(url)
                collected.append(
                    {
                        "title": _compact_text(item.get("title", "") or PLATFORM_LABELS.get(inferred_platform, "Viral video"), limit=88),
                        "url": url,
                        "platform": PLATFORM_LABELS.get(inferred_platform, inferred_platform.title()),
                        "platform_key": inferred_platform,
                        "view_count": view_count or 0,
                        "view_count_label": _format_view_count(view_count) if view_count else "实时命中",
                        "summary": _compact_text(item.get("content", ""), limit=140),
                        "score": score,
                        "image_url": images[index] if index < len(images) else "",
                        "favicon": item.get("favicon", "") or "",
                    }
                )

    for platform_name in requested_platforms:
        _collect_for_platform(platform_name)

    if not collected and len(requested_platforms) == 1:
        for fallback_platform in SUPPORTED_VIRAL_PLATFORMS:
            if fallback_platform == requested_platforms[0]:
                continue
            _collect_for_platform(fallback_platform)

    collected.sort(key=lambda item: (item.get("view_count", 0), item.get("score", 0.0)), reverse=True)
    return collected[:max_results]
