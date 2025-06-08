from sqlalchemy.orm import Session
from server.models.entities import Tag


def resolve_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    tag_objects = []
    for name in tag_names:
        tag = db.query(Tag).filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tag_objects.append(tag)
    return tag_objects
