from fastapi import APIRouter, Request, Cookie, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from server.models.entities import User
from server.security import get_db, get_optional_user

templates = Jinja2Templates(directory="server/templates")
router = APIRouter()


@router.get("/about", response_class=HTMLResponse)
def about_page(
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    user: User = get_optional_user(access_token, db)
    return templates.TemplateResponse(request, "about.html", {"request": request, "user": user})