from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import DATABASE_URL, ensure_database_schema  # noqa: E402


def init_db() -> None:
    ensure_database_schema()
    print(f"✅ Database schema initialized: {DATABASE_URL}")


if __name__ == "__main__":
    init_db()
