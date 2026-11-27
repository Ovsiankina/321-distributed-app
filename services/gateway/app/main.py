from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, catalog, fallback, home, streaming, subtitles, v2

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
app.include_router(auth.router)
app.include_router(streaming.router)
app.include_router(v2.router)
app.include_router(fallback.router)


@app.middleware("http")
async def mark_v1_deprecated(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/api/") and not path.startswith("/api/v2"):
        response.headers["Deprecation"] = "true"
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}
