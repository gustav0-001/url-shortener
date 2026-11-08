from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import links

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="URL Shortener",
    description="Сервис для сокращения ссылок",
    version="0.1.0",
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(links.router)



