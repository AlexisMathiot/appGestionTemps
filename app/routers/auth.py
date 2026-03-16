from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.exceptions import ConflictError
from app.schemas.auth import RegisterForm
from app.services import auth_service
from app.services.session_service import SESSION_COOKIE_NAME, SESSION_MAX_AGE, create_session_cookie

router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="app/templates")


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

    # Validate with Pydantic
    try:
        RegisterForm(email=email, password=password, password_confirm=password_confirm)
    except ValidationError as e:
        for error in e.errors():
            if not error["loc"]:
                # model_validator errors (no loc) → password_confirm
                errors.setdefault("password_confirm", error["msg"])
            else:
                field = str(error["loc"][-1])
                errors.setdefault(field, error["msg"])
        return templates.TemplateResponse(
            request,
            error_template,
            {"errors": errors, "form_data": form_data},
            status_code=422,
        )

    # Create user
    try:
        user = await auth_service.create_user(db, email, password)
    except ConflictError:
        errors["email"] = "Un compte avec cet email existe déjà"
        return templates.TemplateResponse(
            request,
            error_template,
            {"errors": errors, "form_data": form_data},
            status_code=422,
        )

    # Set session cookie and redirect
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_cookie(str(user.id)),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=not request.app.debug,
    )
    # For HTMX: add HX-Redirect header so HTMX follows the redirect
    response.headers["HX-Redirect"] = "/"
    return response
