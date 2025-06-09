from fastapi import APIRouter, Request, Depends, Query, Cookie
from jose import JWTError, jwt
from server.security import SECRET_KEY, ALGORITHM
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from server.models.entities import User
from server.security import get_db
from server.services.entries import EntryService
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="server/templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def yellowpages(
    request: Request,
    q: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = 10,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    user = None
    if access_token:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username:
                user = db.query(User).filter_by(username=username).first()
        except JWTError:
            pass

    offset = (page - 1) * limit
    entries, total = EntryService.search_public_entries(db, query=q, tag=tag, limit=limit, offset=offset)
    total_pages = (total // limit) + (1 if total % limit > 0 else 0)

    return templates.TemplateResponse("yellowpages.html", {
        "request": request,
        "user": user,
        "entries": entries,
        "query": q,
        "tag": tag,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": (page * limit) < total,
    })
