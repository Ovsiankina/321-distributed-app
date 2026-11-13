from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .db import SessionLocal, init_db, ping_database
from .routers import auth
from .seed import seed_users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Stream321 Auth", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)


def validation_detail(errors: list[dict]) -> str:
    fields = set()
    for error in errors:
        location = error["loc"]
        if error["type"] == "extra_forbidden" or len(location) != 2:
            return "Requête invalide"
        fields.add(location[1])
    if "email" in fields:
        return "Email invalide"
    if "password" in fields:
        return "Mot de passe invalide"
    return "Requête invalide"


@app.exception_handler(RequestValidationError)
def invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # Le contrat veut un 400 et { "detail": "<message>" }, pas le 422 de FastAPI.
    return JSONResponse(
        status_code=400, content={"detail": validation_detail(exc.errors())}
    )


@app.get("/health")
def health():
    try:
        ping_database()
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "service": "auth"},
        )
    return {"status": "ok", "service": "auth"}
