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


def test_empty_fixtures_dir_falls_back_to_the_default(config, monkeypatch):
    monkeypatch.setenv("AUTH_FIXTURES_DIR", "")
    assert config.load_settings().fixtures_dir == config.SERVICE_ROOT / "fixtures"


def test_database_password_is_added_without_parsing(config, monkeypatch):
    monkeypatch.setenv("AUTH_DATABASE_URL", "mariadb+pymysql://auth@auth-db:3306/auth")
    monkeypatch.setenv("AUTH_DB_PASSWORD", "p@ss:w/rd#%")
    url = config.load_settings().database_url
    assert (url.username, url.password, url.host, url.port, url.database) == (
        "auth",
        "p@ss:w/rd#%",
        "auth-db",
        3306,
        "auth",
    )


def test_unreadable_database_url_is_rejected(config, monkeypatch):
    monkeypatch.setenv("AUTH_DATABASE_URL", "pas une url")
    with pytest.raises(config.ConfigError, match="AUTH_DATABASE_URL"):
        config.load_settings()


def test_service_refuses_to_start_without_a_key(auth_env, monkeypatch):
    monkeypatch.delenv("AUTH_JWT_PRIVATE_KEY")
    with pytest.raises(ValueError, match="AUTH_JWT_PRIVATE_KEY"):
        importlib.import_module("app.main")
