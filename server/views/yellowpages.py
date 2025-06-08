from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from server.security import get_db
from server.services.entries import search_public_entries
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
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    entries, total = search_public_entries(db, query=q, tag=tag, limit=limit, offset=offset)
    total_pages = (total // limit) + (1 if total % limit > 0 else 0)

    return templates.TemplateResponse("yellowpages.html", {
        "request": request,
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