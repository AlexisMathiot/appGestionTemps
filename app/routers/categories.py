from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.routers.helpers import htmx_redirect
from app.schemas.category import CategoryCreate, SubCategoryCreate
from app.services import category_service
from app.services.flash_service import flash

router = APIRouter(prefix="/categories", tags=["categories"])
templates = Jinja2Templates(directory="app/templates")


async def _parse_category_form(request: Request) -> tuple[CategoryCreate | None, dict[str, str], dict]:
    """Parse et valide le formulaire catégorie. Retourne (validated, errors, form_data)."""
    form = await request.form()
    name = form.get("name", "").strip()
    emoji = form.get("emoji", "💼")
    color = form.get("color", "#3B82F6")
    goal_type = form.get("goal_type") or None
    raw_goal_value = form.get("goal_value")

    form_data = {
        "name": name, "emoji": emoji, "color": color,
        "goal_enabled": bool(goal_type or raw_goal_value),
        "goal_type": goal_type,
        "goal_value": raw_goal_value,
    }

    errors: dict[str, str] = {}
    try:
        validated = CategoryCreate(
            name=name, emoji=emoji, color=color,
            goal_type=goal_type, goal_value=raw_goal_value,
        )
    except ValidationError as e:
        for error in e.errors():
            if error["loc"]:
                field = str(error["loc"][-1])
            else:
                field = "general"
            errors.setdefault(field, error["msg"])
        return None, errors, form_data

    return validated, errors, form_data


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
    validated, errors, form_data = await _parse_category_form(request)

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
                "form_data": form_data,
            },
            status_code=422,
        )

    await category_service.create_category(
        db, user.id, validated.name, validated.emoji, validated.color,
        validated.goal_type, validated.goal_value,
    )

    response = htmx_redirect(request, "/")
    flash(response, "success", "Catégorie créée !")
    return response


@router.get("/{category_id}/edit", response_class=HTMLResponse)
async def edit_category_form(
    category_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    is_htmx = request.headers.get("HX-Request") == "true"
    template = "components/_category_edit_form.html" if is_htmx else "pages/home.html"
    context = {
        "category": category,
        "user": user,
        "errors": {},
        "form_data": {
            "name": category.name,
            "emoji": category.emoji,
            "color": category.color,
            "goal_enabled": bool(category.goal_type),
            "goal_type": category.goal_type,
            "goal_value": category.goal_value,
        },
    }
    if not is_htmx:
        context["active_page"] = "home"
    return templates.TemplateResponse(request, template, context)


@router.post("/{category_id}/edit", response_class=HTMLResponse)
async def edit_category(
    category_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    validated, errors, form_data = await _parse_category_form(request)

    if errors:
        return templates.TemplateResponse(
            request,
            "components/_category_edit_form.html",
            {
                "category": category,
                "user": user,
                "errors": errors,
                "form_data": form_data,
            },
            status_code=422,
        )

    await category_service.update_category(
        db, category, validated.name, validated.emoji, validated.color,
        validated.goal_type, validated.goal_value,
    )

    response = htmx_redirect(request, "/")
    flash(response, "success", "Catégorie modifiée !")
    return response


@router.post("/{category_id}/delete", response_class=HTMLResponse)
async def delete_category(
    category_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    await category_service.delete_category(db, category)

    response = htmx_redirect(request, "/")
    flash(response, "success", "Catégorie supprimée !")
    return response


# --- Page de détail catégorie et sous-catégories ---


async def _parse_subcategory_form(
    request: Request,
) -> tuple[SubCategoryCreate | None, dict[str, str], dict]:
    """Parse et valide le formulaire sous-catégorie. Retourne (validated, errors, form_data)."""
    form = await request.form()
    name = form.get("name", "").strip()
    emoji = form.get("emoji", "💼")

    form_data = {"name": name, "emoji": emoji}

    errors: dict[str, str] = {}
    try:
        validated = SubCategoryCreate(name=name, emoji=emoji)
    except ValidationError as e:
        for error in e.errors():
            if error["loc"]:
                field = str(error["loc"][-1])
            else:
                field = "general"
            errors.setdefault(field, error["msg"])
        return None, errors, form_data

    return validated, errors, form_data


@router.get("/{category_id}", response_class=HTMLResponse)
async def category_detail(
    category_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    subcategories = await category_service.get_subcategories(db, category_id, user.id)

    return templates.TemplateResponse(
        request,
        "pages/category_detail.html",
        {
            "active_page": "home",
            "user": user,
            "category": category,
            "subcategories": subcategories,
            "errors": {},
            "form_data": {},
        },
    )


@router.post("/{category_id}/subcategories", response_class=HTMLResponse)
async def create_subcategory(
    category_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    validated, errors, form_data = await _parse_subcategory_form(request)

    if errors:
        subcategories = await category_service.get_subcategories(db, category_id, user.id)
        return templates.TemplateResponse(
            request,
            "pages/category_detail.html",
            {
                "active_page": "home",
                "user": user,
                "category": category,
                "subcategories": subcategories,
                "errors": errors,
                "form_data": form_data,
            },
            status_code=422,
        )

    await category_service.create_subcategory(db, category, validated.name, validated.emoji)

    response = htmx_redirect(request, f"/categories/{category_id}")
    flash(response, "success", "Sous-catégorie créée !")
    return response


@router.get("/{category_id}/subcategories/{sub_id}/edit", response_class=HTMLResponse)
async def edit_subcategory_form(
    category_id: UUID,
    sub_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    subcategory = await category_service.get_subcategory_by_id(db, sub_id, user.id)
    if not subcategory or subcategory.parent_id != category_id:
        return Response(status_code=404)

    return templates.TemplateResponse(
        request,
        "components/_subcategory_edit_form.html",
        {
            "category": category,
            "subcategory": subcategory,
            "user": user,
            "errors": {},
            "form_data": {"name": subcategory.name, "emoji": subcategory.emoji},
        },
    )


@router.post("/{category_id}/subcategories/{sub_id}/edit", response_class=HTMLResponse)
async def edit_subcategory(
    category_id: UUID,
    sub_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    subcategory = await category_service.get_subcategory_by_id(db, sub_id, user.id)
    if not subcategory or subcategory.parent_id != category_id:
        return Response(status_code=404)

    validated, errors, form_data = await _parse_subcategory_form(request)

    if errors:
        return templates.TemplateResponse(
            request,
            "components/_subcategory_edit_form.html",
            {
                "category": category,
                "subcategory": subcategory,
                "user": user,
                "errors": errors,
                "form_data": form_data,
            },
            status_code=422,
        )

    await category_service.update_subcategory(db, subcategory, validated.name, validated.emoji)

    response = htmx_redirect(request, f"/categories/{category_id}")
    flash(response, "success", "Sous-catégorie modifiée !")
    return response


@router.post("/{category_id}/subcategories/{sub_id}/delete", response_class=HTMLResponse)
async def delete_subcategory(
    category_id: UUID,
    sub_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = await category_service.get_category_by_id(db, category_id, user.id)
    if not category:
        return Response(status_code=404)

    subcategory = await category_service.get_subcategory_by_id(db, sub_id, user.id)
    if not subcategory or subcategory.parent_id != category_id:
        return Response(status_code=404)

    await category_service.delete_subcategory(db, subcategory)

    response = htmx_redirect(request, f"/categories/{category_id}")
    flash(response, "success", "Sous-catégorie supprimée !")
    return response
