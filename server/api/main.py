from contextlib import asynccontextmanager
from math import ceil
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
    get_entry_count
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


# API ROUTES
@app.post("/entries", response_model=EntryOut, dependencies=[Depends(verify_token)])
def create_entry_api(entry_in: EntryIn):
    dto = create_entry(entry_in)
    return dto.to_entry_out()


@app.get("/entries", response_model=list[EntryOut], dependencies=[Depends(verify_token)])
def list_entries(
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
):
    offset = (page - 1) * limit
    dtos = get_all_entries(limit=limit, offset=offset)

    if tag:
        dtos = [dto for dto in dtos if tag in dto.tags]

    return [dto.to_entry_out() for dto in dtos]


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


def build_page_range(page: int, total_pages: int) -> list:
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    range_list = []

    if page > 3:
        range_list.append(1)
        if page > 4:
            range_list.append("...")

    start = max(2, page - 1)
    end = min(total_pages - 1, page + 1)
    range_list.extend(range(start, end + 1))

    if page < total_pages - 2:
        if page < total_pages - 3:
            range_list.append("...")
        range_list.append(total_pages)

    return range_list


# WEB FRONTEND ROUTE
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 10
):
    offset = (page - 1) * limit

    if q:
        all_entries = get_all_entries(limit=10000, offset=0)
        filtered = [
            e for e in all_entries
            if q.lower() in e.title.lower()
            or q.lower() in e.description.lower()
            or any(q.lower() in tag.lower() for tag in e.tags)
        ]
        total = len(filtered)
        entries = filtered[offset:offset + limit]
    else:
        total = get_entry_count()
        entries = get_all_entries(limit=limit, offset=offset)

    total_pages = ceil(total / limit)
    page_range = build_page_range(page, total_pages)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "entries": entries,
        "query": q,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "page_range": page_range,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    })