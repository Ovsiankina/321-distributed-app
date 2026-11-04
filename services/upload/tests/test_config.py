import pytest

from app.config import ConfigError, catalog_timeout_seconds
from app.main import prepare_runtime


def test_catalog_timeout_rejects_non_numeric(monkeypatch):
    monkeypatch.setenv("UPLOAD_CATALOG_TIMEOUT_SECONDS", "abc")
    with pytest.raises(ConfigError, match="UPLOAD_CATALOG_TIMEOUT_SECONDS"):
        catalog_timeout_seconds()


def test_catalog_timeout_rejects_non_positive(monkeypatch):
    monkeypatch.setenv("UPLOAD_CATALOG_TIMEOUT_SECONDS", "0")
    with pytest.raises(ConfigError, match="UPLOAD_CATALOG_TIMEOUT_SECONDS"):
        catalog_timeout_seconds()


def test_prepare_runtime_rejects_invalid_catalog_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_DATA_DIR", str(tmp_path / "incoming"))
    monkeypatch.setenv("UPLOAD_CATALOG_TIMEOUT_SECONDS", "abc")
    with pytest.raises(ConfigError, match="UPLOAD_CATALOG_TIMEOUT_SECONDS"):
        prepare_runtime()
