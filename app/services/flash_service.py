import json

from fastapi import Request, Response

FLASH_COOKIE_NAME = "flash"


def flash(response: Response, category: str, message: str) -> None:
    """Set a one-time flash message on the response."""
    response.set_cookie(
        key=FLASH_COOKIE_NAME,
        value=json.dumps({"category": category, "message": message}),
        max_age=60,
        httponly=True,
        samesite="lax",
    )


def read_flash(request: Request) -> dict[str, str] | None:
    """Read flash data from the request cookie (does not delete it)."""
    cookie = request.cookies.get(FLASH_COOKIE_NAME)
    if not cookie:
        return None
    try:
        data = json.loads(cookie)
        if isinstance(data, dict) and "category" in data and "message" in data:
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None
