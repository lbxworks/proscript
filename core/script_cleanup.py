from __future__ import annotations

import re


SCRIPT_START_PATTERNS = (
    re.compile(r"(?m)^###\s+"),
    re.compile(r"(?m)^\*\*(?:Title|标题|Título|Titre|Titel|العنوان|タイトル)\*\*"),
    re.compile(r"(?m)^\|\s*\[?\d{2}:\d{2}-\d{2}:\d{2}\]?\s*\|"),
    re.compile(r"(?m)^\[\d{2}:\d{2}-\d{2}:\d{2}\]\s*\|"),
)

LEADING_CODE_FENCE = re.compile(r"^\s*```(?:markdown|md)?\s*", flags=re.IGNORECASE)
TRAILING_CODE_FENCE = re.compile(r"\s*```\s*$", flags=re.IGNORECASE)


def _strip_outer_code_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```") or not stripped.endswith("```"):
        return stripped
    stripped = LEADING_CODE_FENCE.sub("", stripped, count=1)
    stripped = TRAILING_CODE_FENCE.sub("", stripped, count=1)
    return stripped.strip()


def _find_script_start(text: str) -> int | None:
    start_indexes = [match.start() for pattern in SCRIPT_START_PATTERNS if (match := pattern.search(text))]
    if not start_indexes:
        return None
    return min(start_indexes)


def sanitize_script_markdown(value: str | None) -> str:
    text = _strip_outer_code_fences(str(value or "").replace("\r\n", "\n").replace("\r", "\n"))
    if not text:
        return ""

    start_index = _find_script_start(text)
    if start_index is not None and text[:start_index].strip():
        text = text[start_index:]

    return text.strip()
