from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import or_, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import NoResultFound

from server.models.entities import Entry, Tag
from server.models.schemas import EntryCreate


class TagService:
    @staticmethod
    def resolve_tags(db: Session, tags: List[str]) -> List[Tag]:
        """
        Ensure all tag names exist as Tag objects in the database.

        Args:
            db (Session): SQLAlchemy session.
            tags (List[str]): List of tag names to resolve or create.

        Returns:
            List[Tag]: Corresponding Tag objects, newly created if missing.
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


class EntryService:
    @staticmethod
    def get_entry_by_id(db: Session, entry_id: int, user_id: Optional[int] = None) -> Entry:
        """
        Retrieve a single entry by its ID, optionally scoped to a specific user.

        Args:
            db (Session): SQLAlchemy session.
            entry_id (int): ID of the entry to fetch.
            user_id (Optional[int]): If provided, restrict result to entries owned by the user.

        Returns:
            Entry: The matched entry object.

        Raises:
            NoResultFound: If the entry does not exist or is not accessible by the user.
        """
        query = db.query(Entry).options(joinedload(Entry.tags)).filter(Entry.id == entry_id)
        if user_id is not None:
            query = query.filter(Entry.user_id == user_id)
        entry = query.first()
        if not entry:
            raise NoResultFound("Entry not found or access denied")
        return entry
    

    @staticmethod
    def get_pending_submissions(db: Session, limit: int = 10, offset: int = 0):
        """
        Return entries submitted for public listing but not yet approved,
        excluding deleted ones.
        """
        q = (
            db.query(Entry)
            .filter(
                Entry.submitted_to_public == True,
                Entry.is_public_copy == False,
                Entry.is_deleted == False
            )
            .order_by(Entry.id.desc())
        )
        total = q.count()
        entries = q.offset(offset).limit(limit).all()
        return entries, total
    
    @staticmethod
    def get_public_entries(db: Session, limit: int = 10, offset: int = 0):
        """
        Return admin-approved public entries (forked copies), excluding deleted ones.
        """
        q = (
            db.query(Entry)
            .filter(
                Entry.is_public_copy == True,
                Entry.is_deleted == False
            )
            .order_by(Entry.id.desc())
        )
        total = q.count()
        entries = q.offset(offset).limit(limit).all()
        return entries, total


    @staticmethod
    def get_deleted_entries(db: Session, limit: int, offset: int) -> tuple[list[Entry], int]:
        """
        Return soft-deleted admin-approved public entries (forked copies).
        """
        query = db.query(Entry).filter(
            Entry.is_public_copy == True,
            Entry.is_deleted == True
        ).order_by(Entry.deleted_at.desc())
        total = query.count()
        entries = query.offset(offset).limit(limit).all()
        return entries, total


    @staticmethod
    def create_entry(db: Session, entry_in: EntryCreate, user_id: int) -> Entry:
        """
        Create a new entry for a user, resolving its associated tags.

        Args:
            db (Session): SQLAlchemy session.
            entry_in (EntryCreate): Input data for the new entry.
            user_id (int): ID of the user creating the entry.

        Returns:
            Entry: The newly created entry.
        """
        tags = TagService.resolve_tags(db, entry_in.tags or [])
        entry = Entry(
            url=entry_in.url,
            title=entry_in.title,
            notes=entry_in.notes,
            tags=tags,
            user_id=user_id,
            date_added=datetime.now(timezone.utc)
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def update_entry(db: Session, entry_id: int, user_id: int, data: EntryCreate) -> Entry:
        """
        Update an existing entry owned by the user with new data and tags.

        Args:
            db (Session): SQLAlchemy session.
            entry_id (int): ID of the entry to update.
            user_id (int): ID of the user who must own the entry.
            data (EntryCreate): New entry data.

        Returns:
            Entry: The updated entry.

        Raises:
            NoResultFound: If the entry is not found or not owned by the user.
        """
        entry = EntryService.get_entry_by_id(db, entry_id, user_id)
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
        Soft-delete a user-owned entry by marking it as deleted.

        Args:
            db (Session): SQLAlchemy session.
            entry_id (int): ID of the entry.
            user_id (int): ID of the user who must own the entry.

        Returns:
            None
        """
        entry = EntryService.get_entry_by_id(db, entry_id, user_id)
        entry.is_deleted = True
        db.commit()

    @staticmethod
    def restore_entry(db: Session, entry_id: int, user_id: int) -> None:
        """
        Restore a previously soft-deleted entry owned by the user.

        Args:
            db (Session): SQLAlchemy session.
            entry_id (int): ID of the entry.
            user_id (int): ID of the user who must own the entry.

        Returns:
            None
        """
        entry = EntryService.get_entry_by_id(db, entry_id, user_id)
        entry.is_deleted = False
        db.commit()
    
    @staticmethod
    def filter_entries(
        db: Session,
        user_id: Optional[int] = None,
        public_only: bool = False,
        tag: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Entry], int]:
        """
        Unified entry search/filter method. Supports user scope, public scope, tag filtering, and text search.

        Args:
            db (Session): SQLAlchemy session.
            user_id (Optional[int]): If provided, limits to entries owned by the user.
            public_only (bool): If True, limits to admin-managed public entries.
            tag (Optional[str]): If provided, filters entries by tag name.
            query (Optional[str]): Case-insensitive search across title, notes, and URL.
            limit (int): Max number of entries to return.
            offset (int): Number of entries to skip.

        Returns:
            Tuple[List[Entry], int]: List of entries and total result count.
        """
        q = db.query(Entry).options(joinedload(Entry.tags)).filter(Entry.is_deleted == False)

        if user_id is not None:
            q = q.filter(Entry.user_id == user_id, Entry.is_public_copy == False)

        if public_only:
            q = q.filter(Entry.is_public_copy == True)

        if tag:
            q = q.filter(Entry.tags.any(Tag.name == tag))

        if query:
            pattern = f"%{query}%"
            q = q.filter(
                or_(
                    Entry.title.ilike(pattern),
                    Entry.notes.ilike(pattern),
                    Entry.url.ilike(pattern),
                )
            )

        total = q.count()
        entries = q.order_by(Entry.id.desc()).offset(offset).limit(limit).all()
        return entries, total
    
    @staticmethod
    def search_user_entries_fts(
        db: Session,
        user_id: int,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Entry], int]:
        # Step 1: Get matching IDs from subquery
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

        # Step 2: Load full entries
        entries = (
            db.query(Entry)
            .filter(Entry.id.in_(ids))
            .options(joinedload(Entry.tags))
            .order_by(Entry.id.desc())
            .all()
        )

        # Step 3: Count total
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
    def search_public_entries_fts(
        db: Session,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Entry], int]:
        """
        Perform full-text search across public (admin-managed) entries.

        Args:
            db (Session): SQLAlchemy session.
            query (str): Search query string for FTS match.
            limit (int): Maximum number of entries to return.
            offset (int): Number of entries to skip (for pagination).

        Returns:
            Tuple[List[Entry], int]: A tuple containing:
                - List of matching Entry objects (admin-approved public copies).
                - Total number of matches for pagination purposes.
        """
        sql = text("""
            SELECT e.id
            FROM (
                SELECT rowid
                FROM entry_fts
                WHERE entry_fts MATCH :query
            ) fts
            JOIN entries e ON e.id = fts.rowid
            WHERE e.is_public_copy = 1
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
            WHERE e.is_public_copy = 1
        """)
        total = db.execute(count_sql, {"query": query}).scalar()

        return entries, total