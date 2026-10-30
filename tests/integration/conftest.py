import os
import subprocess

import pytest

from docker_catalog_db import MARIADB_HOST_URL, start_catalog_db, stop_catalog_db


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: nécessite Docker ou plusieurs microservices démarrés",
    )


@pytest.fixture(scope="session")
def integration_mariadb_url():
    if os.environ.get("SKIP_INTEGRATION_DOCKER") == "1":
        pytest.skip("SKIP_INTEGRATION_DOCKER=1")
    try:
        start_catalog_db()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        pytest.skip(f"Docker indisponible ou compose en échec : {exc}")
    yield MARIADB_HOST_URL
    stop_catalog_db()
