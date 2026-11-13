from conftest import login, register
from gateway_openapi import assert_matches_gateway_schema


def _fail(client, times, email="alice@example.com"):
    for _ in range(times):
        assert login(client, email=email, password="mauvais").status_code == 401


def test_eleventh_attempt_returns_429_without_hashing(client, monkeypatch):
    register(client)
    _fail(client, 10)

    def must_not_hash(*_args):
        raise AssertionError("un login bloqué ne doit pas hacher")

    monkeypatch.setattr("app.routers.auth.verify_password", must_not_hash)
    monkeypatch.setattr("app.routers.auth.verify_dummy_password", must_not_hash)
    # Même le bon mot de passe est refusé tant que la fenêtre court.
    response = login(client)
    assert response.status_code == 429
    assert response.json() == {"detail": "Trop de tentatives, réessayez plus tard"}
    assert 1 <= int(response.headers["Retry-After"]) <= 60
    assert_matches_gateway_schema(response.json(), "/api/auth/login", "post", "429")


def test_success_resets_the_counter(client):
    register(client)
    _fail(client, 9)
    assert login(client).status_code == 200
    _fail(client, 9)
    assert login(client).status_code == 200


def test_unknown_email_is_counted_like_a_known_one(client):
    _fail(client, 10, email="inconnu@example.com")
    assert login(client, email="inconnu@example.com").status_code == 429


def test_failures_on_one_email_do_not_block_another(client):
    register(client)
    register(client, email="bob@example.com")
    _fail(client, 10)
    assert login(client, email="bob@example.com").status_code == 200


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _limiter(clock):
    from app.rate_limit import LoginRateLimiter

    return LoginRateLimiter(max_failures=10, window_seconds=60, clock=clock)


def test_block_lasts_until_the_window_ends(auth_env):
    clock = FakeClock()
    limiter = _limiter(clock)
    for _ in range(10):
        limiter.record_failure("a@b.ch")
    assert limiter.retry_after("a@b.ch") == 60
    clock.now += 59.5
    assert limiter.retry_after("a@b.ch") == 1
    clock.now += 0.5
    assert limiter.retry_after("a@b.ch") == 0


def test_failures_in_two_windows_do_not_add_up(auth_env):
    clock = FakeClock()
    limiter = _limiter(clock)
    for _ in range(9):
        limiter.record_failure("a@b.ch")
    clock.now += 60
    for _ in range(9):
        limiter.record_failure("a@b.ch")
    assert limiter.retry_after("a@b.ch") == 0


def test_expired_entries_are_pruned(auth_env):
    clock = FakeClock()
    limiter = _limiter(clock)
    for index in range(100):
        limiter.record_failure(f"{index}@b.ch")
    clock.now += 60
    limiter.record_failure("dernier@b.ch")
    assert list(limiter._failures) == ["dernier@b.ch"]
