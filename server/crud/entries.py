from datetime import datetime, timezone
import json
from typing import Optional

from sqlalchemy.orm import Session

from server.models.orm import Entry
from server.models.schemas import EntryCreate, EntryOut


def create_entry(db: Session, entry_in: EntryCreate, user_id: int) -> EntryOut:
    entry = Entry(
        **entry_in.model_dump(exclude={"tags"}),
        tags=json.dumps(entry_in.tags),  # Serialize to JSON string
        user_id=user_id,
        date_added=datetime.now(timezone.utc)
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _to_entry_out(entry)


def get_entry_by_id(db: Session, entry_id: int) -> Optional[EntryOut]:
    entry = db.query(Entry).filter(Entry.id == entry_id, Entry.deleted == False).first()
    return _to_entry_out(entry) if entry else None


def get_all_entries(db: Session, limit: int = 10, offset: int = 0) -> list[EntryOut]:
    entries = db.query(Entry).filter(Entry.deleted == False).offset(offset).limit(limit).all()
    return [_to_entry_out(e) for e in entries]


def get_entries_for_user(db: Session, user_id: int, limit: int = 10, offset: int = 0) -> list[EntryOut]:
    entries = db.query(Entry).filter(
        Entry.user_id == user_id,
        Entry.deleted == False
    ).offset(offset).limit(limit).all()
    return [_to_entry_out(e) for e in entries]


def update_entry(db: Session, entry_id: int, update: EntryCreate) -> Optional[EntryOut]:
    entry = db.query(Entry).filter(Entry.id == entry_id, Entry.deleted == False).first()
    if not entry:
        return None
    for key, value in update.model_dump().items():
        if key == "tags":
            setattr(entry, key, json.dumps(value))  # Serialize
        else:
            setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return _to_entry_out(entry)


def delete_entry(db: Session, entry_id: int) -> bool:
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def get_entry_count(db: Session) -> int:
    return db.query(Entry).filter(Entry.deleted == False).count()


def get_public_entries(db: Session, limit: int, offset: int) -> list[EntryOut]:
    entries = db.query(Entry).filter(
        Entry.public == True,
        Entry.deleted == False
    ).offset(offset).limit(limit).all()
    return [_to_entry_out(e) for e in entries]


def get_public_entry_count(db: Session) -> int:
    return db.query(Entry).filter(Entry.public == True, Entry.deleted == False).count()


def _to_entry_out(entry: Entry) -> EntryOut:
    return EntryOut.model_validate({
        **entry.__dict__,
        "tags": json.loads(entry.tags or "[]")  # Parse the JSON string
    })
