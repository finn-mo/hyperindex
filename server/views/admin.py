from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from server.models.entities import Entry, User
from server.models.schemas import EntryCreate
from server.services.admin import AdminEntryService
from server.services.shared import SharedEntryService
from server.security import get_db, require_admin
from server.utils.context import build_admin_panel_context
from server.utils.pagination import offset

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
    """
    Render the admin moderation dashboard.

    Displays three paginated tabs: pending submissions, public entries, and deleted items.
    Only accessible to users with admin privileges.

    Args:
        request (Request): Incoming HTTP request.
        page_pending (int): Page index for pending submissions tab.
        page_public (int): Page index for public entries tab.
        page_deleted (int): Page index for deleted entries tab.
        limit (int): Number of entries per page.
        user (User): Authenticated admin user.
        db (Session): Database session.

    Returns:
        HTMLResponse: Rendered admin panel with tabbed entry lists.
    """
    offset_pending = offset(page_pending, limit)
    offset_public = offset(page_public, limit)
    offset_deleted = offset(page_deleted, limit)

    pending_entries, total_pending = AdminEntryService.get_pending_submissions(db, limit=limit, offset=offset_pending)
    public_entries, total_public = AdminEntryService.get_public_entries(db, limit=limit, offset=offset_public)
    deleted_entries, total_deleted = AdminEntryService.get_deleted_entries(db, limit=limit, offset=offset_deleted)

    return templates.TemplateResponse(
        "admin_panel.html",
        build_admin_panel_context(
            request=request,
            user=user,
            pending_entries=pending_entries,
            total_pending=total_pending,
            page_pending=page_pending,
            public_entries=public_entries,
            total_public=total_public,
            page_public=page_public,
            deleted_entries=deleted_entries,
            total_deleted=total_deleted,
            page_deleted=page_deleted,
            limit=limit,
        )
    )



@router.post("/admin/approve/{entry_id}")
def approve_entry(
    entry_id: int,
    page_pending: int = Query(1),
    page_public: int = Query(1),
    active_tab: str = Query("pending"),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    """
    Approve a submitted entry for public listing.

    Forks the user entry into a new admin-managed public entry.
    Redirects back to the admin panel with tab and pagination preserved.

    Args:
        entry_id (int): ID of the user-submitted entry.
        page_pending (int): Current pending page (for redirect).
        page_public (int): Current public page (for redirect).
        active_tab (str): Which tab was active before action.
        db (Session): Database session.
        user (User): Authenticated admin user.

    Returns:
        RedirectResponse: Redirect to admin panel with tab context.
    """
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
    """
    Reject a submitted entry, marking it as reviewed but not published.

    Removes it from the pending list without creating a public copy.

    Args:
        entry_id (int): ID of the entry to reject.
        page_pending (int): Current pending page (for redirect).
        page_public (int): Current public page (for redirect).
        active_tab (str): Which tab was active before action.
        db (Session): Database session.
        user (User): Authenticated admin user.

    Returns:
        RedirectResponse: Redirect to admin panel with tab context.
    """
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
    """
    Render the edit form for a public (admin-owned) entry.

    Args:
        entry_id (int): ID of the public entry to edit.
        request (Request): HTTP request context.
        db (Session): Database session.
        user (User): Authenticated admin user.

    Returns:
        HTMLResponse: Rendered edit form with pre-filled entry data.
    """
    entry = AdminEntryService.get_entry_for_edit(db, entry_id)

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
    """
    Process updates to an existing public entry.

    Overwrites admin-managed entry metadata based on form input.

    Args:
        entry_id (int): ID of the entry to update.
        request (Request): Incoming form data request.
        db (Session): Database session.
        user (User): Authenticated admin user.

    Returns:
        RedirectResponse: Redirect to public entries tab.
    """
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

    """
    Soft-delete a public entry from the Yellow Pages.

    Removes it from public listing but retains it in the deleted tab for possible restoration.

    Args:
        entry_id (int): ID of the public entry to delete.
        request (Request): Incoming form data.
        db (Session): Database session.
        user (User): Authenticated admin user.

    Returns:
        RedirectResponse: Redirect to admin panel with tab context.
    """
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
    """
    Restore a previously deleted public entry.

    Makes the entry visible again in the public Yellow Pages tab.

    Args:
        entry_id (int): ID of the entry to restore.
        request (Request): Incoming form data.
        db (Session): Database session.
        user (User): Authenticated admin user.

    Returns:
        RedirectResponse: Redirect to admin panel with tab context.
    """
    form_data = await request.form()
    page_deleted = form_data.get("page_deleted", "1")
    page_pending = form_data.get("page_pending", "1")
    page_public = form_data.get("page_public", "1")
    active_tab = form_data.get("active_tab", "deleted")

    SharedEntryService.restore_entry(db, entry_id)

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
    """
    Permanently purge a deleted entry from the system.

    Irreversibly removes admin-managed entry from the database.

    Args:
        entry_id (int): ID of the deleted entry to purge.
        request (Request): Incoming form data.
        db (Session): Database session.
        user (User): Authenticated admin user.

    Returns:
        RedirectResponse: Redirect to admin panel with tab context.
    """
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