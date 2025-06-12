def build_pagination_context(page: int, limit: int, total: int) -> dict:
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
    return {
        "user": user,
        "entries": entries,
        "tag": tag,
        "query": query,
        **build_pagination_context(page, limit, total)
    }


def build_rolodex_context(request, user, entries, page, limit, total, tag, query, all_tags):
    return {
        "request": request,
        "user": user,
        "entries": entries,
        "selected_tag": tag,
        "query": query,
        "all_tags": all_tags,
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
