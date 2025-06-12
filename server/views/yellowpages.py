from fastapi import APIRouter, Request, Depends, Query, Cookie
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from fastapi.templating import Jinja2Templates

from server.security import get_db, get_optional_user
from server.services.shared import EntryQueryService, SharedEntryService
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
    sort: str = Query("alpha", pattern="^(recent|alpha)$"),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Render the public Yellow Pages directory.

    Supports optional full-text search (`q`), tag filtering (`tag`), pagination, and sorting.
    Uses access token (if present) to identify optional user for context rendering.

    Args:
        request (Request): Incoming HTTP request object for template rendering.
        q (Optional[str]): Full-text search query.
        tag (Optional[str]): Tag filter for narrowing results.
        page (int): Page number for pagination (1-based).
        limit (int): Number of entries per page.
        sort (str): Sort order, either "recent" or "alpha".
        access_token (Optional[str]): JWT token for optional user context.
        db (Session): Database session dependency.

    Returns:
        HTMLResponse: Rendered Yellow Pages listing with entries and filters applied.
    """
    user = get_optional_user(access_token, db)
    offset_value = offset(page, limit)

    if q:
        entries, total = SharedEntryService.search_public_entries_fts(
            db, query=q, limit=limit, offset=offset_value, sort=sort
        )
    else:
        entries, total = EntryQueryService.get_entries(
            db=db,
            public_only=True,
            tag=tag,
            page=page,
            per_page=limit,
            sort=sort
        )


    return templates.TemplateResponse(
        request,
        "yellowpages.html",
        build_yellowpages_context(user, entries, page, limit, total, tag, q, sort)
    )