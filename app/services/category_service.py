import uuid

from sqlalchemy import select
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
