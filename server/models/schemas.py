from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BaseEntry(BaseModel):
    url: str
    title: str
    tags: list[str] = []
    description: Optional[str] = None

class EntryIn(BaseEntry):
    pass

class EntryOut(BaseEntry):
    id: int
    date_added: datetime
    archived_url: Optional[str] = None
    snapshot_dir: Optional[str] = None
    deleted: bool = False