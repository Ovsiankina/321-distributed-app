from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Configuration minimale recommandée par OWASP : 19 MiB, 2 itérations, parallélisme 1.
_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)

# Vérifié quand l'email est inconnu, pour que ce login dure autant qu'un mauvais
# mot de passe et ne révèle pas quels comptes existent.
_DUMMY_HASH = _hasher.hash("pas un vrai mot de passe")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(_DUMMY_HASH, password)
