from __future__ import annotations

import hashlib
import json
import mimetypes
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

import httpx


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "source_catalog.json"
RAW_DIR = PROJECT_ROOT / "data" / "knowledge_base" / "raw"
STATUS_JSON_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "crawl_status.json"
STATUS_MD_PATH = PROJECT_ROOT / "docs" / "rag_kb_collection_status.md"

USER_AGENT = "my-grad-proj-rag-collector/1.0 (+https://github.com/infiniflow/ragflow)"
TIMEOUT = httpx.Timeout(25.0, connect=12.0, read=25.0, write=25.0, pool=12.0)


def load_catalog() -> List[Dict[str, object]]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def guess_extension(url: str, content_type: str) -> str:
    lowered_type = content_type.lower()
    if "pdf" in lowered_type or url.lower().endswith(".pdf"):
        return ".pdf"
    if "html" in lowered_type or "text/" in lowered_type:
        return ".html"

    guessed = mimetypes.guess_extension(lowered_type.split(";")[0].strip())
    return guessed or ".bin"


def sanitize_filename(source_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", source_id)


def detect_blocked_page(content: bytes, content_type: str) -> str:
    if "html" not in content_type.lower():
        return ""

    try:
        text = content.decode("utf-8", errors="ignore").lower()
    except Exception:
        return ""

    block_signals = [
        "captcha",
        "access denied",
        "just a moment",
        "enable javascript",
        "request blocked",
    ]
    for signal in block_signals:
        if signal in text:
            return signal
    return ""


def build_client() -> httpx.Client:
    return httpx.Client(
        follow_redirects=True,
        timeout=TIMEOUT,
        headers={
            "User-Agent": USER_AGENT,
            "Connection": "close",
        },
    )


def download_source(entry: Dict[str, object]) -> Dict[str, object]:
    source_id = str(entry["id"])
    url = str(entry.get("url", "") or "").strip()
    status = {
        "id": source_id,
        "title": entry.get("title", ""),
        "category": entry.get("category", ""),
        "region": entry.get("region", ""),
        "market": entry.get("market", ""),
        "platform": entry.get("platform", ""),
        "language": entry.get("language", ""),
        "url": url,
        "crawl_mode": entry.get("crawl_mode", ""),
        "priority": entry.get("priority", ""),
        "notes": entry.get("notes", ""),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    crawl_mode = str(entry.get("crawl_mode", "auto"))
    if crawl_mode != "auto":
        status["status"] = "manual_required"
        status["reason"] = "manual_source"
        return status

    try:
        with build_client() as client:
            response = client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "application/octet-stream")
            blocked_signal = detect_blocked_page(response.content, content_type)
            if blocked_signal:
                status["status"] = "blocked"
                status["reason"] = f"anti_bot_or_js:{blocked_signal}"
                status["http_status"] = response.status_code
                return status

            extension = guess_extension(url, content_type)
            target_name = f"{sanitize_filename(source_id)}{extension}"
            target_path = RAW_DIR / target_name
            target_path.write_bytes(response.content)

            status["status"] = "downloaded"
            status["http_status"] = response.status_code
            status["content_type"] = content_type
            status["file_path"] = str(target_path.relative_to(PROJECT_ROOT))
            status["file_size"] = target_path.stat().st_size
            status["sha256"] = hashlib.sha256(response.content).hexdigest()
            status["final_url"] = str(response.url)
            status["domain"] = urlparse(str(response.url)).netloc
            return status
    except httpx.HTTPStatusError as exc:
        status["status"] = "failed"
        status["reason"] = f"http_{exc.response.status_code}"
        status["http_status"] = exc.response.status_code
        status["final_url"] = str(exc.request.url)
        return status
    except Exception as exc:
        status["status"] = "failed"
        status["reason"] = str(exc)
        return status


def write_status_json(results: List[Dict[str, object]]) -> None:
    STATUS_JSON_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def render_status_markdown(results: List[Dict[str, object]]) -> str:
    counter = Counter(item["status"] for item in results)
    lines = [
        "# RAG 知识库采集状态",
        "",
        f"- 生成时间：`{datetime.now(timezone.utc).isoformat()}`",
        f"- 总来源数：`{len(results)}`",
        f"- 已下载：`{counter.get('downloaded', 0)}`",
        f"- 需要人工处理：`{counter.get('manual_required', 0)}`",
        f"- 抓取失败：`{counter.get('failed', 0)}`",
        f"- 访问被拦截：`{counter.get('blocked', 0)}`",
        "",
        "## 状态表",
        "",
        "| ID | 类别 | 市场 | 平台 | 状态 | 说明 | 本地文件 |",
        "|---|---|---|---|---|---|---|",
    ]

    for item in results:
        note = item.get("reason") or item.get("notes") or ""
        file_path = item.get("file_path", "")
        lines.append(
            f"| {item['id']} | {item.get('category','')} | {item.get('market','')} | "
            f"{item.get('platform','')} | {item.get('status','')} | {str(note).replace('|', '/')} | {file_path} |"
        )

    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- `downloaded`：已成功抓取并保存到本地。",
            "- `manual_required`：内部文档、需要登录、需要人工检索或尚未确定官方入口。",
            "- `failed`：请求失败或返回非 2xx。",
            "- `blocked`：站点疑似有反爬、验证码或强依赖浏览器环境。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_status_markdown(results: List[Dict[str, object]]) -> None:
    STATUS_MD_PATH.write_text(render_status_markdown(results), encoding="utf-8")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_MD_PATH.parent.mkdir(parents=True, exist_ok=True)

    catalog = load_catalog()
    results: List[Dict[str, object]] = []
    try:
        for entry in catalog:
            result = download_source(entry)
            results.append(result)
            write_status_json(results)
            write_status_markdown(results)
            print(f"{result['status']:>15} | {result['id']}", flush=True)
    finally:
        write_status_json(results)
        write_status_markdown(results)

    print(f"\nSaved status JSON to: {STATUS_JSON_PATH}")
    print(f"Saved status Markdown to: {STATUS_MD_PATH}")


if __name__ == "__main__":
    main()
