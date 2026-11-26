import jwt
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from fastapi import HTTPException, Request

from . import config

_LEEWAY = 30


def require_jwt(request: Request) -> dict:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentification requise")
    token = header.split(" ", 1)[1].strip()
    pem = config.jwt_public_key_pem().strip()
    if not pem:
        raise HTTPException(status_code=503, detail="Service indisponible")
    try:
        key = load_pem_public_key(pem.encode())
        payload = jwt.decode(
            token,
            key,
            algorithms=["EdDSA"],
            issuer=config.jwt_issuer(),
            audience=config.jwt_audience(),
            leeway=_LEEWAY,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Authentification requise") from None
    if not isinstance(payload, dict) or not str(payload.get("sub") or "").strip():
        raise HTTPException(status_code=401, detail="Authentification requise")
    return payload
