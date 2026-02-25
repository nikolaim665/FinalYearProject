"""
Database engine, session factory, and helpers.

In Docker  : SQLite at /data/qlc.db  (persisted via Docker volume)
Locally    : SQLite at <project-root>/qlc.db  (fallback when /data doesn't exist)
Override   : set DATABASE_URL env var to any SQLAlchemy-compatible URL
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base  # noqa: re-export so callers can do `from database import Base`

# Resolve default DB path: prefer /data (Docker volume), fall back to project root
_data_dir = Path("/data")
_local_db = Path(__file__).parent.parent.parent / "qlc.db"
_default_url = (
    f"sqlite:///{_data_dir}/qlc.db"
    if _data_dir.exists()
    else f"sqlite:///{_local_db}"
)

DATABASE_URL = os.getenv("DATABASE_URL", _default_url)

engine = create_engine(
    DATABASE_URL,
    # Required for SQLite when used with FastAPI's threaded request handling
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist yet. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)
