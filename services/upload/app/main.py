from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .routers import upload


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config.data_dir().mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Stream321 Upload", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upload.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "upload"}
