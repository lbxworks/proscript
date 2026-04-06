from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import math
import os
import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple

import httpx
from fastembed import TextEmbedding
from filelock import FileLock, Timeout
from qdrant_client import QdrantClient, models


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_ROOT = PROJECT_ROOT / "data" / "knowledge_base"
PROCESSED_DIR = KB_ROOT / "processed"
BRAND_DIR = KB_ROOT / "brand"
QDRANT_ROOT = PROJECT_ROOT / "data" / "qdrant"
QDRANT_PATH = QDRANT_ROOT / "compliance_kb"
INDEX_META_PATH = QDRANT_ROOT / "compliance_kb_meta.json"
COLLECTION_NAME = "compliance_chunks"
MODEL_DIR_ROOT = QDRANT_ROOT / "models"
HF_PUBLIC_BASE_URL = os.getenv("HF_PUBLIC_BASE_URL", "https://huggingface.co").rstrip("/")
MODEL_LOCK_PATH = QDRANT_ROOT / "fastembed_model.lock"
INDEX_LOCK_PATH = QDRANT_ROOT / "qdrant_index.lock"

EMBED_MODEL_NAME = os.getenv(
    "COMPLIANCE_EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
FALLBACK_DIMENSION = 384
CHUNK_TARGET_CHARS = 1200
CHUNK_OVERLAP_CHARS = 220
RELEVANT_SOURCE_CATEGORIES = {
    "market_law",
    "platform_policy",
    "brand_policy",
    "campaign_brief",
    "brand_history",
}
FASTEMBED_COMMON_FILES = [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
]
FASTEMBED_OPTIONAL_FILES = ["preprocessor_config.json"]
ProgressCallback = Callable[[str, str, float | None], None]
_MODEL_THREAD_LOCK = threading.RLock()
_INDEX_THREAD_LOCK = threading.RLock()


def _emit_progress(
    progress_callback: ProgressCallback | None,
    stage: str,
    message: str,
    progress: float | None = None,
) -> None:
    if progress_callback is None:
        return
    progress_callback(stage, message, progress)


@contextmanager
def _guarded_lock(
    lock_path: Path,
    thread_lock: threading.RLock,
    *,
    progress_callback: ProgressCallback | None = None,
    stage: str = "lock",
    wait_message: str = "Waiting for another session to finish initialization...",
):
    QDRANT_ROOT.mkdir(parents=True, exist_ok=True)
    file_lock = FileLock(str(lock_path))
    with thread_lock:
        while True:
            try:
                file_lock.acquire(timeout=1)
                break
            except Timeout:
                _emit_progress(progress_callback, stage, wait_message, None)
        try:
            yield
        finally:
            file_lock.release()


def _split_json_metadata_block(text: str) -> Tuple[Dict[str, Any], str]:
    match = re.match(r"^\s*```json\s*(\{.*?\})\s*```\s*", text, flags=re.DOTALL)
    if not match:
        return {}, text

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}, text

    body = text[match.end():].strip()
    return payload, body


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[^\W_]+", text.lower(), flags=re.UNICODE)


def _safe_slug(value: str) -> str:
    lowered = value.lower().strip().replace(" ", "_")
    lowered = re.sub(r"[^a-z0-9_:-]+", "_", lowered)
    return re.sub(r"_+", "_", lowered).strip("_") or "chunk"


def _stable_point_id(value: str) -> int:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).hexdigest()
    return int(digest, 16) % (2**63 - 1)


def _lookup_fastembed_model_metadata(model_name: str) -> Dict[str, Any] | None:
    for item in TextEmbedding.list_supported_models():
        if str(item.get("model", "")).lower() == model_name.lower():
            return item
    return None


def _model_dir_for_name(model_name: str) -> Path:
    return MODEL_DIR_ROOT / _safe_slug(model_name)


def _is_complete_model_dir(model_dir: Path, required_files: Sequence[str]) -> bool:
    for file_name in required_files:
        file_path = model_dir / file_name
        if not file_path.exists() or file_path.stat().st_size <= 0:
            return False
    return True


def _hf_resolve_url(repo_id: str, file_name: str) -> str:
    return f"{HF_PUBLIC_BASE_URL}/{repo_id}/resolve/main/{file_name}"


