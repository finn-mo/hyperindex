from collections import Counter
import csv
import json
from pathlib import Path
import sqlite3
from typing import Optional

from core.config import Config
from core.models import Entry


def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a SQLite connection to the database."""
    path = db_path or Config.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the entries table if it does not exist."""
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
            )
        """)


def entry_from_row(row: sqlite3.Row) -> Entry:
    """Convert a database row into an Entry object"""
    return Entry(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        tags=parse_tags(row["tags"]),
        description=row["description"],
        date_added=row["date_added"],
        archived_url=row["archived_url"],
        snapshot_dir=row["snapshot_dir"],
        deleted=bool(row["deleted"])
    )


def entry_to_db_tuple(entry: Entry) -> tuple[str, str, str, str, str, str, str]:
    """Convert an Entry object to a tuple for insertion into the database"""
    return (
        entry.url,
        entry.title,
        ", ".join(entry.tags or []),
        entry.description,
        entry.date_added,
        entry.archived_url,
        entry.snapshot_dir
    )


def parse_tags(tag_string: str) -> list[str]:
    """Split a comma-separated tag string into a list of lowercase tags"""
    return [t.strip().lower() for t in tag_string.split(",") if t.strip()]


def add_entry(entry: Entry) -> None:
    """Insert a new entry into the database"""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO entries (url, title, tags, description, date_added, archived_url, snapshot_dir) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            entry_to_db_tuple(entry)
        )


def get_entry(entry_id: int) -> Optional[Entry]:
    """Return a single entry by ID, or None if not found"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ? AND deleted = 0", (entry_id,)).fetchone()
        return entry_from_row(row) if row else None


def update_entry(
        entry_id: int,
        title: Optional[str] = None,
        tags: Optional[str] = None,
        desc: Optional[str] = None,
        add_tags: Optional[list[str]] = None,
        remove_tags: Optional[list[str]] = None
    ) -> bool:
    """Update an entry’s title, description, or tags"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ? AND deleted = 0", (entry_id,)).fetchone()
        if not row:
            return False

        updates = []
        values = []

        if tags is not None:
            updates.append("tags = ?")
            values.append(tags)
        elif add_tags or remove_tags:
            existing_tags = row["tags"]
            updated_tags = set(parse_tags(existing_tags)) if existing_tags else set()
            if add_tags:
                updated_tags.update(parse_tags(",".join(add_tags)))
            if remove_tags:
                updated_tags.difference_update(parse_tags(",".join(remove_tags)))
            updates.append("tags = ?")
            values.append(", ".join(sorted(updated_tags)))

        if title is not None:
            updates.append("title = ?")
            values.append(title)
        if desc is not None:
            updates.append("description = ?")
            values.append(desc)

        if updates:
            values.append(entry_id)
            conn.execute(f"UPDATE entries SET {', '.join(updates)} WHERE id = ?", values)
            return True

    return False


def delete_entry(entry_id: int) -> bool:
    """Soft-delete an entry, return True if successful"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ? AND deleted = 0", (entry_id,)).fetchone()
        if not row:
            return False
        conn.execute("UPDATE entries SET deleted = 1 WHERE id = ?", (entry_id,))
        return True


def restore_entry(entry_id: int) -> bool:
    """Restore a previously deleted entry by ID"""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ? AND deleted = 1", (entry_id,)).fetchone()
        if not row:
            return False
        conn.execute("UPDATE entries SET deleted = 0 WHERE id = ?", (entry_id,))
        return True


def purge_deleted_entries() -> None:
    """Permanently delete all entries marked as deleted"""
    with get_conn() as conn:
        conn.execute("DELETE FROM entries WHERE deleted = 1")


def list_entries(include_deleted: bool = False) -> list[Entry]:
    """Return a list of entries, optionally including deleted ones."""
    with get_conn() as conn:
        sql = "SELECT * FROM entries"
        if not include_deleted:
            sql += " WHERE deleted = 0"
        sql += " ORDER BY id"
        rows = conn.execute(sql).fetchall()
        return [entry_from_row(row) for row in rows]


def list_deleted_entries() -> list[Entry]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM entries WHERE deleted = 1 ORDER BY id").fetchall()
        return [entry_from_row(row) for row in rows]


def search_entries(query: Optional[str] = None, tag: Optional[str] = None) -> list[Entry]:
    """Return a list of Entry objects that match the given query or tag"""
    sql = "SELECT * FROM entries WHERE deleted = 0"
    params = []

    if query:
        sql += " AND (title LIKE ? OR description LIKE ? OR url LIKE ?)"
        like = f"%{query.lower()}%"
        params.extend([like, like, like])

    if tag:
        sql += " AND lower(tags) LIKE ?"
        params.append(f"%{tag.lower()}%")

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [entry_from_row(row) for row in rows]


def count_tags() -> Counter:
    """Return a frequency count of all tags across entries"""
    with get_conn() as conn:
        rows = conn.execute("SELECT tags FROM entries").fetchall()
        tags = []
        for row in rows:
            tags += parse_tags(row["tags"]) if row["tags"] else []
        return Counter(tags)


def export_entries_json(
        filename="export.json",
        export_dir: Optional[Path] = None,
        include_deleted: bool = False
    ) -> str:
    """Export all entries to a JSON file"""
    entries = list_entries(include_deleted=include_deleted)
    data = [e.__dict__ for e in entries]
    path = (export_dir or Config.EXPORT_DIR) / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return str(path)


def export_entries_csv(
        filename="export.csv",
        export_dir: Optional[Path] = None,
        include_deleted: bool = False
    ) -> str:
    """Export all entries to a CSV file"""
    entries = list_entries(include_deleted=include_deleted)
    path = (export_dir or Config.EXPORT_DIR) / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "url", "title", "tags", "description", "date_added", "archived_url", "snapshot_dir", "deleted"])
        for e in entries:
            writer.writerow([
                e.id,
                e.url,
                e.title,
                ", ".join(e.tags or []),
                e.description,
                e.date_added,
                e.archived_url,
                e.snapshot_dir,
                int(e.deleted)
            ])
    return str(path)