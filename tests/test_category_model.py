import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.services import auth_service


@pytest.mark.asyncio
async def test_create_category(db_session: AsyncSession):
    """Test creating a basic category."""
    user = await auth_service.create_user(db_session, "cat-create@test.com", "password123")

    category = Category(
        user_id=user.id,
        name="Travail",
        emoji="💼",
        color="#FF5733",
        position=0,
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    assert category.id is not None
    assert category.user_id == user.id
    assert category.name == "Travail"
    assert category.emoji == "💼"
    assert category.color == "#FF5733"
    assert category.position == 0
    assert category.parent_id is None
    assert category.goal_type is None
    assert category.goal_value is None
    assert category.created_at is not None


@pytest.mark.asyncio
async def test_category_self_reference(db_session: AsyncSession):
    """Test parent/child self-referential relationship."""
    user = await auth_service.create_user(db_session, "cat-selfref@test.com", "password123")

    parent = Category(
        user_id=user.id,
        name="Sport",
        emoji="🏃",
        color="#00FF00",
        position=0,
    )
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)

    child = Category(
        user_id=user.id,
        name="Course à pied",
        emoji="👟",
        color="#00FF00",
        parent_id=parent.id,
        position=0,
    )
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)

    assert child.parent_id == parent.id

    # Reload parent to check children relationship
    result = await db_session.execute(
        select(Category).where(Category.id == parent.id)
    )
    parent_reloaded = result.scalar_one()
    await db_session.refresh(parent_reloaded, ["children"])
    assert len(parent_reloaded.children) == 1
    assert parent_reloaded.children[0].id == child.id


@pytest.mark.asyncio
async def test_category_isolation_by_user(db_session: AsyncSession):
    """Test that categories are isolated per user."""
    user1 = await auth_service.create_user(db_session, "user1@test.com", "password123")
    user2 = await auth_service.create_user(db_session, "user2@test.com", "password123")

    cat1 = Category(
        user_id=user1.id, name="User1 Cat", emoji="🔴", color="#FF0000", position=0
    )
    cat2 = Category(
        user_id=user2.id, name="User2 Cat", emoji="🔵", color="#0000FF", position=0
    )
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    # Query only user1's categories
    result = await db_session.execute(
        select(Category).where(Category.user_id == user1.id)
    )
    user1_cats = result.scalars().all()
    assert len(user1_cats) == 1
    assert user1_cats[0].name == "User1 Cat"

    # Query only user2's categories
    result = await db_session.execute(
        select(Category).where(Category.user_id == user2.id)
    )
    user2_cats = result.scalars().all()
    assert len(user2_cats) == 1
    assert user2_cats[0].name == "User2 Cat"


@pytest.mark.asyncio
async def test_category_with_goal(db_session: AsyncSession):
    """Test category with optional goal fields."""
    user = await auth_service.create_user(db_session, "cat-goal@test.com", "password123")

    category = Category(
        user_id=user.id,
        name="Lecture",
        emoji="📖",
        color="#8B4513",
        goal_type="daily",
        goal_value=30,
        position=0,
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    assert category.goal_type == "daily"
    assert category.goal_value == 30
