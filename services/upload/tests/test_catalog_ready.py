from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.catalog_client import ensure_catalog_ready


@patch("app.catalog_client.httpx.Client")
def test_ensure_catalog_ready_accepts_200_ok(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok", "service": "catalog"}
    mock_client.get.return_value = mock_response

    ensure_catalog_ready()


@patch("app.catalog_client.httpx.Client")
def test_ensure_catalog_ready_raises_503_on_non_200(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_client.get.return_value = mock_response

    with pytest.raises(HTTPException) as exc:
        ensure_catalog_ready()
    assert exc.value.status_code == 503
    assert exc.value.detail == "Catalog indisponible"


@patch("app.catalog_client.httpx.Client")
def test_ensure_catalog_ready_raises_503_on_connection_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_client.get.side_effect = httpx.ConnectError("refused")

    with pytest.raises(HTTPException) as exc:
        ensure_catalog_ready()
    assert exc.value.status_code == 503


@patch("app.catalog_client.httpx.Client")
def test_ensure_catalog_ready_raises_503_on_wrong_service_name(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok", "service": "other"}
    mock_client.get.return_value = mock_response

    with pytest.raises(HTTPException) as exc:
        ensure_catalog_ready()
    assert exc.value.status_code == 503
