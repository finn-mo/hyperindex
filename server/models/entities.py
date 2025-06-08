from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from server.db.connection import Base

entry_tags = Table(
    'entry_tags',
    Base.metadata,
    Column('entry_id', Integer, ForeignKey('entries.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)

    entries = relationship("Entry", back_populates="owner")

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    entries = relationship("Entry", secondary=entry_tags, back_populates="tags")

class Entry(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    title = Column(String)
    notes = Column(String)
    is_deleted = Column(Boolean, default=False)
    is_public_copy = Column(Boolean, default=False)
    submitted_to_public = Column(Boolean, default=False)
    original_id = Column(Integer, ForeignKey("entries.id"), nullable=True)
    original = relationship("Entry", remote_side="Entry.id", backref="admin_forks")

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="entries")
    tags = relationship("Tag", secondary=entry_tags, back_populates="entries")