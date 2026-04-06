from __future__ import annotations

from typing import Dict, List, Optional


MARKETS: List[Dict[str, str]] = [
    {"code": "US", "label": "United States", "region": "AMER", "default_language": "en"},
    {"code": "CA", "label": "Canada", "region": "AMER", "default_language": "en"},
    {"code": "MX", "label": "Mexico", "region": "LATAM", "default_language": "es"},
    {"code": "BR", "label": "Brazil", "region": "LATAM", "default_language": "pt-BR"},
    {"code": "AR", "label": "Argentina", "region": "LATAM", "default_language": "es"},
    {"code": "GB", "label": "United Kingdom", "region": "EU", "default_language": "en"},
    {"code": "ES", "label": "Spain", "region": "EU", "default_language": "es"},
    {"code": "DE", "label": "Germany", "region": "EU", "default_language": "de"},
    {"code": "FR", "label": "France", "region": "EU", "default_language": "fr"},
    {"code": "IT", "label": "Italy", "region": "EU", "default_language": "it"},
    {"code": "PT", "label": "Portugal", "region": "EU", "default_language": "pt-PT"},
    {"code": "DK", "label": "Denmark", "region": "EU", "default_language": "da"},
    {"code": "FI", "label": "Finland", "region": "EU", "default_language": "fi"},
    {"code": "SE", "label": "Sweden", "region": "EU", "default_language": "sv"},
    {"code": "NO", "label": "Norway", "region": "EU", "default_language": "no"},
    {"code": "AE", "label": "United Arab Emirates", "region": "MENA", "default_language": "ar"},
    {"code": "SA", "label": "Saudi Arabia", "region": "MENA", "default_language": "ar"},
]


COUNTRY_TO_REGION = {market["code"]: market["region"] for market in MARKETS}
COUNTRY_TO_LANGUAGE = {market["code"]: market["default_language"] for market in MARKETS}


PLATFORM_ALIASES = {
    "tiktok": "tiktok",
    "douyin": "douyin",
    "youtube": "youtube",
    "youtube shorts": "youtube",
    "instagram": "instagram",
    "instagram reels": "instagram",
    "x": "x",
    "twitter": "x",
    "reddit": "reddit",
    "discord": "discord",
}


DISTRIBUTION_MODES = ["organic", "branded_content", "paid_ads"]


PRODUCT_CATEGORIES = [
    "general",
    "beauty",
    "electronics",
    "fashion",
    "food_beverage",
    "health_supplement",
]


LANGUAGE_ALIASES = {
    "中文 (chinese)": "zh",
    "中文": "zh",
    "english": "en",
    "español (spanish)": "es",
    "español": "es",
    "espanol (spanish)": "es",
    "espanol": "es",
    "spanish": "es",
    "português (portuguese)": "pt-BR",
    "português": "pt-BR",
    "portugues (portuguese)": "pt-BR",
    "portugues": "pt-BR",
    "portuguese": "pt-BR",
    "français (french)": "fr",
    "français": "fr",
    "francais (french)": "fr",
    "francais": "fr",
    "french": "fr",
    "deutsch (german)": "de",
    "deutsch": "de",
    "german": "de",
    "italiano": "it",
    "italian": "it",
    "dansk": "da",
    "danish": "da",
    "suomi": "fi",
    "finnish": "fi",
    "svenska": "sv",
    "swedish": "sv",
    "norsk": "no",
    "norwegian": "no",
    "العربية (arabic)": "ar",
    "العربية": "ar",
    "arabic": "ar",
    "日本語 (japanese)": "ja",
    "日本語": "ja",
    "japanese": "ja",
}


def canonicalize_platform(value: Optional[str]) -> str:
    if not value:
        return "tiktok"

    lowered = value.strip().lower()
    for alias, canonical in PLATFORM_ALIASES.items():
        if alias in lowered:
            return canonical
    return lowered.replace(" ", "_")


def canonicalize_language(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    lowered = value.strip().lower()
    return LANGUAGE_ALIASES.get(lowered, lowered)


def get_region_for_country(country_code: Optional[str]) -> str:
    if not country_code:
        return "GLOBAL"
    return COUNTRY_TO_REGION.get(country_code.upper(), "GLOBAL")


def get_default_language_for_country(country_code: Optional[str]) -> Optional[str]:
    if not country_code:
        return None
    return COUNTRY_TO_LANGUAGE.get(country_code.upper())


def get_market_by_code(country_code: Optional[str]) -> Optional[Dict[str, str]]:
    if not country_code:
        return None

    normalized = country_code.upper()
    for market in MARKETS:
        if market["code"] == normalized:
            return market
    return None
