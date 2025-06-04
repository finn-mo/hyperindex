from datetime import datetime, timezone
from typing import Optional

from server.db.entries import (
    insert_entry,
    fetch_entry_by_id,
    fetch_all_entries,
    delete_entry_by_id,
    update_entry_by_id,
    count_entries
)
from server.models.dto import EntryDTO
from server.models.schemas import EntryIn


def create_entry(entry_in: EntryIn) -> EntryDTO:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    entry_dto = EntryDTO(
        id=None,
        url=entry_in.url,
        title=entry_in.title,
        tags=entry_in.tags,
        description=entry_in.description,
        date_added=now,
        archived_url=None,
        snapshot_dir=None,
        deleted=False,
    )

    entry_dto.id = insert_entry(entry_dto)
    return entry_dto


def get_entry_by_id(entry_id: int) -> Optional[EntryDTO]:
    return fetch_entry_by_id(entry_id)


def get_all_entries(limit: int, offset: int) -> list[EntryDTO]:
    return fetch_all_entries(limit=limit, offset=offset)


def get_entry_count() -> int:
    return count_entries()


def delete_entry(entry_id: int) -> bool:
    return delete_entry_by_id(entry_id)


def update_entry(entry_id: int, update: EntryIn) -> Optional[EntryDTO]:
    existing = fetch_entry_by_id(entry_id)
    if not existing:
        return None

    updated = EntryDTO(
        id=entry_id,
        url=update.url,
        title=update.title,
        tags=update.tags,
        description=update.description,
        date_added=existing.date_added,
        archived_url=existing.archived_url,
        snapshot_dir=existing.snapshot_dir,
        deleted=existing.deleted,
    )

    success = update_entry_by_id(entry_id, updated)
    return updated if success else None