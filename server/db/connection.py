from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from server.settings import settings

Base = declarative_base()

from server.models.entities import Entry, User  # Ensure models are registered

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
