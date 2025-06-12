from datetime import datetime, timezone
from typing import Tuple, List

from sqlalchemy.orm import Session
from fastapi import HTTPException

from server.models.entities import Entry, User
from server.models.schemas import EntryCreate
from server.services.shared import TagService


class AdminEntryService:
    @staticmethod
    def approve_entry(db: Session, entry_id: int, admin_user: User) -> None:
        entry = db.get(Entry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        if entry.is_public_copy:
            raise HTTPException(status_code=400, detail="Entry already approved")

        admin_entry = Entry(
            title=entry.title,
            url=entry.url,
            notes=entry.notes,
            user_id=admin_user.id,
            is_public_copy=True,
            original_id=entry.id,
            tags=entry.tags[:],  # clone tag references
        )
        db.add(admin_entry)
        entry.submitted_to_public = False
        db.commit()

    @staticmethod
    def reject_entry(db: Session, entry_id: int) -> None:
        entry = db.get(Entry, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        if entry.is_public_copy:
            raise HTTPException(status_code=400, detail="Cannot reject an already approved entry")

        entry.submitted_to_public = False
        db.commit()

    @staticmethod
    def update_entry(db: Session, entry_id: int, data: EntryCreate) -> Entry:
        entry = db.get(Entry, entry_id)
        if not entry or not entry.is_public_copy:
            raise HTTPException(status_code=404, detail="Admin-managed entry not found")

        entry.title = data.title
        entry.url = data.url
        entry.notes = data.notes
        entry.tags = TagService.resolve_tags(db, data.tags or [])
        db.commit()
        db.refresh(entry)
        return entry


    @staticmethod
    def delete_entry(db: Session, entry_id: int) -> None:
        entry = db.get(Entry, entry_id)
        if not entry or not entry.is_public_copy:
            raise HTTPException(status_code=404, detail="Entry not found or not an admin entry")

        entry.deleted_at = datetime.now(timezone.utc)
        entry.is_deleted = True
        db.commit()

    @staticmethod
    def purge_entry(db: Session, entry_id: int) -> None:
        entry = db.get(Entry, entry_id)
        if not entry or not entry.is_public_copy or not entry.is_deleted:
            raise HTTPException(status_code=404, detail="Cannot purge entry")

        db.delete(entry)
        db.commit()

    @staticmethod
    def get_pending_submissions(db: Session, limit: int = 10, offset: int = 0) -> Tuple[List[Entry], int]:
        query = (
            db.query(Entry)
            .filter(
                Entry.submitted_to_public == True,
                Entry.is_public_copy == False,
                Entry.is_deleted == False
            )
            .order_by(Entry.id.desc())
        )
        total = query.count()
        entries = query.offset(offset).limit(limit).all()
        return entries, total

    @staticmethod
    def get_public_entries(db: Session, limit: int = 10, offset: int = 0) -> Tuple[List[Entry], int]:
        query = (
            db.query(Entry)
            .filter(
                Entry.is_public_copy == True,
                Entry.is_deleted == False
            )
            .order_by(Entry.id.desc())
        )
        total = query.count()
        entries = query.offset(offset).limit(limit).all()
        return entries, total

    @staticmethod
    def get_deleted_entries(db: Session, limit: int = 10, offset: int = 0) -> Tuple[List[Entry], int]:
        query = (
            db.query(Entry)
            .filter(
                Entry.is_public_copy == True,
                Entry.is_deleted == True
            )
            .order_by(Entry.deleted_at.desc())
        )
        total = query.count()
        entries = query.offset(offset).limit(limit).all()
        return entries, total

    @staticmethod
    def get_entry_for_edit(db: Session, entry_id: int) -> Entry:
        entry = db.get(Entry, entry_id)
        if not entry or not entry.is_public_copy:
            raise HTTPException(status_code=404, detail="Entry not found")
        return entry