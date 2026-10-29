from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext

load_dotenv(Path(__file__).resolve().parent / '.env')
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-to-a-long-random-secret')
ALGORITHM = 'HS256'
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def normalize_email(email: str) -> str:
    return (email or '').strip().lower()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False

def create_token(data: dict, minutes: int = 1440) -> str:
    payload = data.copy()
    payload['exp'] = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
