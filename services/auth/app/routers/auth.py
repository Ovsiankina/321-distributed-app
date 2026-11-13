import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        token=issue_token(user.id),
        email=user.email,
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
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Cet email est déjà utilisé"
        ) from None
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    email = normalize_email(body.email)
    retry_after = login_limiter.retry_after(email)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives, réessayez plus tard",
            headers={"Retry-After": str(retry_after)},
        )
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        verify_dummy_password(body.password)
    if user is None or not verify_password(user.password_hash, body.password):
        login_limiter.record_failure(email)
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    login_limiter.reset(email)
    return _token_response(user)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return UserResponse(id=user.id, email=user.email)
