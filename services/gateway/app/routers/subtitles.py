from fastapi import APIRouter, Request

from .. import config
from ..proxy import forward_request

router = APIRouter(tags=["proxy"])


@router.api_route(
    "/api/subtitles/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_subtitles(path: str, request: Request):
    return await forward_request(
        request,
        upstream_base=config.subtitles_upstream_base(),
        path_prefix="/api/subtitles/",
        path_suffix=path,
        timeout_seconds=config.subtitles_timeout_seconds(),
    )
