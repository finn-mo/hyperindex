import os
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.getenv("HYPERINDEX_SERVER_DB", "server/data/yellowpages.db"))


def get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                tags TEXT,
                description TEXT,
                date_added TEXT,
                archived_url TEXT,
                snapshot_dir TEXT,
                deleted INTEGER DEFAULT 0
            );
        """)