def _download_with_curl(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "curl",
        "-L",
        "-C",
        "-",
        "--retry",
        "10",
        "--retry-delay",
        "2",
        "--fail",
        "-o",
        str(destination),
        url,
    ]
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=False,
    )


def _download_with_httpx(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial_path = destination.with_suffix(destination.suffix + ".part")
    existing_size = partial_path.stat().st_size if partial_path.exists() else 0
    headers = {"Range": f"bytes={existing_size}-"} if existing_size > 0 else {}

    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            if existing_size > 0 and response.status_code != 206:
                partial_path.unlink(missing_ok=True)
                existing_size = 0
                headers = {}
                with client.stream("GET", url, headers=headers) as fresh_response:
                    fresh_response.raise_for_status()
                    with partial_path.open("wb") as file_handle:
                        for chunk in fresh_response.iter_bytes():
                            if chunk:
                                file_handle.write(chunk)
            else:
                mode = "ab" if existing_size > 0 else "wb"
                with partial_path.open(mode) as file_handle:
                    for chunk in response.iter_bytes():
                        if chunk:
                            file_handle.write(chunk)

    partial_path.replace(destination)


def _download_public_model_file(url: str, destination: Path, *, optional: bool = False) -> None:
    last_error: Exception | None = None
    for downloader in (_download_with_curl, _download_with_httpx):
        try:
            downloader(url, destination)
            if destination.exists() and destination.stat().st_size > 0:
                return
        except Exception as exc:
            last_error = exc

    if optional:
        return
    raise RuntimeError(f"Failed to download {url}: {last_error}")


def _prepare_fastembed_model_dir(
    model_name: str,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    metadata = _lookup_fastembed_model_metadata(model_name)
    if metadata is None:
        raise ValueError(f"Unsupported FastEmbed model: {model_name}")

    sources = dict(metadata.get("sources") or {})
    hf_repo = str(sources.get("hf") or "").strip()
    if not hf_repo:
        raise ValueError(f"Model {model_name} does not expose a public Hugging Face source.")

    required_files = list(FASTEMBED_COMMON_FILES)
    model_file = str(metadata.get("model_file", "")).strip()
    if model_file:
        required_files.append(model_file)
    for extra in metadata.get("additional_files", []) or []:
        if extra:
            required_files.append(str(extra))
    required_files = sorted(set(required_files))

    model_dir = _model_dir_for_name(model_name)
    _emit_progress(
        progress_callback,
        "model_check",
        f"Checking multilingual embedding model: {model_name}",
        0.08,
    )

    with _guarded_lock(
        MODEL_LOCK_PATH,
        _MODEL_THREAD_LOCK,
        progress_callback=progress_callback,
        stage="model_wait",
        wait_message="Waiting for the shared FastEmbed model lock...",
    ):
        if _is_complete_model_dir(model_dir, required_files):
            _emit_progress(
                progress_callback,
                "model_ready",
                "Embedding model is already available locally.",
                0.22,
            )
            return model_dir

        model_dir.mkdir(parents=True, exist_ok=True)
        total_required = max(len(required_files), 1)
        for index, file_name in enumerate(required_files, start=1):
            target = model_dir / file_name
            step_progress = 0.12 + (index - 1) / total_required * 0.24
            if target.exists() and target.stat().st_size > 0:
                _emit_progress(
                    progress_callback,
                    "model_file_ready",
                    f"Model file already present: {file_name}",
                    step_progress,
                )
                continue
            _emit_progress(
                progress_callback,
                "model_download",
                f"Downloading model file {index}/{total_required}: {file_name}",
                step_progress,
            )
            _download_public_model_file(_hf_resolve_url(hf_repo, file_name), target)

        for optional_file in FASTEMBED_OPTIONAL_FILES:
            target = model_dir / optional_file
            if target.exists() and target.stat().st_size > 0:
                continue
            _emit_progress(
                progress_callback,
                "model_optional",
                f"Checking optional model file: {optional_file}",
                0.38,
            )
            _download_public_model_file(_hf_resolve_url(hf_repo, optional_file), target, optional=True)

        manifest = {
            "model_name": model_name,
            "hf_repo": hf_repo,
            "required_files": required_files,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
        }
        (model_dir / "codex_model_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        _emit_progress(
            progress_callback,
            "model_done",
            "Multilingual embedding model is ready.",
            0.42,
        )
        return model_dir


def _normalize_scope_value(value: Any, default: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return default
    return normalized


def _language_variants(value: str) -> List[str]:
    normalized = value.lower().strip()
    if not normalized:
        return []
    return [item.strip() for item in re.split(r"[/,;|]+|-", normalized) if item.strip()]


def _looks_like_table(line: str) -> bool:
    return line.lstrip().startswith("|") and line.rstrip().endswith("|")


def _looks_like_list(line: str) -> bool:
    stripped = line.lstrip()
    return bool(re.match(r"^([-*+]|\d+\.)\s+", stripped))


def _is_noise_line(line: str) -> bool:
    cleaned = _normalize_text(line)
    if not cleaned:
        return True

    lowered = cleaned.lower()
    if re.fullmatch(r"page \d+(\s+of\s+\d+)?", lowered):
        return True
    if lowered in {"draft", "confidential", "table of contents", "toc"}:
        return True
    return False


def _split_long_block(block: str, max_chars: int) -> List[str]:
    cleaned = _normalize_text(block)
    if len(cleaned) <= max_chars:
        return [cleaned]

    sentences = re.split(r"(?<=[.!?。！？])\s+", cleaned)
    parts: List[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            parts.append(current)
            current = sentence
            continue
        current = candidate

    if current:
        parts.append(current)
    return parts or [cleaned]


@dataclass
class ChunkRecord:
    chunk_id: str
    doc_id: str
    source_title: str
    source_type: str
    source_category: str
    source_url: str
    platform: str
    country_code: str
    region_pack: str
    language: str
    distribution_mode: str
    brand_id: str
    priority: str
    is_global_fallback: bool
    heading_path: str
    chunk_index: int
    text: str
    path: str

    def payload(self) -> Dict[str, Any]:
        excerpt = self.text[:1400]
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "source_title": self.source_title,
            "source_type": self.source_type,
            "source_category": self.source_category,
            "source_url": self.source_url,
            "platform": self.platform,
            "country_code": self.country_code,
            "region_pack": self.region_pack,
            "language": self.language,
            "distribution_mode": self.distribution_mode,
            "brand_id": self.brand_id,
            "priority": self.priority,
            "is_global_fallback": self.is_global_fallback,
            "heading_path": self.heading_path,
            "chunk_index": self.chunk_index,
            "text": excerpt,
            "path": self.path,
        }


class Embedder:
    def __init__(
        self,
        model_name: str = EMBED_MODEL_NAME,
        cache_dir: Path | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.model_name = model_name
        self.cache_dir = str(cache_dir or (QDRANT_ROOT / "model_cache"))
        self._backend = None
        self._dimension = self._lookup_dimension(model_name)
        self.backend_name = "hash"
        self.progress_callback = progress_callback

    def _lookup_dimension(self, model_name: str) -> int:
        for item in TextEmbedding.list_supported_models():
            if item.get("model") == model_name:
                return int(item.get("dim", FALLBACK_DIMENSION))
        return FALLBACK_DIMENSION

    @property
    def dimension(self) -> int:
        return self._dimension

    def _ensure_backend(self) -> None:
        if self._backend is not None:
            return

        if self.model_name.lower() in {"hash", "lexical_hash", "fallback_hash"}:
            self._backend = None
            self.backend_name = "hash"
            return

        try:
            specific_model_path = _prepare_fastembed_model_dir(
                self.model_name,
                progress_callback=self.progress_callback,
            )
            _emit_progress(
                self.progress_callback,
                "model_load",
                "Loading the multilingual embedding runtime...",
                0.45,
            )
            self._backend = TextEmbedding(
                model_name=self.model_name,
                cache_dir=self.cache_dir,
                lazy_load=True,
                specific_model_path=str(specific_model_path),
            )
            self.backend_name = self.model_name
            _emit_progress(
                self.progress_callback,
                "model_loaded",
                "Embedding runtime loaded successfully.",
                0.5,
            )
        except Exception as exc:
            print(f"⚠️ [Compliance Embedder] FastEmbed model prep failed: {exc}")
            self._backend = None
            self.backend_name = "hash"

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        self._ensure_backend()
        cleaned = [text if text.strip() else "empty document" for text in texts]

        if self._backend is not None:
            try:
                vectors = list(self._backend.embed(cleaned, batch_size=64))
                return [vector.tolist() for vector in vectors]
            except Exception as exc:
                print(f"⚠️ [Compliance Embedder] Falling back to hash embeddings: {exc}")
                self._backend = None
                self.backend_name = "hash"

        return [self._hash_embed(text) for text in cleaned]

    def _hash_embed(self, text: str) -> List[float]:
        vector = [0.0] * self._dimension
        tokens = _tokenize(text) or ["empty"]
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def _iter_source_paths() -> Iterable[Path]:
    if PROCESSED_DIR.exists():
        yield from sorted(PROCESSED_DIR.glob("*.md"))
    if BRAND_DIR.exists():
        yield from sorted(BRAND_DIR.rglob("*.md"))


def _load_source_documents() -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    for path in _iter_source_paths():
        if path.stem.lower() in {"readme", "manifest"}:
            continue

        text = path.read_text(encoding="utf-8")
        metadata, body = _split_json_metadata_block(text)
        if not body.strip():
            continue

        source_category = str(
            metadata.get("source_category")
            or metadata.get("document_type")
            or metadata.get("source_type")
            or ""
        ).lower()
        if source_category and source_category not in RELEVANT_SOURCE_CATEGORIES:
            continue

        doc = {
            "doc_id": metadata.get("doc_id", metadata.get("source_id", path.stem)),
            "source_title": metadata.get("source_title", metadata.get("title", path.stem)),
            "source_type": str(metadata.get("source_type", metadata.get("document_type", "policy"))).lower(),
            "source_category": source_category or "platform_policy",
            "source_url": metadata.get("source_url", ""),
            "platform": str(metadata.get("platform", "all")).lower() or "all",
            "country_code": str(
                metadata.get("country_code")
                or metadata.get("region")
                or "GLOBAL"
            ).upper(),
            "region_pack": str(metadata.get("region_pack", "GLOBAL")).upper() or "GLOBAL",
            "language": str(metadata.get("language", "")).lower(),
            "distribution_mode": str(metadata.get("distribution_mode", "all")).lower() or "all",
            "brand_id": str(metadata.get("brand_id", "all")).lower() or "all",
            "priority": str(metadata.get("priority", "P2")).upper(),
            "is_global_fallback": bool(metadata.get("is_global_fallback", False)),
            "body": body.strip(),
            "path": str(path),
        }
        documents.append(doc)
    return documents


def _group_markdown_blocks(body: str) -> List[Tuple[str, str]]:
    raw_lines = body.splitlines()
    blocks: List[Tuple[str, str]] = []
    index = 0

    while index < len(raw_lines):
        line = raw_lines[index].rstrip()
        if _is_noise_line(line):
            index += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading_match:
            blocks.append(("heading", f"{heading_match.group(1)} {heading_match.group(2).strip()}"))
            index += 1
            continue

        if _looks_like_table(line):
            table_lines = [line]
            index += 1
            while index < len(raw_lines) and _looks_like_table(raw_lines[index].rstrip()):
                table_lines.append(raw_lines[index].rstrip())
                index += 1
            blocks.append(("table", "\n".join(table_lines).strip()))
            continue

        if _looks_like_list(line):
            list_lines = [line]
            index += 1
            while index < len(raw_lines):
                next_line = raw_lines[index].rstrip()
                if not next_line.strip():
                    break
                if _looks_like_list(next_line) or next_line.startswith("  "):
                    list_lines.append(next_line)
                    index += 1
                    continue
                break
            blocks.append(("list", "\n".join(list_lines).strip()))
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(raw_lines):
            next_line = raw_lines[index].rstrip()
            if not next_line.strip():
                break
            if re.match(r"^(#{1,6})\s+", next_line) or _looks_like_table(next_line) or _looks_like_list(next_line):
                break
            paragraph_lines.append(next_line)
            index += 1
        blocks.append(("paragraph", _normalize_text(" ".join(paragraph_lines))))

    return blocks


def _chunk_document(document: Dict[str, Any]) -> List[ChunkRecord]:
    blocks = _group_markdown_blocks(str(document["body"]))
    if not blocks:
        return []

    chunk_records: List[ChunkRecord] = []
    heading_stack: List[str] = []
    current_texts: List[str] = []
    current_heading_path = document["source_title"]
    chunk_index = 0

    def flush_chunk() -> None:
        nonlocal current_texts, chunk_index, current_heading_path
        if not current_texts:
            return

        joined = "\n\n".join(item for item in current_texts if item.strip()).strip()
        if not joined:
            current_texts = []
            return

        chunk_id = f"{document['doc_id']}::{chunk_index:03d}::{_safe_slug(current_heading_path)}"
        chunk_records.append(
            ChunkRecord(
                chunk_id=chunk_id,
                doc_id=str(document["doc_id"]),
                source_title=str(document["source_title"]),
                source_type=str(document["source_type"]),
                source_category=str(document["source_category"]),
                source_url=str(document["source_url"]),
                platform=str(document["platform"]),
                country_code=str(document["country_code"]),
                region_pack=str(document["region_pack"]),
                language=str(document["language"]),
                distribution_mode=str(document["distribution_mode"]),
                brand_id=str(document["brand_id"]),
                priority=str(document["priority"]),
                is_global_fallback=bool(document["is_global_fallback"]),
                heading_path=current_heading_path,
                chunk_index=chunk_index,
                text=joined,
                path=str(document["path"]),
            )
        )
        chunk_index += 1
        overlap_seed = joined[-CHUNK_OVERLAP_CHARS:].strip()
        current_texts = [overlap_seed] if overlap_seed else []

    for block_type, block_text in blocks:
        if block_type == "heading":
            flush_chunk()
            level = len(block_text.split(" ", 1)[0])
            heading_title = block_text[level + 1 :].strip()
            while len(heading_stack) >= level:
                heading_stack.pop()
            heading_stack.append(heading_title)
            current_heading_path = " > ".join([str(document["source_title"])] + heading_stack)
            current_texts = [f"Section: {current_heading_path}"]
            continue

        candidate_blocks = [block_text]
        if block_type == "paragraph":
            candidate_blocks = _split_long_block(block_text, CHUNK_TARGET_CHARS)

        for candidate in candidate_blocks:
            tentative = "\n\n".join(current_texts + [candidate]).strip()
            if current_texts and len(tentative) > CHUNK_TARGET_CHARS:
                flush_chunk()
                current_texts = [f"Section: {current_heading_path}", candidate]
                continue
            current_texts.append(candidate)

    flush_chunk()
    return chunk_records


def _load_all_chunk_payloads() -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    for document in _load_source_documents():
        for chunk in _chunk_document(document):
            payloads.append(chunk.payload())
    return payloads


def _build_index_fingerprint(documents: Sequence[Dict[str, Any]], embedder: Embedder) -> str:
    hash_input = {
        "backend": embedder.backend_name,
        "model_name": embedder.model_name,
        "dimension": embedder.dimension,
        "documents": [
            {
                "doc_id": document["doc_id"],
                "path": document["path"],
                "mtime_ns": Path(str(document["path"])).stat().st_mtime_ns,
                "size": Path(str(document["path"])).stat().st_size,
            }
            for document in documents
        ],
    }
    payload = json.dumps(hash_input, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_index_meta() -> Dict[str, Any]:
    if not INDEX_META_PATH.exists():
        return {}
    try:
        return json.loads(INDEX_META_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_index_meta(meta: Dict[str, Any]) -> None:
    QDRANT_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_client() -> QdrantClient:
    QDRANT_ROOT.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_PATH))


def _delete_collection_if_exists(client: QdrantClient) -> None:
    try:
        if client.collection_exists(COLLECTION_NAME):
            client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass


def ensure_qdrant_index(
    force_rebuild: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> Dict[str, Any]:
    documents = _load_source_documents()
    _emit_progress(
        progress_callback,
        "index_check",
        f"Checking compliance index against {len(documents)} source documents...",
        0.52,
    )

    with _guarded_lock(
        INDEX_LOCK_PATH,
        _INDEX_THREAD_LOCK,
        progress_callback=progress_callback,
        stage="index_wait",
        wait_message="Waiting for the shared Qdrant indexing lock...",
    ):
        embedder = Embedder(progress_callback=progress_callback)
        embedder._ensure_backend()
        fingerprint = _build_index_fingerprint(documents, embedder)
        meta = _load_index_meta()
        client = _make_client()

        collection_ready = False
        try:
            collection_ready = client.collection_exists(COLLECTION_NAME)
        except Exception:
            collection_ready = False

        if (
            not force_rebuild
            and collection_ready
            and meta.get("fingerprint") == fingerprint
            and meta.get("collection_name") == COLLECTION_NAME
        ):
            _emit_progress(
                progress_callback,
                "index_ready",
                "Qdrant index is already up to date.",
                1.0,
            )
            return {
                "status": "ready",
                "documents": len(documents),
                "chunks": int(meta.get("chunks", 0)),
                "embedding_backend": meta.get("embedding_backend", embedder.backend_name),
                "fingerprint": fingerprint,
            }

        chunks: List[ChunkRecord] = []
        total_documents = max(len(documents), 1)
        for index, document in enumerate(documents, start=1):
            chunks.extend(_chunk_document(document))
            progress = 0.56 + index / total_documents * 0.1
            _emit_progress(
                progress_callback,
                "chunking",
                f"Chunking document {index}/{total_documents}: {document['source_title']}",
                progress,
            )

        if not chunks:
            _delete_collection_if_exists(client)
            _save_index_meta(
                {
                    "collection_name": COLLECTION_NAME,
                    "fingerprint": fingerprint,
                    "chunks": 0,
                    "documents": len(documents),
                    "embedding_backend": embedder.backend_name,
                    "built_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            _emit_progress(
                progress_callback,
                "index_empty",
                "No eligible knowledge chunks were found. The compliance index remains empty.",
                1.0,
            )
            return {
                "status": "empty",
                "documents": len(documents),
                "chunks": 0,
                "embedding_backend": embedder.backend_name,
                "fingerprint": fingerprint,
            }

        _emit_progress(
            progress_callback,
            "embedding",
            f"Generating multilingual embeddings for {len(chunks)} chunks...",
            0.7,
        )
        texts = [chunk.text for chunk in chunks]
        vectors = embedder.embed(texts)

        _emit_progress(
            progress_callback,
            "qdrant_prepare",
            "Preparing local Qdrant collection...",
            0.82,
        )
        _delete_collection_if_exists(client)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=embedder.dimension, distance=models.Distance.COSINE),
        )

        total_batches = max(math.ceil(len(chunks) / 64), 1)
        for batch_index, start in enumerate(range(0, len(chunks), 64), start=1):
            batch = chunks[start : start + 64]
            batch_vectors = vectors[start : start + 64]
            points = [
                models.PointStruct(
                    id=_stable_point_id(chunk.chunk_id),
                    vector=vector,
                    payload=chunk.payload(),
                )
                for chunk, vector in zip(batch, batch_vectors, strict=False)
            ]
            client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
            progress = 0.86 + batch_index / total_batches * 0.12
            _emit_progress(
                progress_callback,
                "qdrant_write",
                f"Writing vector batch {batch_index}/{total_batches} into Qdrant...",
                progress,
            )

        _save_index_meta(
            {
                "collection_name": COLLECTION_NAME,
                "fingerprint": fingerprint,
                "chunks": len(chunks),
                "documents": len(documents),
                "embedding_backend": embedder.backend_name,
                "model_name": embedder.model_name,
                "built_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _emit_progress(
            progress_callback,
            "index_done",
            "Compliance index is ready for multilingual retrieval.",
            1.0,
        )
        return {
            "status": "rebuilt",
            "documents": len(documents),
            "chunks": len(chunks),
            "embedding_backend": embedder.backend_name,
            "fingerprint": fingerprint,
        }


def _matches_language(language_value: str, target_languages: Sequence[str]) -> bool:
    if not target_languages:
        return False
    variants = set(_language_variants(language_value))
    if not variants:
        return False
    return any(language in variants for language in target_languages)


def _scope_match(payload: Dict[str, Any], scope: Dict[str, Any]) -> bool:
    target_platform = str(scope.get("target_platform", "")).lower()
    target_country = str(scope.get("target_country", "")).upper()
    target_region = str(scope.get("target_region_pack", "")).upper()
    target_mode = str(scope.get("distribution_mode", "")).lower()
    target_brand = str(scope.get("brand_id", "all")).lower()

    platform = str(payload.get("platform", "")).lower()
    country_code = str(payload.get("country_code", "")).upper()
    region_pack = str(payload.get("region_pack", "")).upper()
    distribution_mode = str(payload.get("distribution_mode", "")).lower()
    brand_id = str(payload.get("brand_id", "")).lower()

    if platform and platform not in {target_platform, "all", "global"}:
        return False
    if distribution_mode and distribution_mode not in {target_mode, "all", "global"}:
        return False
    if brand_id and brand_id not in {target_brand, "all", "global"}:
        return False

    if country_code and country_code not in {target_country, "GLOBAL", "ALL"}:
        return False
    if not country_code and region_pack and region_pack not in {target_region, "GLOBAL", "ALL"}:
        return False
    return True


def _lexical_overlap_score(query_text: str, chunk_text: str) -> int:
    query_tokens = set(_tokenize(query_text))
    if not query_tokens:
        return 0
    chunk_tokens = set(_tokenize(chunk_text))
    return len(query_tokens & chunk_tokens)


def _priority_score(priority: str) -> int:
    mapping = {"P0": 12, "P1": 8, "P2": 4, "P3": 1}
    return mapping.get(priority.upper(), 0)


def _scope_priority(payload: Dict[str, Any], scope: Dict[str, Any]) -> int:
    target_country = str(scope.get("target_country", "")).upper()
    target_region = str(scope.get("target_region_pack", "")).upper()
    target_platform = str(scope.get("target_platform", "")).lower()
    target_mode = str(scope.get("distribution_mode", "")).lower()

    score = 0
    if str(payload.get("country_code", "")).upper() == target_country:
        score += 18
    elif str(payload.get("region_pack", "")).upper() == target_region:
        score += 10
    elif bool(payload.get("is_global_fallback")):
        score += 2

    if str(payload.get("platform", "")).lower() == target_platform:
        score += 8
    if str(payload.get("distribution_mode", "")).lower() == target_mode:
        score += 6
    score += _priority_score(str(payload.get("priority", "P2")))
    return score


def _build_query_filter(scope: Dict[str, Any], source_categories: Sequence[str]) -> models.Filter:
    target_platform = str(scope.get("target_platform", "")).lower()
    target_mode = str(scope.get("distribution_mode", "")).lower()
    target_brand = str(scope.get("brand_id", "all")).lower()

    return models.Filter(
        must=[
            models.FieldCondition(
                key="source_category",
                match=models.MatchAny(any=list(source_categories)),
            ),
            models.FieldCondition(
                key="platform",
                match=models.MatchAny(any=[target_platform, "all", "global"]),
            ),
            models.FieldCondition(
                key="distribution_mode",
                match=models.MatchAny(any=[target_mode, "all", "global"]),
            ),
            models.FieldCondition(
                key="brand_id",
                match=models.MatchAny(any=[target_brand, "all", "global"]),
            ),
        ]
    )


def _select_balanced_payloads(
    ranked: Sequence[Tuple[float, Dict[str, Any]]],
    limit: int,
) -> List[Tuple[float, Dict[str, Any]]]:
    by_category: Dict[str, List[Tuple[float, Dict[str, Any]]]] = {}
    for item in ranked:
        category = str(item[1].get("source_category", "other")).lower()
        by_category.setdefault(category, []).append(item)

    selected: List[Tuple[float, Dict[str, Any]]] = []
    seen = set()

    def take(category: str, quota: int) -> None:
        for score, payload in by_category.get(category, []):
            if len(selected) >= limit:
                return
            chunk_id = payload.get("chunk_id")
            if chunk_id in seen:
                continue
            selected.append((score, payload))
            seen.add(chunk_id)
            if len([1 for _, current in selected if current.get("source_category") == category]) >= quota:
                return

    take("market_law", min(3, limit))
    take("platform_policy", min(3, limit))
    take("brand_policy", 1)
    take("campaign_brief", 1)
    take("brand_history", 1)

    for score, payload in ranked:
        if len(selected) >= limit:
            break
        chunk_id = payload.get("chunk_id")
        if chunk_id in seen:
            continue
        selected.append((score, payload))
        seen.add(chunk_id)

    selected.sort(key=lambda item: item[0], reverse=True)
    return selected[:limit]


def _fallback_rank_for_category(
    query_text: str,
    scope: Dict[str, Any],
    target_languages: Sequence[str],
    category: str,
    limit: int,
) -> List[Tuple[float, Dict[str, Any]]]:
    ranked: List[Tuple[float, Dict[str, Any]]] = []
    for payload in _load_all_chunk_payloads():
        if str(payload.get("source_category", "")).lower() != category:
            continue
        if not _scope_match(payload, scope):
            continue
        lexical_score = _lexical_overlap_score(query_text, str(payload.get("text", "")))
        scope_bonus = _scope_priority(payload, scope)
        language_bonus = 5 if _matches_language(str(payload.get("language", "")), target_languages) else 0
        final_score = lexical_score * 6 + scope_bonus + language_bonus
        ranked.append((float(final_score), payload))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[:limit]


def retrieve_evidence(query_text: str, scope: Dict[str, Any], limit: int = 8) -> List[Dict[str, Any]]:
    ensure_qdrant_index()
    embedder = Embedder()
    query_vector = embedder.embed([query_text])[0]
    client = _make_client()

    if not client.collection_exists(COLLECTION_NAME):
        return []

    target_languages = [str(item).lower() for item in scope.get("knowledge_languages", []) or []]
    ranked: List[Tuple[float, Dict[str, Any]]] = []
    category_groups = [
        ["market_law"],
        ["platform_policy"],
        ["brand_policy", "campaign_brief", "brand_history"],
    ]

    for source_categories in category_groups:
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=_build_query_filter(scope, source_categories),
            limit=max(limit * 3, 8),
            with_payload=True,
            with_vectors=False,
        )

        for point in response.points:
            payload = dict(point.payload or {})
            if not _scope_match(payload, scope):
                continue

            lexical_score = _lexical_overlap_score(query_text, str(payload.get("text", "")))
            scope_bonus = _scope_priority(payload, scope)
            language_bonus = 5 if _matches_language(str(payload.get("language", "")), target_languages) else 0
            final_score = float(point.score or 0.0) * 100 + lexical_score * 3 + scope_bonus + language_bonus
            ranked.append((final_score, payload))

    ranked.sort(key=lambda item: item[0], reverse=True)
    existing_categories = {str(payload.get("source_category", "")).lower() for _, payload in ranked}
    for required_category in ("market_law", "platform_policy"):
        if required_category not in existing_categories:
            ranked.extend(
                _fallback_rank_for_category(
                    query_text=query_text,
                    scope=scope,
                    target_languages=target_languages,
                    category=required_category,
                    limit=max(4, limit),
                )
            )

    ranked.sort(key=lambda item: item[0], reverse=True)
    ranked = _select_balanced_payloads(ranked, limit)

    evidence: List[Dict[str, Any]] = []
    for score, payload in ranked:
        evidence.append(
            {
                "doc_id": payload.get("doc_id", ""),
                "source_title": payload.get("source_title", ""),
                "source_type": payload.get("source_type", ""),
                "source_category": payload.get("source_category", ""),
                "source_url": payload.get("source_url", ""),
                "platform": payload.get("platform", ""),
                "distribution_mode": payload.get("distribution_mode", ""),
                "country_code": payload.get("country_code", ""),
                "region_pack": payload.get("region_pack", ""),
                "language": payload.get("language", ""),
                "page_num": payload.get("page_num", ""),
                "heading_path": payload.get("heading_path", ""),
                "block_id": payload.get("chunk_id", payload.get("block_id", "")),
                "is_global_fallback": payload.get("is_global_fallback", False),
                "excerpt": payload.get("text", ""),
                "path": payload.get("path", ""),
                "priority": payload.get("priority", "P2"),
                "score": round(score, 3),
            }
        )

    return evidence


def get_index_status() -> Dict[str, Any]:
    meta = _load_index_meta()
    if not meta:
        return {
            "collection_name": COLLECTION_NAME,
            "chunks": 0,
            "documents": 0,
            "status": "missing",
        }
    return {
        "collection_name": meta.get("collection_name", COLLECTION_NAME),
        "chunks": int(meta.get("chunks", 0)),
        "documents": int(meta.get("documents", 0)),
        "embedding_backend": meta.get("embedding_backend", "unknown"),
        "built_at": meta.get("built_at", ""),
        "status": "ready",
    }


def initialize_runtime(
    progress_callback: ProgressCallback | None = None,
    force_rebuild: bool = False,
) -> Dict[str, Any]:
    _emit_progress(
        progress_callback,
        "startup",
        "Starting compliance runtime initialization...",
        0.02,
    )
    result = ensure_qdrant_index(force_rebuild=force_rebuild, progress_callback=progress_callback)
    model_dir = _model_dir_for_name(EMBED_MODEL_NAME)
    return {
        **result,
        "model_name": EMBED_MODEL_NAME,
        "model_dir": str(model_dir),
        "index_status": get_index_status(),
    }
