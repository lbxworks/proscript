from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
LEGACY_SQLITE_PATH = PROJECT_ROOT / "data" / "app.db"

load_dotenv(dotenv_path=ENV_PATH, override=False)

DEFAULT_DATABASE_URL = f"postgresql+psycopg2:///{os.getenv('POSTGRES_DB', 'pro_script_ai')}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip()


class Base(DeclarativeBase):
    pass


def _build_engine():
    connect_args: dict[str, object] = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        DATABASE_URL,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)

_SCHEMA_LOCK = threading.Lock()
_SCHEMA_READY = False


def ensure_database_schema() -> None:
    global _SCHEMA_READY

    if _SCHEMA_READY:
        return

    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        from backend import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        _SCHEMA_READY = True


@contextmanager
def session_scope() -> Iterator[Session]:
    ensure_database_schema()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
