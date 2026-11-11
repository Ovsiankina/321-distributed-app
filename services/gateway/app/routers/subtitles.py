import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from .. import config

router = APIRouter(tags=["proxy"])

_FORWARD_HEADERS = ("authorization", "content-type")


@router.api_route(
    "/api/subtitles/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_subtitles(path: str, request: Request):
    upstream = config.subtitles_upstream_base()
    query = request.url.query
    target = f"{upstream}/api/subtitles/{path}"
    if query:
        target = f"{target}?{query}"

    headers = {
        name: request.headers[name]
        for name in _FORWARD_HEADERS
        if name in request.headers
    }
    body = await request.body()

    try:
        async with httpx.AsyncClient(
            timeout=config.subtitles_timeout_seconds()
        ) as client:
            upstream_response = await client.request(
                request.method,
                target,
                headers=headers,
                content=body if body else None,
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Service indisponible")

    response_headers = {}
    for key, value in upstream_response.headers.items():
        lowered = key.lower()
        if lowered in ("transfer-encoding", "connection", "keep-alive"):
            continue
        response_headers[key] = value

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )
