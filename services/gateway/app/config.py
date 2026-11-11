import os


def listen_port() -> int:
    raw = os.environ.get("GATEWAY_PORT", "8000")
    try:
        port = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"GATEWAY_PORT doit être un entier (reçu {raw!r})") from exc
    if port < 1 or port > 65535:
        raise ValueError(f"GATEWAY_PORT hors plage (reçu {port})")
    return port


def subtitles_upstream_base() -> str:
    return os.environ.get(
        "GATEWAY_SUBTITLES_URL", "http://127.0.0.1:8004"
    ).rstrip("/")


def subtitles_timeout_seconds() -> float:
    raw = os.environ.get("GATEWAY_SUBTITLES_TIMEOUT_SECONDS", "5.0")
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"GATEWAY_SUBTITLES_TIMEOUT_SECONDS doit être un nombre (reçu {raw!r})"
        ) from exc
    if timeout <= 0:
        raise ValueError(
            f"GATEWAY_SUBTITLES_TIMEOUT_SECONDS doit être positif (reçu {raw!r})"
        )
    return timeout
