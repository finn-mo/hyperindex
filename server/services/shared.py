from typing import List, Optional, Tuple
from sqlalchemy import or_, text
from sqlalchemy.orm import Session, joinedload

from sqlalchemy.exc import NoResultFound

from server.models.entities import Entry, Tag


class TagService:
    """Utility for resolving tag strings into Tag model instances."""
    @staticmethod
    def resolve_tags(db: Session, tags: List[str]) -> List[Tag]:
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
    """Shared entry logic used across multiple interfaces (e.g., rolodex, yellowpages)."""
    @staticmethod
    def get_entry_by_id(db: Session, entry_id: int, user_id: int | None = None) -> Entry:
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
    
class EntryFilter:
    """Flexible entry filter with tag, text, and user/public options."""
    def __init__(self, db_session, base_query):
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
        base = db.query(Entry)
        ef = cls(db, base).filter_deleted(False)

        if user_id:
            ef = ef.filter_by_user(user_id)
        elif public_only:
            ef = ef.filter_public_only()

        if tag:
            ef = ef.filter_by_tag(tag)
        if query:
            ef = ef.full_text_search_like(query)

        entries = ef.paginate(page, per_page).all()
        total = ef.count()
        return entries, total

    def filter_by_user(self, user_id):
        self.query = self.query.filter(Entry.user_id == user_id, Entry.is_public_copy == False)
        return self

    def filter_public_only(self):
        self.query = self.query.filter(Entry.is_public_copy == True)
        return self

    def filter_by_tag(self, tag):
        self.query = self.query.filter(Entry.tags.any(Tag.name == tag))
        return self

    def full_text_search_like(self, query):  # For LIKE fallback
        pattern = f"%{query}%"
        self.query = self.query.filter(
            or_(
                Entry.title.ilike(pattern),
                Entry.notes.ilike(pattern),
                Entry.url.ilike(pattern),
            )
        )
        return self

    def paginate(self, page: int, per_page: int):
        self.query = self.query.order_by(Entry.id.desc())
        self.query = self.query.offset((page - 1) * per_page).limit(per_page)
        return self

    def all(self):
        return self.query.all()

    def count(self):
        return self.query.count()
    
    def filter_deleted(self, is_deleted: bool = False):
        self.query = self.query.filter(Entry.is_deleted == is_deleted)
        return self