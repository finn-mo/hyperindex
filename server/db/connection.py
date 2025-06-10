from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from server.settings import settings

Base = declarative_base()

from server.models.entities import Entry, User  # Ensure models are registered

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # Create standalone FTS table (no content=)
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entry_fts USING fts5(
                title, notes, url
            );
        """))
        # Populate FTS table if empty
        count = conn.execute(text("SELECT count(*) FROM entry_fts")).scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO entry_fts(rowid, title, notes, url)
                SELECT id, title, notes, url FROM entries WHERE is_deleted = 0;
            """))

        # Trigger: After INSERT
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
                INSERT INTO entry_fts(rowid, title, notes, url)
                VALUES (new.id, new.title, new.notes, new.url);
            END;
        """))

        # Trigger: After UPDATE
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
                UPDATE entry_fts
                SET title = new.title,
                    notes = new.notes,
                    url = new.url
                WHERE rowid = new.id;
            END;
        """))

        # Trigger: After DELETE
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
                DELETE FROM entry_fts WHERE rowid = old.id;
            END;
        """))

        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()