from __future__ import annotations

import copy
import json
import re
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import fitz
from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning
from markdownify import markdownify as html_to_markdown


PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_ROOT = PROJECT_ROOT / "data" / "knowledge_base"
RAW_DIR = KB_ROOT / "raw"
CATALOG_PATH = KB_ROOT / "source_catalog.json"
OUTPUT_DIR = KB_ROOT / "processed"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

PARSER_VERSION = "rag-normalizer-v1"

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

PLATFORM_DISPLAY = {
    "all": "All Platforms",
    "discord": "Discord",
    "douyin": "Douyin / WeChat Channels",
    "instagram": "Instagram Reels",
    "ragflow": "RAGFlow",
    "reddit": "Reddit",
    "tiktok": "TikTok",
    "x": "X",
    "youtube": "YouTube Shorts",
}

COUNTRY_CODE_ALIASES = {
    "UK": "GB",
}

DOCUMENT_TYPE_MAP = {
    "internal_brand": "internal_brand_reference",
    "market_law": "market_law",
    "platform_policy": "platform_policy",
    "technical_reference": "technical_reference",
}

NOISE_ATTR_KEYWORDS = {
    "alert",
    "banner",
    "breadcrumb",
    "cookie",
    "footer",
    "header",
    "hero-nav",
    "lang-switcher",
    "language",
    "masthead",
    "menu",
    "nav",
    "newsletter",
    "pagination",
    "promo",
    "related",
    "search",
    "share",
    "sidebar",
    "social",
    "subscribe",
    "toc",
    "toolbar",
}

NOISE_HEADING_PATTERNS = {
    "back to top",
    "contact us",
    "contact the competition bureau",
    "ctx footer menu 1",
    "ctx footer menu 2",
    "ctx footer menu 3",
    "footer",
    "further reading",
    "language selection",
    "menu",
    "ready to get started?",
    "search form",
    "site menu",
    "want to receive updates?",
    "wxt search form",
    "you are here",
}

WATERMARK_PATTERNS = (
    "draft",
    "confidential",
)

PAGE_NO_RE = re.compile(r"^(page\s+)?\d+\s*$", flags=re.IGNORECASE)
LIST_RE = re.compile(r"^(\d+[\.\)]|[A-Za-z][\.\)]|[-*•])\s+")
MULTISPACE_RE = re.compile(r"\s+")
EMPTY_TABLE_ROW_RE = re.compile(r"^\|\s*(\|\s*)+\|?$")
TOC_LINK_RE = re.compile(r"^\[table of contents\]\(.*\)$", flags=re.IGNORECASE)
ASA_FOOTER_RE = re.compile(r"^(?:\d+\s+)?legal, decent, honest and truthful(?:\s+\d+)?$", flags=re.IGNORECASE)


def load_catalog_map() -> Dict[str, Dict[str, Any]]:
    items = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {str(item["id"]): item for item in items}


def normalize_whitespace(text: str) -> str:
    return MULTISPACE_RE.sub(" ", text.replace("\u00a0", " ")).strip()


def normalize_line_key(text: str) -> str:
    text = normalize_whitespace(text).strip(" |:-").lower()
    text = re.sub(r"\s+\d+$", "", text).strip()
    return text


def clean_line(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2022", "•")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\uf0b7", "•")
    text = normalize_whitespace(text)
    return text


def attr_text(tag: Tag) -> str:
    if not isinstance(tag, Tag) or not getattr(tag, "attrs", None):
        return ""
    attrs: List[str] = []
    for key in ("id", "class", "role", "aria-label", "data-testid"):
        value = tag.attrs.get(key)
        if isinstance(value, list):
            attrs.extend(str(item) for item in value)
        elif value:
            attrs.append(str(value))
    return " ".join(attrs).lower()


def safe_text(tag: Tag) -> str:
    return normalize_whitespace(tag.get_text(" ", strip=True))


def link_density(tag: Tag) -> float:
    text = safe_text(tag)
    if not text:
        return 1.0
    link_text = sum(len(safe_text(a)) for a in tag.find_all("a"))
    return min(1.0, link_text / max(1, len(text)))


