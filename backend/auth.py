import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from database import get_db
from fastapi import Depends, HTTPException, status
from fastapi._compat.v2 import ValidationError
from fastapi.security import OAuth2PasswordBearer
from models import User
from pwdlib import PasswordHash
from sqlalchemy.sql import text

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=30,
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        os.environ["JWT_KEY"],
        algorithm="HS256",
    )
    return encoded_jwt


def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and return the subject (user id) if valid."""
    try:
        payload = jwt.decode(
            token,
            os.environ["JWT_KEY"],
            algorithms="HS256",
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")


async def get_current_user(token=Depends(oauth2_scheme), db=Depends(get_db)) -> User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = (
        db.execute(
            text("select * from users where id = :id").bindparams(id=user_id_int)
        )
        .mappings()
        .first()
    )
    try:
        user = User.model_validate(result)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


currentUser = Annotated[User, Depends(get_current_user)]
