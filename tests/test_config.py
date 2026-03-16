from app.config import Settings


def test_settings_default_values():
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
        SECRET_KEY="test-key",
    )
    assert s.APP_NAME == "appGestionTemps"
    assert s.DEBUG is True


def test_settings_database_url_is_asyncpg():
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
        SECRET_KEY="test-key",
    )
    assert "asyncpg" in s.DATABASE_URL
