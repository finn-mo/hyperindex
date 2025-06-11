from datetime import datetime, timezone

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from server.models.entities import Entry, User
from server.services.entries import EntryService
from server.security import get_current_user, get_db, require_admin

templates = Jinja2Templates(directory="server/templates")
router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
def admin_panel(
    request: Request,
    page_pending: int = Query(1, ge=1),
    page_public: int = Query(1, ge=1),
    page_deleted: int = Query(1, ge=1),
    limit: int = 10,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    offset_pending = (page_pending - 1) * limit
    offset_public = (page_public - 1) * limit
    offset_deleted = (page_deleted - 1) * limit

    pending_entries, total_pending = EntryService.get_pending_submissions(db, limit=limit, offset=offset_pending)
    public_entries, total_public = EntryService.get_public_entries(db, limit=limit, offset=offset_public)
    deleted_entries, total_deleted = EntryService.get_deleted_entries(db, limit=limit, offset=offset_deleted)

    return templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "user": user,
        "pending_entries": pending_entries,
        "public_entries": public_entries,
        "deleted_entries": deleted_entries,
        "page_pending": page_pending,
        "page_public": page_public,
        "page_deleted": page_deleted,
        "total_pages_pending": (total_pending + limit - 1) // limit,
        "total_pages_public": (total_public + limit - 1) // limit,
        "total_pages_deleted": (total_deleted + limit - 1) // limit,
    })




@router.post("/admin/approve/{entry_id}")
def approve_entry(
    entry_id: int,
    page_pending: int = Query(1),
    page_public: int = Query(1),
    active_tab: str = Query("pending"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    entry = db.get(Entry, entry_id)
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

    return RedirectResponse(
        f"/admin?page_pending={page_pending}&page_public={page_public}#tab-{active_tab}",
        status_code=302
    )


@router.post("/admin/reject/{entry_id}")
def reject_entry(
    entry_id: int,
    page_pending: int = Query(1),
    page_public: int = Query(1),
    active_tab: str = Query("pending"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    entry = db.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.is_public_copy:
        raise HTTPException(status_code=400, detail="Cannot reject an already approved entry")

    entry.submitted_to_public = False
    db.commit()

    return RedirectResponse(
        f"/admin?page_pending={page_pending}&page_public={page_public}#tab-{active_tab}",
        status_code=302
    )


@router.post("/admin/delete/{entry_id}")
async def delete_admin_entry(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    form_data = await request.form()
    page_pending = form_data.get("page_pending", "1")
    page_public = form_data.get("page_public", "1")
    active_tab = form_data.get("active_tab", "pending")

    entry = db.get(Entry, entry_id)
    if not entry or not entry.is_public_copy:
        raise HTTPException(status_code=404, detail="Entry not found or not an admin entry")

    entry.deleted_at = datetime.now(timezone.utc)
    entry.is_deleted = True
    db.commit()

    redirect_url = f"/admin?page_pending={page_pending}&page_public={page_public}#tab-{active_tab}"
    return RedirectResponse(redirect_url, status_code=302)


@router.post("/admin/restore/{entry_id}")
async def restore_admin_entry(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    form_data = await request.form()
    page_deleted = form_data.get("page_deleted", "1")
    page_pending = form_data.get("page_pending", "1")
    page_public = form_data.get("page_public", "1")
    active_tab = form_data.get("active_tab", "deleted")

    entry = db.get(Entry, entry_id)
    if not entry or not entry.is_public_copy or not entry.is_deleted:
        raise HTTPException(status_code=404, detail="Cannot restore entry")

    entry.is_deleted = False
    entry.deleted_at = None
    db.commit()

    redirect_url = (
        f"/admin?page_pending={page_pending}&page_public={page_public}"
        f"&page_deleted={page_deleted}#tab-{active_tab}"
    )
    return RedirectResponse(redirect_url, status_code=302)


@router.post("/admin/purge/{entry_id}")
async def purge_admin_entry(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    form_data = await request.form()
    page_deleted = form_data.get("page_deleted", "1")
    page_pending = form_data.get("page_pending", "1")
    page_public = form_data.get("page_public", "1")
    active_tab = form_data.get("active_tab", "deleted")

    entry = db.get(Entry, entry_id)
    if not entry or not entry.is_public_copy or not entry.is_deleted:
        raise HTTPException(status_code=404, detail="Cannot purge entry")

    db.delete(entry)
    db.commit()

    redirect_url = (
        f"/admin?page_pending={page_pending}&page_public={page_public}"
        f"&page_deleted={page_deleted}#tab-{active_tab}"
    )
    return RedirectResponse(redirect_url, status_code=302)
