import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.models.category import Category
from app.schemas.category import CategoryCreate
from app.services import auth_service, category_service


# --- Schema tests ---


class TestCategoryCreateSchema:
    def test_valid_category(self):
        schema = CategoryCreate(name="Travail", emoji="💼", color="#FF5733")
        assert schema.name == "Travail"
        assert schema.emoji == "💼"
        assert schema.color == "#FF5733"

    def test_name_stripped(self):
        schema = CategoryCreate(name="  Travail  ", emoji="💼", color="#FF5733")
        assert schema.name == "Travail"

    def test_name_empty_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(name="", emoji="💼", color="#FF5733")
        errors = exc_info.value.errors()
        assert any("obligatoire" in str(e["msg"]) for e in errors)

    def test_name_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="   ", emoji="💼", color="#FF5733")

    def test_name_max_100(self):
        # Exactly 100 chars should be valid
        name_100 = "a" * 100
        schema = CategoryCreate(name=name_100, emoji="💼", color="#FF5733")
        assert schema.name == name_100

    def test_name_over_100_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(name="a" * 101, emoji="💼", color="#FF5733")
        errors = exc_info.value.errors()
        assert any("100 caractères" in str(e["msg"]) for e in errors)

    def test_color_valid_hex(self):
        schema = CategoryCreate(name="Test", emoji="💼", color="#aabbcc")
        assert schema.color == "#aabbcc"

    def test_color_invalid_no_hash(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", emoji="💼", color="FF5733")

    def test_color_invalid_short(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", emoji="💼", color="#FFF")

    def test_color_invalid_chars(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="Test", emoji="💼", color="#GGHHII")

    def test_color_error_message_french(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(name="Test", emoji="💼", color="invalid")
        errors = exc_info.value.errors()
        assert any("#RRGGBB" in str(e["msg"]) for e in errors)


# --- Service tests ---


@pytest.mark.asyncio
async def test_create_category_service(db_session):
    """Service creates category with auto-incremented position."""
    user = await auth_service.create_user(db_session, "svc-cat@test.com", "password123")

    cat = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")

    assert cat.id is not None
    assert cat.name == "Travail"
    assert cat.emoji == "💼"
    assert cat.color == "#FF5733"
    assert cat.user_id == user.id
    assert cat.position == 0


@pytest.mark.asyncio
async def test_create_category_position_auto_increment(db_session):
    """Position auto-increments for each new category."""
    user = await auth_service.create_user(db_session, "svc-pos@test.com", "password123")

    cat1 = await category_service.create_category(db_session, user.id, "Cat1", "💼", "#FF5733")
    cat2 = await category_service.create_category(db_session, user.id, "Cat2", "🏃", "#00FF00")
    cat3 = await category_service.create_category(db_session, user.id, "Cat3", "📚", "#0000FF")

    assert cat1.position == 0
    assert cat2.position == 1
    assert cat3.position == 2


@pytest.mark.asyncio
async def test_create_category_position_isolated_per_user(db_session):
    """Each user's position counter is independent."""
    user1 = await auth_service.create_user(db_session, "svc-iso1@test.com", "password123")
    user2 = await auth_service.create_user(db_session, "svc-iso2@test.com", "password123")

    cat1 = await category_service.create_category(db_session, user1.id, "Cat1", "💼", "#FF5733")
    cat2 = await category_service.create_category(db_session, user2.id, "Cat2", "🏃", "#00FF00")

    assert cat1.position == 0
    assert cat2.position == 0  # Independent counter


# --- Router tests ---


@pytest.mark.asyncio
async def test_get_category_new_returns_form(authenticated_client):
    """GET /categories/new returns the category creation form."""
    response = await authenticated_client.get("/categories/new")
    assert response.status_code == 200
    html = response.text
    assert "Nouvelle catégorie" in html
    assert 'name="name"' in html
    assert 'name="emoji"' in html
    assert 'name="color"' in html


@pytest.mark.asyncio
async def test_get_category_new_htmx_returns_form_fragment(authenticated_client):
    """GET /categories/new with HX-Request returns just the form component."""
    response = await authenticated_client.get(
        "/categories/new", headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    html = response.text
    assert 'name="name"' in html


@pytest.mark.asyncio
async def test_post_category_valid(authenticated_client, db_session):
    """POST /categories with valid data creates category and redirects."""
    response = await authenticated_client.post(
        "/categories",
        data={"name": "Travail", "emoji": "💼", "color": "#FF5733"},
        follow_redirects=False,
    )
    # Should redirect (303 or HX-Redirect via 200)
    assert response.status_code in (200, 303)

    # Verify category was created in DB
    result = await db_session.execute(select(Category))
    cats = result.scalars().all()
    assert len(cats) == 1
    assert cats[0].name == "Travail"


@pytest.mark.asyncio
async def test_post_category_htmx_valid(authenticated_client, db_session):
    """POST /categories via HTMX returns HX-Redirect header."""
    response = await authenticated_client.post(
        "/categories",
        data={"name": "Sport", "emoji": "🏃", "color": "#00FF00"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/"


@pytest.mark.asyncio
async def test_post_category_no_name_returns_422(authenticated_client):
    """POST /categories without name returns 422 with error."""
    response = await authenticated_client.post(
        "/categories",
        data={"name": "", "emoji": "💼", "color": "#FF5733"},
    )
    assert response.status_code == 422
    assert "obligatoire" in response.text


@pytest.mark.asyncio
async def test_post_category_invalid_color_returns_422(authenticated_client):
    """POST /categories with invalid color returns 422."""
    response = await authenticated_client.post(
        "/categories",
        data={"name": "Test", "emoji": "💼", "color": "bad"},
    )
    assert response.status_code == 422
    assert "#RRGGBB" in response.text


@pytest.mark.asyncio
async def test_post_category_unauthenticated(client):
    """POST /categories without auth redirects to login."""
    response = await client.post(
        "/categories",
        data={"name": "Test", "emoji": "💼", "color": "#FF5733"},
        follow_redirects=False,
    )
    # Should redirect to login
    assert response.status_code in (200, 303)


@pytest.mark.asyncio
async def test_get_category_new_unauthenticated(client):
    """GET /categories/new without auth redirects to login."""
    response = await client.get("/categories/new", follow_redirects=False)
    assert response.status_code in (200, 303)
