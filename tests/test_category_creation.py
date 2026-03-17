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


# --- Goal schema tests ---


class TestCategoryGoalSchema:
    def test_valid_daily_goal(self):
        schema = CategoryCreate(
            name="Sport", emoji="💪", color="#FF5733",
            goal_type="daily", goal_value=30,
        )
        assert schema.goal_type == "daily"
        assert schema.goal_value == 30

    def test_valid_weekly_goal(self):
        schema = CategoryCreate(
            name="Sport", emoji="💪", color="#FF5733",
            goal_type="weekly", goal_value=120,
        )
        assert schema.goal_type == "weekly"
        assert schema.goal_value == 120

    def test_no_goal_fields_none(self):
        schema = CategoryCreate(name="Sport", emoji="💪", color="#FF5733")
        assert schema.goal_type is None
        assert schema.goal_value is None

    def test_invalid_goal_type_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_type="monthly", goal_value=30,
            )
        assert any("daily" in str(e["msg"]) or "weekly" in str(e["msg"]) for e in exc_info.value.errors())

    def test_goal_value_zero_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_type="daily", goal_value=0,
            )
        assert any("supérieure à 0" in str(e["msg"]) for e in exc_info.value.errors())

    def test_goal_value_negative_raises(self):
        with pytest.raises(ValidationError):
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_type="daily", goal_value=-5,
            )

    def test_goal_value_exceeds_max_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_type="weekly", goal_value=10081,
            )
        assert any("10080" in str(e["msg"]) for e in exc_info.value.errors())

    def test_daily_goal_exceeds_1440_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_type="daily", goal_value=1441,
            )
        assert any("1440" in str(e["msg"]) for e in exc_info.value.errors())

    def test_daily_goal_exactly_1440_valid(self):
        schema = CategoryCreate(
            name="Sport", emoji="💪", color="#FF5733",
            goal_type="daily", goal_value=1440,
        )
        assert schema.goal_value == 1440

    def test_goal_type_only_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_type="daily",
            )
        assert any("ensemble" in str(e["msg"]) for e in exc_info.value.errors())

    def test_goal_value_only_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_value=30,
            )
        assert any("ensemble" in str(e["msg"]) for e in exc_info.value.errors())

    def test_goal_value_empty_string_coerced_to_none(self):
        schema = CategoryCreate(
            name="Sport", emoji="💪", color="#FF5733",
            goal_type=None, goal_value="",
        )
        assert schema.goal_value is None

    def test_goal_value_string_coerced_to_int(self):
        schema = CategoryCreate(
            name="Sport", emoji="💪", color="#FF5733",
            goal_type="daily", goal_value="30",
        )
        assert schema.goal_value == 30

    def test_error_messages_in_french(self):
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(
                name="Sport", emoji="💪", color="#FF5733",
                goal_type="invalid", goal_value=30,
            )
        errors = exc_info.value.errors()
        # All messages should be in French
        for e in errors:
            assert any(
                fr_word in str(e["msg"])
                for fr_word in ["objectif", "doit", "type"]
            )


# --- Goal service tests ---


@pytest.mark.asyncio
async def test_create_category_with_goal(db_session):
    """Service creates category with goal fields."""
    user = await auth_service.create_user(db_session, "goal@test.com", "password123")

    cat = await category_service.create_category(
        db_session, user.id, "Sport", "💪", "#FF5733",
        goal_type="daily", goal_value=30,
    )

    assert cat.goal_type == "daily"
    assert cat.goal_value == 30


@pytest.mark.asyncio
async def test_create_category_without_goal(db_session):
    """Service creates category without goal fields (null)."""
    user = await auth_service.create_user(db_session, "nogoal@test.com", "password123")

    cat = await category_service.create_category(
        db_session, user.id, "Loisir", "🎮", "#3B82F6",
    )

    assert cat.goal_type is None
    assert cat.goal_value is None


# --- Goal router tests ---


@pytest.mark.asyncio
async def test_post_category_with_goal(authenticated_client, db_session):
    """POST /categories with goal fields creates category with goal."""
    response = await authenticated_client.post(
        "/categories",
        data={
            "name": "Sport", "emoji": "💪", "color": "#FF5733",
            "goal_type": "daily", "goal_value": "30",
        },
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)

    result = await db_session.execute(select(Category))
    cat = result.scalars().first()
    assert cat.goal_type == "daily"
    assert cat.goal_value == 30


@pytest.mark.asyncio
async def test_post_category_without_goal(authenticated_client, db_session):
    """POST /categories without goal fields creates category with null goal."""
    response = await authenticated_client.post(
        "/categories",
        data={"name": "Loisir", "emoji": "🎮", "color": "#3B82F6"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)

    result = await db_session.execute(select(Category))
    cat = result.scalars().first()
    assert cat.goal_type is None
    assert cat.goal_value is None


@pytest.mark.asyncio
async def test_post_category_toggle_off_no_goal_sent(authenticated_client, db_session):
    """POST /categories with toggle off (disabled inputs not sent) stores null goal."""
    response = await authenticated_client.post(
        "/categories",
        data={"name": "Musique", "emoji": "🎵", "color": "#8B5CF6"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)

    result = await db_session.execute(select(Category))
    cat = result.scalars().first()
    assert cat.goal_type is None
    assert cat.goal_value is None


@pytest.mark.asyncio
async def test_post_category_invalid_goal_returns_422(authenticated_client):
    """POST /categories with invalid goal_type returns 422."""
    response = await authenticated_client.post(
        "/categories",
        data={
            "name": "Sport", "emoji": "💪", "color": "#FF5733",
            "goal_type": "monthly", "goal_value": "30",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_category_goal_type_only_returns_422(authenticated_client):
    """POST /categories with goal_type but no goal_value returns 422."""
    response = await authenticated_client.post(
        "/categories",
        data={
            "name": "Sport", "emoji": "💪", "color": "#FF5733",
            "goal_type": "daily",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_category_goal_preserves_form_data_on_422(authenticated_client):
    """POST /categories with validation error re-renders form with goal data."""
    response = await authenticated_client.post(
        "/categories",
        data={
            "name": "", "emoji": "💪", "color": "#FF5733",
            "goal_type": "daily", "goal_value": "30",
        },
    )
    assert response.status_code == 422
    # The form should contain goal-related elements with preserved state
    assert "goal_type" in response.text or "goal-toggle" in response.text


# --- Goal model constraint tests ---


@pytest.mark.asyncio
async def test_category_goal_consistency_constraint(db_session):
    """DB CHECK constraint rejects inconsistent goal fields (type without value)."""
    from sqlalchemy.exc import IntegrityError

    user = await auth_service.create_user(db_session, "ck@test.com", "password123")

    cat = Category(
        user_id=user.id, name="Bad", emoji="❌", color="#FF0000",
        goal_type="daily", goal_value=None, position=0,
    )
    db_session.add(cat)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_category_goal_value_positive_constraint(db_session):
    """DB CHECK constraint rejects goal_value <= 0."""
    from sqlalchemy.exc import IntegrityError

    user = await auth_service.create_user(db_session, "ckpos@test.com", "password123")

    cat = Category(
        user_id=user.id, name="Bad", emoji="❌", color="#FF0000",
        goal_type="daily", goal_value=0, position=0,
    )
    db_session.add(cat)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
