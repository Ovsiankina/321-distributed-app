import importlib

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from conftest import private_key_pem


@pytest.fixture
def config(auth_env):
    return importlib.import_module("app.config")


@pytest.mark.parametrize("name", ["AUTH_DATABASE_URL", "AUTH_JWT_PRIVATE_KEY"])
def test_missing_required_variable_is_rejected(config, monkeypatch, name):
    monkeypatch.delenv(name)
    with pytest.raises(config.ConfigError, match=name):
        config.load_settings()


def test_unreadable_private_key_is_rejected(config, monkeypatch):
    monkeypatch.setenv("AUTH_JWT_PRIVATE_KEY", "pas une clé")
    with pytest.raises(config.ConfigError, match="PEM"):
        config.load_settings()


def test_non_ed25519_key_is_rejected(config, monkeypatch):
    monkeypatch.setenv(
        "AUTH_JWT_PRIVATE_KEY", private_key_pem(ec.generate_private_key(ec.SECP256R1()))
    )
    with pytest.raises(config.ConfigError, match="Ed25519"):
        config.load_settings()


@pytest.mark.parametrize("value", ["abc", "0", "-1"])
def test_invalid_lifetime_is_rejected(config, monkeypatch, value):
    monkeypatch.setenv("AUTH_TOKEN_TTL_HOURS", value)
    with pytest.raises(config.ConfigError, match="AUTH_TOKEN_TTL_HOURS"):
        config.load_settings()


def test_defaults(config):
    settings = config.load_settings()
    assert settings.jwt_issuer == "stream321-auth"
    assert settings.jwt_audience == "stream321-api"
    assert settings.token_ttl_hours == 1


def test_service_refuses_to_start_without_a_key(auth_env, monkeypatch):
    monkeypatch.delenv("AUTH_JWT_PRIVATE_KEY")
    with pytest.raises(ValueError, match="AUTH_JWT_PRIVATE_KEY"):
        importlib.import_module("app.main")
