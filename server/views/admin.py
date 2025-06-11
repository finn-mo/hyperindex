from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from server.models.entities import Entry, User
from server.security import get_current_user, get_db

templates = Jinja2Templates(directory="server/templates")
router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.is_admin:
        return RedirectResponse("/rolodex", status_code=302)

    pending_entries = db.query(Entry).filter(
        Entry.submitted_to_public == True,
        Entry.is_public_copy == False,
        Entry.is_deleted == False
    ).order_by(Entry.id.desc()).all()

    public_entries = db.query(Entry).filter(
        Entry.is_public_copy == True,
        Entry.is_deleted == False
    ).order_by(Entry.id.desc()).all()

    return templates.TemplateResponse(request, "admin_panel.html", {
        "request": request,
        "user": user,
        "pending_entries": pending_entries,
        "public_entries": public_entries,
    })


@router.post("/admin/approve/{entry_id}")
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
    if entry.is_public_copy:
        raise HTTPException(status_code=400, detail="Entry already approved")

    cloned_tags = entry.tags[:]
    admin_entry = Entry(
        title=entry.title,
        url=entry.url,
        notes=entry.notes,
        user_id=user.id,
        is_public_copy=True,
        original_id=entry.id,
        tags=cloned_tags,
    )
    db.add(admin_entry)
    entry.submitted_to_public = False
    db.commit()

    return RedirectResponse("/admin", status_code=302)


@router.post("/admin/reject/{entry_id}")
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
    if entry.is_public_copy:
        raise HTTPException(status_code=400, detail="Cannot reject an already approved entry")

    entry.submitted_to_public = False
    db.commit()
    return RedirectResponse("/admin", status_code=302)