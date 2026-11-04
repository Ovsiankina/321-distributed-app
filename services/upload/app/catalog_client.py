import httpx
from fastapi import HTTPException

from . import config


def ensure_catalog_ready() -> None:
    base = config.catalog_base_url().rstrip("/")
    url = f"{base}/health"
    try:
        with httpx.Client(timeout=config.catalog_timeout_seconds()) as client:
            response = client.get(url)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Catalog indisponible")
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="Catalog indisponible")
    try:
        body = response.json()
    except ValueError:
        raise HTTPException(status_code=503, detail="Catalog indisponible")
    if not isinstance(body, dict):
        raise HTTPException(status_code=503, detail="Catalog indisponible")
    if body.get("status") != "ok" or body.get("service") != "catalog":
        raise HTTPException(status_code=503, detail="Catalog indisponible")
