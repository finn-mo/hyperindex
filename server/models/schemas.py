from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class TagSchema(BaseModel):
    name: str


class EntryBase(BaseModel):
    url: str
    title: Optional[str]
    notes: Optional[str]
    is_public: Optional[bool] = False
    tags: Optional[List[str]] = Field(default_factory=list)


class EntryCreate(EntryBase):
    pass


class EntryUpdate(EntryBase):
    pass


class EntryOut(EntryBase):
    id: int
    user_id: int
    is_deleted: bool
    date_added: datetime

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str