from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .db import SessionLocal, init_db, ping_database
from .routers import catalog
from .seed import sync_catalog_on_startup


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        sync_catalog_on_startup(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Stream321 Catalog", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(catalog.router)


@app.get("/health")
def health():
    try:
        ping_database()
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "service": "catalog"},
        )
    return {"status": "ok", "service": "catalog"}
