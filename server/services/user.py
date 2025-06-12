from datetime import datetime, timezone
from typing import List, Tuple

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from server.models.entities import Entry, Tag
from server.models.schemas import EntryCreate
from server.services.shared import SharedEntryService, TagService


class UserEntryService:
    """
    Service layer for user-owned entries.

    Provides methods to create, update, delete, search, and submit personal entries
    for potential inclusion in the public Yellow Pages.
    """

    @staticmethod
    def create_entry(db: Session, entry_in: EntryCreate, user_id: int) -> Entry:
        """
        Create a new personal entry for the given user.

        Resolves tag references and assigns metadata. Commits entry to database.

        Args:
            db (Session): SQLAlchemy database session.
            entry_in (EntryCreate): Input data from form or API.
            user_id (int): ID of the owning user.

        Returns:
            Entry: The created Entry object.
        """
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
        """
        Update an existing user-owned entry with new metadata and tags.

        Args:
            db (Session): Database session.
            entry_id (int): ID of the entry to update.
            user_id (int): Must match entry owner.
            data (EntryCreate): Updated entry content.

        Returns:
            Entry: The updated Entry instance.

        Raises:
            NoResultFound: If entry is not found or access is denied.
        """
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
        """
        Soft-delete a user-owned entry.

        Marks the entry as deleted but does not remove it from the database.

        Args:
            db (Session): Database session.
            entry_id (int): Entry to delete.
            user_id (int): Must match entry owner.
        """
        entry = SharedEntryService.get_entry_by_id(db, entry_id, user_id)
        entry.is_deleted = True
        db.commit()

    @staticmethod
    def submit_for_review(db: Session, entry_id: int, user_id: int) -> None:
        """
        Submit a user-owned entry for admin review.

        Flags the entry as submitted. Only valid for non-deleted, non-public entries.

        Args:
            db (Session): Database session.
            entry_id (int): ID of the entry to submit.
            user_id (int): Must match entry owner.

        Raises:
            HTTPException: If entry is deleted or is already a public copy.
        """
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
        """
        Perform a full-text search on a user's entries using SQLite FTS.

        Args:
            db (Session): Database session.
            user_id (int): Owner of the entries to search.
            query (str): Full-text search query.
            limit (int): Max number of results.
            offset (int): Pagination offset.

        Returns:
            Tuple[List[Entry], int]: Search result entries and total count.
        """
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
        """
        Retrieve all distinct tag names used by the user on active entries.

        Args:
            db (Session): Database session.
            user_id (int): ID of the user.

        Returns:
            List[str]: List of distinct tag names.
        """
        return [
            tag for (tag,) in (
                db.query(Tag.name)
                .join(Entry.tags)
                .filter(Entry.user_id == user_id, Entry.is_deleted == False)
                .distinct()
                .all()
            )
        ]