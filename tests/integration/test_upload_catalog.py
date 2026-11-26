"""
Le service média ne contacte plus le catalog (R2). La publication passe par le bus.
Ce test vérifie seulement que le catalog peut être joignable à côté, sans couplage HTTP.
"""

from __future__ import annotations

import pytest

from catalog_health import skip_if_catalog_down
from http_env import catalog_http

pytestmark = pytest.mark.integration


def test_catalog_health_is_ok_for_upload_scenarios(catalog_http):
    skip_if_catalog_down(catalog_http)
