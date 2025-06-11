from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from server.models.entities import Entry, User
from server.models.schemas import EntryCreate
from server.services.admin import AdminEntryService
from server.security import get_db, require_admin

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

    pending_entries, total_pending = AdminEntryService.get_pending_submissions(db, limit=limit, offset=offset_pending)
    public_entries, total_public = AdminEntryService.get_public_entries(db, limit=limit, offset=offset_public)
    deleted_entries, total_deleted = AdminEntryService.get_deleted_entries(db, limit=limit, offset=offset_deleted)

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
    user: User = Depends(require_admin)
):
    AdminEntryService.approve_entry(db, entry_id, user)
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
    user: User = Depends(require_admin)
):
    AdminEntryService.reject_entry(db, entry_id)
    return RedirectResponse(
        f"/admin?page_pending={page_pending}&page_public={page_public}#tab-{active_tab}",
        status_code=302
    )


@router.get("/admin/edit/{entry_id}", response_class=HTMLResponse)
def edit_admin_entry_form(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    entry = db.get(Entry, entry_id)
    if not entry or not entry.is_public_copy:
        raise HTTPException(status_code=404, detail="Entry not found")

    return templates.TemplateResponse("edit_entry_admin.html", {
        "request": request,
        "entry": entry,
        "user": user
    })


@router.post("/admin/edit/{entry_id}")
async def update_admin_entry(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    form_data = await request.form()
    title = form_data.get("title", "").strip()
    url = form_data.get("url", "").strip()
    notes = form_data.get("notes", "").strip()
    tags_raw = form_data.get("tags", "")
    tag_list = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]

    entry_data = EntryCreate(
        title=title,
        url=url,
        notes=notes,
        tags=tag_list
    )

    AdminEntryService.update_entry(db, entry_id, entry_data)

    return RedirectResponse("/admin#tab-public", status_code=302)


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

    AdminEntryService.delete_entry(db, entry_id)

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

    AdminEntryService.restore_entry(db, entry_id)

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

    AdminEntryService.purge_entry(db, entry_id)

    redirect_url = (
        f"/admin?page_pending={page_pending}&page_public={page_public}"
        f"&page_deleted={page_deleted}#tab-{active_tab}"
    )
    return RedirectResponse(redirect_url, status_code=302)