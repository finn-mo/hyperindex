import tempfile
from pathlib import Path
import pytest

from client.core.models import Entry
from client.core.config import Config
from client.core.storage import (
    init_db,
    add_entry,
    get_entry,
    update_entry,
    delete_entry,
    restore_entry,
    purge_deleted_entries,
    list_entries,
    list_deleted_entries,
    search_entries,
    count_tags
)


pytestmark = pytest.mark.storage


@pytest.fixture(scope="function")
def temp_storage():
    with tempfile.TemporaryDirectory() as tmp:
        test_dir = Path(tmp)
        Config.set_test_config(test_dir)
        init_db()
        yield


def test_add_and_get_entry(temp_storage):
    entry = Entry(
        url="https://example.com",
        title="Example",
        tags=["test", "example"],
        description="Just a test",
        date_added="2025-06-03T00:00:00Z"
    )
    add_entry(entry)
    entries = list_entries()
    assert len(entries) == 1
    assert entries[0].title == "Example"


def test_update_entry(temp_storage):
    entry = Entry(
        url="https://update.com",
        title="Before",
        tags=["tag1"],
        description="Old",
        date_added="2025-06-03T00:00:00Z"
    )
    add_entry(entry)
    assert update_entry(1, title="After", tags="tag2", desc="New")
    updated = get_entry(1)
    assert updated.title == "After"
    assert updated.description == "New"
    assert "tag2" in updated.tags


def test_delete_restore_purge(temp_storage):
    entry = Entry(
        url="https://delete.com",
        title="DeleteMe",
        tags=["tmp"],
        description="Trash test",
        date_added="2025-06-03T00:00:00Z"
    )
    add_entry(entry)
    assert delete_entry(1)
    assert len(list_deleted_entries()) == 1
    assert restore_entry(1)
    assert delete_entry(1)
    purge_deleted_entries()
    assert len(list_deleted_entries()) == 0


def test_search_and_tags(temp_storage):
    add_entry(Entry(
        url="https://find.com",
        title="Find Me",
        tags=["search", "find"],
        description="Searchable content",
        date_added="2025-06-03T00:00:00Z"
    ))
    add_entry(Entry(
        url="https://other.com",
        title="Other",
        tags=["misc"],
        description="Nothing here",
        date_added="2025-06-03T00:00:00Z"
    ))
    results = search_entries(query="find")
    assert len(results) == 1
    assert results[0].title == "Find Me"
    tag_counts = count_tags()
    assert tag_counts["search"] == 1
    assert tag_counts["find"] == 1