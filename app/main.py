from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.exceptions import AuthenticationRequired
from app.routers import auth, categories, pages
from app.services.flash_service import FLASH_COOKIE_NAME, read_flash
from app.services.session_service import SESSION_COOKIE_NAME

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)


@app.middleware("http")
async def flash_middleware(request: Request, call_next):
    """Read flash cookie into request.state and delete it from the response."""
    flash_data = read_flash(request)
    request.state.flash = flash_data
    response = await call_next(request)
    if flash_data:
        response.delete_cookie(key=FLASH_COOKIE_NAME, httponly=True, samesite="lax")
    return response


app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(categories.router)


@app.exception_handler(AuthenticationRequired)
async def auth_required_handler(request: Request, exc: AuthenticationRequired):
    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = exc.redirect_url
    else:
        response = RedirectResponse(url=exc.redirect_url, status_code=303)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=not app.debug,
    )
    return response


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory="app/static"), name="static")
