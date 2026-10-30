"""Démarrage MariaDB catalog pour les tests d'intégration."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

CATALOG_SERVICE = Path(__file__).resolve().parents[2] / "services" / "catalog"
COMPOSE = (
    "docker",
    "compose",
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.integration.yml",
    "-p",
    "catalog-int",
)
MARIADB_HOST_URL = "mariadb+pymysql://catalog:catalog@127.0.0.1:3310/catalog"


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*COMPOSE, *args],
        cwd=CATALOG_SERVICE,
        check=check,
        capture_output=True,
        text=True,
    )


def wait_for_healthy(timeout_s: float = 120.0) -> None:
    import pymysql

    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            conn = pymysql.connect(
                host="127.0.0.1",
                port=3310,
                user="catalog",
                password="catalog",
                database="catalog",
            )
            conn.close()
            return
        except Exception as exc:  # noqa: BLE001 — sonde de disponibilité
            last_error = exc
            time.sleep(2)
    raise TimeoutError(f"catalog-db injoignable sur 127.0.0.1:3310 : {last_error}")


def start_catalog_db() -> None:
    _run("up", "-d", "catalog-db")
    wait_for_healthy()


def stop_catalog_db() -> None:
    _run("down", "-v")
