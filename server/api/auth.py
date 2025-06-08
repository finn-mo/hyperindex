from fastapi import APIRouter, HTTPException, status, Depends, Form
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse

from server.models.entities import User
from server.security import create_token, get_db

router = APIRouter(tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register")
def register_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
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
    resp = RedirectResponse(url="/rolodex", status_code=302)
    resp.set_cookie(key="access_token", value=token, httponly=True)
    return resp