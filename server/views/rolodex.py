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

    all_tags = (
        db.query(Tag.name)
        .join(Entry.tags)
        .filter(Entry.user_id == user.id, Entry.is_deleted == False)
        .distinct()
        .all()
    )

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
            all_tags=[t[0] for t in all_tags],
        )
    )


@router.get("/entries/new", response_class=HTMLResponse)
def new_entry_form(request: Request, user: User = Depends(get_current_user)):
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
    entry = (
        db.get(Entry, entry_id)
        if user.is_admin else SharedEntryService.get_entry_by_id(db, entry_id, user.id)
    )
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
    UserEntryService.submit_for_review(db, entry_id, user.id)
    return RedirectResponse("/rolodex", status_code=302)