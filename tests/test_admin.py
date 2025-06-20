import pytest
from server.models.schemas import EntryCreate
from server.services.user import UserEntryService
from server.models.entities import Entry
from sqlalchemy.orm.exc import NoResultFound


def test_pending_list_view_requires_admin(client):
    response = client.get("/admin")
    assert response.status_code in (401, 403)


def test_approve_submission_creates_admin_copy(client, db_session, test_user, admin_token):
    entry_data = EntryCreate(
        url="https://approved.com",
        title="To Approve",
        notes="Pending approval",
        tags=["review"]
    )
    entry = UserEntryService.create_entry(db_session, entry_data, test_user.id)
    entry.submitted = True
    db_session.commit()

    client.cookies.set("access_token", admin_token)
    response = client.post(f"/admin/{entry.id}/approve")
    assert response.status_code == 200

    admin_copy = db_session.query(Entry).filter_by(is_public_copy=True, title="To Approve").first()
    assert admin_copy is not None
    assert admin_copy.notes == "Pending approval"


def test_reject_submission_sets_flag(client, db_session, test_user, admin_token):
    entry_data = EntryCreate(
        url="https://rejected.com",
        title="Reject Me",
        notes="Will be rejected",
        tags=["reject"]
    )
    entry = UserEntryService.create_entry(db_session, entry_data, test_user.id)
    entry.submitted_to_public = True
    db_session.commit()

    client.cookies.set("access_token", admin_token)
    response = client.post(f"/admin/{entry.id}/reject")
    assert response.status_code == 200

    db_session.refresh(entry)
    assert entry.submitted_to_public is False


def test_edit_admin_copy_persists_changes(client, db_session, admin_token):
    admin_entry = Entry(
        url="https://editme.com",
        title="Edit Me",
        notes="Original",
        user_id=999,
        is_public_copy=True
    )
    db_session.add(admin_entry)
    db_session.commit()

    client.cookies.set("access_token", admin_token)
    response = client.post(
        f"/admin/{admin_entry.id}/edit",
        data={"title": "Edited Title", "notes": "Updated", "tags": "edited"},
        follow_redirects=False
    )
    assert response.status_code == 302

    db_session.refresh(admin_entry)
    assert admin_entry.title == "Edited Title"
    assert admin_entry.notes == "Updated"


def test_delete_and_restore_admin_entry(client, db_session, admin_token):
    admin_entry = Entry(
        url="https://deletable.com",
        title="Deletable",
        notes="To delete",
        user_id=999,
        is_public_copy=True
    )
    db_session.add(admin_entry)
    db_session.commit()

    client.cookies.set("access_token", admin_token)
    del_resp = client.post(f"/admin/{admin_entry.id}/delete")
    assert del_resp.status_code == 200

    db_session.refresh(admin_entry)
    assert admin_entry.is_deleted is True

    restore_resp = client.post(f"/admin/{admin_entry.id}/restore")
    assert restore_resp.status_code == 200

    db_session.refresh(admin_entry)
    assert admin_entry.is_deleted is False


def test_permanent_purge_removes_admin_entry(client, db_session, admin_token):
    admin_entry = Entry(
        url="https://purge.com",
        title="Purge",
        notes="Final delete",
        user_id=999,
        is_public_copy=True,
        is_deleted=True
    )
    db_session.add(admin_entry)
    db_session.commit()

    client.cookies.set("access_token", admin_token)
    purge_resp = client.post(f"/admin/{admin_entry.id}/purge")
    assert purge_resp.status_code == 200

    with pytest.raises(NoResultFound):
        db_session.query(Entry).filter_by(id=admin_entry.id).one()
