import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.exceptions import AuthenticationRequired
from app.models.user import User
from app.services.session_service import SESSION_COOKIE_NAME, get_user_id_from_cookie


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        raise AuthenticationRequired()
    user_id = get_user_id_from_cookie(cookie)
    if not user_id:
        raise AuthenticationRequired()
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise AuthenticationRequired()
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationRequired()
    return user
