from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "app.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_trend_snapshots_table() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trend_snapshots (
                module_name TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                filters_json TEXT NOT NULL DEFAULT '{}',
                payload_json TEXT NOT NULL DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (module_name, scope_key)
            )
            """
        )
        connection.commit()


def fetch_trend_snapshot(module_name: str, scope_key: str) -> dict[str, Any] | None:
    ensure_trend_snapshots_table()

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT module_name, scope_key, filters_json, payload_json, updated_at
            FROM trend_snapshots
            WHERE module_name = ? AND scope_key = ?
            """,
            (module_name, scope_key),
        )
        row = cursor.fetchone()

    if row is None:
        return None

    return {
        "module_name": str(row["module_name"]),
        "scope_key": str(row["scope_key"]),
        "filters": json.loads(str(row["filters_json"] or "{}")),
        "payload": json.loads(str(row["payload_json"] or "{}")),
        "updated_at": str(row["updated_at"] or ""),
    }


def upsert_trend_snapshot(
    *,
    module_name: str,
    scope_key: str,
    filters: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    ensure_trend_snapshots_table()

    filters_json = json.dumps(filters, ensure_ascii=False, sort_keys=True)
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO trend_snapshots (module_name, scope_key, filters_json, payload_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(module_name, scope_key) DO UPDATE SET
                filters_json = excluded.filters_json,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (module_name, scope_key, filters_json, payload_json),
        )
        connection.commit()
        cursor.execute(
            """
            SELECT updated_at
            FROM trend_snapshots
            WHERE module_name = ? AND scope_key = ?
            """,
            (module_name, scope_key),
        )
        row = cursor.fetchone()

    return {
        "module_name": module_name,
        "scope_key": scope_key,
        "filters": filters,
        "payload": payload,
        "updated_at": str(row["updated_at"] if row is not None else ""),
    }


def _derive_style_prompt(name: str, notes: str) -> str:
    cleaned_notes = notes.strip()
    if cleaned_notes:
        return cleaned_notes
    return f"你是达人{name}，请基于达人定位输出自然、有辨识度的短视频脚本。"


def _create_user_from_talent(cursor: sqlite3.Cursor, *, name: str, notes: str) -> int:
    cursor.execute(
        """
        INSERT INTO users (name, style_prompt, few_shot)
        VALUES (?, ?, ?)
        """,
        (name, _derive_style_prompt(name, notes), ""),
    )
    return int(cursor.lastrowid)


def _sync_existing_talent_users(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        SELECT id, name, notes
        FROM talent_profiles
        WHERE user_id IS NULL
        ORDER BY id
        """
    )
    missing_user_rows = cursor.fetchall()

    for row in missing_user_rows:
        user_id = _create_user_from_talent(
            cursor,
            name=str(row["name"] or f"达人 {row['id']}"),
            notes=str(row["notes"] or ""),
        )
        cursor.execute(
            """
            UPDATE talent_profiles
            SET user_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (user_id, int(row["id"])),
        )


def ensure_talent_profiles_table() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'talent_profiles'
            """
        )
        table_exists = cursor.fetchone() is not None

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS talent_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                platform TEXT NOT NULL DEFAULT '未设置',
                email TEXT DEFAULT '',
                recent_video_link TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                collaboration_progress TEXT NOT NULL DEFAULT '待沟通',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )

        if not table_exists:
            cursor.execute(
                """
                SELECT id, name, style_prompt
                FROM users
                ORDER BY id
                """
            )
            missing_profiles = cursor.fetchall()

            for row in missing_profiles:
                notes = str(row["style_prompt"] or "").strip() or "从原 users 表同步，待补充达人备注。"
                payload = (
                    int(row["id"]),
                    int(row["id"]),
                    str(row["name"] or f"达人 {row['id']}"),
                    "未设置",
                    "",
                    "",
                    notes,
                    "待沟通",
                )
                try:
                    cursor.execute(
                        """
                        INSERT INTO talent_profiles (
                            id,
                            user_id,
                            name,
                            platform,
                            email,
                            recent_video_link,
                            notes,
                            collaboration_progress
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        payload,
                    )
                except sqlite3.IntegrityError:
                    cursor.execute(
                        """
                        INSERT INTO talent_profiles (
                            user_id,
                            name,
                            platform,
                            email,
                            recent_video_link,
                            notes,
                            collaboration_progress
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        payload[1:],
                    )

        _sync_existing_talent_users(cursor)
        connection.commit()


def list_talent_profiles() -> list[dict[str, Any]]:
    ensure_talent_profiles_table()

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                id,
                user_id,
                name,
                platform,
                email,
                recent_video_link,
                notes,
                collaboration_progress,
                updated_at
            FROM talent_profiles
            ORDER BY id
            """
        )
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def create_talent_profile(
    *,
    name: str,
    platform: str,
    email: str,
    recent_video_link: str,
    notes: str,
    collaboration_progress: str,
) -> dict[str, Any]:
    ensure_talent_profiles_table()

    with get_connection() as connection:
        cursor = connection.cursor()
        user_id = _create_user_from_talent(cursor, name=name, notes=notes)
        cursor.execute(
            """
            INSERT INTO talent_profiles (
                user_id,
                name,
                platform,
                email,
                recent_video_link,
                notes,
                collaboration_progress
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, platform, email, recent_video_link, notes, collaboration_progress),
        )
        talent_id = int(cursor.lastrowid)
        connection.commit()

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                name,
                platform,
                email,
                recent_video_link,
                notes,
                collaboration_progress,
                updated_at
            FROM talent_profiles
            WHERE id = ?
            """,
            (talent_id,),
        )
        row = cursor.fetchone()

    if row is None:
        raise LookupError("新建达人后未能读取资料。")

    return dict(row)


def update_talent_profile(
    *,
    talent_id: int,
    name: str,
    platform: str,
    email: str,
    recent_video_link: str,
    notes: str,
    collaboration_progress: str,
) -> dict[str, Any] | None:
    ensure_talent_profiles_table()

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id
            FROM talent_profiles
            WHERE id = ?
            """,
            (talent_id,),
        )
        existing_row = cursor.fetchone()
        if existing_row is None:
            return None

        user_id = existing_row["user_id"]
        if user_id is None:
            user_id = _create_user_from_talent(cursor, name=name, notes=notes)
        else:
            cursor.execute(
                """
                UPDATE users
                SET
                    name = ?,
                    style_prompt = ?
                WHERE id = ?
                """,
                (name, _derive_style_prompt(name, notes), int(user_id)),
            )

        cursor.execute(
            """
            UPDATE talent_profiles
            SET
                user_id = ?,
                name = ?,
                platform = ?,
                email = ?,
                recent_video_link = ?,
                notes = ?,
                collaboration_progress = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (user_id, name, platform, email, recent_video_link, notes, collaboration_progress, talent_id),
        )

        connection.commit()
        cursor.execute(
            """
            SELECT
                id,
                user_id,
                name,
                platform,
                email,
                recent_video_link,
                notes,
                collaboration_progress,
                updated_at
            FROM talent_profiles
            WHERE id = ?
            """,
            (talent_id,),
        )
        row = cursor.fetchone()

    return dict(row) if row is not None else None


