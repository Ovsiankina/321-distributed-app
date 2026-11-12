from fastapi import APIRouter, Request

from .. import config
from ..proxy import forward_request

router = APIRouter(tags=["catalog"])


@router.api_route(
    "/api/catalog/{path:path}",
    methods=["GET", "HEAD", "OPTIONS"],
)
async def proxy_catalog(path: str, request: Request):
    return await forward_request(
        request,
        upstream_base=config.catalog_upstream_base(),
        path_prefix="/api/catalog/",
        path_suffix=path,
        timeout_seconds=config.catalog_timeout_seconds(),
    )
