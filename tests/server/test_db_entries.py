import pytest
from datetime import datetime, timezone

from server.db.entries import insert_entry, fetch_entry_by_id
from server.models.dto import EntryDTO

@pytest.mark.db
@pytest.mark.slow
def test_insert_and_fetch_entry(temp_db):
    entry = EntryDTO(
        id=None,
        url="https://example.com",
        title="Example",
        tags=["test", "example"],
        description="A test entry",
        date_added=datetime.now(timezone.utc).isoformat(),
        archived_url=None,
        snapshot_dir=None,
        deleted=False
    )

    new_id = insert_entry(entry)
    fetched = fetch_entry_by_id(new_id)
    assert fetched is not None
    assert fetched.url == entry.url
    assert fetched.title == entry.title