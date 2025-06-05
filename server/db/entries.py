from sqlalchemy.orm import Session
from server.models.orm import Entry, Tag
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload


def get_entries_by_user(db: Session, user_id: int):
    return (
        db.query(Entry)
        .options(joinedload(Entry.tags))
        .filter(Entry.user_id == user_id)
        .filter(Entry.is_deleted == 0)
        .all()
    )


def get_entry_by_id(db: Session, entry_id: int, user_id: int) -> Entry:
    entry = db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user_id).first()
    if entry is None:
        raise NoResultFound("Entry not found or access denied")
    return entry

def create_entry(db: Session, entry: Entry, user_id: int) -> Entry:
    entry.user_id = user_id
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def soft_delete_entry(db: Session, entry_id: int, user_id: int) -> None:
    entry = get_entry_by_id(db, entry_id, user_id)
    entry.is_deleted = 1
    db.commit()

def restore_entry(db: Session, entry_id: int, user_id: int) -> None:
    entry = get_entry_by_id(db, entry_id, user_id)
    entry.is_deleted = 0
    db.commit()

def update_entry(db: Session, entry_id: int, user_id: int, data: dict) -> Entry:
    entry = get_entry_by_id(db, entry_id, user_id)
    for key, value in data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry
