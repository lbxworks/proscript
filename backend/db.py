from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "app.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


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
