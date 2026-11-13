from app.passwords import hash_password, verify_password


def test_verify_accepts_the_right_password():
    assert verify_password(hash_password("un mot de passe"), "un mot de passe") is True


def test_verify_rejects_a_wrong_password():
    assert verify_password(hash_password("un mot de passe"), "un autre") is False


def test_same_password_gives_different_hashes():
    assert hash_password("un mot de passe") != hash_password("un mot de passe")


def test_hash_uses_owasp_argon2id_parameters():
    assert hash_password("un mot de passe").startswith(
        "$argon2id$v=19$m=19456,t=2,p=1$"
    )


def test_unreadable_hash_is_rejected_without_raising():
    assert verify_password("pas un hash", "un mot de passe") is False
    assert verify_password("$argon2id$v=19$m=19456,t=2,p=1$abc$def", "x") is False
