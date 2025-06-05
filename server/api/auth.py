from fastapi import APIRouter, HTTPException, status, Depends, Form, Response
from sqlalchemy.orm import Session

from passlib.context import CryptContext
from server.db.connection import SessionLocal
from server.models.orm import User
from server.models.schemas import UserOut
from server.security.auth import create_token
from server.models.schemas import Token
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

router = APIRouter(tags=["auth"])  # <--- corrected

templates = Jinja2Templates(directory="server/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    print(f"POST /auth/register invoked with username={username}")

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
    return {"status": "registered"}

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": user.username})
    resp = RedirectResponse(url="/dashboard", status_code=302)
    resp.set_cookie(key="access_token", value=token, httponly=True)
    return resp

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})