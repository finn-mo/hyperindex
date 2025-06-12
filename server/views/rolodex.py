from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from server.security import get_current_user, get_db
from server.models.entities import User, Entry, Tag
from server.models.schemas import EntryCreate
from server.services.user import UserEntryService
from server.services.shared import EntryQueryService, SharedEntryService
from server.utils.context import build_rolodex_context
from server.utils.pagination import offset


templates = Jinja2Templates(directory="server/templates")
router = APIRouter()


@router.get("/rolodex", response_class=HTMLResponse)
def rolodex(
    request: Request,
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Render the user's private Rolodex view.

    Supports optional full-text search (`q`) and tag filtering (`tag`) with pagination.
    Displays user-specific saved entries and personal tags.

    Args:
        request (Request): HTTP request object for rendering.
        tag (Optional[str]): Filter entries by tag.
        q (Optional[str]): Full-text query string.
        page (int): Current pagination page (1-indexed).
        limit (int): Number of entries per page.
        user (User): Authenticated user via dependency injection.
        db (Session): SQLAlchemy database session.

    Returns:
        HTMLResponse: Rendered template with user entries and filters applied.
    """
    offset_value = offset(page, limit)

    if q:
        entries, total = UserEntryService.search_entries(
            db, user_id=user.id, query=q, limit=limit, offset=offset_value
        )
    else:
        entries, total = EntryQueryService.get_entries(
            db=db,
            user_id=user.id,
            tag=tag,
            page=page,
            per_page=limit
        )

    all_tags = UserEntryService.get_user_tags(db, user.id)

    return templates.TemplateResponse(
        "rolodex.html",
        build_rolodex_context(
            request=request,
            user=user,
            entries=entries,
            page=page,
            limit=limit,
            total=total,
            tag=tag,
            query=q,
            all_tags=[t[0] for t in all_tags]
        )
    )


@router.get("/entries/new", response_class=HTMLResponse)
def new_entry_form(request: Request, user: User = Depends(get_current_user)):
    """
    Render the new entry creation form for authenticated users.

    Args:
        request (Request): HTTP request for rendering context.
        user (User): Authenticated user from session.

    Returns:
        HTMLResponse: Rendered template for entry creation.
    """
    return templates.TemplateResponse(request, "new_entry.html", {"user": user})


@router.post("/entries/new")
def create_entry_from_form(
    url: str = Form(...),
    title: str = Form(...),
    tags: str = Form(""),
    notes: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process form submission to create a new personal entry.

    Parses and sanitizes input fields, creates entry with user ownership,
    and redirects to the Rolodex view.

    Args:
        url (str): URL of the resource.
        title (str): Title of the entry.
        tags (str): Comma-separated tags string.
        notes (str): Optional notes.
        user (User): Authenticated user.
        db (Session): Database session.

    Returns:
        RedirectResponse: Redirect to Rolodex after creation.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    entry_in = EntryCreate(url=url, title=title, notes=notes, tags=tag_list)
    UserEntryService.create_entry(db, entry_in, user.id)
    return RedirectResponse("/rolodex", status_code=303)


@router.get("/entries/{entry_id}/edit", response_class=HTMLResponse)
def edit_entry_form(
    entry_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Render the entry editing form for a specific entry.

    Verifies user ownership before rendering. Raises 404 if not found.

    Args:
        entry_id (int): ID of the entry to edit.
        request (Request): HTTP request object.
        user (User): Authenticated user.
        db (Session): Database session.

    Returns:
        HTMLResponse: Rendered edit form template.
    """
    entry = SharedEntryService.get_entry_by_id(db, entry_id, user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return templates.TemplateResponse(request, "edit_entry.html", {"entry": entry})


@router.post("/entries/{entry_id}/edit")
def edit_entry(
    entry_id: int,
    title: str = Form(...),
    url: str = Form(...),
    notes: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process updates to an existing personal entry.

    Validates user access and applies updates via service layer.

    Args:
        entry_id (int): ID of the entry to update.
        title (str): Updated title.
        url (str): Updated URL.
        notes (str): Optional notes.
        tags (str): Updated comma-separated tags.
        user (User): Authenticated user.
        db (Session): Database session.

    Returns:
        RedirectResponse: Redirect to Rolodex or Admin view.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    entry_data = EntryCreate(title=title, url=url, notes=notes, tags=tag_list)
    
    UserEntryService.update_entry(db, entry_id, user.id, entry_data)

    return RedirectResponse(
        "/admin" if user.is_admin else "/rolodex",
        status_code=302
    )


@router.post("/entries/{entry_id}/delete")
def delete_entry(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft-delete a personal entry owned by the user.

    Marks the entry as deleted. Redirects based on role.

    Args:
        entry_id (int): ID of the entry to delete.
        user (User): Authenticated user.
        db (Session): Database session.

    Returns:
        RedirectResponse: Redirect to Rolodex or Admin view.
    """
    UserEntryService.soft_delete_entry(db, entry_id, user.id)

    return RedirectResponse(
        "/admin" if user.is_admin else "/rolodex",
        status_code=302
    )


@router.post("/entries/{entry_id}/submit")
def submit_entry_for_review(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a personal entry to the public directory for review.

    Marks entry for admin review queue. No changes to ownership or data.

    Args:
        entry_id (int): ID of the entry to submit.
        user (User): Authenticated user.
        db (Session): Database session.

    Returns:
        RedirectResponse: Redirect to Rolodex after submission.
    """
    UserEntryService.submit_for_review(db, entry_id, user.id)
    return RedirectResponse("/rolodex", status_code=302)