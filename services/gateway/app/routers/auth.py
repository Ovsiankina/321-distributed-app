from fastapi import APIRouter, Request

from .. import config
from ..proxy import forward_request

router = APIRouter(tags=["auth"])


@router.api_route(
    "/api/auth/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_auth(path: str, request: Request):
    return await forward_request(
        request,
        upstream_base=config.auth_upstream_base(),
        path_prefix="/api/auth/",
        path_suffix=path,
        timeout_seconds=config.auth_timeout_seconds(),
    )
