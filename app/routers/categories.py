from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.category import CategoryCreate
from app.services import category_service
from app.services.flash_service import flash

router = APIRouter(prefix="/categories", tags=["categories"])
templates = Jinja2Templates(directory="app/templates")


def _redirect(request: Request, url: str) -> Response:
    """Return HX-Redirect for HTMX requests, RedirectResponse for normal requests."""
    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = url
        return response
    return RedirectResponse(url=url, status_code=303)


@router.get("/new")
async def new_category(
    request: Request,
    user: User = Depends(get_current_user),
):
    is_htmx = request.headers.get("HX-Request") == "true"
    template = "components/_category_form.html" if is_htmx else "pages/category_new.html"
    return templates.TemplateResponse(
        request,
        template,
        {
            "active_page": "home",
            "user": user,
            "errors": {},
            "form_data": {},
        },
    )


@router.post("", response_class=HTMLResponse)
async def create_category(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    name = form.get("name", "").strip()
    emoji = form.get("emoji", "💼")
    color = form.get("color", "#3B82F6")

    errors: dict[str, str] = {}
    try:
        validated = CategoryCreate(name=name, emoji=emoji, color=color)
    except ValidationError as e:
        for error in e.errors():
            field = str(error["loc"][-1]) if error["loc"] else "general"
            errors.setdefault(field, error["msg"])

    if errors:
        is_htmx = request.headers.get("HX-Request") == "true"
        template = "components/_category_form.html" if is_htmx else "pages/category_new.html"
        return templates.TemplateResponse(
            request,
            template,
            {
                "active_page": "home",
                "user": user,
                "errors": errors,
                "form_data": {"name": name, "emoji": emoji, "color": color},
            },
            status_code=422,
        )

    await category_service.create_category(
        db, user.id, validated.name, validated.emoji, validated.color
    )

    response = _redirect(request, "/")
    flash(response, "success", "Catégorie créée !")
    return response
