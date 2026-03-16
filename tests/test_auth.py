import pytest

from app.models.user import User
from app.services.auth_service import verify_password
from app.services.session_service import SESSION_COOKIE_NAME, get_user_id_from_cookie


@pytest.mark.asyncio
async def test_register_page_returns_200(client):
    response = await client.get("/auth/register")
    assert response.status_code == 200
    assert "Créer un compte" in response.text


@pytest.mark.asyncio
async def test_register_page_contains_form(client):
    response = await client.get("/auth/register")
    assert 'hx-post="/auth/register"' in response.text
    assert 'name="email"' in response.text
    assert 'name="password"' in response.text
    assert 'name="password_confirm"' in response.text


@pytest.mark.asyncio
async def test_register_success_redirects(client, db_session):
    response = await client.post(
        "/auth/register",
        data={"email": "test@example.com", "password": "password123", "password_confirm": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"


@pytest.mark.asyncio
async def test_register_success_sets_session_cookie(client, db_session):
    response = await client.post(
        "/auth/register",
        data={"email": "cookie@example.com", "password": "password123", "password_confirm": "password123"},
        follow_redirects=False,
    )
    assert SESSION_COOKIE_NAME in response.cookies
    cookie_value = response.cookies[SESSION_COOKIE_NAME]
    user_id = get_user_id_from_cookie(cookie_value)
    assert user_id is not None


@pytest.mark.asyncio
async def test_register_success_creates_user_in_db(client, db_session):
    await client.post(
        "/auth/register",
        data={"email": "dbuser@example.com", "password": "password123", "password_confirm": "password123"},
        follow_redirects=False,
    )
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "dbuser@example.com"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == "dbuser@example.com"


@pytest.mark.asyncio
async def test_register_password_is_hashed(client, db_session):
    await client.post(
        "/auth/register",
        data={"email": "hash@example.com", "password": "password123", "password_confirm": "password123"},
        follow_redirects=False,
    )
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "hash@example.com"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.password_hash != "password123"
    assert verify_password("password123", user.password_hash)


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_422(client, db_session):
    # Create first user
    await client.post(
        "/auth/register",
        data={"email": "dup@example.com", "password": "password123", "password_confirm": "password123"},
        follow_redirects=False,
    )
    # Try duplicate
    response = await client.post(
        "/auth/register",
        data={"email": "dup@example.com", "password": "password123", "password_confirm": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "existe déjà" in response.text


@pytest.mark.asyncio
async def test_register_short_password_returns_error(client):
    response = await client.post(
        "/auth/register",
        data={"email": "short@example.com", "password": "1234567", "password_confirm": "1234567"},
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "8 caractères" in response.text


@pytest.mark.asyncio
async def test_register_password_mismatch_returns_error(client):
    response = await client.post(
        "/auth/register",
        data={"email": "mismatch@example.com", "password": "password123", "password_confirm": "different123"},
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "correspondent pas" in response.text


@pytest.mark.asyncio
async def test_register_hx_redirect_header(client, db_session):
    response = await client.post(
        "/auth/register",
        data={"email": "hx@example.com", "password": "password123", "password_confirm": "password123"},
        follow_redirects=False,
    )
    assert response.headers.get("hx-redirect") == "/"
