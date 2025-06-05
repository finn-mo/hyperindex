from pydantic import BaseModel
from typing import List, Optional

class TagSchema(BaseModel):
    name: str

class EntryBase(BaseModel):
    url: str
    title: Optional[str]
    notes: Optional[str]
    is_public: Optional[bool] = False
    tags: Optional[List[str]] = []

class EntryCreate(EntryBase):
    pass

class EntryUpdate(EntryBase):
    pass

class EntryOut(EntryBase):
    id: int
    user_id: int
    is_deleted: bool

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str