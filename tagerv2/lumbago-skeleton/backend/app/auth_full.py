from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from .db import SessionLocal
from .models_user import User
from .security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from sqlalchemy.orm import Session
import datetime

router = APIRouter(prefix='/auth')

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

def get_db():
    db = SessionLocal();
    try:
        yield db
    finally:
        db.close()

@router.post('/register')
def register(data: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email==data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    u = User(email=data.email, hashed_password=hash_password(data.password), display_name=data.display_name)
    db.add(u); db.commit(); db.refresh(u)
    return {'id': u.id, 'email': u.email, 'display_name': u.display_name}

@router.post('/login')
def login(data: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email==data.email).first()
    if not u or not verify_password(u.hashed_password, data.password):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    access = create_access_token({'sub': u.email, 'uid': u.id})
    refresh = create_refresh_token({'sub': u.email, 'uid': u.id})
    return {'access_token': access, 'refresh_token': refresh, 'token_type': 'bearer'}

class RefreshIn(BaseModel):
    refresh_token: str

@router.post('/refresh')
def refresh_token(body: RefreshIn):
    try:
        payload = decode_token(body.refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail='Invalid refresh token')
    access = create_access_token({'sub': payload.get('sub'), 'uid': payload.get('uid')})
    return {'access_token': access}

# dependency to get current user from Authorization header
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail='Missing authorization')
    try:
        scheme, token = authorization.split()
        payload = decode_token(token)
        uid = payload.get('uid')
        user = db.query(User).filter(User.id==uid).first()
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        return user
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid token')
