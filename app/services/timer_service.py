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
