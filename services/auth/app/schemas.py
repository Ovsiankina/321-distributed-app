from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validated_email(value: str) -> str:
    # test_environment accepte les domaines .test des tests d'intégration.
    # Les domaines réservés comme .local restent refusés : seul le seed les utilise.
    result = validate_email(
        value.strip().lower(), check_deliverability=False, test_environment=True
    )
    # Forme normalisée : domaine IDNA (UTS-46), partie locale en NFC. Deux écritures
    # d'une même adresse donnent la même chaîne.
    return result.normalized


def normalize_email(value: str) -> str:
    """Email tel qu'il est stocké et comparé, à l'inscription, au login et au seed."""
    try:
        return _validated_email(value)
    except EmailNotValidError:
        # Le login ne contrôle pas le format, et validate_email refuse les adresses
        # .local des créateurs seedés.
        return value.strip().lower()


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        return _validated_email(value)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Pas de contrôle de format : les comptes seedés sont en .local.
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class TokenResponse(BaseModel):
    token: str
    email: str
    expires_in_hours: int


class UserResponse(BaseModel):
    id: int
    email: str
