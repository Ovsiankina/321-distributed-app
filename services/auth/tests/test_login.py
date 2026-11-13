import pytest

from conftest import SEED_PASSWORD, SEEDED_EMAIL, bearer, decode, login, register
from gateway_openapi import assert_matches_gateway_schema

LOGIN_PATH = "/api/auth/login"


def test_seeded_creator_can_log_in(client):
    response = login(client, email=SEEDED_EMAIL, password=SEED_PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == SEEDED_EMAIL
    assert_matches_gateway_schema(body, LOGIN_PATH, "post", "200")


def test_login_returns_a_token_for_the_registered_user(client):
    registered = register(client).json()
    response = login(client, email="ALICE@example.com")
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"
    me = client.get("/api/auth/me", headers=bearer(response.json()["token"])).json()
    assert decode(response.json()["token"])["sub"] == str(me["id"])
    assert decode(registered["token"])["sub"] == str(me["id"])


def test_unknown_email_and_wrong_password_get_identical_responses(client):
    register(client)
    unknown = login(client, email="inconnu@example.com")
    wrong = login(client, password="mauvais-mot-de-passe")
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.content == wrong.content
    assert wrong.json() == {"detail": "Identifiants incorrects"}
    assert_matches_gateway_schema(wrong.json(), LOGIN_PATH, "post", "401")


def test_unknown_email_still_verifies_a_hash(client, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.auth.verify_dummy_password",
        lambda password: calls.append(password),
    )
    register(client)
    login(client, password="mauvais-mot-de-passe")
    assert calls == []
    login(client, email="inconnu@example.com", password="essai")
    assert calls == ["essai"]


def test_login_does_not_check_the_email_format(client):
    response = login(client, email="pas-un-email")
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("payload", "detail"),
    [
        ({"email": "alice@example.com"}, "Mot de passe invalide"),
        ({"password": "secret12"}, "Email invalide"),
        (
            {"email": "alice@example.com", "password": "x" * 129},
            "Mot de passe invalide",
        ),
        (
            {"email": "alice@example.com", "password": "secret12", "x": 1},
            "Requête invalide",
        ),
    ],
)
def test_malformed_body_returns_400(client, payload, detail):
    response = client.post(LOGIN_PATH, json=payload)
    assert response.status_code == 400
    assert response.json() == {"detail": detail}
    assert_matches_gateway_schema(response.json(), LOGIN_PATH, "post", "400")


@pytest.mark.parametrize(
    "content",
    [b"{pas du json", b'{"email": "\xff@x.ch", "password": "abcdef"}'],
)
def test_unreadable_body_returns_400(client, content):
    response = client.post(
        LOGIN_PATH,
        content=content,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Requête invalide"}


def test_unreadable_password_hash_is_a_failed_login(client):
    from app.db import SessionLocal
    from app.models import User

    register(client)
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == "alice@example.com").update(
            {"password_hash": "pas un hash argon2"}
        )
        db.commit()
    finally:
        db.close()
    for _ in range(10):
        response = login(client)
        assert response.status_code == 401
        assert response.json() == {"detail": "Identifiants incorrects"}
    # Ces échecs sont comptés comme les autres.
    assert login(client).status_code == 429
