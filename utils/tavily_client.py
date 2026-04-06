from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from tavily import TavilyClient


current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)


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


@lru_cache(maxsize=64)
def tavily_search(
    query: str,
    country: str = "",
    days: int = 30,
    max_results: int = 5,
) -> dict[str, Any]:
    client = get_tavily_client()
    if client is None:
        raise RuntimeError("Tavily client is not configured.")

    search_kwargs = {
        "query": query,
        "topic": "general",
        "days": days,
        "max_results": max_results,
        "include_answer": "advanced",
        "include_favicon": True,
        "search_depth": "basic",
        "timeout": 45,
    }
    if country:
        search_kwargs["country"] = country

    response = client.search(**search_kwargs)
    results = response.get("results", []) or []
    if results or response.get("answer"):
        return response

    search_kwargs["search_depth"] = "advanced"
    return client.search(**search_kwargs)
