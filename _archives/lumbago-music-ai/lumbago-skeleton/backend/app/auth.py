from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt, os
from .db import SessionLocal
from .models_sql import Track
from sqlalchemy.orm import Session

router = APIRouter(prefix='/auth')

SECRET = os.getenv('JWT_SECRET', 'devsecret')
ALGORITHM = 'HS256'
ACCESS_EXPIRE_MINUTES = 60*24

class UserIn(BaseModel):
    email: str
    password: str

# Dummy user store (replace with real DB model)
USERS = {'admin@local': {'password': 'password', 'id': 1, 'name': 'Admin'}}

def create_token(data: dict, expires_delta: int = ACCESS_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({'exp': expire.isoformat()})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)

@router.post('/login')
def login(u: UserIn):
    user = USERS.get(u.email)
    if not user or user['password'] != u.password:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_token({'sub': u.email, 'uid': user['id']})
    return {'access_token': token, 'token_type': 'bearer'}
