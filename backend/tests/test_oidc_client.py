import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from app.auth.oidc import DefaultOIDCClient
from app.config import Settings


def make_settings(
    token_endpoint: str | None = "https://idp.example.com/oauth/token",
    client_id: str | None = "pmis-client",
    client_secret: str | None = "super-secret-key-12345",
    timeout: float = 5.0,
) -> Settings:
    return Settings(
        database_url=None,
        oidc_token_endpoint=token_endpoint,
        oidc_client_id=client_id,
        oidc_client_secret=SecretStr(client_secret) if client_secret else None,
        oidc_timeout_seconds=timeout,
        session_cookie_secure=True,
    )


def test_exchange_code_success():
    settings = make_settings()
    client = DefaultOIDCClient(settings)

    mock_response_data = {
        "access_token": "mock-access-token-999",
        "token_type": "Bearer",
        "id_token": "mock-id-token.jwt.signature",
        "expires_in": 300,
    }
    raw_response = json.dumps(mock_response_data).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = raw_response
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = client.exchange_code(
            code="test-auth-code-xyz",
            redirect_uri="http://127.0.0.1:8000/api/v1/auth/callback",
        )

        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://idp.example.com/oauth/token"
        assert req.get_method() == "POST"
        assert req.headers["Content-type"] == "application/x-www-form-urlencoded"

        body = req.data.decode("utf-8")
        assert "grant_type=authorization_code" in body
        assert "code=test-auth-code-xyz" in body
        assert "client_id=pmis-client" in body
        assert "client_secret=super-secret-key-12345" in body

        assert result["id_token"] == "mock-id-token.jwt.signature"
        assert result["access_token"] == "mock-access-token-999"


def test_exchange_code_missing_configuration():
    # Missing token endpoint
    settings_no_endpoint = make_settings(token_endpoint=None)
    client_no_endpoint = DefaultOIDCClient(settings_no_endpoint)
    with pytest.raises(HTTPException) as exc_info:
        client_no_endpoint.exchange_code("code", "http://127.0.0.1:8000/callback")
    assert exc_info.value.status_code == 500

    # Missing client id
    settings_no_client = make_settings(client_id=None)
    client_no_client = DefaultOIDCClient(settings_no_client)
    with pytest.raises(HTTPException) as exc_info:
        client_no_client.exchange_code("code", "http://127.0.0.1:8000/callback")
    assert exc_info.value.status_code == 500


def test_exchange_code_provider_http_error():
    settings = make_settings()
    client = DefaultOIDCClient(settings)

    err = urllib.error.HTTPError(
        url="https://idp.example.com/oauth/token",
        code=400,
        msg="Bad Request",
        hdrs={},  # type: ignore
        fp=io.BytesIO(b'{"error":"invalid_grant","error_description":"Code expired"}'),
    )

    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(HTTPException) as exc_info:
            client.exchange_code("test-auth-code-xyz", "http://127.0.0.1:8000/callback")
        assert exc_info.value.status_code == 400
        # Verify no credentials leaked
        assert "super-secret-key-12345" not in str(exc_info.value.detail)
        assert "test-auth-code-xyz" not in str(exc_info.value.detail)


def test_exchange_code_malformed_json():
    settings = make_settings()
    client = DefaultOIDCClient(settings)

    mock_resp = MagicMock()
    mock_resp.read.return_value = b"<html>Service Unavailable</html>"
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(HTTPException) as exc_info:
            client.exchange_code("code-123", "http://127.0.0.1:8000/callback")
        assert exc_info.value.status_code == 502
        assert "super-secret-key-12345" not in str(exc_info.value.detail)


def test_exchange_code_missing_id_token():
    settings = make_settings()
    client = DefaultOIDCClient(settings)

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"access_token": "abc"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(HTTPException) as exc_info:
            client.exchange_code("code-123", "http://127.0.0.1:8000/callback")
        assert exc_info.value.status_code in (400, 502)
        assert "id_token" in str(exc_info.value.detail).lower()


