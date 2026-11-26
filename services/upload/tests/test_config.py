import pytest

from app.config import ConfigError, max_upload_bytes


def test_max_upload_rejects_non_numeric(monkeypatch):
    monkeypatch.setenv("UPLOAD_MAX_BYTES", "abc")
    with pytest.raises(ConfigError, match="UPLOAD_MAX_BYTES"):
        max_upload_bytes()
