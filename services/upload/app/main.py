import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import amqp_url, data_dir
from .messaging import consume_rejected
from .routers import stream, upload


@asynccontextmanager
async def lifespan(_app: FastAPI):
    data_dir().mkdir(parents=True, exist_ok=True)
    consumer = asyncio.create_task(consume_rejected()) if amqp_url() else None
    try:
        yield
    finally:
        if consumer is not None:
            consumer.cancel()


app = FastAPI(title="Stream321 Media", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upload.router)
app.include_router(stream.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "media"}
