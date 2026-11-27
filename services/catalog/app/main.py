from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

import asyncio

from .bus import amqp_url, consume_uploaded, publish_messages
from .db import SessionLocal, init_db, ping_database
from .events import startup_messages
from .models import Video
from .routers import catalog
from .seed import sync_catalog_on_startup


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        synced = sync_catalog_on_startup(db)
        pending = startup_messages(db.query(Video).all(), synced.removed)
    finally:
        db.close()
    publisher = asyncio.create_task(publish_messages(pending)) if amqp_url() else None
    consumer = asyncio.create_task(consume_uploaded()) if amqp_url() else None
    try:
        yield
    finally:
        for task in (publisher, consumer):
            if task is not None:
                task.cancel()


app = FastAPI(title="321-distributed-app Catalog", version="0.1.0", lifespan=lifespan)
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
