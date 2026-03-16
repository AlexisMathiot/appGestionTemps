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
