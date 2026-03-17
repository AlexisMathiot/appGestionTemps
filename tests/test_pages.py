from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.asyncio
async def test_home_returns_200(authenticated_client):
    response = await authenticated_client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_home_contains_html(authenticated_client):
    response = await authenticated_client.get("/")
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_home_contains_local_css(authenticated_client):
    response = await authenticated_client.get("/")
    assert "css/style.css" in response.text


@pytest.mark.asyncio
async def test_home_contains_local_htmx(authenticated_client):
    response = await authenticated_client.get("/")
    assert "js/htmx.min.js" in response.text


@pytest.mark.asyncio
async def test_home_contains_navbar(authenticated_client):
    response = await authenticated_client.get("/")
    assert "navbar" in response.text


@pytest.mark.asyncio
async def test_home_no_cdn_references(authenticated_client):
    response = await authenticated_client.get("/")
    assert "cdn.jsdelivr.net" not in response.text
    assert "cdn.tailwindcss.com" not in response.text
    assert "unpkg.com" not in response.text


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
async def test_prefers_reduced_motion_in_css():
    css = (_PROJECT_ROOT / "app/static/css/input.css").read_text()
    assert "prefers-reduced-motion" in css


@pytest.mark.asyncio
async def test_focus_visible_in_css():
    css = (_PROJECT_ROOT / "app/static/css/input.css").read_text()
    assert "focus-visible" in css


@pytest.mark.asyncio
async def test_nav_has_hx_push_url(authenticated_client):
    response = await authenticated_client.get("/")
    assert 'hx-push-url="true"' in response.text


@pytest.mark.asyncio
async def test_nav_has_logout_button(authenticated_client):
    response = await authenticated_client.get("/")
    assert "Déconnexion" in response.text
