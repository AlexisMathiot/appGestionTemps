from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.exceptions import ConflictError
from app.schemas.auth import RegisterForm
from app.services import auth_service
from app.services.session_service import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE,
    create_session_cookie,
)

router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="app/templates")


def _redirect(request: Request, url: str) -> Response:
    """Return HX-Redirect for HTMX requests, RedirectResponse for normal requests."""
    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = url
        return response
    return RedirectResponse(url=url, status_code=303)


def _set_session_cookie(response: Response, user_id: str, *, debug: bool) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_cookie(user_id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=not debug,
    )


# --- Register ---


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(
        request, "pages/register.html", {"errors": {}, "form_data": {}}
    )


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    password_confirm: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    form_data = {"email": email}
    errors: dict[str, str] = {}
    is_htmx = request.headers.get("HX-Request") == "true"
    error_template = "components/_register_form.html" if is_htmx else "pages/register.html"

    try:
        RegisterForm(email=email, password=password, password_confirm=password_confirm)
    except ValidationError as e:
        for error in e.errors():
            if not error["loc"]:
                errors.setdefault("password_confirm", error["msg"])
            else:
                field = str(error["loc"][-1])
                errors.setdefault(field, error["msg"])
        return templates.TemplateResponse(
            request, error_template, {"errors": errors, "form_data": form_data}, status_code=422,
        )

    try:
        user = await auth_service.create_user(db, email, password)
    except ConflictError:
        errors["email"] = "Un compte avec cet email existe déjà"
        return templates.TemplateResponse(
            request, error_template, {"errors": errors, "form_data": form_data}, status_code=422,
        )

    response = _redirect(request, "/")
    _set_session_cookie(response, str(user.id), debug=request.app.debug)
    return response


# --- Login ---


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request, "pages/login.html", {"error": None, "form_data": {}}
    )


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    form_data = {"email": email}
    is_htmx = request.headers.get("HX-Request") == "true"
    error_template = "components/_login_form.html" if is_htmx else "pages/login.html"

    user = await auth_service.authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            request,
            error_template,
            {"error": "Email ou mot de passe incorrect", "form_data": form_data},
            status_code=422,
        )

    response = _redirect(request, "/")
    _set_session_cookie(response, str(user.id), debug=request.app.debug)
    return response


# --- Logout ---


def _delete_session_cookie(response: Response, *, debug: bool) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=not debug,
    )


@router.post("/logout")
async def logout(request: Request):
    response = _redirect(request, "/auth/login")
    _delete_session_cookie(response, debug=request.app.debug)
    return response
