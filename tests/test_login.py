import pytest

from app.services import auth_service
from app.services.session_service import SESSION_COOKIE_NAME, get_user_id_from_cookie


@pytest.mark.asyncio
async def test_login_page_returns_200(client):
    response = await client.get("/auth/login")
    assert response.status_code == 200
    assert "Se connecter" in response.text


@pytest.mark.asyncio
async def test_login_page_contains_form(client):
    response = await client.get("/auth/login")
    assert 'hx-post="/auth/login"' in response.text
    assert 'name="email"' in response.text
    assert 'name="password"' in response.text


@pytest.mark.asyncio
async def test_login_success_redirects(client, db_session):
    await auth_service.create_user(db_session, "login@example.com", "password123")
    response = await client.post(
        "/auth/login",
        data={"email": "login@example.com", "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"


@pytest.mark.asyncio
async def test_login_success_sets_session_cookie(client, db_session):
    await auth_service.create_user(db_session, "cookie@example.com", "password123")
    response = await client.post(
        "/auth/login",
        data={"email": "cookie@example.com", "password": "password123"},
        follow_redirects=False,
    )
    assert SESSION_COOKIE_NAME in response.cookies
    user_id = get_user_id_from_cookie(response.cookies[SESSION_COOKIE_NAME])
    assert user_id is not None


@pytest.mark.asyncio
async def test_login_success_hx_redirect(client, db_session):
    await auth_service.create_user(db_session, "hx@example.com", "password123")
    response = await client.post(
        "/auth/login",
        data={"email": "hx@example.com", "password": "password123"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("hx-redirect") == "/"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_422(client, db_session):
    await auth_service.create_user(db_session, "wrong@example.com", "password123")
    response = await client.post(
        "/auth/login",
        data={"email": "wrong@example.com", "password": "wrongpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "incorrect" in response.text


@pytest.mark.asyncio
async def test_login_unknown_email_returns_422(client, db_session):
    response = await client.post(
        "/auth/login",
        data={"email": "unknown@example.com", "password": "password123"},
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "incorrect" in response.text


@pytest.mark.asyncio
async def test_login_generic_error_message(client, db_session):
    """Error message should be the same for unknown email and wrong password."""
    await auth_service.create_user(db_session, "generic@example.com", "password123")

    # Wrong password
    r1 = await client.post(
        "/auth/login",
        data={"email": "generic@example.com", "password": "wrong"},
        follow_redirects=False,
    )
    # Unknown email
    r2 = await client.post(
        "/auth/login",
        data={"email": "noexist@example.com", "password": "password123"},
        follow_redirects=False,
    )
    # Both should show the same generic message
    assert "Email ou mot de passe incorrect" in r1.text
    assert "Email ou mot de passe incorrect" in r2.text


@pytest.mark.asyncio
async def test_logout_clears_cookie(authenticated_client):
    response = await authenticated_client.post("/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"
    # Cookie should be deleted (max-age=0 or removed)
    assert SESSION_COOKIE_NAME in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_logout_hx_redirect(authenticated_client):
    response = await authenticated_client.post(
        "/auth/logout", headers={"HX-Request": "true"}, follow_redirects=False
    )
    assert response.status_code == 200
    assert response.headers.get("hx-redirect") == "/auth/login"


@pytest.mark.asyncio
async def test_protected_route_redirects_unauthenticated(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


@pytest.mark.asyncio
async def test_stats_redirects_unauthenticated(client):
    response = await client.get("/stats", follow_redirects=False)
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_protected_route_works_authenticated(authenticated_client):
    response = await authenticated_client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_htmx_request_gets_hx_redirect_header(client):
    response = await client.get(
        "/",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.headers.get("hx-redirect") == "/auth/login"
