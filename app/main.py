from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
