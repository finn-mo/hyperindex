import os
import pytest

from server.db.connection import init_db


@pytest.fixture(scope="session", autouse=True)
def temp_db(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    original = os.environ.get("HYPERINDEX_SERVER_DB")

    os.environ["HYPERINDEX_SERVER_DB"] = str(db_path)
    init_db()

    yield db_path

    if original is not None:
        os.environ["HYPERINDEX_SERVER_DB"] = original
    else:
        os.environ.pop("HYPERINDEX_SERVER_DB", None)

    try:
        db_path.unlink(missing_ok=True)
    except Exception:
        pass