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
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|){3,}\s*$")
TIME_HEADER_PATTERN = re.compile(r"(time|时间|时码|time code)", flags=re.IGNORECASE)
VISUAL_HEADER_PATTERN = re.compile(r"(visual|镜头|画面|动作)", flags=re.IGNORECASE)
AUDIO_HEADER_PATTERN = re.compile(r"(audio|声音|对白|旁白|bgm)", flags=re.IGNORECASE)
SCENE_MARKER_PATTERN = re.compile(
    r"^\s*(scene|场景|镜头|escena|scène|szene|مشهد|シーン)\b",
    flags=re.IGNORECASE,
)
INT_EXT_PATTERN = re.compile(
    r"^\s*(int|ext|int/ext|interior|exterior|室内|室外|内景|外景|int\.|ext\.)\b",
    flags=re.IGNORECASE,
)


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


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|").strip()
    if not stripped:
        return []
    return [cell.strip() for cell in stripped.split("|")]


def _is_script_table_header(cells: list[str]) -> bool:
    if len(cells) != 4:
        return False
    header_text = " | ".join(cells)
    return bool(
        TIME_HEADER_PATTERN.search(header_text)
        and VISUAL_HEADER_PATTERN.search(header_text)
        and AUDIO_HEADER_PATTERN.search(header_text)
    )


def _render_table_row(cells: list[str]) -> str:
    return f"| {' | '.join(cells)} |"


def _repair_four_column_script_row(cells: list[str]) -> list[str]:
    if len(cells) <= 4:
        return cells

    if len(cells) >= 6 and SCENE_MARKER_PATTERN.search(cells[1]) and INT_EXT_PATTERN.search(cells[2]):
        return [
            cells[0],
            " / ".join(part for part in cells[1:4] if part),
            cells[4],
            " | ".join(part for part in cells[5:] if part),
        ]

    return [
        cells[0],
        " / ".join(part for part in cells[1:-2] if part),
        cells[-2],
        cells[-1],
    ]


def _repair_script_tables(text: str) -> str:
    lines = text.split("\n")
    repaired_lines: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        cells = _split_table_row(line) if line.lstrip().startswith("|") else []

        if (
            cells
            and _is_script_table_header(cells)
            and index + 1 < len(lines)
            and TABLE_SEPARATOR_PATTERN.match(lines[index + 1].strip())
        ):
            repaired_lines.append(_render_table_row(cells))
            repaired_lines.append(lines[index + 1].strip())
            index += 2

            while index < len(lines):
                row_line = lines[index]
                if not row_line.lstrip().startswith("|"):
                    break

                row_cells = _split_table_row(row_line)
                if row_cells:
                    repaired_lines.append(_render_table_row(_repair_four_column_script_row(row_cells)))
                else:
                    repaired_lines.append(row_line)
                index += 1
            continue

        repaired_lines.append(line)
        index += 1

    return "\n".join(repaired_lines)


def sanitize_script_markdown(value: str | None) -> str:
    text = _strip_outer_code_fences(str(value or "").replace("\r\n", "\n").replace("\r", "\n"))
    if not text:
        return ""

    start_index = _find_script_start(text)
    if start_index is not None and text[:start_index].strip():
        text = text[start_index:]

    text = _repair_script_tables(text)
    return text.strip()
