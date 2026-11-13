from email_validator import validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        email = normalize_email(value)
        # test_environment accepte les domaines .test des tests d'intégration.
        # Les domaines réservés comme .local restent refusés : seul le seed les utilise.
        validate_email(email, check_deliverability=False, test_environment=True)
        return email


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
