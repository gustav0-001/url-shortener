from fastapi import FastAPI

from app.routers import links


app = FastAPI(
    title="URL Shortener",
    description="Сервис для сокращения ссылок",
    version="0.1.0",
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(links.router)



