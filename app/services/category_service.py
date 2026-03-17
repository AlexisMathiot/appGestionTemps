import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


async def get_user_categories(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Category]:
    """Return root categories (parent_id IS NULL) for a user, sorted by position."""
    result = await db.execute(
        select(Category)
        .where(Category.user_id == user_id, Category.parent_id.is_(None))
        .order_by(Category.position, Category.created_at)
    )
    return list(result.scalars().all())


async def create_category(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    emoji: str,
    color: str,
) -> Category:
    """Create a new root category with auto-incremented position.

    Uses advisory lock to prevent race conditions on position calculation.
    """
    # Advisory lock scoped to user_id to serialize position calculation
    lock_id = uuid.UUID(str(user_id)).int & 0x7FFFFFFFFFFFFFFF
    await db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})

    result = await db.execute(
        select(func.coalesce(func.max(Category.position), -1)).where(
            Category.user_id == user_id, Category.parent_id.is_(None)
        )
    )
    max_position = result.scalar()

    category = Category(
        user_id=user_id,
        name=name,
        emoji=emoji,
        color=color,
        position=max_position + 1,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category
