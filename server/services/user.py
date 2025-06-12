from datetime import datetime, timezone
from typing import List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from server.models.entities import Entry, Tag
from server.models.schemas import EntryCreate
from server.services.shared import SharedEntryService, TagService


class UserEntryService:
    @staticmethod
    def create_entry(db: Session, entry_in: EntryCreate, user_id: int) -> Entry:
        tags = TagService.resolve_tags(db, entry_in.tags or [])
        entry = Entry(
            url=entry_in.url,
            title=entry_in.title,
            notes=entry_in.notes,
            tags=tags,
            user_id=user_id,
            date_added=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def update_entry(db: Session, entry_id: int, user_id: int, data: EntryCreate) -> Entry:
        entry = SharedEntryService.get_entry_by_id(db, entry_id, user_id)
        entry.url = data.url
        entry.title = data.title
        entry.notes = data.notes
        entry.tags = TagService.resolve_tags(db, data.tags or [])
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def soft_delete_entry(db: Session, entry_id: int, user_id: int) -> None:
        entry = SharedEntryService.get_entry_by_id(db, entry_id, user_id)
        entry.is_deleted = True
        db.commit()

    @staticmethod
    def submit_for_review(db: Session, entry_id: int, user_id: int) -> None:
        entry = SharedEntryService.get_entry_by_id(db, entry_id, user_id)
        if entry.is_deleted:
            raise HTTPException(status_code=404, detail="Entry not found")
        if entry.is_public_copy:
            raise HTTPException(status_code=400, detail="Cannot submit admin-managed entries")
        if not entry.submitted_to_public:
            entry.submitted_to_public = True
            db.commit()

    @staticmethod
    def search_entries(
        db: Session, user_id: int, query: str, limit: int = 10, offset: int = 0
    ) -> Tuple[List[Entry], int]:
        from sqlalchemy import text

        sql = text("""
            SELECT e.id
            FROM (
                SELECT rowid
                FROM entry_fts
                WHERE entry_fts MATCH :query
            ) fts
            JOIN entries e ON e.id = fts.rowid
            WHERE e.user_id = :user_id AND e.is_deleted = 0
            ORDER BY e.id DESC
            LIMIT :limit OFFSET :offset
        """)
        id_rows = db.execute(sql, {
            "user_id": user_id,
            "query": query,
            "limit": limit,
            "offset": offset
        }).fetchall()

        ids = [row[0] for row in id_rows]
        if not ids:
            return [], 0

        entries = (
            db.query(Entry)
            .filter(Entry.id.in_(ids))
            .order_by(Entry.id.desc())
            .all()
        )

        count_sql = text("""
            SELECT COUNT(*)
            FROM (
                SELECT rowid
                FROM entry_fts
                WHERE entry_fts MATCH :query
            ) fts
            JOIN entries e ON e.id = fts.rowid
            WHERE e.user_id = :user_id AND e.is_deleted = 0
        """)
        total = db.execute(count_sql, {
            "user_id": user_id,
            "query": query
        }).scalar()

        return entries, total
    
    @staticmethod
    def get_user_tags(db: Session, user_id: int) -> List[str]:
        return [
            tag for (tag,) in (
                db.query(Tag.name)
                .join(Entry.tags)
                .filter(Entry.user_id == user_id, Entry.is_deleted == False)
                .distinct()
                .all()
            )
        ]