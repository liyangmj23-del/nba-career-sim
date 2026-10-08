"""Create one private SQLite save database per signed browser session."""
import hashlib
import shutil
from pathlib import Path
from threading import Lock

from config import SEED_DB_PATH, SESSION_DB_DIR

_init_lock = Lock()


def get_or_create_session_database(session_id: str) -> Path:
    """Return a seeded database path that cannot be chosen by the client."""
    safe_id = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    SESSION_DB_DIR.mkdir(parents=True, exist_ok=True)
    target = SESSION_DB_DIR / f"{safe_id}.db"

    if target.exists():
        return target

    with _init_lock:
        if not target.exists():
            if not SEED_DB_PATH.exists():
                raise FileNotFoundError(f"Seed database missing: {SEED_DB_PATH}")
            temporary = target.with_suffix(".db.tmp")
            shutil.copyfile(SEED_DB_PATH, temporary)
            temporary.replace(target)

    return target
