import time

import jwt

from .config import settings

ALGORITHM = "EdDSA"
CLOCK_SKEW_SECONDS = 30

_public_key = settings.jwt_private_key.public_key()


def issue_token(user_id: int) -> str:
    now = int(time.time())
    claims = {
        "iss": settings.jwt_issuer,
        "sub": str(user_id),
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + settings.token_ttl_hours * 3600,
    }
    return jwt.encode(claims, settings.jwt_private_key, algorithm=ALGORITHM)


def verify_token(token: str) -> int:
    """Retourne l'id de l'utilisateur, ou lève jwt.InvalidTokenError."""
    claims = jwt.decode(
        token,
        _public_key,
        # Liste fermée : refuse "none" et les tokens HS256.
        algorithms=[ALGORITHM],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        leeway=CLOCK_SKEW_SECONDS,
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )
    try:
        return int(claims["sub"])
    except ValueError as exc:
        raise jwt.InvalidTokenError("sub n'est pas un identifiant") from exc
