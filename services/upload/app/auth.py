import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import JWT_ALGORITHM, JWT_LEEWAY_SECONDS, load_jwt_settings

_bearer = HTTPBearer(auto_error=False)


def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentification requise")
    token = credentials.credentials
    settings = load_jwt_settings()
    try:
        payload = jwt.decode(
            token,
            settings.public_key,
            algorithms=[JWT_ALGORITHM],
            issuer=settings.issuer,
            audience=settings.audience,
            leeway=JWT_LEEWAY_SECONDS,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Authentification requise")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=401, detail="Authentification requise")
    return payload