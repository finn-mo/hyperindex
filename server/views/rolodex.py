# server/views/rolodex.py

from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from server.security import get_current_user, get_db
from server.models.entities import User, Entry, Tag
from server.models.schemas import EntryCreate
from server.services.entries import (
    create_entry, get_entry_by_id, soft_delete_entry
)
from server.services.tags import resolve_tags
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="server/templates")
router = APIRouter()


@router.get("/rolodex", response_class=HTMLResponse)
def rolodex(
    request: Request,
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    query = db.query(Entry).filter(
        Entry.user_id == user.id,
        Entry.is_deleted == False,
        Entry.is_public_copy == False
    )
    if tag:
        query = query.filter(Entry.tags.any(name=tag))

    total = query.count()
    entries = query.order_by(Entry.id.desc()).offset(offset).limit(limit).all()
    all_tags = (
        db.query(Entry)
        .filter(Entry.user_id == user.id, Entry.is_deleted == False)
        .join(Entry.tags)
        .with_entities(Tag.name)
        .distinct()
        .all()
    )

    total_pages = (total // limit) + (1 if total % limit > 0 else 0)
    return templates.TemplateResponse("rolodex.html", {
        "request": request,
        "user": user,
        "entries": entries,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": (page * limit) < total,
        "selected_tag": tag,
        "all_tags": [t[0] for t in all_tags],
    })


@router.get("/entries/new", response_class=HTMLResponse)
def new_entry_form(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("new_entry.html", {"request": request, "user": user})


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
    return create_entry(db, entry_in, user.id), RedirectResponse("/rolodex", status_code=302)


@router.get("/entries/{entry_id}/edit", response_class=HTMLResponse)
def edit_entry_form(
    entry_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = (
        db.query(Entry).get(entry_id)
        if user.is_admin else get_entry_by_id(db, entry_id, user.id)
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return templates.TemplateResponse("edit_entry.html", {"request": request, "entry": entry})


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
    entry = db.query(Entry).get(entry_id)
    if not entry or (not user.is_admin and entry.user_id != user.id):
        raise HTTPException(status_code=404, detail="Entry not found")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    entry.title = title
    entry.url = url
    entry.notes = notes
    entry.tags = resolve_tags(db, tag_list)
    db.commit()

    return RedirectResponse(
        "/admin" if entry.is_public_copy else "/rolodex",
        status_code=302
    )


@router.post("/entries/{entry_id}/delete")
def delete_entry(entry_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    soft_delete_entry(db, entry_id, user.id)
    return RedirectResponse("/rolodex", status_code=302)


@router.post("/entries/{entry_id}/submit")
def submit_entry_for_review(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = get_entry_by_id(db, entry_id, user.id)
    if not entry or entry.is_deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.is_public_copy:
        raise HTTPException(status_code=400, detail="Cannot submit admin-managed entries")

    if not entry.submitted_to_public:
        entry.submitted_to_public = True
        db.commit()

    return RedirectResponse("/rolodex", status_code=302)
