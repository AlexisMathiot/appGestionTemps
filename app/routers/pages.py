from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def home(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "pages/home.html", {"active_page": "home", "user": user}
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
