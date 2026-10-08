import sqlite3
from contextvars import ContextVar
from contextlib import contextmanager
from config import DB_PATH

_database_path = ContextVar("database_path", default=str(DB_PATH))


def bind_database_path(path: str):
    """Use a database path for the current request/task context."""
    return _database_path.set(str(path))


def reset_database_path(token) -> None:
    _database_path.reset(token)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_database_path.get(), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db():
    """用法: with db() as conn: conn.execute(...)"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
