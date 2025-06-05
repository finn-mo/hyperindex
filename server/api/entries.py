# server/api/entries.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.models.schemas import EntryCreate, EntryOut, EntryUpdate
from server.db.connection import SessionLocal
from server.db.entries import (
    get_entries_by_user, get_entry_by_id, create_entry,
    update_entry, soft_delete_entry, restore_entry
)
from server.security.auth import get_current_user
from server.models.orm import User, Entry

router = APIRouter(tags=["entries"]) 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/entries", response_model=list[EntryOut])
def list_entries(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_entries_by_user(db, user.id)

@router.post("/entries", response_model=EntryOut)
def create(db_entry: EntryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entry = create_entry(db, Entry(**db_entry.dict()), user.id)
    return entry

@router.get("/entries/{entry_id}", response_model=EntryOut)
def read(entry_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_entry_by_id(db, entry_id, user.id)

@router.put("/entries/{entry_id}", response_model=EntryOut)
def update(entry_id: int, update_data: EntryUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return update_entry(db, entry_id, user.id, update_data.dict())

@router.delete("/entries/{entry_id}")
def delete(entry_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    soft_delete_entry(db, entry_id, user.id)
    return {"status": "deleted"}

@router.patch("/entries/{entry_id}/restore")
def restore(entry_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    restore_entry(db, entry_id, user.id)
    return {"status": "restored"}

@router.patch("/entries/{entry_id}/publish")
def publish_entry(entry_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entry = get_entry_by_id(db, entry_id, user.id)
    entry.is_public = 1
    db.commit()
    return {"status": "published"}
