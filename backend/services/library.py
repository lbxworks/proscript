from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.compliance_kb import (
    get_knowledge_index_status,
    initialize_knowledge_runtime,
    normalize_raw_knowledge_files,
    rebuild_knowledge_runtime,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_ROOT = PROJECT_ROOT / "data" / "knowledge_base"
RAW_ROOT = KNOWLEDGE_BASE_ROOT / "raw"
PROCESSED_ROOT = KNOWLEDGE_BASE_ROOT / "processed"
SOURCE_CATALOG_PATH = KNOWLEDGE_BASE_ROOT / "source_catalog.json"
MANIFEST_PATH = PROCESSED_ROOT / "manifest.json"

RAW_UPLOAD_SUFFIXES = {".html", ".pdf"}
DIRECT_UPLOAD_SUFFIXES = {".md", ".markdown", ".txt"}
SUPPORTED_UPLOAD_SUFFIXES = RAW_UPLOAD_SUFFIXES | DIRECT_UPLOAD_SUFFIXES
DEFAULT_CATEGORY = "platform_policy"
DEFAULT_MARKET = "GLOBAL"
DEFAULT_REGION = "GLOBAL"
DEFAULT_PLATFORM = "all"
DEFAULT_LANGUAGE = "en"
DEFAULT_PRIORITY = "P2"
COUNTRY_CODE_ALIASES = {
    "UK": "GB",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _slugify_source_id(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or f"library_{_utc_now().strftime('%Y%m%d_%H%M%S')}"


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    elif "T" not in normalized and "+" not in normalized:
        normalized = normalized.replace(" ", "T") + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _build_display_timestamp(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).isoformat()


def _build_country_code(market: str) -> str:
    normalized = str(market or DEFAULT_MARKET).upper()
    if normalized in {"GLOBAL", "EU", "INTERNAL"}:
        return ""
    return COUNTRY_CODE_ALIASES.get(normalized, normalized)


def _infer_source_type(category: str) -> str:
    return "law" if category == "market_law" else "policy"


def _load_catalog_entries() -> list[dict[str, Any]]:
    payload = _read_json(SOURCE_CATALOG_PATH, [])
    return payload if isinstance(payload, list) else []


def _save_catalog_entries(items: list[dict[str, Any]]) -> None:
    _write_json(SOURCE_CATALOG_PATH, items)


def _load_processed_manifest() -> list[dict[str, Any]]:
    payload = _read_json(MANIFEST_PATH, [])
    return payload if isinstance(payload, list) else []


def _resolve_unique_source_id(base_source_id: str, suffix: str) -> str:
    candidate = base_source_id
    counter = 1

    while True:
        raw_conflicts = list(RAW_ROOT.glob(f"{candidate}.*"))
        processed_md = PROCESSED_ROOT / f"{candidate}.md"
        processed_json = PROCESSED_ROOT / f"{candidate}.json"
        catalog_conflict = any(item.get("id") == candidate for item in _load_catalog_entries())

        if suffix in RAW_UPLOAD_SUFFIXES:
            exact_raw_path = RAW_ROOT / f"{candidate}{suffix}"
            has_other_raw_conflict = any(path != exact_raw_path for path in raw_conflicts)
            if exact_raw_path.exists() and not has_other_raw_conflict and not processed_md.exists():
                return candidate
            if not raw_conflicts and not processed_md.exists() and not processed_json.exists() and not catalog_conflict:
                return candidate
        else:
            if processed_md.exists() and processed_json.exists() and not raw_conflicts:
                return candidate
            if not raw_conflicts and not processed_md.exists() and not processed_json.exists() and not catalog_conflict:
                return candidate

        candidate = f"{base_source_id}_{counter}"
        counter += 1


def _upsert_catalog_entry(
    *,
    source_id: str,
    title: str,
    category: str,
    market: str,
    region: str,
    platform: str,
    language: str,
    source_url: str,
    notes: str,
    priority: str,
) -> dict[str, Any]:
    items = _load_catalog_entries()
    payload = {
        "id": source_id,
        "title": title,
        "category": category,
        "region": region,
        "market": market,
        "platform": platform,
        "language": language,
        "url": source_url,
        "crawl_mode": "manual_upload",
        "priority": priority,
        "notes": notes,
    }

    for index, item in enumerate(items):
        if item.get("id") == source_id:
            items[index] = payload
            _save_catalog_entries(items)
            return payload

    items.append(payload)
    items.sort(key=lambda item: str(item.get("id", "")))
    _save_catalog_entries(items)
    return payload


def _build_processed_metadata(
    *,
    source_id: str,
    title: str,
    category: str,
    market: str,
    region: str,
    platform: str,
    language: str,
    source_url: str,
    notes: str,
    priority: str,
    raw_file: str = "",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "title": title,
        "platform": platform.lower() or DEFAULT_PLATFORM,
        "platform_display": platform,
        "region": market.upper() or DEFAULT_MARKET,
        "region_pack": region.upper() or DEFAULT_REGION,
        "document_type": category,
        "source_category": category,
        "language": language.lower() or DEFAULT_LANGUAGE,
        "source_url": source_url,
        "priority": priority.upper() or DEFAULT_PRIORITY,
        "notes": notes,
        "raw_file": raw_file,
        "processed_at": _utc_now_iso(),
        "parser_version": "library-direct-upload-v1",
        "doc_id": source_id,
        "source_title": title,
        "source_type": _infer_source_type(category),
        "country_code": _build_country_code(market),
        "distribution_mode": "all",
        "brand_id": "all",
        "block_id": source_id,
        "is_global_fallback": market.upper() in {"GLOBAL", "EU"},
    }


def _write_processed_markdown(*, source_id: str, metadata: dict[str, Any], body: str) -> None:
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    md_path = PROCESSED_ROOT / f"{source_id}.md"
    json_path = PROCESSED_ROOT / f"{source_id}.json"
    title = str(metadata.get("title", source_id)).strip()
    stripped_body = body.strip()
    if not stripped_body.startswith("# "):
        stripped_body = f"# {title}\n\n{stripped_body}"
    metadata_block = "```json\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n```\n\n"
    md_path.write_text(metadata_block + stripped_body + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _decode_text_upload(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _build_document_item(
    *,
    source_id: str,
    title: str,
    category: str,
    platform: str,
    market: str,
    region: str,
    language: str,
    source_url: str,
    notes: str,
    priority: str,
    status: str,
    updated_at: str,
    raw_path: str = "",
    markdown_path: str = "",
    metadata_path: str = "",
    raw_suffix: str = "",
    file_origin: str = "",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "title": title,
        "category": category,
        "platform": platform,
        "market": market,
        "region": region,
        "language": language,
        "source_url": source_url,
        "notes": notes,
        "priority": priority,
        "status": status,
        "updated_at": updated_at,
        "raw_path": raw_path,
        "markdown_path": markdown_path,
        "metadata_path": metadata_path,
        "raw_suffix": raw_suffix,
        "file_origin": file_origin,
    }


def get_library_health(*, initialize: bool = False) -> dict[str, Any]:
    runtime_status = (
        initialize_knowledge_runtime(force_rebuild=False)
        if initialize
        else get_knowledge_index_status()
    )
    return {
        **runtime_status,
        "knowledge_base_root": str(KNOWLEDGE_BASE_ROOT),
        "raw_root": str(RAW_ROOT),
        "processed_root": str(PROCESSED_ROOT),
    }


def list_library_documents() -> dict[str, Any]:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)

    runtime_status = get_knowledge_index_status()
    built_at = _parse_timestamp(str(runtime_status.get("built_at", "") or ""))
    catalog_entries = _load_catalog_entries()
    catalog_map = {str(item.get("id", "")): item for item in catalog_entries}
    manifest_entries = _load_processed_manifest()
    manifest_map = {str(item.get("source_id", "")): item for item in manifest_entries if item.get("source_id")}

    processed_items: dict[str, dict[str, Any]] = {}
    for metadata_path in sorted(PROCESSED_ROOT.glob("*.json")):
        if metadata_path.name == "manifest.json":
            continue
        metadata_payload = _read_json(metadata_path, {})
        if not isinstance(metadata_payload, dict):
            continue
        source_id = str(
            metadata_payload.get("source_id")
            or metadata_payload.get("doc_id")
            or metadata_path.stem
        )
        processed_at = _parse_timestamp(str(metadata_payload.get("processed_at", "") or ""))
        status = "indexed"
        if built_at is None or (processed_at is not None and built_at < processed_at):
            status = "pending_rebuild"

        raw_file = str(metadata_payload.get("raw_file", "") or "")
        raw_path = PROJECT_ROOT / raw_file if raw_file else None
        manifest_entry = manifest_map.get(source_id, {})
        processed_items[source_id] = _build_document_item(
            source_id=source_id,
            title=str(metadata_payload.get("title", source_id)),
            category=str(
                metadata_payload.get("source_category")
                or metadata_payload.get("document_type")
                or DEFAULT_CATEGORY
            ),
            platform=str(metadata_payload.get("platform", DEFAULT_PLATFORM)),
            market=str(metadata_payload.get("region", DEFAULT_MARKET)),
            region=str(metadata_payload.get("region_pack", DEFAULT_REGION)),
            language=str(metadata_payload.get("language", DEFAULT_LANGUAGE)),
            source_url=str(metadata_payload.get("source_url", "")),
            notes=str(metadata_payload.get("notes", "")),
            priority=str(metadata_payload.get("priority", DEFAULT_PRIORITY)),
            status=status,
            updated_at=_build_display_timestamp(processed_at or datetime.fromtimestamp(metadata_path.stat().st_mtime, tz=timezone.utc)),
            raw_path=str(raw_path) if raw_path and raw_path.exists() else "",
            markdown_path=str((PROCESSED_ROOT / f"{source_id}.md")) if (PROCESSED_ROOT / f"{source_id}.md").exists() else str(manifest_entry.get("markdown_path", "")),
            metadata_path=str(metadata_path),
            raw_suffix=str(manifest_entry.get("raw_suffix", raw_path.suffix.lower() if raw_path else "")),
            file_origin="processed",
        )

    raw_only_items: list[dict[str, Any]] = []
    for raw_path in sorted(RAW_ROOT.glob("*")):
        if not raw_path.is_file():
            continue
        source_id = raw_path.stem
        if source_id in processed_items:
            item = processed_items[source_id]
            if not item["raw_path"]:
                item["raw_path"] = str(raw_path)
            if not item["raw_suffix"]:
                item["raw_suffix"] = raw_path.suffix.lower()
            continue

        catalog_entry = catalog_map.get(source_id, {})
        raw_only_items.append(
            _build_document_item(
                source_id=source_id,
                title=str(catalog_entry.get("title", raw_path.stem)),
                category=str(catalog_entry.get("category", DEFAULT_CATEGORY)),
                platform=str(catalog_entry.get("platform", DEFAULT_PLATFORM)),
                market=str(catalog_entry.get("market", DEFAULT_MARKET)),
                region=str(catalog_entry.get("region", DEFAULT_REGION)),
                language=str(catalog_entry.get("language", DEFAULT_LANGUAGE)),
                source_url=str(catalog_entry.get("url", "")),
                notes=str(catalog_entry.get("notes", "")),
                priority=str(catalog_entry.get("priority", DEFAULT_PRIORITY)),
                status="pending_rebuild",
                updated_at=_build_display_timestamp(datetime.fromtimestamp(raw_path.stat().st_mtime, tz=timezone.utc)),
                raw_path=str(raw_path),
                raw_suffix=raw_path.suffix.lower(),
                file_origin="raw",
            )
        )

    all_items = list(processed_items.values()) + raw_only_items
    all_items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return {
        "items": all_items,
        "total": len(all_items),
        "built_at": str(runtime_status.get("built_at", "") or ""),
    }


def upload_library_document(
    *,
    filename: str,
    content: bytes,
    title: str,
    category: str,
    market: str,
    region: str,
    platform: str,
    language: str,
    source_url: str = "",
    notes: str = "",
    priority: str = DEFAULT_PRIORITY,
) -> dict[str, Any]:
    if not content:
        raise ValueError("上传文件为空。")

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_SUFFIXES:
        raise ValueError("仅支持上传 pdf、html、md、markdown、txt 文件。")

    base_source_id = _slugify_source_id(Path(filename).stem)
    source_id = _resolve_unique_source_id(base_source_id, suffix)
    normalized_title = title.strip() or Path(filename).stem
    normalized_category = category.strip() or DEFAULT_CATEGORY
    normalized_market = market.strip().upper() or DEFAULT_MARKET
    normalized_region = region.strip().upper() or DEFAULT_REGION
    normalized_platform = platform.strip().lower() or DEFAULT_PLATFORM
    normalized_language = language.strip().lower() or DEFAULT_LANGUAGE
    normalized_priority = priority.strip().upper() or DEFAULT_PRIORITY
    normalized_source_url = source_url.strip()
    normalized_notes = notes.strip()

    if suffix in RAW_UPLOAD_SUFFIXES:
        RAW_ROOT.mkdir(parents=True, exist_ok=True)
        raw_path = RAW_ROOT / f"{source_id}{suffix}"
        raw_path.write_bytes(content)
        _upsert_catalog_entry(
            source_id=source_id,
            title=normalized_title,
            category=normalized_category,
            market=normalized_market,
            region=normalized_region,
            platform=normalized_platform,
            language=normalized_language,
            source_url=normalized_source_url,
            notes=normalized_notes,
            priority=normalized_priority,
        )
        item = _build_document_item(
            source_id=source_id,
            title=normalized_title,
            category=normalized_category,
            platform=normalized_platform,
            market=normalized_market,
            region=normalized_region,
            language=normalized_language,
            source_url=normalized_source_url,
            notes=normalized_notes,
            priority=normalized_priority,
            status="pending_rebuild",
            updated_at=_utc_now_iso(),
            raw_path=str(raw_path),
            raw_suffix=suffix,
            file_origin="raw",
        )
        return {"item": item}

    body = _decode_text_upload(content).strip()
    if not body:
        raise ValueError("文本资料内容为空。")

    metadata = _build_processed_metadata(
        source_id=source_id,
        title=normalized_title,
        category=normalized_category,
        market=normalized_market,
        region=normalized_region,
        platform=normalized_platform,
        language=normalized_language,
        source_url=normalized_source_url,
        notes=normalized_notes,
        priority=normalized_priority,
    )
    _write_processed_markdown(source_id=source_id, metadata=metadata, body=body)
    item = _build_document_item(
        source_id=source_id,
        title=normalized_title,
        category=normalized_category,
        platform=normalized_platform,
        market=normalized_market,
        region=normalized_region,
        language=normalized_language,
        source_url=normalized_source_url,
        notes=normalized_notes,
        priority=normalized_priority,
        status="pending_rebuild",
        updated_at=_utc_now_iso(),
        markdown_path=str(PROCESSED_ROOT / f"{source_id}.md"),
        metadata_path=str(PROCESSED_ROOT / f"{source_id}.json"),
        raw_suffix=suffix,
        file_origin="processed",
    )
    return {"item": item}


def rebuild_library() -> dict[str, Any]:
    normalize_result = normalize_raw_knowledge_files()
    runtime_status = rebuild_knowledge_runtime()
    return {
        "normalized": normalize_result,
        "runtime": {
            **runtime_status,
            "knowledge_base_root": str(KNOWLEDGE_BASE_ROOT),
            "raw_root": str(RAW_ROOT),
            "processed_root": str(PROCESSED_ROOT),
        },
    }
