from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import DATABASE_URL, LEGACY_SQLITE_PATH, engine, ensure_database_schema, session_scope  # noqa: E402
from backend.models import Script, TalentProfile, TrendSnapshot, User  # noqa: E402


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text_value = str(value).strip()
    if not text_value:
        return None
    try:
        return datetime.fromisoformat(text_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return {}
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _load_sqlite_rows(table_name: str) -> list[dict[str, Any]]:
    connection = sqlite3.connect(LEGACY_SQLITE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def _sync_postgres_sequence(table_name: str, column_name: str = "id") -> None:
    if not DATABASE_URL.startswith("postgresql"):
        return

    query = text(
        """
        SELECT setval(
            pg_get_serial_sequence(:table_name, :column_name),
            COALESCE((SELECT MAX(id) FROM ONLY """ + table_name + """), 1),
            (SELECT COUNT(*) > 0 FROM ONLY """ + table_name + """)
        )
        """
    )
    with engine.begin() as connection:
        connection.execute(query, {"table_name": table_name, "column_name": column_name})


def migrate() -> dict[str, Any]:
    ensure_database_schema()

    users = _load_sqlite_rows("users")
    scripts = _load_sqlite_rows("scripts")
    talents = _load_sqlite_rows("talent_profiles")
    trend_snapshots = _load_sqlite_rows("trend_snapshots")

    with session_scope() as session:
        for row in users:
            session.merge(
                User(
                    id=row["id"],
                    name=row["name"],
                    style_prompt=row["style_prompt"],
                    few_shot=row.get("few_shot"),
                )
            )

        for row in talents:
            session.merge(
                TalentProfile(
                    id=row["id"],
                    user_id=row.get("user_id"),
                    name=row["name"],
                    platform=row.get("platform") or "未设置",
                    email=row.get("email") or "",
                    recent_video_link=row.get("recent_video_link") or "",
                    notes=row.get("notes") or "",
                    collaboration_progress=row.get("collaboration_progress") or "待沟通",
                    created_at=_parse_datetime(row.get("created_at")),
                    updated_at=_parse_datetime(row.get("updated_at")),
                )
            )

        for row in scripts:
            session.merge(
                Script(
                    id=row["id"],
                    user_id=row.get("user_id"),
                    topic=row["topic"],
                    platform=row.get("platform"),
                    duration=row.get("duration"),
                    creativity=row.get("creativity"),
                    language=row.get("language"),
                    content=row["content"],
                    created_at=_parse_datetime(row.get("created_at")),
                )
            )

        for row in trend_snapshots:
            session.merge(
                TrendSnapshot(
                    module_name=row["module_name"],
                    scope_key=row["scope_key"],
                    filters_json=_parse_json(row.get("filters_json")),
                    payload_json=_parse_json(row.get("payload_json")),
                    updated_at=_parse_datetime(row.get("updated_at")),
                )
            )

    for table_name in ("users", "scripts", "talent_profiles"):
        _sync_postgres_sequence(table_name)

    return {
        "database_url": DATABASE_URL,
        "sqlite_path": str(LEGACY_SQLITE_PATH),
        "users": len(users),
        "talent_profiles": len(talents),
        "scripts": len(scripts),
        "trend_snapshots": len(trend_snapshots),
    }


if __name__ == "__main__":
    summary = migrate()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
