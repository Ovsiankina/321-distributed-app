import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User
from ..passwords import hash_password, verify_dummy_password, verify_password
from ..rate_limit import login_limiter
from ..schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    normalize_email,
)
from ..tokens import issue_token, verify_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


def _token_response(user_id: int, email: str) -> TokenResponse:
    return TokenResponse(
        token=issue_token(user_id),
        email=email,
        expires_in_hours=settings.token_ttl_hours,
    )


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Authentification requise")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized()
    try:
        user_id = verify_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise _unauthorized() from None
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user


@router.post("/register", status_code=201, response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        # La contrainte UNIQUE tranche : pas de SELECT préalable, donc pas de
        # course entre deux inscriptions simultanées.
        db.flush()
        # Lu avant le commit, qui expire l'objet : après, il coûterait un SELECT.
        user_id = user.id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Cet email est déjà utilisé"
        ) from None
    return _token_response(user_id, body.email)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = normalize_email(body.email)
    # Compté avant de hacher : des requêtes simultanées ne passent pas toutes le
    # contrôle avant que le premier échec soit enregistré.
    retry_after = login_limiter.acquire(email)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives, réessayez plus tard",
            headers={"Retry-After": str(retry_after)},
        )
    account = db.execute(
        select(User.id, User.password_hash).where(User.email == email)
    ).one_or_none()
    # Rend la connexion au pool avant le hachage Argon2, qui dure des dizaines de ms.
    db.close()
    if account is None:
        verify_dummy_password(body.password)
    if account is None or not verify_password(account.password_hash, body.password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    login_limiter.reset(email)
    # La comparaison est binaire : l'email normalisé est celui qui est stocké.
    return _token_response(account.id, email)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return UserResponse(id=user.id, email=user.email)
