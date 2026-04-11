from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import DATABASE_URL, engine  # noqa: E402


BUSINESS_TABLES = {
    "users",
    "scripts",
    "talent_profiles",
    "trend_snapshots",
}


def _build_alembic_config() -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    return config


def _list_tables() -> set[str]:
    with engine.connect() as connection:
        return set(inspect(connection).get_table_names())


def main() -> int:
    config = _build_alembic_config()
    existing_tables = _list_tables()
    has_version_table = "alembic_version" in existing_tables
    discovered_business_tables = existing_tables & BUSINESS_TABLES

    if not has_version_table and discovered_business_tables == BUSINESS_TABLES:
        command.stamp(config, "head")
        print("✅ Alembic 已接管现有 PostgreSQL 业务表。")
        return 0

    if not has_version_table and discovered_business_tables:
        missing_tables = ", ".join(sorted(BUSINESS_TABLES - discovered_business_tables))
        found_tables = ", ".join(sorted(discovered_business_tables))
        raise SystemExit(
            "检测到 PostgreSQL 中只有部分业务表，无法安全自动接管。\n"
            f"已发现表: {found_tables or '无'}\n"
            f"缺失表: {missing_tables or '无'}\n"
            "请先清理不完整库，或手动确认后再执行迁移。"
        )

    command.upgrade(config, "head")
    print("✅ Alembic 迁移已应用到最新版本。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