def remove_noise_nodes(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "canvas",
            "form",
            "button",
            "input",
            "select",
            "textarea",
            "iframe",
            "picture",
            "img",
            "video",
            "audio",
        ]
    ):
        tag.decompose()

    for tag in list(soup.find_all(True)):
        attrs = attr_text(tag)
        if attrs and any(keyword in attrs for keyword in NOISE_ATTR_KEYWORDS):
            text_length = len(safe_text(tag))
            if tag.name in {"nav", "header", "footer", "aside"} or text_length < 1600 or link_density(tag) > 0.45:
                tag.decompose()
                continue
        if getattr(tag, "attrs", None) and tag.get("aria-hidden") == "true":
            tag.decompose()


def score_candidate(tag: Tag) -> float:
    text = safe_text(tag)
    text_len = len(text)
    if text_len < 300:
        return -1.0

    headings = len(tag.find_all(re.compile(r"^h[1-6]$")))
    paragraphs = len(tag.find_all("p"))
    list_items = len(tag.find_all("li"))
    tables = len(tag.find_all("table"))
    density = link_density(tag)
    attrs = attr_text(tag)

    score = text_len
    score += headings * 550
    score += paragraphs * 100
    score += list_items * 40
    score += tables * 260
    score -= density * 2200

    if tag.name in {"article", "main"}:
        score += 1500
    if "content" in attrs or "article" in attrs or "policy" in attrs or "markdown" in attrs:
        score += 800
    if any(keyword in attrs for keyword in NOISE_ATTR_KEYWORDS):
        score -= 2400
    return score


def pick_content_root(soup: BeautifulSoup) -> Tag:
    preferred_selectors = [
        'article.markdown-body',
        'div[data-testid="readme"] article',
        'div[data-testid="readme"]',
        'div.markdown-body',
        'article[data-testid="readme"]',
    ]
    for selector in preferred_selectors:
        found = soup.select_one(selector)
        if isinstance(found, Tag) and len(safe_text(found)) > 400:
            return found

    preferred = [
        *soup.find_all("article"),
        *soup.find_all("main"),
        *soup.find_all(attrs={"role": "main"}),
    ]
    best: Tag | None = None
    best_score = -1.0

    for tag in preferred + soup.find_all(["section", "div", "body"]):
        score = score_candidate(tag)
        if score > best_score:
            best = tag
            best_score = score

    return best or soup.body or soup


def strip_noise_sections(root: Tag) -> None:
    for tag in list(root.find_all(True)):
        if tag.name in {"nav", "header", "footer", "aside"}:
            tag.decompose()
            continue

        attrs = attr_text(tag)
        if attrs and any(keyword in attrs for keyword in NOISE_ATTR_KEYWORDS):
            if link_density(tag) > 0.35 or len(safe_text(tag)) < 1200:
                tag.decompose()
                continue

        if tag.name and re.fullmatch(r"h[1-6]", tag.name):
            heading = safe_text(tag).lower()
            if heading in NOISE_HEADING_PATTERNS:
                parent = tag.parent if isinstance(tag.parent, Tag) else None
                if parent and parent is not root and len(safe_text(parent)) < 1800:
                    parent.decompose()
                else:
                    tag.decompose()


def html_markdown(root: Tag) -> str:
    html = str(root)
    markdown = html_to_markdown(
        html,
        heading_style="ATX",
        bullets="-",
        wrap=False,
        strip=["span"],
    )
    return markdown


def tidy_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    cleaned: List[str] = []
    prev_blank = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = clean_line(line)

        if not stripped:
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
            continue

        lower = stripped.lower()
        if PAGE_NO_RE.match(stripped):
            continue
        if EMPTY_TABLE_ROW_RE.match(stripped):
            continue
        if TOC_LINK_RE.match(stripped):
            continue
        if ASA_FOOTER_RE.match(stripped):
            continue
        if lower == "table of contents":
            continue
        if any(lower == token for token in WATERMARK_PATTERNS):
            continue
        if stripped.startswith("[Skip") or stripped.startswith("Cookie"):
            continue

        line = line.replace("\t", " ").rstrip()
        cleaned.append(line)
        prev_blank = False

    # Remove duplicated consecutive lines.
    deduped: List[str] = []
    for line in cleaned:
        if deduped and normalize_line_key(deduped[-1]) == normalize_line_key(line) and line.strip():
            continue
        deduped.append(line)

    text = "\n".join(deduped)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{2,}(\| --- )", r"\n\1", text)
    return text.strip() + "\n"


