from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import or_, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import NoResultFound

from server.models.entities import Entry, Tag


class TagService:
    """Utility for resolving tag strings into Tag model instances."""

    @staticmethod
    def resolve_tags(db: Session, tags: List[str]) -> List[Tag]:
        """
        Convert a list of tag names into Tag model instances.

        Creates new tags in the database if they do not already exist.

        Args:
            db (Session): SQLAlchemy session.
            tags (List[str]): List of tag names to resolve.

        Returns:
            List[Tag]: List of resolved or newly created Tag instances.
        """
        tag_objects = []
        for tag_name in tags:
            tag = db.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            tag_objects.append(tag)
        return tag_objects


class SharedEntryService:
    """Shared entry logic used across multiple contexts (rolodex, yellowpages, admin)."""

    @staticmethod
    def get_entry_by_id(db: Session, entry_id: int, user_id: int | None = None) -> Entry:
        """
        Retrieve an entry by ID, optionally filtering by user ID.

        Args:
            db (Session): Database session.
            entry_id (int): ID of the entry to retrieve.
            user_id (Optional[int]): If provided, restricts access to entries owned by this user.

        Returns:
            Entry: The matching entry.

        Raises:
            NoResultFound: If entry is not found or does not belong to the user.
        """
        query = db.query(Entry).options(joinedload(Entry.tags)).filter(Entry.id == entry_id)
        if user_id is not None:
            query = query.filter(Entry.user_id == user_id)
        entry = query.first()
        if not entry:
            raise NoResultFound("Entry not found or access denied")
        return entry

    @staticmethod
    def search_public_entries_fts(
        db: Session,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Entry], int]:
        """
        Perform full-text search on public entries using SQLite FTS.

        Args:
            db (Session): Database session.
            query (str): Full-text search query string.
            limit (int): Maximum number of entries to return.
            offset (int): Number of entries to skip.

        Returns:
            Tuple[List[Entry], int]: List of matched entries and total result count.
        """
        sql = text("""
            SELECT e.id
            FROM (
                SELECT rowid
                FROM entry_fts
                WHERE entry_fts MATCH :query
            ) fts
            JOIN entries e ON e.id = fts.rowid
            WHERE e.is_public_copy = 1 AND e.is_deleted = 0
            ORDER BY e.id DESC
            LIMIT :limit OFFSET :offset
        """)
        id_rows = db.execute(sql, {
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
            WHERE e.is_public_copy = 1 AND e.is_deleted = 0
        """)
        total = db.execute(count_sql, {"query": query}).scalar()

        return entries, total
    
    @staticmethod
    def restore_entry(db: Session, entry_id: int) -> None:
        """
        Restore a soft-deleted public entry.

        Args:
            db (Session): Database session.
            entry_id (int): ID of the entry to restore.

        Raises:
            HTTPException: If entry is not found, not deleted, or not public.
        """
        entry = db.get(Entry, entry_id)
        if not entry or not entry.is_public_copy or not entry.is_deleted:
            raise HTTPException(status_code=404, detail="Cannot restore entry")

        entry.is_deleted = False
        entry.deleted_at = None
        db.commit()


class EntryQueryService:
    """Flexible filtered query interface for retrieving entries by tags, user, text, and state."""

    def __init__(self, db_session, base_query):
        """
        Initialize the entry filter service.

        Args:
            db_session (Session): SQLAlchemy database session.
            base_query: SQLAlchemy base query object.
        """
        self.db = db_session
        self.query = base_query

    @classmethod
    def get_entries(
        cls,
        db: Session,
        user_id: Optional[int] = None,
        public_only: bool = False,
        tag: Optional[str] = None,
        query: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Entry], int]:
        """
        Retrieve entries based on various filter options.

        Args:
            db (Session): Database session.
            user_id (Optional[int]): Restrict results to entries owned by this user.
            public_only (bool): If True, restrict to admin-approved public entries.
            tag (Optional[str]): Filter by tag name.
            query (Optional[str]): Perform LIKE-based full-text match.
            page (int): Page number (1-indexed).
            per_page (int): Entries per page.

        Returns:
            Tuple[List[Entry], int]: List of entries and total count.
        """
        base = db.query(Entry)
        ef = cls(db, base)._filter_deleted(False)

        if user_id:
            ef = ef._filter_by_user(user_id)
        elif public_only:
            ef = ef._filter_public_only()

        if tag:
            ef = ef._filter_by_tag(tag)
        if query:
            ef = ef._full_text_search_like(query)

        entries = ef._paginate(page, per_page)._all()
        total = ef._count()
        return entries, total

    def _filter_by_user(self, user_id):
        """Restrict entries to a specific user, excluding public copies."""
        self.query = self.query.filter(Entry.user_id == user_id, Entry.is_public_copy == False)
        return self

    def _filter_public_only(self):
        """Restrict query to admin-approved public entries only."""
        self.query = self.query.filter(Entry.is_public_copy == True)
        return self

    def _filter_by_tag(self, tag):
        """Filter entries by a specific tag name."""
        self.query = self.query.filter(Entry.tags.any(Tag.name == tag))
        return self

    def _full_text_search_like(self, query):
        """Apply LIKE-based full-text search on title, notes, or URL."""
        pattern = f"%{query}%"
        self.query = self.query.filter(
            or_(
                Entry.title.ilike(pattern),
                Entry.notes.ilike(pattern),
                Entry.url.ilike(pattern),
            )
        )
        return self

    def _paginate(self, page: int, per_page: int):
        """Apply pagination to the query."""
        self.query = self.query.order_by(Entry.id.desc())
        self.query = self.query.offset((page - 1) * per_page).limit(per_page)
        return self

    def _all(self):
        """Execute the query and return all matching entries."""
        return self.query.all()

    def _count(self):
        """Return the total count of entries matching current filters."""
        return self.query.count()

    def _filter_deleted(self, is_deleted: bool = False):
        """Include or exclude deleted entries based on boolean flag."""
        self.query = self.query.filter(Entry.is_deleted == is_deleted)
        return self