from server.models.schemas import EntryCreate
from server.services.user import UserEntryService
from server.services.shared import EntryQueryService


def test_create_entry(db_session, test_user):
    """Test that a new entry can be created and is correctly linked to the user and tags."""
    entry_data = EntryCreate(
        url="https://example.com",
        title="Example Entry",
        notes="A test entry",
        tags=["test", "example"]
    )
    entry = UserEntryService.create_entry(db_session, entry_data, test_user.id)

    assert entry.id is not None
    assert entry.user_id == test_user.id
    assert entry.title == "Example Entry"
    assert entry.notes == "A test entry"
    assert len(entry.tags) == 2
    assert sorted([tag.name for tag in entry.tags]) == ["example", "test"]


def test_filter_entries_by_tag(db_session, test_user):
    """Ensure that filtering by tag only returns matching entries."""
    UserEntryService.create_entry(
        db_session,
        EntryCreate(url="http://one", title="One", notes="Some notes", tags=["alpha"]),
        test_user.id
    )
    UserEntryService.create_entry(
        db_session,
        EntryCreate(url="http://two", title="Two", notes="Some more notes", tags=["beta"]),
        test_user.id
    )

    results, total = EntryQueryService.get_entries(db_session, user_id=test_user.id, tag="alpha")
    assert total == 1
    assert results[0].title == "One"
