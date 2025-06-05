from sqlalchemy.orm import Session
from sqlalchemy import or_
from server.models.orm import Entry, Tag
from typing import Optional

def search_public_entries(db, query: Optional[str], tag: Optional[str], limit: int, offset: int):
    base_query = db.query(Entry).filter(Entry.is_public == True)

    if query:
        search = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Entry.title.ilike(search),
                Entry.notes.ilike(search),
                Entry.url.ilike(search),
            )
        )

    if tag:
        base_query = base_query.filter(Entry.tags.any(Tag.name == tag))

    total = base_query.count()
    entries = base_query.order_by(Entry.id.desc()).offset(offset).limit(limit).all()
    return entries, total