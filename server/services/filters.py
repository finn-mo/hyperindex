from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from server.models.entities import Entry, Tag

class EntryFilter:
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
