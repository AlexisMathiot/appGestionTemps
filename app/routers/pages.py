from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import category_service, timer_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def home(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    categories = await category_service.get_user_categories(db, user.id)
    active_timer = await timer_service.get_active_timer(db, user.id)

    is_paused = False
    paused_seconds = 0
    if active_timer:
        is_paused = active_timer.paused_at is not None
        paused_seconds = active_timer.paused_seconds

    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {
            "active_page": "home",
            "user": user,
            "categories": categories,
            "active_timer": active_timer,
            "is_paused": is_paused,
            "paused_seconds": paused_seconds,
            "today_summary": "0h 0min",
            "errors": {},
            "form_data": {},
        },
    )


@router.get("/stats")
async def stats(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "pages/stats.html", {"active_page": "stats", "user": user}
    )


@router.get("/settings")
async def settings_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "pages/settings.html", {"active_page": "settings", "user": user}
    )