def test_exchange_code_redacts_secrets_on_network_error():
    settings = make_settings()
    client = DefaultOIDCClient(settings)

    url_err = urllib.error.URLError("Connection refused to https://idp.example.com/oauth/token")
    with patch("urllib.request.urlopen", side_effect=url_err):
        with pytest.raises(HTTPException) as exc_info:
            client.exchange_code("code-sensitive-data", "http://127.0.0.1:8000/callback")
        assert exc_info.value.status_code == 502
        assert "code-sensitive-data" not in str(exc_info.value.detail)
        assert "super-secret-key-12345" not in str(exc_info.value.detail)


def test_local_oidc_config_and_realm_credential_safety():
    """Verify that realm.json, compose.yaml, and .env.example do not contain

    static secrets, and that per-run credentials are required without fallback defaults.
    """
    repo_root = Path(__file__).resolve().parents[2]

    # 1. Inspect dev/keycloak/realm.json
    realm_path = repo_root / "dev" / "keycloak" / "realm.json"
    assert realm_path.is_file(), "dev/keycloak/realm.json must exist"
    realm_text = realm_path.read_text(encoding="utf-8")
    assert "synthetic-client-secret-local-dev-only" not in realm_text, (
        "realm.json must not commit static client secret"
    )
    assert "synthetic-pass-1" not in realm_text, (
        "realm.json must not commit synthetic user password 1"
    )
    assert "synthetic-pass-2" not in realm_text, (
        "realm.json must not commit synthetic user password 2"
    )

    realm_data = json.loads(realm_text)
    client = next(c for c in realm_data.get("clients", []) if c.get("clientId") == "pmis-local")
    assert client.get("secret") == "${OIDC_CLIENT_SECRET}", (
        "Client secret must be dynamic placeholder ${OIDC_CLIENT_SECRET}"
    )

    user1 = next(u for u in realm_data.get("users", []) if u.get("username") == "synthetic-admin-1")
    assert user1["credentials"][0]["value"] == "${KC_SYNTHETIC_ADMIN1_PASSWORD}", (
        "synthetic-admin-1 password must be placeholder ${KC_SYNTHETIC_ADMIN1_PASSWORD}"
    )
    user2 = next(u for u in realm_data.get("users", []) if u.get("username") == "synthetic-admin-2")
    assert user2["credentials"][0]["value"] == "${KC_SYNTHETIC_ADMIN2_PASSWORD}", (
        "synthetic-admin-2 password must be placeholder ${KC_SYNTHETIC_ADMIN2_PASSWORD}"
    )

    # 2. Inspect compose.yaml
    compose_path = repo_root / "compose.yaml"
    assert compose_path.is_file(), "compose.yaml must exist"
    compose_text = compose_path.read_text(encoding="utf-8")
    assert "admin_local_dev" not in compose_text, (
        "compose.yaml must not contain static default admin password"
    )
    assert "KC_BOOTSTRAP_ADMIN_PASSWORD:-" not in compose_text, (
        "compose.yaml must not provide fallback default for KC_BOOTSTRAP_ADMIN_PASSWORD"
    )
    assert "${KC_BOOTSTRAP_ADMIN_PASSWORD:?" in compose_text, (
        "compose.yaml must require explicit KC_BOOTSTRAP_ADMIN_PASSWORD per run"
    )
    assert "${OIDC_CLIENT_SECRET:?" in compose_text, (
        "compose.yaml must require explicit OIDC_CLIENT_SECRET per run"
    )
    assert "${KC_SYNTHETIC_ADMIN1_PASSWORD:?" in compose_text, (
        "compose.yaml must require explicit KC_SYNTHETIC_ADMIN1_PASSWORD per run"
    )
    assert "${KC_SYNTHETIC_ADMIN2_PASSWORD:?" in compose_text, (
        "compose.yaml must require explicit KC_SYNTHETIC_ADMIN2_PASSWORD per run"
    )

    # 3. Inspect .env.example
    env_example_path = repo_root / ".env.example"
    assert env_example_path.is_file(), ".env.example must exist"
    env_example_text = env_example_path.read_text(encoding="utf-8")
    assert "synthetic-client-secret-local-dev-only" not in env_example_text, (
        ".env.example must not contain static client secret"
    )
    assert "synthetic-pass-1" not in env_example_text
    assert "synthetic-pass-2" not in env_example_text
    assert "admin_local_dev" not in env_example_text
