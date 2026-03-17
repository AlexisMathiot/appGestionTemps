import pytest

from app.models.category import Category
from app.services import auth_service
from app.services.session_service import SESSION_COOKIE_NAME, create_session_cookie


@pytest.mark.asyncio
async def test_home_empty_state(authenticated_client):
    """Home page shows empty state when user has no categories."""
    response = await authenticated_client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Créez votre première catégorie" in html
    assert "Aujourd'hui : 0h 0min" in html
    # "+" button always visible (header circle button)
    assert "btn-circle" in html


@pytest.mark.asyncio
async def test_home_with_categories(client, db_session):
    """Home page shows category cards when user has categories."""
    user = await auth_service.create_user(db_session, "home@test.com", "password123")
    cookie_value = create_session_cookie(str(user.id))
    client.cookies.set(SESSION_COOKIE_NAME, cookie_value)

    cat1 = Category(
        user_id=user.id, name="Travail", emoji="💼", color="#FF5733", position=0
    )
    cat2 = Category(
        user_id=user.id, name="Sport", emoji="🏃", color="#00FF00", position=1
    )
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    response = await client.get("/")
    assert response.status_code == 200
    html = response.text

    # Categories are displayed
    assert "Travail" in html
    assert "💼" in html
    assert "Sport" in html
    assert "🏃" in html
    # Empty state NOT shown
    assert "Créez votre première catégorie" not in html
    # Summary header present
    assert "Aujourd'hui : 0h 0min" in html
    # "+" button still visible (header circle button)
    assert "btn-circle" in html


@pytest.mark.asyncio
async def test_home_category_isolation(client, db_session):
    """User only sees their own categories, not other users'."""
    user1 = await auth_service.create_user(db_session, "u1@test.com", "password123")
    user2 = await auth_service.create_user(db_session, "u2@test.com", "password123")

    cat1 = Category(
        user_id=user1.id, name="CatUser1", emoji="🔴", color="#FF0000", position=0
    )
    cat2 = Category(
        user_id=user2.id, name="CatUser2", emoji="🔵", color="#0000FF", position=0
    )
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    # Login as user1
    cookie_value = create_session_cookie(str(user1.id))
    client.cookies.set(SESSION_COOKIE_NAME, cookie_value)

    response = await client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "CatUser1" in html
    assert "CatUser2" not in html
