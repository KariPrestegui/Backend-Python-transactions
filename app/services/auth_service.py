

import base64
import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_env
from app.models.user import User

logger = logging.getLogger(__name__)


SECRET_KEY = get_env("JWT_SECRET_KEY", required=True)
ALGORITHM = get_env("JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(get_env("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default="30"))
_ITERATIONS = 260_000
_HASH_NAME   = "sha256"


def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        _HASH_NAME,
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    key_b64  = base64.b64encode(key).decode("utf-8")
    return f"{salt_b64}:{key_b64}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_b64, key_b64 = stored.split(":")
        salt        = base64.b64decode(salt_b64)
        stored_key  = base64.b64decode(key_b64)
        derived_key = hashlib.pbkdf2_hmac(
            _HASH_NAME,
            password.encode("utf-8"),
            salt,
            _ITERATIONS,
        )
        return hmac.compare_digest(derived_key, stored_key)
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, email: str, password: str) -> User:
    if get_user_by_email(db, email):
        raise ValueError(f"Email '{email}' is already registered")

    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered new user: %s", user.id)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

