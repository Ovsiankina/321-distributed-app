import threading
import time
from concurrent.futures import ThreadPoolExecutor

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


def test_concurrent_failures_cannot_exceed_the_limit(client, monkeypatch):
    register(client)
    # Un hachage lent élargit la fenêtre entre le contrôle et le comptage : toutes les
    # requêtes passeraient le contrôle si le compteur avançait après le hachage.
    from app.passwords import verify_password

    def slow_verify(password_hash, password):
        time.sleep(0.05)
        return verify_password(password_hash, password)

    monkeypatch.setattr("app.routers.auth.verify_password", slow_verify)
    with ThreadPoolExecutor(max_workers=30) as pool:
        statuses = list(
            pool.map(lambda _: login(client, password="mauvais").status_code, range(30))
        )
    assert statuses.count(401) == 10
    assert statuses.count(429) == 20


def test_attempt_is_counted_before_hashing(client, monkeypatch):
    from app.passwords import verify_dummy_password
    from app.rate_limit import login_limiter

    counted = []

    def spy(password):
        counted.append(len(login_limiter._attempts["inconnu@example.com"]))
        verify_dummy_password(password)

    monkeypatch.setattr("app.routers.auth.verify_dummy_password", spy)
    login(client, email="inconnu@example.com")
    assert counted == [1]


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _limiter(clock):
    from app.rate_limit import LoginRateLimiter

    return LoginRateLimiter(max_attempts=10, window_seconds=60, clock=clock)


def _acquire(limiter, email, times):
    return [limiter.acquire(email) for _ in range(times)]


def test_block_lasts_until_the_window_ends(auth_env):
    clock = FakeClock()
    limiter = _limiter(clock)
    assert _acquire(limiter, "a@b.ch", 10) == [0] * 10
    assert limiter.acquire("a@b.ch") == 60
    clock.now += 59.5
    assert limiter.acquire("a@b.ch") == 1
    clock.now += 0.5
    assert limiter.acquire("a@b.ch") == 0


def test_attempts_in_two_windows_do_not_add_up(auth_env):
    clock = FakeClock()
    limiter = _limiter(clock)
    _acquire(limiter, "a@b.ch", 9)
    clock.now += 60
    assert _acquire(limiter, "a@b.ch", 10) == [0] * 10


def test_no_burst_across_the_window_boundary(auth_env):
    # Une fenêtre fixe laissait passer 19 essais en 0,1 s autour de sa fin.
    clock = FakeClock()
    limiter = _limiter(clock)
    limiter.acquire("a@b.ch")
    clock.now += 59.9
    assert _acquire(limiter, "a@b.ch", 9) == [0] * 9
    clock.now += 0.1
    # Seul le premier essai est sorti de la fenêtre : une seule place se libère.
    assert limiter.acquire("a@b.ch") == 0
    assert limiter.acquire("a@b.ch") == 60


def test_reset_frees_every_attempt(auth_env):
    limiter = _limiter(FakeClock())
    _acquire(limiter, "a@b.ch", 10)
    limiter.reset("a@b.ch")
    assert _acquire(limiter, "a@b.ch", 10) == [0] * 10


def test_concurrent_acquires_allow_exactly_the_limit(auth_env):
    limiter = _limiter(FakeClock())
    barrier = threading.Barrier(40)

    def attempt(_):
        barrier.wait()
        return limiter.acquire("a@b.ch")

    with ThreadPoolExecutor(max_workers=40) as pool:
        results = list(pool.map(attempt, range(40)))
    assert results.count(0) == 10


def test_expired_entries_are_pruned(auth_env):
    clock = FakeClock()
    limiter = _limiter(clock)
    for index in range(100):
        limiter.acquire(f"{index}@b.ch")
    clock.now += 60
    limiter.acquire("dernier@b.ch")
    assert list(limiter._attempts) == ["dernier@b.ch"]
