from datetime import datetime, timedelta, timezone
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext

load_dotenv(Path(__file__).resolve().parent / '.env')
# Never sign login tokens with a key that is written in the source code: a missing or placeholder
# SECRET_KEY gets a random key for this run (everyone is logged out on restart).
SECRET_KEY = os.getenv('SECRET_KEY', '').strip()
if len(SECRET_KEY) < 32 or 'change' in SECRET_KEY.lower():     # empty, too short, or a copied "change-this..." placeholder
    SECRET_KEY = secrets.token_urlsafe(48)
    print('WARNING: SECRET_KEY is not set in .env; using a random key for this run. Set a long random SECRET_KEY to keep logins across restarts.')
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
