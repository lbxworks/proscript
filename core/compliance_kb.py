from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple


KB_ROOT = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
SUPPORTED_SUFFIXES = {".md", ".txt", ".markdown"}


def _split_front_matter(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    lines = text.splitlines()
    metadata: Dict[str, str] = {}
    body_start = 0

    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            body_start = index + 1
            break
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        metadata[key.strip()] = raw_value.strip()

    body = "\n".join(lines[body_start:]).strip()
    return metadata, body


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[^\W_]+", text.lower(), flags=re.UNICODE)


def _normalize_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def load_knowledge_base() -> List[Dict[str, object]]:
    if not KB_ROOT.exists():
        return []

    documents: List[Dict[str, object]] = []

    for path in KB_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if path.stem.lower() == "readme":
            continue

        raw_text = path.read_text(encoding="utf-8")
        metadata, body = _split_front_matter(raw_text)
        if not body:
            continue

        document = {
            "doc_id": metadata.get("doc_id", path.stem),
            "source_title": metadata.get("source_title", path.stem.replace("_", " ").title()),
            "source_type": metadata.get("source_type", "policy"),
            "source_url": metadata.get("source_url", ""),
            "platform": metadata.get("platform", "").lower(),
            "distribution_mode": metadata.get("distribution_mode", "").lower(),
            "country_code": metadata.get("country_code", "").upper(),
            "region_pack": metadata.get("region_pack", "").upper(),
            "language": metadata.get("language", "").lower(),
            "brand_id": metadata.get("brand_id", "").lower(),
            "effective_from": metadata.get("effective_from", ""),
            "effective_to": metadata.get("effective_to", ""),
            "page_num": metadata.get("page_num", ""),
            "heading_path": metadata.get("heading_path", ""),
            "block_id": metadata.get("block_id", path.stem),
            "is_global_fallback": _normalize_bool(metadata.get("is_global_fallback", "false")),
            "body": body,
            "path": str(path),
            "tokens": set(_tokenize(body)),
        }
        documents.append(document)

    return documents


def _is_scope_match(document: Dict[str, object], scope: Dict[str, object]) -> bool:
    platform = str(document.get("platform", "")).lower()
    distribution_mode = str(document.get("distribution_mode", "")).lower()
    country_code = str(document.get("country_code", "")).upper()
    region_pack = str(document.get("region_pack", "")).upper()
    brand_id = str(document.get("brand_id", "")).lower()
    source_type = str(document.get("source_type", "")).lower()

    target_platform = str(scope.get("target_platform", "")).lower()
    target_country = str(scope.get("target_country", "")).upper()
    target_region = str(scope.get("target_region_pack", "")).upper()
    target_distribution = str(scope.get("distribution_mode", "")).lower()
    target_brand = str(scope.get("brand_id", "")).lower()

    if platform and platform not in {target_platform, "all", "global"}:
        return False

    if distribution_mode and distribution_mode not in {target_distribution, "all", "global"}:
        return False

    if brand_id and target_brand and brand_id not in {target_brand, "all", "global"}:
        return False

    if source_type == "law":
        if country_code:
            return country_code == target_country
        return bool(region_pack and region_pack == target_region)

    if country_code and country_code not in {target_country, "GLOBAL", "ALL"}:
        return False

    if region_pack and region_pack not in {target_region, "GLOBAL", "ALL"} and not country_code:
        return False

    return True


def _score_document(document: Dict[str, object], query_tokens: set, scope: Dict[str, object]) -> int:
    score = 0
    overlap = len(query_tokens & set(document.get("tokens", set())))
    score += overlap * 4

    target_country = str(scope.get("target_country", "")).upper()
    target_region = str(scope.get("target_region_pack", "")).upper()
    target_platform = str(scope.get("target_platform", "")).lower()
    target_distribution = str(scope.get("distribution_mode", "")).lower()

    if str(document.get("country_code", "")).upper() == target_country:
        score += 12
    elif str(document.get("region_pack", "")).upper() == target_region:
        score += 6

    if str(document.get("platform", "")).lower() == target_platform:
        score += 8

    if str(document.get("distribution_mode", "")).lower() == target_distribution:
        score += 5

    if str(document.get("source_type", "")).lower() == "law":
        score += 4

    if bool(document.get("is_global_fallback")):
        score -= 2

    return score


def retrieve_evidence(query_text: str, scope: Dict[str, object], limit: int = 6) -> List[Dict[str, object]]:
    documents = load_knowledge_base()
    if not documents:
        return []

    query_tokens = set(_tokenize(query_text))
    if not query_tokens:
        query_tokens = set(_tokenize(str(scope)))

    scored_documents: List[Tuple[int, Dict[str, object]]] = []
    for document in documents:
        if not _is_scope_match(document, scope):
            continue
        score = _score_document(document, query_tokens, scope)
        if score <= 0:
            continue
        scored_documents.append((score, document))

    scored_documents.sort(key=lambda item: item[0], reverse=True)

    evidence: List[Dict[str, object]] = []
    for score, document in scored_documents[:limit]:
        evidence.append(
            {
                "doc_id": document["doc_id"],
                "source_title": document["source_title"],
                "source_type": document["source_type"],
                "source_url": document["source_url"],
                "platform": document["platform"],
                "distribution_mode": document["distribution_mode"],
                "country_code": document["country_code"],
                "region_pack": document["region_pack"],
                "language": document["language"],
                "effective_from": document["effective_from"],
                "effective_to": document["effective_to"],
                "page_num": document["page_num"],
                "heading_path": document["heading_path"],
                "block_id": document["block_id"],
                "is_global_fallback": document["is_global_fallback"],
                "excerpt": str(document["body"])[:900],
                "path": document["path"],
                "score": score,
            }
        )

    return evidence
