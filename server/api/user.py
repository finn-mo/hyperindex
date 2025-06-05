from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.models.schemas import EntryOut
from server.security.auth import get_current_user, get_db
from server.models.orm import User
from server.crud.entries import get_entries_for_user, get_public_entries

router = APIRouter(tags=["user"])

@router.get("/user/rolodex", response_model=list[EntryOut])
def get_user_rolodex(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return get_entries_for_user(db, user.id, limit=1000, offset=0)