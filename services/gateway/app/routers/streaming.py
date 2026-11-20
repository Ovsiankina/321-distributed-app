from fastapi import APIRouter, Request

from .. import config
from ..proxy import forward_request

router = APIRouter(tags=["streaming"])


@router.api_route(
    "/api/stream/{path:path}",
    methods=["GET", "HEAD", "OPTIONS"],
)
async def proxy_streaming(path: str, request: Request):
    return await forward_request(
        request,
        upstream_base=config.streaming_upstream_base(),
        path_prefix="/api/stream/",
        path_suffix=path,
        timeout_seconds=config.streaming_timeout_seconds(),
    )
