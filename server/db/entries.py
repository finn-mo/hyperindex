import logging
import sqlite3
from typing import Optional

from server.db.connection import get_conn
from server.models.dto import EntryDTO


def entry_from_row(row: sqlite3.Row) -> EntryDTO:
    return EntryDTO(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        tags=[t.strip() for t in row["tags"].split(",") if t.strip()],
        description=row["description"],
        date_added=row["date_added"],
        archived_url=row["archived_url"],
        snapshot_dir=row["snapshot_dir"],
        deleted=bool(row["deleted"])
    )


def insert_entry(entry: EntryDTO) -> int:
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO entries
                (url, title, tags, description, date_added, archived_url, snapshot_dir, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.url,
                    entry.title,
                    ", ".join(entry.tags),
                    entry.description,
                    entry.date_added,
                    entry.archived_url,
                    entry.snapshot_dir,
                    int(entry.deleted),
                ),
            )
            return cursor.lastrowid
    except sqlite3.Error as e:
        logging.error(f"Insert failed: {e}")
        raise


def fetch_entry_by_id(entry_id: int) -> Optional[EntryDTO]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return entry_from_row(row) if row else None


def fetch_all_entries(limit: int, offset: int) -> list[EntryDTO]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM entries ORDER BY id LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
        return [entry_from_row(row) for row in rows]


def count_entries() -> int:
    with get_conn() as conn:
        result = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
        return result[0] if result else 0


def delete_entry_by_id(entry_id: int) -> bool:
    try:
        with get_conn() as conn:
            result = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            return result.rowcount > 0
    except sqlite3.Error as e:
        logging.error(f"Delete failed for entry {entry_id}: {e}")
        return False


def update_entry_by_id(entry_id: int, update: EntryDTO) -> bool:
    try:
        with get_conn() as conn:
            result = conn.execute(
                """
                UPDATE entries
                SET url = ?, title = ?, tags = ?, description = ?, date_added = ?,
                    archived_url = ?, snapshot_dir = ?, deleted = ?
                WHERE id = ?
                """,
                (
                    update.url,
                    update.title,
                    ", ".join(update.tags),
                    update.description,
                    update.date_added,
                    update.archived_url,
                    update.snapshot_dir,
                    int(update.deleted),
                    entry_id
                )
            )
            return result.rowcount > 0
    except sqlite3.Error as e:
        logging.error(f"Update failed for entry {entry_id}: {e}")
        return False