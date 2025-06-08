from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import NoResultFound

from server.models.entities import Entry, Tag
from server.models.schemas import EntryCreate


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


def get_entry_by_id(db: Session, entry_id: int, user_id: Optional[int] = None) -> Entry:
    query = db.query(Entry).options(joinedload(Entry.tags)).filter(Entry.id == entry_id)
    if user_id is not None:
        query = query.filter(Entry.user_id == user_id)
    entry = query.first()
    if not entry:
        raise NoResultFound("Entry not found or access denied")
    return entry


def create_entry(db: Session, entry_in: EntryCreate, user_id: int) -> Entry:
    tags = resolve_tags(db, entry_in.tags or [])
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


def update_entry(db: Session, entry_id: int, user_id: int, data: EntryCreate) -> Entry:
    entry = get_entry_by_id(db, entry_id, user_id)
    entry.url = data.url
    entry.title = data.title
    entry.notes = data.notes
    entry.tags = resolve_tags(db, data.tags or [])
    db.commit()
    db.refresh(entry)
    return entry


def soft_delete_entry(db: Session, entry_id: int, user_id: int) -> None:
    entry = get_entry_by_id(db, entry_id, user_id)
    entry.is_deleted = True
    db.commit()


def restore_entry(db: Session, entry_id: int, user_id: int) -> None:
    entry = get_entry_by_id(db, entry_id, user_id)
    entry.is_deleted = False
    db.commit()


def get_entries_by_user(db: Session, user_id: int, tag: Optional[str] = None, limit: int = 10, offset: int = 0) -> Tuple[List[Entry], int]:
    query = (
        db.query(Entry)
        .options(joinedload(Entry.tags))
        .filter(Entry.user_id == user_id, Entry.is_deleted == False, Entry.is_public_copy == False)
    )
    if tag:
        query = query.filter(Entry.tags.any(Tag.name == tag))
    total = query.count()
    entries = query.order_by(Entry.id.desc()).offset(offset).limit(limit).all()
    return entries, total


def search_public_entries(db: Session, query: Optional[str], tag: Optional[str], limit: int, offset: int) -> Tuple[List[Entry], int]:
    base_query = db.query(Entry).filter(Entry.is_public_copy == True)

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