def delete_talent_profile(talent_id: int) -> bool:
    ensure_talent_profiles_table()

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id
            FROM talent_profiles
            WHERE id = ?
            """,
            (talent_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return False

        user_id = row["user_id"]
        if user_id is not None:
            cursor.execute(
                """
                UPDATE scripts
                SET user_id = NULL
                WHERE user_id = ?
                """,
                (int(user_id),),
            )

        cursor.execute("DELETE FROM talent_profiles WHERE id = ?", (talent_id,))
        deleted = cursor.rowcount > 0
        if deleted and user_id is not None:
            cursor.execute("DELETE FROM users WHERE id = ?", (int(user_id),))
        connection.commit()

    return deleted


def fetch_user_profile(user_id: int) -> dict[str, Any] | None:
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id, name, style_prompt, few_shot
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            )
            row = cursor.fetchone()
    except sqlite3.Error:
        return None

    return dict(row) if row is not None else None


def save_script_record(
    *,
    user_id: int,
    topic: str,
    platform: str,
    duration: str,
    creativity: float,
    language: str,
    content: str,
) -> int | None:
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO scripts (user_id, topic, platform, duration, creativity, language, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, topic, platform, duration, creativity, language, content),
            )
            connection.commit()
            return int(cursor.lastrowid)
    except sqlite3.Error:
        return None
