from __future__ import annotations

from core.compliance_config import (
    canonicalize_language,
    canonicalize_platform,
    get_default_language_for_country,
    get_region_for_country,
)


def run_compliance_scope_resolver(state: dict) -> dict:
    print("🧭 [Agent] Compliance Scope Resolver — Normalizing platform, market, and language scope...")

    target_country = str(state.get("target_country", "US")).upper()
    target_platform = canonicalize_platform(state.get("target_platform", "tiktok"))
    distribution_mode = str(state.get("distribution_mode", "branded_content")).lower()
    product_category = str(state.get("product_category", "general")).lower()
    brand_id = str(state.get("brand_id", "default")).lower()

    selected_languages = state.get("target_languages", []) or ["English"]
    knowledge_languages = []
    for language in selected_languages:
        normalized = canonicalize_language(language)
        if normalized and normalized not in knowledge_languages:
            knowledge_languages.append(normalized)

    default_market_language = get_default_language_for_country(target_country)
    if default_market_language and default_market_language not in knowledge_languages:
        knowledge_languages.append(default_market_language)

    resolved_scope = {
        "target_country": target_country,
        "target_region_pack": get_region_for_country(target_country),
        "target_platform": target_platform,
        "distribution_mode": distribution_mode,
        "product_category": product_category,
        "brand_id": brand_id,
        "knowledge_languages": knowledge_languages,
    }

    return {
        **resolved_scope,
        "compliance_scope": resolved_scope,
    }
