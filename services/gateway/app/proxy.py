import httpx
from fastapi import HTTPException, Request, Response

_FORWARD_HEADERS = ("authorization", "content-type")
_V2_HEADERS = (
    "authorization",
    "content-type",
    "content-length",
    "range",
    "if-range",
)
_HOP_BY_HOP = frozenset({"transfer-encoding", "connection", "keep-alive"})


async def forward_request(
    request: Request,
    *,
    upstream_base: str,
    path_prefix: str,
    path_suffix: str,
    timeout_seconds: float,
) -> Response:
    upstream = upstream_base.rstrip("/")
    query = request.url.query
    target = f"{upstream}{path_prefix}{path_suffix}"
    if query:
        target = f"{target}?{query}"

    headers = {
        name: request.headers[name]
        for name in _FORWARD_HEADERS
        if name in request.headers
    }
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            upstream_response = await client.request(
                request.method,
                target,
                headers=headers,
                content=body if body else None,
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Service indisponible")

    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in _HOP_BY_HOP
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )


async def forward_v2(
    request: Request,
    *,
    upstream_base: str,
    path_prefix: str,
    path_suffix: str,
    timeout_seconds: float,
    identity: dict | None = None,
    forwarded_prefix: str = "/api/v2",
) -> Response:
    """Proxy v2 : Range transmis, identité calculée par la Gateway uniquement."""
    upstream = upstream_base.rstrip("/")
    query = request.url.query
    target = f"{upstream}{path_prefix}{path_suffix}"
    if query:
        target = f"{target}?{query}"

    headers = {
        name: request.headers[name]
        for name in _V2_HEADERS
        if name in request.headers
    }
    headers["x-forwarded-prefix"] = forwarded_prefix
    if identity is not None:
        headers["x-user-id"] = str(identity["sub"])
        channel = identity.get("channel_id")
        if channel:
            headers["x-channel-id"] = str(channel)
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            async with client.stream(
                request.method,
                target,
                headers=headers,
                content=body if body else None,
            ) as upstream_response:
                content = await upstream_response.aread()
                status_code = upstream_response.status_code
                response_headers = {
                    key: value
                    for key, value in upstream_response.headers.items()
                    if key.lower() not in _HOP_BY_HOP
                }
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Service indisponible")

    return Response(content=content, status_code=status_code, headers=response_headers)
