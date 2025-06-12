def build_pagination_context(page: int, limit: int, total: int) -> dict:
    """
    Construct pagination metadata for template rendering.

    Calculates total pages and navigation flags (has_prev, has_next).

    Args:
        page (int): Current page number (1-based).
        limit (int): Number of items per page.
        total (int): Total number of items.

    Returns:
        dict: Dictionary containing pagination context.
    """
    total_pages = (total + limit - 1) // limit
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": (page * limit) < total,
    }


def build_yellowpages_context(user, entries, page, limit, total, tag, query):
    """
    Build template context for the public Yellow Pages view.

    Includes pagination, filtering fields, and user state if available.

    Args:
        user: Optional user object (may be None).
        entries: List of public entries to render.
        page (int): Current pagination page.
        limit (int): Entries per page.
        total (int): Total entry count.
        tag (str): Tag filter string (or None).
        query (str): Search query string (or None).

    Returns:
        dict: Render context dictionary for yellowpages.html.
    """
    return {
        "user": user,
        "entries": entries,
        "tag": tag,
        "query": query,
        "action": "/",
        "tag_field": bool(tag),
        **build_pagination_context(page, limit, total)
    }


def build_rolodex_context(request, user, entries, page, limit, total, tag, query, all_tags):
    """
    Build template context for a user's private Rolodex dashboard.

    Includes pagination, filters, and tag autocomplete options.

    Args:
        request: FastAPI request object.
        user: Authenticated user.
        entries: List of user-owned entries.
        page (int): Current page number.
        limit (int): Entries per page.
        total (int): Total number of results.
        tag (str): Tag filter (if any).
        query (str): Search query (if any).
        all_tags (List[str]): List of all user tag strings.

    Returns:
        dict: Render context for rolodex.html.
    """
    return {
        "request": request,
        "user": user,
        "entries": entries,
        "tag": tag,
        "query": query,
        "all_tags": all_tags,
        "action": "/rolodex",
        "tag_field": bool(tag),
        **build_pagination_context(page, limit, total)
    }



def build_admin_panel_context(
    request,
    user,
    pending_entries, total_pending, page_pending,
    public_entries, total_public, page_public,
    deleted_entries, total_deleted, page_deleted,
    limit
):
    """
    Build context for the admin panel with tabbed moderation sections.

    Organizes paginated entries for pending, public, and deleted categories.

    Args:
        request: FastAPI request object.
        user: Authenticated admin user.
        pending_entries: Entries awaiting review.
        total_pending (int): Count of pending entries.
        page_pending (int): Current page in pending tab.
        public_entries: Admin-managed public entries.
        total_public (int): Count of public entries.
        page_public (int): Current page in public tab.
        deleted_entries: Soft-deleted public entries.
        total_deleted (int): Count of deleted entries.
        page_deleted (int): Current page in deleted tab.
        limit (int): Entries per page across all tabs.

    Returns:
        dict: Render context for admin_panel.html.
    """
    return {
        "request": request,
        "user": user,
        "pending_entries": pending_entries,
        "public_entries": public_entries,
        "deleted_entries": deleted_entries,
        "page_pending": page_pending,
        "total_pages_pending": (total_pending + limit - 1) // limit,
        "page_public": page_public,
        "total_pages_public": (total_public + limit - 1) // limit,
        "page_deleted": page_deleted,
        "total_pages_deleted": (total_deleted + limit - 1) // limit,
    }
