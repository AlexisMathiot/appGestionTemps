from itsdangerous import URLSafeTimedSerializer

from app.config import settings

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 86400 * 30  # 30 days

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def create_session_cookie(user_id: str) -> str:
    return _serializer.dumps(str(user_id), salt="session")


def get_user_id_from_cookie(cookie: str, max_age: int = SESSION_MAX_AGE) -> str | None:
    try:
        return _serializer.loads(cookie, salt="session", max_age=max_age)
    except Exception:
        return None


# --- Password reset tokens ---

RESET_TOKEN_MAX_AGE = 3600  # 1 hour


def create_reset_token(email: str, password_hash: str) -> str:
    """Create a password-reset token embedding email + hash fingerprint."""
    return _serializer.dumps(
        {"e": email, "ph": password_hash[:16]}, salt="password-reset"
    )


def verify_reset_token(token: str) -> dict[str, str] | None:
    """Verify a password-reset token. Returns {"email": ..., "ph": ...} or None."""
    try:
        data = _serializer.loads(token, salt="password-reset", max_age=RESET_TOKEN_MAX_AGE)
        if isinstance(data, dict) and "e" in data and "ph" in data:
            return data
        return None
    except Exception:
        return None
