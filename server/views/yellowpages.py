from fastapi import APIRouter, Request, Depends, Query, Cookie
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from fastapi.templating import Jinja2Templates

from server.security import get_db, get_optional_user
from server.services.shared import SharedEntryService, EntryFilter
from server.utils.context import build_yellowpages_context
from server.utils.pagination import offset

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
    offset_value = offset(page, limit)

    if q:
        entries, total = SharedEntryService.search_public_entries_fts(
            db, query=q, limit=limit, offset=offset_value
        )
    else:
        entries, total = EntryFilter.get_entries(
            db=db,
            public_only=True,
            tag=tag,
            page=page,
            per_page=limit
        )

    return templates.TemplateResponse(
        request,
        "yellowpages.html",
        build_yellowpages_context(user, entries, page, limit, total, tag, q)
    )