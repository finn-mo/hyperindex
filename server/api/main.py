from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from server.db.connection import init_db
from server.crud.entries import (
    create_entry,
    get_all_entries,
    get_entry_by_id,
    update_entry,
    delete_entry,
)
from server.models.schemas import EntryIn, EntryOut
from server.security.auth import verify_token


templates = Jinja2Templates(directory="server/templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Hyperindex API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="server/static"), name="static")

@app.post("/entries", response_model=EntryOut, dependencies=[Depends(verify_token)])
def create_entry_api(entry_in: EntryIn):
    dto = create_entry(entry_in)
    return dto.to_entry_out()


@app.get("/entries", response_model=list[EntryOut], dependencies=[Depends(verify_token)])
def list_entries(
    tag: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    dtos = get_all_entries()
    filtered = [
        dto for dto in dtos
        if not tag or tag in dto.tags
    ]
    return [dto.to_entry_out() for dto in filtered[offset:offset + limit]]


@app.get("/entries/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: int):
    dto = get_entry_by_id(entry_id)
    if not dto:
        raise HTTPException(status_code=404, detail="Entry not found")
    return dto.to_entry_out()


@app.put("/entries/{entry_id}", response_model=EntryOut, dependencies=[Depends(verify_token)])
def update_entry_api(entry_id: int, entry_in: EntryIn):
    dto = update_entry(entry_id, entry_in)
    if not dto:
        raise HTTPException(status_code=404, detail="Entry not found or update failed")
    return dto.to_entry_out()


@app.delete("/entries/{entry_id}", response_model=dict, dependencies=[Depends(verify_token)])
def delete_entry_api(entry_id: int):
    success = delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted successfully"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def read_index(request: Request, q: Optional[str] = Query(None)):
    entries = get_all_entries()
    
    if q:
        q_lower = q.lower()
        entries = [
            e for e in entries
            if q_lower in e.title.lower()
            or q_lower in e.description.lower()
            or any(q_lower in tag.lower() for tag in e.tags)
        ]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "entries": entries,
        "query": q
    })