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
    """
    Render the static About page.

    Attempts to identify the user via access token to provide optional context.
    Used to describe the purpose and scope of the application.

    Args:
        request (Request): Incoming HTTP request.
        access_token (str): Optional JWT token from cookie.
        db (Session): Database session for user lookup.

    Returns:
        HTMLResponse: Rendered about page with optional user context.
    """
    user: User = get_optional_user(access_token, db)
    return templates.TemplateResponse(request, "about.html", {"request": request, "user": user})