import json

from conftest import FULL_FIXTURES, SEED_PASSWORD, login, register


def _users():
    from app.db import SessionLocal
    from app.models import User

    db = SessionLocal()
    try:
        return {user.email: user for user in db.query(User).all()}
    finally:
        db.close()


def _seed(path=None):
    from app.db import SessionLocal
    from app.seed import seed_users

    db = SessionLocal()
    try:
        seed_users(db, path)
    finally:
        db.close()


def _write_fixture(tmp_path, users):
    path = tmp_path / "users.json"
    path.write_text(
        json.dumps({"default_password": "autre-mot-de-passe", "users": users}),
        encoding="utf-8",
    )
    return path


def test_full_fixture_seeds_the_eight_creators(full_client):
    fixture = json.loads((FULL_FIXTURES / "users.json").read_text(encoding="utf-8"))
    users = _users()
    assert {email: user.channel_id for email, user in users.items()} == {
        entry["email"]: entry["channel_id"] for entry in fixture["users"]
    }
    first = fixture["users"][0]["email"]
    assert (
        login(
            full_client, email=first, password=fixture["default_password"]
        ).status_code
        == 200
    )


def test_seed_normalizes_emails(client):
    assert "autre.createur@stream321.local" in _users()
    response = login(
        client, email="Autre.Createur@stream321.local", password=SEED_PASSWORD
    )
    assert response.status_code == 200


def test_seeded_accounts_get_distinct_salts(client):
    hashes = [user.password_hash for user in _users().values()]
    assert len(set(hashes)) == len(hashes)


def test_seed_is_idempotent_and_keeps_password_hashes(client):
    before = {email: user.password_hash for email, user in _users().items()}
    _seed()
    after = {email: user.password_hash for email, user in _users().items()}
    assert after == before


def test_seed_updates_the_channel_id_of_an_existing_creator(client, tmp_path):
    _seed(
        _write_fixture(
            tmp_path, [{"email": "createur@stream321.local", "channel_id": "UCnouveau"}]
        )
    )
    users = _users()
    assert users["createur@stream321.local"].channel_id == "UCnouveau"
    # Le mot de passe n'est pas réécrit avec le nouveau mot de passe par défaut.
    assert (
        login(
            client, email="createur@stream321.local", password=SEED_PASSWORD
        ).status_code
        == 200
    )


def test_seed_never_deletes_accounts(client, tmp_path):
    register(client)
    _seed(_write_fixture(tmp_path, []))
    assert {"alice@example.com", "createur@stream321.local"} <= set(_users())
