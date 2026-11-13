import pytest

from conftest import login, register
from gateway_openapi import assert_matches_gateway_schema

REGISTER_PATH = "/api/auth/register"


def test_register_returns_a_token_and_never_the_hash(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"token", "email", "expires_in_hours"}
    assert body["email"] == "alice@example.com"
    assert body["expires_in_hours"] == 1
    assert "argon2" not in response.text
    assert_matches_gateway_schema(body, REGISTER_PATH, "post", "201")


def test_register_stores_an_argon2id_hash(client):
    from app.db import SessionLocal
    from app.models import User

    register(client, password="secret12")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "alice@example.com").one()
    finally:
        db.close()
    assert user.password_hash.startswith("$argon2id$")
    assert "secret12" not in user.password_hash
    assert user.channel_id is None


def test_register_normalizes_the_email(client):
    response = register(client, email="  Alice@Example.COM ")
    assert response.status_code == 201
    assert response.json()["email"] == "alice@example.com"


@pytest.mark.parametrize("second_email", ["alice@example.com", "ALICE@example.com"])
def test_duplicate_email_returns_409(client, second_email):
    assert register(client).status_code == 201
    response = register(client, email=second_email)
    assert response.status_code == 409
    assert response.json() == {"detail": "Cet email est déjà utilisé"}
    assert_matches_gateway_schema(response.json(), REGISTER_PATH, "post", "409")


@pytest.mark.parametrize(
    ("password", "status"),
    [("12345", 400), ("123456", 201), ("x" * 128, 201), ("x" * 129, 400)],
)
def test_password_length_bounds(client, password, status):
    response = register(client, password=password)
    assert response.status_code == status
    if status == 400:
        assert response.json() == {"detail": "Mot de passe invalide"}


@pytest.mark.parametrize(
    "email",
    ["pas-un-email", "alice@example", "alice@stream321.local", 12345],
)
def test_invalid_email_returns_400(client, email):
    response = client.post(REGISTER_PATH, json={"email": email, "password": "secret12"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Email invalide"}
    assert_matches_gateway_schema(response.json(), REGISTER_PATH, "post", "400")


def test_example_test_domain_is_accepted(client):
    # tests/integration/http_env.py inscrit des adresses en @example.test.
    assert register(client, email="integration-abc123@example.test").status_code == 201


def test_missing_password_returns_400(client):
    response = client.post(REGISTER_PATH, json={"email": "alice@example.com"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Mot de passe invalide"}


def test_unknown_field_returns_400(client):
    response = client.post(
        REGISTER_PATH,
        json={"email": "alice@example.com", "password": "secret12", "displayName": "A"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Requête invalide"}


@pytest.mark.parametrize(
    "content",
    [
        b"{pas du json",
        b'["alice@example.com"]',
        b"",
        # Pas de l'UTF-8 valide : FastAPI lève une HTTPException en anglais.
        b'{"email": "\xff@x.ch", "password": "secret12"}',
    ],
)
def test_unreadable_body_returns_400(client, content):
    response = client.post(
        REGISTER_PATH, content=content, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Requête invalide"}


@pytest.mark.parametrize(
    ("first", "second"),
    [
        # Domaine en caractères pleine chasse : IDNA le ramène à example.com.
        ("alice@example.com", "alice@\uff45xample.com"),
        # « é » précomposé (NFC) puis « e » suivi de l'accent combinant (NFD).
        ("jos\u00e9@example.com", "jose\u0301@example.com"),
    ],
)
def test_two_spellings_of_one_address_are_one_account(client, first, second):
    assert register(client, email=first).status_code == 201
    assert register(client, email=second).status_code == 409
    assert login(client, email=second).status_code == 200
