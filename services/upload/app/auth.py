import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config

_bearer = HTTPBearer(auto_error=False)


def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentification requise")
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret(),
            algorithms=[config.jwt_algorithm()],
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Authentification requise")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=401, detail="Authentification requise")
    return payload
