from typing import Optional

from fastapi import FastAPI, Request, Response, Depends, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from server.api.auth import router as auth_router
from server.api.user import router as user_router
from server.api.entries import router as entries_router
from server.api.yellowpages import router as yellowpages_router

from server.db.connection import init_db, SessionLocal
from server.db.entries import get_entries_by_user, create_entry, get_entry_by_id, update_entry, soft_delete_entry
from server.db.public import search_public_entries
from server.models.orm import User, Entry, Tag
from server.security.auth import get_current_user, get_db


app = FastAPI()
init_db()

# Mount static files (must be before defining routes that use it)
app.mount("/static", StaticFiles(directory="server/static"), name="static")

# Routers
app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/user")
app.include_router(entries_router, prefix="/entries")
app.include_router(yellowpages_router, prefix="/yellowpages")

templates = Jinja2Templates(directory="server/templates")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = 10,
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        offset = (page - 1) * limit

        base_query = (
            db.query(Entry)
            .options(joinedload(Entry.tags))
            .filter(Entry.user_id == user.id, Entry.is_deleted == 0)
        )

        if tag:
            base_query = base_query.filter(Entry.tags.any(Tag.name == tag))

        total = base_query.count()

        entries = (
            base_query
            .order_by(Entry.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Get all tags used by this user
        all_tags = (
            db.query(Tag)
            .join(Tag.entries)
            .filter(Entry.user_id == user.id)
            .distinct()
            .all()
        )
    finally:
        db.close()

    total_pages = (total // limit) + (1 if total % limit > 0 else 0)

    return templates.TemplateResponse("dashboard.html", {
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
        "all_tags": all_tags,
    })


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/entries/new", response_class=HTMLResponse)
def new_entry_form(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("new_entry.html", {
        "request": request,
        "user": user
    })


@app.post("/entries/new")
def create_entry_from_form(
    request: Request,
    url: str = Form(...),
    title: str = Form(...),
    tags: str = Form(""),
    notes: str = Form(""),
    user: User = Depends(get_current_user)
):
    db = SessionLocal()
    try:
        tag_objects = []
        for tag_name in [t.strip() for t in tags.split(",") if t.strip()]:
            tag = db.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()  # ensure tag.id is available
            tag_objects.append(tag)

        entry = Entry(
            url=url,
            title=title,
            notes=notes,
            tags=tag_objects,
            user_id=user.id,
        )
        create_entry(db, entry, user.id)
    finally:
        db.close()

    return RedirectResponse("/dashboard", status_code=302)


@app.get("/", response_class=HTMLResponse)
def index(
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

    return templates.TemplateResponse("index.html", {
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


@app.get("/entries/{entry_id}/edit", response_class=HTMLResponse)
def edit_entry_form(
    entry_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.is_admin:
        entry = db.query(Entry).get(entry_id)
    else:
        entry = get_entry_by_id(db, entry_id, user.id)

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return templates.TemplateResponse("edit_entry.html", {"request": request, "entry": entry})


@app.post("/entries/{entry_id}/edit")
def edit_entry(
    entry_id: int,
    request: Request,
    title: str = Form(...),
    url: str = Form(...),
    notes: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.is_admin:
        entry = db.query(Entry).get(entry_id)
    else:
        entry = get_entry_by_id(db, entry_id, user.id)

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    tag_objects = []
    for tag_name in [t.strip() for t in tags.split(",") if t.strip()]:
        tag = db.query(Tag).filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        tag_objects.append(tag)

    entry.title = title
    entry.url = url
    entry.notes = notes
    entry.tags = tag_objects

    db.commit()

    # Redirect admin back to the admin panel, users to dashboard
    redirect_url = "/admin" if user.is_admin else "/dashboard"
    return RedirectResponse(redirect_url, status_code=302)


@app.post("/entries/{entry_id}/delete")
def delete_entry(entry_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    soft_delete_entry(db, entry_id, user.id)
    return RedirectResponse("/dashboard", status_code=302)


@app.post("/entries/{entry_id}/submit")
def submit_entry_for_review(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = get_entry_by_id(db, entry_id, user.id)
    if not entry or entry.is_deleted:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry.is_public:
        raise HTTPException(status_code=400, detail="Entry already public")

    if not entry.submitted_to_public:
        entry.submitted_to_public = True
        db.commit()

    return RedirectResponse("/dashboard", status_code=302)


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        return RedirectResponse("/dashboard", status_code=302)

    pending_entries = db.query(Entry).filter(
        Entry.submitted_to_public == True,
        Entry.is_public == False
    ).order_by(Entry.id.desc()).all()

    public_entries = db.query(Entry).filter(
        Entry.is_public == True
    ).order_by(Entry.id.desc()).all()

    return templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "user": user,
        "pending_entries": pending_entries,
        "public_entries": public_entries,
    })


@app.post("/admin/approve/{entry_id}")
def approve_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    entry = db.query(Entry).get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry.is_public:
        raise HTTPException(status_code=400, detail="Entry already approved")

    entry.is_public = True
    db.commit()
    return RedirectResponse("/admin", status_code=302)


@app.post("/admin/reject/{entry_id}")
def reject_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    entry = db.query(Entry).get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if entry.is_public:
        raise HTTPException(status_code=400, detail="Cannot reject an already approved entry")

    entry.submitted_to_public = False
    db.commit()
    return RedirectResponse("/admin", status_code=302)