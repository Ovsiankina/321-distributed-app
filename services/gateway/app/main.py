from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import catalog, fallback, home, subtitles

app = FastAPI(title="Stream321 Gateway", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home.router)
app.include_router(catalog.router)
app.include_router(subtitles.router)
app.include_router(fallback.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}
