import pytest

from app import config


def test_listen_port_default(monkeypatch):
    monkeypatch.delenv("GATEWAY_PORT", raising=False)
    assert config.listen_port() == 8000


def test_listen_port_invalid(monkeypatch):
    monkeypatch.setenv("GATEWAY_PORT", "nope")
    with pytest.raises(ValueError):
        config.listen_port()
