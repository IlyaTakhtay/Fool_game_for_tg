from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt

from backend.src.settings import JWTSettings

jwt_settings = JWTSettings()


def get_token_from_cookie(request: Request) -> str | None:
    """
    Извлекает JWT токен из httpOnly cookie 'access_token'.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (no token in cookie)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        hours=jwt_settings.access_token_expire_hours
    )
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(
        to_encode, jwt_settings.secret_key, algorithm=jwt_settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str = Depends(get_token_from_cookie)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, jwt_settings.secret_key, algorithms=[jwt_settings.algorithm]
        )
        player_id: str = payload.get("player_id")
        player_name: str = payload.get("player_name")
        if player_id is None or player_name is None:
            raise credentials_exception
        return {"player_id": player_id, "player_name": player_name}
    except JWTError:
        raise credentials_exception
