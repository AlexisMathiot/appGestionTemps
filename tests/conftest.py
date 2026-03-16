import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.dependencies import get_db
from app.main import app
from app.models.base import Base
from app.services import auth_service
from app.services.session_service import SESSION_COOKIE_NAME, create_session_cookie

# Test database
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/appgestiontemps_test",
)


@pytest_asyncio.fixture
async def db_session():
    """Provide a clean database session with tables created/dropped per test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP client with DB dependency overridden to use test session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(client, db_session):
    """HTTP client with a logged-in user session."""
    user = await auth_service.create_user(db_session, "testuser@example.com", "password123")
    cookie_value = create_session_cookie(str(user.id))
    client.cookies.set(SESSION_COOKIE_NAME, cookie_value)
    return client
