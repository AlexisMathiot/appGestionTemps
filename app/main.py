from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, pages

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.include_router(pages.router)
app.include_router(auth.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory="app/static"), name="static")