def extract_html_document(path: Path) -> Tuple[str, Dict[str, Any]]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    html_title = normalize_whitespace(soup.title.get_text(" ", strip=True)) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = normalize_whitespace(description_tag.get("content", "")) if description_tag else ""
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical_url = canonical_tag.get("href", "").strip() if canonical_tag else ""

    remove_noise_nodes(soup)
    root = copy.copy(pick_content_root(soup))
    strip_noise_sections(root)
    markdown = tidy_markdown(html_markdown(root))

    meta: Dict[str, Any] = {
        "html_title": html_title,
        "meta_description": description,
    }
    if canonical_url:
        meta["canonical_url"] = canonical_url

    return markdown, meta


def cluster_positions(values: Sequence[float], gap: float = 72.0) -> List[List[float]]:
    if not values:
        return []
    values = sorted(values)
    clusters: List[List[float]] = [[values[0]]]
    for value in values[1:]:
        if abs(value - clusters[-1][-1]) <= gap:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return clusters


def normalize_pdf_paragraph(lines: Sequence[str]) -> str:
    pieces: List[str] = []
    for line in lines:
        cleaned = clean_line(line)
        if not cleaned:
            continue
        if pieces and not LIST_RE.match(cleaned):
            pieces[-1] = pieces[-1].rstrip("-") + (" " if not pieces[-1].endswith(("/", "(", "[", "-")) else "") + cleaned
        else:
            pieces.append(cleaned)
    return "\n".join(piece for piece in pieces if piece)


def build_pdf_blocks(page: fitz.Page) -> List[Dict[str, Any]]:
    page_dict = page.get_text("dict")
    blocks: List[Dict[str, Any]] = []

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue

        raw_lines: List[str] = []
        font_sizes: List[float] = []
        flags: List[int] = []

        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(span.get("text", "") for span in spans)
            if not text.strip():
                continue
            raw_lines.append(text)
            font_sizes.extend(float(span.get("size", 0.0)) for span in spans if span.get("text", "").strip())
            flags.extend(int(span.get("flags", 0)) for span in spans if span.get("text", "").strip())

        if not raw_lines:
            continue

        text = normalize_pdf_paragraph(raw_lines)
        if not text:
            continue

        x0, y0, x1, y1 = block["bbox"]
        blocks.append(
            {
                "kind": "text",
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "y1": float(y1),
                "width": float(x1 - x0),
                "height": float(y1 - y0),
                "text": text,
                "font_size": max(font_sizes) if font_sizes else 0.0,
                "font_flags": max(flags) if flags else 0,
            }
        )

    return blocks


