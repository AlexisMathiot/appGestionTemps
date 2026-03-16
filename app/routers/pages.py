from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request, "pages/home.html", {"active_page": "home"}
    )


@router.get("/stats")
async def stats(request: Request):
    return templates.TemplateResponse(
        request, "pages/stats.html", {"active_page": "stats"}
    )


@router.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse(
        request, "pages/settings.html", {"active_page": "settings"}
    )
