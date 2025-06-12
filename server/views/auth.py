from fastapi import APIRouter, Response, HTTPException, status, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from server.models.entities import User
from server.security import create_token, get_db


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="server/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """
    Render the login form.

    Used to collect username and password input from the user.

    Args:
        request (Request): Incoming HTTP request for template context.

    Returns:
        HTMLResponse: Rendered login form template.
    """
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.post("/login")
def login_post(
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/rolodex"),
    db: Session = Depends(get_db)
):
    """
    Process login credentials and issue authentication token.

    Validates username and password, sets `access_token` cookie if valid,
    then redirects to the next page.

    Args:
        username (str): Username entered in form.
        password (str): Password entered in form.
        next (str): Redirect target after successful login.
        db (Session): Database session.

    Raises:
        HTTPException: If credentials are invalid.

    Returns:
        RedirectResponse: Redirect to `next` path with token cookie set.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": user.username})
    resp = RedirectResponse(url=next, status_code=302)
    resp.set_cookie(key="access_token", value=token, httponly=True)
    return resp


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """
    Render the registration form.

    Presents fields for new users to create an account.

    Args:
        request (Request): Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered registration page.
    """
    return templates.TemplateResponse(request, "register.html", {"request": request})


@router.post("/register")
def register_post(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Process new user registration.

    Validates uniqueness, hashes password, stores user in DB.

    Args:
        username (str): Desired username.
        password (str): Password to be hashed and stored.
        db (Session): Database session.

    Raises:
        HTTPException: If username already exists.

    Returns:
        RedirectResponse: Redirect to login page after successful registration.
    """
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/logout")
def logout():
    """
    Log out the current user.

    Clears the `access_token` cookie and redirects to homepage.

    Returns:
        RedirectResponse: Redirect to home with session cleared.
    """
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response