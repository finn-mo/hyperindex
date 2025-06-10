import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.api.main import app
from server.models.entities import Base, User
from server.db.connection import get_db  # Now properly located in connection.py
from server.security import pwd_context, create_token

# Use in-memory SQLite DB for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# --- Create engine and session factory once per test session ---
@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="session")
def SessionLocal(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Setup and teardown for each test function ---
@pytest.fixture(scope="function")
def db_session(SessionLocal, engine):
    connection = engine.connect()
    transaction = connection.begin()

    session = SessionLocal(bind=connection)
    Base.metadata.create_all(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# --- Override FastAPI's DB dependency ---
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    user = User(username="testuser", password_hash=pwd_context.hash("testpass"))
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def access_token(test_user):
    return create_token({"sub": test_user.username})