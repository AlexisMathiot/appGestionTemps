import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.time_entry import TimeEntry


class TimerAlreadyActiveError(ConflictError):
    def __init__(self):
        super().__init__("Un timer est déjà en cours")


class TimerNotActiveError(ConflictError):
    def __init__(self):
        super().__init__("Aucun timer en cours")


class TimerAlreadyPausedError(ConflictError):
    def __init__(self):
        super().__init__("Le timer est déjà en pause")


class TimerNotPausedError(ConflictError):
    def __init__(self):
        super().__init__("Le timer n'est pas en pause")


class CategoryNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__("Catégorie introuvable")


async def get_active_timer(
    db: AsyncSession, user_id: uuid.UUID
) -> TimeEntry | None:
    """Return the active timer (ended_at IS NULL) for a user, with category loaded."""
    result = await db.execute(
        select(TimeEntry)
        .options(selectinload(TimeEntry.category))
        .where(TimeEntry.user_id == user_id, TimeEntry.ended_at.is_(None))
        .order_by(TimeEntry.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def start_timer(
    db: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID
) -> TimeEntry:
    """Start a new timer for the given category.

    Raises CategoryNotFoundError if category doesn't exist or doesn't belong to user.
    Raises TimerAlreadyActiveError if a timer is already running.
    """
    # 1. Verify category belongs to user
    result = await db.execute(
        select(Category).where(
            Category.id == category_id, Category.user_id == user_id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise CategoryNotFoundError()

    # 2. Check no active timer
    active = await get_active_timer(db, user_id)
    if active:
        raise TimerAlreadyActiveError()

    # 3. Create the entry
    entry = TimeEntry(
        user_id=user_id,
        category_id=category_id,
        started_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise TimerAlreadyActiveError()
    await db.refresh(entry, attribute_names=["category"])
    return entry


async def pause_timer(
    db: AsyncSession, user_id: uuid.UUID
) -> TimeEntry:
    """Pause the active timer.

    Raises TimerNotActiveError if no timer is running.
    Raises TimerAlreadyPausedError if the timer is already paused.
    """
    active = await get_active_timer(db, user_id)
    if not active:
        raise TimerNotActiveError()
    if active.paused_at is not None:
        raise TimerAlreadyPausedError()

    active.paused_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(active, attribute_names=["category"])
    return active


async def resume_timer(
    db: AsyncSession, user_id: uuid.UUID
) -> TimeEntry:
    """Resume a paused timer.

    Raises TimerNotActiveError if no timer is running.
    Raises TimerNotPausedError if the timer is not paused.
    """
    active = await get_active_timer(db, user_id)
    if not active:
        raise TimerNotActiveError()
    if active.paused_at is None:
        raise TimerNotPausedError()

    now = datetime.now(timezone.utc)
    pause_duration = int((now - active.paused_at).total_seconds())
    active.paused_seconds += pause_duration
    active.paused_at = None
    await db.commit()
    await db.refresh(active, attribute_names=["category"])
    return active
