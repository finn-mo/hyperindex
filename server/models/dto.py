from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from server.models.schemas import EntryOut


@dataclass
class EntryDTO:
    id: Optional[int]
    url: str
    title: str
    tags: list[str]
    description: Optional[str]
    date_added: str
    archived_url: Optional[str]
    snapshot_dir: Optional[str]
    deleted: bool

    @staticmethod
    def from_row(row) -> "EntryDTO":
        return EntryDTO(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            tags=[t.strip() for t in row["tags"].split(",") if t.strip()],
            description=row["description"],
            date_added=row["date_added"],
            archived_url=row["archived_url"],
            snapshot_dir=row["snapshot_dir"],
            deleted=bool(row["deleted"]),
        )

    def to_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "tags": ", ".join(self.tags),
            "description": self.description,
            "date_added": self.date_added,
            "archived_url": self.archived_url,
            "snapshot_dir": self.snapshot_dir,
            "deleted": int(self.deleted),
        }

    def to_entry_out(self) -> EntryOut:
        return EntryOut(
            id=self.id,
            url=self.url,
            title=self.title,
            tags=self.tags,
            description=self.description,
            date_added=datetime.fromisoformat(self.date_added),
            archived_url=self.archived_url,
            snapshot_dir=self.snapshot_dir,
            deleted=self.deleted,
        )