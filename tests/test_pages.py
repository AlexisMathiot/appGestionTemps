import pytest


@pytest.mark.asyncio
async def test_home_returns_200(authenticated_client):
    response = await authenticated_client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_home_contains_html(authenticated_client):
    response = await authenticated_client.get("/")
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_home_contains_daisyui(authenticated_client):
    response = await authenticated_client.get("/")
    assert "daisyui" in response.text


@pytest.mark.asyncio
async def test_home_contains_htmx(authenticated_client):
    response = await authenticated_client.get("/")
    assert "htmx.org" in response.text


@pytest.mark.asyncio
async def test_home_contains_navbar(authenticated_client):
    response = await authenticated_client.get("/")
    assert "navbar" in response.text


@pytest.mark.asyncio
async def test_home_contains_theme(authenticated_client):
    response = await authenticated_client.get("/")
    assert "appgestiontemps" in response.text


@pytest.mark.asyncio
async def test_home_has_active_nav(authenticated_client):
    response = await authenticated_client.get("/")
    assert "text-primary" in response.text


@pytest.mark.asyncio
async def test_stats_returns_200(authenticated_client):
    response = await authenticated_client.get("/stats")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_stats_contains_placeholder(authenticated_client):
    response = await authenticated_client.get("/stats")
    assert "Statistiques" in response.text


@pytest.mark.asyncio
async def test_settings_returns_200(authenticated_client):
    response = await authenticated_client.get("/settings")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_settings_contains_placeholder(authenticated_client):
    response = await authenticated_client.get("/settings")
    assert "Param" in response.text


@pytest.mark.asyncio
async def test_prefers_reduced_motion_in_base(authenticated_client):
    response = await authenticated_client.get("/")
    assert "prefers-reduced-motion" in response.text


@pytest.mark.asyncio
async def test_focus_visible_in_base(authenticated_client):
    response = await authenticated_client.get("/")
    assert "focus-visible" in response.text


@pytest.mark.asyncio
async def test_nav_has_hx_push_url(authenticated_client):
    response = await authenticated_client.get("/")
    assert 'hx-push-url="true"' in response.text


@pytest.mark.asyncio
async def test_nav_has_logout_button(authenticated_client):
    response = await authenticated_client.get("/")
    assert "Déconnexion" in response.text
