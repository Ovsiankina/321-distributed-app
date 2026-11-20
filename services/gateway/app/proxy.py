import httpx
from fastapi import HTTPException, Request, Response

_FORWARD_HEADERS = ("authorization", "content-type")
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
