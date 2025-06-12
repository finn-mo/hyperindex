from server.settings import settings

def offset(page: int, limit: int) -> int:
    clamped_limit = min(limit, settings.MAX_PAGE_SIZE)
    return max(0, (page - 1)) * clamped_limit