# URL Shortener
![CI](https://github.com/gustav0-001/url-shortener/actions/workflows/ci.yml/badge.svg)

Сервис сокращения ссылок на FastAPI, SQLModel, PostgreSQL и Alembic.

## Запуск локально:

Приложение вместе с базой одной командой:
```
docker compose up --build
```
## Разработка без контейнера для приложения
Скопируй `.env.example` в `.env`, затем:

```
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

## Тесты:
```
pip install -r requirements-dev.txt
python -m pytest -v
```