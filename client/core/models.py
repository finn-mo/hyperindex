from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Entry:
    id: Optional[int] = None
    url: str = ""
    title: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    date_added: str = ""
    archived_url: str = ""
    snapshot_dir: str = ""
    deleted: bool = False

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "None"
        lines = [
            f"ID: {self.id}" if self.id is not None else "",
            f"Title: {self.title}",
            f"URL: {self.url}",
            f"Tags: {tag_str}",
            f"Description: {self.description or 'None'}",
            f"Date Added: {self.date_added}",
        ]
        if self.archived_url:
            lines.append(f"Archived URL: {self.archived_url}")
        if self.snapshot_dir:
            lines.append(f"Snapshot: {self.snapshot_dir}")
        return "\n".join(line for line in lines if line)