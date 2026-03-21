import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models.category import Category
from app.models.time_entry import TimeEntry
from app.services import auth_service, category_service, timer_service
from app.services.session_service import SESSION_COOKIE_NAME, get_user_id_from_cookie
from app.services.timer_service import CategoryNotFoundError, TimerAlreadyActiveError


def _get_user_id(authenticated_client) -> uuid.UUID:
    """Extract user_id from authenticated client session cookie."""
    cookie = authenticated_client.cookies.get(SESSION_COOKIE_NAME)
    return uuid.UUID(get_user_id_from_cookie(cookie))


# --- Model tests ---


class TestTimeEntryModel:
    @pytest.mark.asyncio
    async def test_create_time_entry(self, db_session):
        """TimeEntry can be created with required fields."""
        user = await auth_service.create_user(db_session, "timer-model@test.com", "password123")
        cat = await category_service.create_category(db_session, user.id, "Work", "💼", "#FF5733")

        entry = TimeEntry(
            user_id=user.id,
            category_id=cat.id,
            started_at=datetime.now(UTC),
        )
        db_session.add(entry)
        await db_session.commit()

        result = await db_session.execute(select(TimeEntry).where(TimeEntry.user_id == user.id))
        saved = result.scalar_one()
        assert saved.id is not None
        assert saved.user_id == user.id
        assert saved.category_id == cat.id
        assert saved.started_at is not None
        assert saved.ended_at is None
        assert saved.duration_seconds is None
        assert saved.note is None
        assert saved.created_at is not None

    @pytest.mark.asyncio
    async def test_time_entry_nullable_fields(self, db_session):
        """TimeEntry nullable fields can be set."""
        user = await auth_service.create_user(db_session, "timer-null@test.com", "password123")

        entry = TimeEntry(
            user_id=user.id,
            category_id=None,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            duration_seconds=3600,
            note="Test note",
        )
        db_session.add(entry)
        await db_session.commit()

        result = await db_session.execute(select(TimeEntry).where(TimeEntry.user_id == user.id))
        saved = result.scalar_one()
        assert saved.category_id is None
        assert saved.ended_at is not None
        assert saved.duration_seconds == 3600
        assert saved.note == "Test note"

    @pytest.mark.asyncio
    async def test_time_entry_cascade_delete_user(self, db_session):
        """TimeEntry is deleted when user is deleted (CASCADE)."""
        user = await auth_service.create_user(db_session, "timer-cascade@test.com", "password123")
        cat = await category_service.create_category(db_session, user.id, "Work", "💼", "#FF5733")

        entry = TimeEntry(
            user_id=user.id,
            category_id=cat.id,
            started_at=datetime.now(UTC),
        )
        db_session.add(entry)
        await db_session.commit()
        entry_id = entry.id

        await db_session.delete(user)
        await db_session.commit()

        result = await db_session.execute(select(TimeEntry).where(TimeEntry.id == entry_id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_time_entry_set_null_category(self, db_session):
        """TimeEntry.category_id is set to NULL when category is deleted (SET NULL)."""
        user = await auth_service.create_user(db_session, "timer-setnull@test.com", "password123")
        cat = await category_service.create_category(db_session, user.id, "Work", "💼", "#FF5733")

        entry = TimeEntry(
            user_id=user.id,
            category_id=cat.id,
            started_at=datetime.now(UTC),
        )
        db_session.add(entry)
        await db_session.commit()
        entry_id = entry.id

        await category_service.delete_category(db_session, cat)

        db_session.expire_all()
        result = await db_session.execute(select(TimeEntry).where(TimeEntry.id == entry_id))
        saved = result.scalar_one()
        assert saved.category_id is None


# --- Service tests ---


class TestTimerService:
    @pytest.mark.asyncio
    async def test_start_timer_success(self, db_session):
        """start_timer creates a TimeEntry with correct data."""
        user = await auth_service.create_user(db_session, "timer-start@test.com", "password123")
        cat = await category_service.create_category(db_session, user.id, "Work", "💼", "#FF5733")

        entry = await timer_service.start_timer(db_session, user.id, cat.id)

        assert entry.id is not None
        assert entry.user_id == user.id
        assert entry.category_id == cat.id
        assert entry.started_at is not None
        assert entry.ended_at is None
        assert entry.category is not None
        assert entry.category.name == "Work"

    @pytest.mark.asyncio
    async def test_start_timer_category_not_found(self, db_session):
        """start_timer raises CategoryNotFoundError for non-existent category."""
        user = await auth_service.create_user(db_session, "timer-404@test.com", "password123")

        with pytest.raises(CategoryNotFoundError):
            await timer_service.start_timer(db_session, user.id, uuid.uuid4())

    @pytest.mark.asyncio
    async def test_start_timer_other_user_category(self, db_session):
        """start_timer raises CategoryNotFoundError for another user's category."""
        user1 = await auth_service.create_user(db_session, "timer-u1@test.com", "password123")
        user2 = await auth_service.create_user(db_session, "timer-u2@test.com", "password123")
        cat = await category_service.create_category(db_session, user1.id, "Work", "💼", "#FF5733")

        with pytest.raises(CategoryNotFoundError):
            await timer_service.start_timer(db_session, user2.id, cat.id)

    @pytest.mark.asyncio
    async def test_start_timer_already_active(self, db_session):
        """start_timer raises TimerAlreadyActiveError if a timer is running."""
        user = await auth_service.create_user(db_session, "timer-dup@test.com", "password123")
        cat1 = await category_service.create_category(db_session, user.id, "Work", "💼", "#FF5733")
        cat2 = await category_service.create_category(db_session, user.id, "Sport", "🏃", "#00FF00")

        await timer_service.start_timer(db_session, user.id, cat1.id)

        with pytest.raises(TimerAlreadyActiveError):
            await timer_service.start_timer(db_session, user.id, cat2.id)

    @pytest.mark.asyncio
    async def test_get_active_timer_with_active(self, db_session):
        """get_active_timer returns the active timer with category loaded."""
        user = await auth_service.create_user(db_session, "timer-active@test.com", "password123")
        cat = await category_service.create_category(db_session, user.id, "Work", "💼", "#FF5733")

        await timer_service.start_timer(db_session, user.id, cat.id)
        active = await timer_service.get_active_timer(db_session, user.id)

        assert active is not None
        assert active.ended_at is None
        assert active.category.name == "Work"

    @pytest.mark.asyncio
    async def test_get_active_timer_none(self, db_session):
        """get_active_timer returns None when no timer is active."""
        user = await auth_service.create_user(db_session, "timer-none@test.com", "password123")

        active = await timer_service.get_active_timer(db_session, user.id)
        assert active is None


# --- Route tests ---


class TestTimerRoutes:
    @pytest.mark.asyncio
    async def test_start_timer_success(self, authenticated_client, db_session):
        """POST /api/timer/start creates timer and returns HTML fragment."""
        user_id = _get_user_id(authenticated_client)
        cat = await category_service.create_category(db_session, user_id, "Work", "💼", "#FF5733")

        response = await authenticated_client.post(
            "/api/timer/start",
            data={"category_id": str(cat.id)},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert "timer-header" in response.text
        assert "Work" in response.text
        assert "💼" in response.text

        # Verify entry created in DB
        result = await db_session.execute(
            select(TimeEntry).where(TimeEntry.user_id == user_id)
        )
        entry = result.scalar_one()
        assert entry.category_id == cat.id
        assert entry.ended_at is None

    @pytest.mark.asyncio
    async def test_start_timer_already_active_flash(self, authenticated_client, db_session):
        """POST /api/timer/start with active timer returns flash message."""
        user_id = _get_user_id(authenticated_client)
        cat1 = await category_service.create_category(db_session, user_id, "Work", "💼", "#FF5733")
        cat2 = await category_service.create_category(db_session, user_id, "Sport", "🏃", "#00FF00")

        # Start first timer
        await authenticated_client.post(
            "/api/timer/start",
            data={"category_id": str(cat1.id)},
            headers={"HX-Request": "true"},
        )

        # Try to start second timer
        response = await authenticated_client.post(
            "/api/timer/start",
            data={"category_id": str(cat2.id)},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert "HX-Redirect" in response.headers

    @pytest.mark.asyncio
    async def test_start_timer_unauthenticated(self, client):
        """POST /api/timer/start without auth redirects to login."""
        response = await client.post(
            "/api/timer/start",
            data={"category_id": str(uuid.uuid4())},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert "HX-Redirect" in response.headers
        assert "/auth/login" in response.headers["HX-Redirect"]

    @pytest.mark.asyncio
    async def test_start_timer_invalid_category(self, authenticated_client):
        """POST /api/timer/start with non-existent category returns 404."""
        response = await authenticated_client.post(
            "/api/timer/start",
            data={"category_id": str(uuid.uuid4())},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_timer_invalid_uuid(self, authenticated_client):
        """POST /api/timer/start with invalid UUID returns 404."""
        response = await authenticated_client.post(
            "/api/timer/start",
            data={"category_id": "not-a-uuid"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_home_with_active_timer(self, authenticated_client, db_session):
        """Home page includes timer restore script when timer is active."""
        user_id = _get_user_id(authenticated_client)
        cat = await category_service.create_category(db_session, user_id, "Work", "💼", "#FF5733")

        # Start a timer
        await authenticated_client.post(
            "/api/timer/start",
            data={"category_id": str(cat.id)},
            headers={"HX-Request": "true"},
        )

        # Load home page
        response = await authenticated_client.get("/")
        assert response.status_code == 200
        assert "timerApp.startTimer" in response.text

    @pytest.mark.asyncio
    async def test_home_without_active_timer(self, authenticated_client):
        """Home page does not include timer script when no timer is active."""
        response = await authenticated_client.get("/")
        assert response.status_code == 200
        assert "timerApp.startTimer" not in response.text
