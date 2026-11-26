from fastapi import HTTPException, Request


def require_creator(request: Request) -> tuple[str, str]:
    """Identité posée par la Gateway (R7). Le client ne parle pas à ce service."""
    user_id = (request.headers.get("x-user-id") or "").strip()
    channel_id = (request.headers.get("x-channel-id") or "").strip()
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentification requise")
    if not channel_id:
        raise HTTPException(status_code=403, detail="Compte non créateur")
    return user_id, channel_id
