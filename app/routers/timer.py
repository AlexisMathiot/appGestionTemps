import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.routers.helpers import htmx_redirect
from app.services import timer_service
from app.services.flash_service import flash
from app.services.timer_service import CategoryNotFoundError, TimerAlreadyActiveError

router = APIRouter(prefix="/api/timer", tags=["timer"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/start", response_class=HTMLResponse)
async def start_timer_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    form = await request.form()
    raw_category_id = form.get("category_id", "")

    # Validate UUID format
    try:
        category_id = uuid.UUID(str(raw_category_id))
    except (ValueError, AttributeError):
        return Response(status_code=404)

    try:
        entry = await timer_service.start_timer(db, user.id, category_id)
    except TimerAlreadyActiveError:
        response = htmx_redirect(request, "/")
        flash(response, "warning", "Un timer est déjà en cours")
        return response
    except CategoryNotFoundError:
        return Response(status_code=404)

    category = entry.category
    return templates.TemplateResponse(
        request,
        "components/_timer_display.html",
        {
            "entry_id": str(entry.id),
            "category_name": category.name if category else "Catégorie supprimée",
            "category_emoji": (category.emoji or "") if category else "",
            "category_color": category.color if category else "#6B7280",
            "started_at": entry.started_at.isoformat(),
        },
    )
