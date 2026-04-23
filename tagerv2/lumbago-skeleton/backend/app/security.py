from argon2 import PasswordHasher
from datetime import datetime, timedelta
import jwt, os

ph = PasswordHasher()
SECRET = os.getenv('JWT_SECRET','devsecret')
ALGORITHM = 'HS256'
ACCESS_EXPIRE_MINUTES = 60
REFRESH_EXPIRE_DAYS = 7

def hash_password(password:str)->str:
    return ph.hash(password)

def verify_password(hash, password):
    try:
        return ph.verify(hash, password)
    except Exception:
        return False

def create_access_token(data:dict, expires_minutes:int=ACCESS_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)

def create_refresh_token(data:dict, expires_days:int=REFRESH_EXPIRE_DAYS):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_days)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)

def decode_token(token:str):
    return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
