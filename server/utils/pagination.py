from server.settings import settings

def offset(page: int, limit: int) -> int:
    """
    Calculate the pagination offset for SQL queries.

    Clamps the `limit` to the maximum page size defined in settings
    and returns the corresponding row offset for the given page.

    Args:
        page (int): 1-based page number.
        limit (int): Requested number of items per page.

    Returns:
        int: Offset value to use in SQL queries (zero-based).
    """
    clamped_limit = min(limit, settings.MAX_PAGE_SIZE)
    return max(0, (page - 1)) * clamped_limit