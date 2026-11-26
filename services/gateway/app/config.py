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


def catalog_upstream_base() -> str:
    return os.environ.get(
        "GATEWAY_CATALOG_URL", "http://127.0.0.1:8002"
    ).rstrip("/")


def catalog_timeout_seconds() -> float:
    raw = os.environ.get("GATEWAY_CATALOG_TIMEOUT_SECONDS", "5.0")
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"GATEWAY_CATALOG_TIMEOUT_SECONDS doit être un nombre (reçu {raw!r})"
        ) from exc
    if timeout <= 0:
        raise ValueError(
            f"GATEWAY_CATALOG_TIMEOUT_SECONDS doit être positif (reçu {raw!r})"
        )
    return timeout


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


def auth_upstream_base() -> str:
    return os.environ.get("GATEWAY_AUTH_URL", "http://127.0.0.1:8001").rstrip("/")


def auth_timeout_seconds() -> float:
    raw = os.environ.get("GATEWAY_AUTH_TIMEOUT_SECONDS", "5.0")
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"GATEWAY_AUTH_TIMEOUT_SECONDS doit être un nombre (reçu {raw!r})"
        ) from exc
    if timeout <= 0:
        raise ValueError(
            f"GATEWAY_AUTH_TIMEOUT_SECONDS doit être positif (reçu {raw!r})"
        )
    return timeout


def streaming_upstream_base() -> str:
    return os.environ.get(
        "GATEWAY_STREAMING_URL", "http://127.0.0.1:8003"
    ).rstrip("/")


def upload_upstream_base() -> str:
    return os.environ.get("GATEWAY_UPLOAD_URL", "http://127.0.0.1:8003").rstrip("/")


def upload_timeout_seconds() -> float:
    raw = os.environ.get("GATEWAY_UPLOAD_TIMEOUT_SECONDS", "120.0")
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"GATEWAY_UPLOAD_TIMEOUT_SECONDS doit être un nombre (reçu {raw!r})"
        ) from exc
    if timeout <= 0:
        raise ValueError(
            f"GATEWAY_UPLOAD_TIMEOUT_SECONDS doit être positif (reçu {raw!r})"
        )
    return timeout


def jwt_public_key_pem() -> str:
    return os.environ.get("GATEWAY_JWT_PUBLIC_KEY", "")


def jwt_issuer() -> str:
    return os.environ.get("GATEWAY_JWT_ISSUER", "stream321-auth")


def jwt_audience() -> str:
    return os.environ.get("GATEWAY_JWT_AUDIENCE", "stream321-api")


def streaming_timeout_seconds() -> float:
    raw = os.environ.get("GATEWAY_STREAMING_TIMEOUT_SECONDS", "30.0")
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"GATEWAY_STREAMING_TIMEOUT_SECONDS doit être un nombre (reçu {raw!r})"
        ) from exc
    if timeout <= 0:
        raise ValueError(
            f"GATEWAY_STREAMING_TIMEOUT_SECONDS doit être positif (reçu {raw!r})"
        )
    return timeout