def table_to_markdown(rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    padded = []
    for row in rows:
        padded.append([clean_line(cell) if cell else "" for cell in list(row) + [""] * (width - len(row))])

    header = padded[0]
    separator = ["---"] * width
    body = padded[1:] if len(padded) > 1 else []

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def is_real_table(rows: Sequence[Sequence[str]]) -> bool:
    if len(rows) < 2:
        return False
    width = max(len(row) for row in rows)
    if width < 2:
        return False

    non_empty = 0
    unique_cells = set()
    max_cell_length = 0
    for row in rows:
        for cell in row:
            cleaned = clean_line(cell) if cell else ""
            if cleaned:
                non_empty += 1
                unique_cells.add(cleaned.lower())
                max_cell_length = max(max_cell_length, len(cleaned))

    if non_empty < 4 or len(unique_cells) < 4:
        return False

    if max_cell_length > 500:
        return False

    header_non_empty = max(
        sum(1 for cell in row if clean_line(cell or ""))
        for row in rows[:2]
    )
    if header_non_empty < 2:
        return False

    avg_non_empty = non_empty / max(1, len(rows))
    if avg_non_empty < 1.8:
        return False

    if width >= 6 and non_empty / max(1, len(rows) * width) < 0.5:
        return False

    return True


def build_pdf_tables(page: fitz.Page) -> List[Dict[str, Any]]:
    tables: List[Dict[str, Any]] = []
    try:
        finder = page.find_tables()
    except Exception:
        return tables

    for table in finder.tables:
        rows = table.extract()
        if not rows or not is_real_table(rows):
            continue
        x0, y0, x1, y1 = table.bbox
        tables.append(
            {
                "kind": "table",
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "y1": float(y1),
                "width": float(x1 - x0),
                "height": float(y1 - y0),
                "text": table_to_markdown(rows),
            }
        )
    return tables


def overlaps(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    x_overlap = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
    y_overlap = min(a["y1"], b["y1"]) - max(a["y0"], b["y0"])
    return x_overlap > 10 and y_overlap > 10


def order_page_elements(elements: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not elements:
        return []

    x_positions = [element["x0"] for element in elements]
    clusters = cluster_positions(x_positions)
    if len(clusters) <= 1:
        return sorted(elements, key=lambda item: (round(item["y0"], 1), round(item["x0"], 1)))

    cluster_centers = [sum(cluster) / len(cluster) for cluster in clusters]

    def cluster_index(x0: float) -> int:
        return min(range(len(cluster_centers)), key=lambda idx: abs(x0 - cluster_centers[idx]))

    return sorted(elements, key=lambda item: (cluster_index(item["x0"]), round(item["y0"], 1)))


def guess_heading_level(text: str, font_size: float, body_font: float) -> int | None:
    plain = clean_line(text)
    if not plain:
        return None
    if plain.startswith("#"):
        return None

    word_count = len(plain.split())
    if word_count > 20:
        return None

    if font_size >= body_font + 11 or len(plain) <= 36 and font_size >= body_font + 6:
        return 1
    if font_size >= body_font + 5:
        return 2
    if font_size >= body_font + 3 and word_count <= 12:
        return 3
    if plain.endswith("?") and word_count <= 12:
        return 2
    return None


def drop_repeated_noise(lines: Sequence[str], page_count: int) -> List[str]:
    keys = [normalize_line_key(line) for line in lines if line.strip()]
    counts = Counter(key for key in keys if key)
    threshold = max(3, page_count // 4)
    repeated = {
        key
        for key, count in counts.items()
        if count >= threshold and (len(key) < 80 or PAGE_NO_RE.match(key))
    }

    cleaned: List[str] = []
    for line in lines:
        key = normalize_line_key(line)
        if key in repeated and (PAGE_NO_RE.match(line.strip()) or len(key) < 80):
            continue
        cleaned.append(line)
    return cleaned


def extract_pdf_document(path: Path) -> Tuple[str, Dict[str, Any]]:
    doc = fitz.open(path)
    page_count = doc.page_count
    document_lines: List[str] = []
    body_font_counter: Counter[float] = Counter()
    pages_with_tables = 0

    page_elements_cache: List[List[Dict[str, Any]]] = []

    for page in doc:
        tables = build_pdf_tables(page)
        text_blocks = build_pdf_blocks(page)
        if tables:
            pages_with_tables += 1

        filtered_blocks = []
        for block in text_blocks:
            if any(overlaps(block, table) for table in tables):
                continue
            filtered_blocks.append(block)
            rounded_size = round(block["font_size"])
            if rounded_size >= 6:
                body_font_counter[rounded_size] += 1

        page_elements_cache.append(order_page_elements([*filtered_blocks, *tables]))

    body_font = float(body_font_counter.most_common(1)[0][0]) if body_font_counter else 11.0

    for page_number, elements in enumerate(page_elements_cache, start=1):
        if document_lines and document_lines[-1].strip():
            document_lines.append("")

        for element in elements:
            if element["kind"] == "table":
                document_lines.append(element["text"])
                document_lines.append("")
                continue

            text = element["text"]
            heading_level = guess_heading_level(text, float(element.get("font_size", body_font)), body_font)
            plain = clean_line(text)

            if PAGE_NO_RE.match(plain):
                continue

            if heading_level:
                document_lines.append(f"{'#' * heading_level} {plain}")
            else:
                document_lines.append(text)
            document_lines.append("")

    cleaned_lines = []
    for line in drop_repeated_noise(document_lines, page_count):
        stripped = line.strip()
        if not stripped:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        lower = stripped.lower()
        if any(lower == token for token in WATERMARK_PATTERNS):
            continue
        cleaned_lines.append(line.rstrip())

    markdown = tidy_markdown("\n".join(cleaned_lines))
    meta = {
        "page_count": page_count,
        "pdf_body_font_size": body_font,
        "pages_with_detected_tables": pages_with_tables,
    }
    return markdown, meta


def build_metadata(entry: Dict[str, Any], raw_path: Path, extra: Dict[str, Any]) -> Dict[str, Any]:
    platform_code = str(entry.get("platform", "all")).lower()
    document_type = DOCUMENT_TYPE_MAP.get(str(entry.get("category", "")), str(entry.get("category", "")))
    region = str(entry.get("market", "GLOBAL"))
    region_pack = str(entry.get("region", "GLOBAL"))
    source_type = "law" if document_type == "market_law" else "policy"
    country_code = COUNTRY_CODE_ALIASES.get(region, region) if region not in {"GLOBAL", "EU", "INTERNAL"} else ""
    is_global_fallback = region in {"GLOBAL", "EU"}

    metadata = {
        "source_id": str(entry["id"]),
        "title": str(entry.get("title", raw_path.stem)),
        "platform": platform_code,
        "platform_display": PLATFORM_DISPLAY.get(platform_code, platform_code.title()),
        "region": region,
        "region_pack": region_pack,
        "document_type": document_type,
        "source_category": str(entry.get("category", "")),
        "language": str(entry.get("language", "")),
        "source_url": str(entry.get("url", "")),
        "priority": str(entry.get("priority", "")),
        "notes": str(entry.get("notes", "")),
        "raw_file": str(raw_path.relative_to(PROJECT_ROOT)),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "parser_version": PARSER_VERSION,
        "doc_id": str(entry["id"]),
        "source_title": str(entry.get("title", raw_path.stem)),
        "source_type": source_type,
        "country_code": country_code,
        "distribution_mode": "all",
        "brand_id": "all",
        "block_id": str(entry["id"]),
        "is_global_fallback": is_global_fallback,
    }
    metadata.update(extra)
    return metadata


def add_title_if_missing(markdown: str, title: str) -> str:
    stripped = markdown.lstrip()
    if stripped.startswith("# "):
        return markdown
    return f"# {title}\n\n{markdown.lstrip()}"


def postprocess_by_source(source_id: str, markdown: str) -> str:
    if source_id == "law_uk_asa_pdf":
        lines = markdown.splitlines()
        try:
            toc_index = lines.index("# Table of contents")
        except ValueError:
            return markdown

        next_index = None
        for index in range(toc_index + 1, len(lines)):
            if lines[index].strip() == "# Who are you?":
                next_index = index
                break

        if next_index is not None:
            kept = lines[:toc_index] + lines[next_index:]
            markdown = "\n".join(kept)

    return markdown


def write_output(source_id: str, metadata: Dict[str, Any], markdown: str) -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = OUTPUT_DIR / f"{source_id}.md"
    json_path = OUTPUT_DIR / f"{source_id}.json"

    metadata_block = "```json\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n```\n\n"
    md_path.write_text(metadata_block + markdown, encoding="utf-8")
    json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "source_id": source_id,
        "markdown_path": str(md_path.relative_to(PROJECT_ROOT)),
        "metadata_path": str(json_path.relative_to(PROJECT_ROOT)),
        "title": metadata["title"],
        "platform": metadata["platform"],
        "region": metadata["region"],
        "document_type": metadata["document_type"],
    }


def process_raw_document(raw_path: Path, catalog_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    source_id = raw_path.stem
    entry = catalog_map.get(source_id)
    if not entry:
        raise KeyError(f"Missing source catalog entry for {source_id}")

    if raw_path.suffix.lower() == ".html":
        markdown, extra = extract_html_document(raw_path)
    elif raw_path.suffix.lower() == ".pdf":
        markdown, extra = extract_pdf_document(raw_path)
    else:
        raise ValueError(f"Unsupported suffix: {raw_path.suffix}")

    metadata = build_metadata(entry, raw_path, extra)
    markdown = add_title_if_missing(markdown, metadata["title"])
    markdown = postprocess_by_source(source_id, markdown)
    markdown = tidy_markdown(markdown)
    result = write_output(source_id, metadata, markdown)
    result["raw_suffix"] = raw_path.suffix.lower()
    return result


def main() -> None:
    catalog_map = load_catalog_map()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, Any]] = []
    for raw_path in sorted(RAW_DIR.glob("*")):
        if not raw_path.is_file():
            continue
        if raw_path.suffix.lower() not in {".html", ".pdf"}:
            continue
        result = process_raw_document(raw_path, catalog_map)
        manifest.append(result)
        print(f"processed | {raw_path.name}", flush=True)

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved {len(manifest)} processed documents to {OUTPUT_DIR}")
    print(f"Saved manifest to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
