from unittest.mock import patch

import pytest

from app.services import auth_service
from app.services.session_service import create_reset_token


async def _create_user_and_token(db_session, email, password="password123"):
    """Helper: create user and return (user, token)."""
    user = await auth_service.create_user(db_session, email, password)
    token = create_reset_token(user.email, user.password_hash)
    return user, token


@pytest.mark.asyncio
async def test_forgot_password_page_returns_200(client):
    response = await client.get("/auth/forgot-password")
    assert response.status_code == 200
    assert "Mot de passe oublié" in response.text


@pytest.mark.asyncio
async def test_forgot_password_known_email_shows_link(client, db_session):
    await auth_service.create_user(db_session, "reset@example.com", "password123")
    response = await client.post(
        "/auth/forgot-password",
        data={"email": "reset@example.com"},
    )
    assert response.status_code == 200
    assert "lien de réinitialisation" in response.text
    assert "/auth/reset-password/" in response.text


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_same_message(client, db_session):
    response = await client.post(
        "/auth/forgot-password",
        data={"email": "unknown@example.com"},
    )
    assert response.status_code == 200
    assert "Si un compte existe" in response.text
    # Should NOT contain a reset link
    assert "/auth/reset-password/" not in response.text


@pytest.mark.asyncio
async def test_reset_password_page_valid_token(client, db_session):
    _, token = await _create_user_and_token(db_session, "valid@example.com")
    response = await client.get(f"/auth/reset-password/{token}")
    assert response.status_code == 200
    assert "Nouveau mot de passe" in response.text


@pytest.mark.asyncio
async def test_reset_password_page_invalid_token(client, db_session):
    response = await client.get("/auth/reset-password/invalid-token-here")
    assert response.status_code == 200
    assert "invalide ou a expiré" in response.text
    assert "Demander un nouveau lien" in response.text


@pytest.mark.asyncio
async def test_reset_password_success(client, db_session):
    _, token = await _create_user_and_token(db_session, "success@example.com", "oldpassword123")
    response = await client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword456", "password_confirm": "newpassword456"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]
    assert "flash" in response.cookies


@pytest.mark.asyncio
async def test_reset_password_success_shows_message(client, db_session):
    _, token = await _create_user_and_token(db_session, "msg@example.com", "oldpassword123")
    response = await client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword456", "password_confirm": "newpassword456"},
        follow_redirects=True,
    )
    assert "réinitialisé avec succès" in response.text


@pytest.mark.asyncio
async def test_reset_password_updates_hash(client, db_session):
    _, token = await _create_user_and_token(db_session, "hash@example.com", "oldpassword123")
    await client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword456", "password_confirm": "newpassword456"},
        follow_redirects=False,
    )
    # New password works
    user = await auth_service.get_user_by_email(db_session, "hash@example.com")
    assert user is not None
    assert auth_service.verify_password("newpassword456", user.password_hash)


@pytest.mark.asyncio
async def test_reset_password_old_password_invalid(client, db_session):
    _, token = await _create_user_and_token(db_session, "old@example.com", "oldpassword123")
    await client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword456", "password_confirm": "newpassword456"},
        follow_redirects=False,
    )
    # Old password no longer works
    user = await auth_service.get_user_by_email(db_session, "old@example.com")
    assert not auth_service.verify_password("oldpassword123", user.password_hash)


@pytest.mark.asyncio
async def test_reset_password_short_password_error(client, db_session):
    _, token = await _create_user_and_token(db_session, "short@example.com")
    response = await client.post(
        f"/auth/reset-password/{token}",
        data={"password": "1234567", "password_confirm": "1234567"},
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "8 caractères" in response.text


@pytest.mark.asyncio
async def test_reset_password_mismatch_error(client, db_session):
    _, token = await _create_user_and_token(db_session, "mismatch@example.com")
    response = await client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword456", "password_confirm": "different456"},
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "correspondent pas" in response.text


@pytest.mark.asyncio
async def test_login_page_has_forgot_password_link(client):
    response = await client.get("/auth/login")
    assert "Mot de passe oublié" in response.text
    assert "/auth/forgot-password" in response.text


# --- Token invalidation tests ---


@pytest.mark.asyncio
async def test_reset_token_invalid_after_use(client, db_session):
    """Token cannot be reused after a successful password reset."""
    _, token = await _create_user_and_token(db_session, "reuse@example.com", "oldpassword123")
    # First reset succeeds
    response = await client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword456", "password_confirm": "newpassword456"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    # Second reset with same token fails (password hash changed → fingerprint mismatch)
    response = await client.get(f"/auth/reset-password/{token}")
    assert "invalide ou a expiré" in response.text


@pytest.mark.asyncio
async def test_reset_token_expired(client, db_session):
    """Expired token shows error message."""
    _, token = await _create_user_and_token(db_session, "expired@example.com")
    with patch(
        "app.services.session_service._serializer.loads",
        side_effect=Exception("token expired"),
    ):
        response = await client.get(f"/auth/reset-password/{token}")
    assert response.status_code == 200
    assert "invalide ou a expiré" in response.text
