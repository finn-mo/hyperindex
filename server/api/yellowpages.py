from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.models.schemas import EntryOut
from server.security.auth import get_db
from server.crud.entries import get_public_entries

router = APIRouter(tags=["yellowpages"])

@router.get("/", response_model=list[EntryOut])
def get_yellowpages(
    db: Session = Depends(get_db)
):
    return get_public_entries(db, limit=1000, offset=0)