from fastapi import APIRouter, HTTPException, Request

from .. import config
from ..auth import require_jwt
from ..proxy import forward_v2

router = APIRouter(prefix="/api/v2", tags=["v2"])


def _auth_needs_jwt(path: str) -> bool:
    head = path.split("/", 1)[0]
    return head in {"me", "favorites"}


@router.api_route(
    "/auth/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def auth_v2(path: str, request: Request):
    identity = require_jwt(request) if _auth_needs_jwt(path) else None
    return await forward_v2(
        request,
        upstream_base=config.auth_upstream_base(),
        path_prefix="/api/auth/",
        path_suffix=path,
        timeout_seconds=config.auth_timeout_seconds(),
        identity=identity,
    )


@router.api_route("/catalog/{path:path}", methods=["GET", "HEAD", "OPTIONS"])
async def catalog_v2(path: str, request: Request):
    return await forward_v2(
        request,
        upstream_base=config.catalog_upstream_base(),
        path_prefix="/api/catalog/",
        path_suffix=path,
        timeout_seconds=config.catalog_timeout_seconds(),
    )


@router.api_route("/stream/{video_id}", methods=["GET", "HEAD"])
async def stream_v2(video_id: str, request: Request):
    return await forward_v2(
        request,
        upstream_base=config.streaming_upstream_base(),
        path_prefix="/api/stream/",
        path_suffix=video_id,
        timeout_seconds=config.streaming_timeout_seconds(),
    )


@router.api_route("/upload/videos", methods=["POST"])
async def upload_v2(request: Request):
    identity = require_jwt(request)
    if not str(identity.get("channel_id") or "").strip():
        raise HTTPException(status_code=403, detail="Compte non créateur")
    return await forward_v2(
        request,
        upstream_base=config.upload_upstream_base(),
        path_prefix="/api/upload/",
        path_suffix="videos",
        timeout_seconds=config.upload_timeout_seconds(),
        identity=identity,
    )


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
def unknown_v2(path: str):
    raise HTTPException(status_code=404, detail="Route inconnue")
