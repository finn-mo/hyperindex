from fastapi import APIRouter, Request, Depends, Query, Cookie
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from server.models.entities import Entry
from server.security import get_db, get_optional_user
from server.services.entries import EntryService
from server.services.filters import EntryFilter
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
    user = get_optional_user(access_token, db)
    offset = (page - 1) * limit

    if q:
        entries, total = EntryService.search_public_entries_fts(
            db, query=q, limit=limit, offset=offset
        )
    else:
        entries, total = EntryFilter.get_entries(
            db=db,
            public_only=True,
            tag=tag,
            page=page,
            per_page=limit
        )

    total_pages = (total // limit) + (1 if total % limit > 0 else 0)

    return templates.TemplateResponse(request, "yellowpages.html", {
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