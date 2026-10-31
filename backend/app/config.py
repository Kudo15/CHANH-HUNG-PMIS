from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")
    database_url: SecretStr | None = None

    # OIDC configuration (provider-neutral, externalized)
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: SecretStr | None = None
    oidc_authorization_endpoint: str | None = None
    oidc_token_endpoint: str | None = None
    oidc_jwks_uri: str | None = None
    oidc_allowed_algorithms: list[str] = ["RS256"]
    oidc_redirect_uri: str = "http://127.0.0.1:8000/api/v1/auth/callback"
    oidc_timeout_seconds: float = 10.0

    # Server-managed session configuration (locked to approved policy values for local first slice)
    session_cookie_name: str = "pmis_session"
    session_cookie_secure: bool = True  # Mandatory Secure=True in every runtime per approved policy
    session_cookie_samesite: Literal["lax"] = "lax"  # Mandatory SameSite=Lax per approved policy
    session_idle_timeout_minutes: int = 30  # Mandatory 30-minute idle timeout
    session_absolute_timeout_hours: int = 12  # Mandatory 12-hour absolute timeout
    csrf_cookie_name: str = "pmis_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    @field_validator("session_cookie_secure")
    @classmethod
    def require_secure_cookies(cls, value: bool) -> bool:
        if not value:
            raise ValueError(
                "session_cookie_secure must be True; "
                "downgrade is forbidden per approved security policy"
            )
        return True

    @field_validator("session_cookie_samesite")
    @classmethod
    def require_lax_samesite(cls, value: str) -> str:
        if value != "lax":
            raise ValueError("session_cookie_samesite must be 'lax' per approved security policy")
        return "lax"

    @field_validator("session_idle_timeout_minutes")
    @classmethod
    def require_30m_idle(cls, value: int) -> int:
        if value != 30:
            raise ValueError("session_idle_timeout_minutes must be 30 per approved security policy")
        return 30

    @field_validator("session_absolute_timeout_hours")
    @classmethod
    def require_12h_absolute(cls, value: int) -> int:
        if value != 12:
            raise ValueError(
                "session_absolute_timeout_hours must be 12 per approved security policy"
            )
        return 12

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            try:
                driver = make_url(value.get_secret_value()).drivername
            except Exception:
                raise ValueError("DATABASE_URL must be a PostgreSQL psycopg URL") from None
            if driver != "postgresql+psycopg":
                raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value
