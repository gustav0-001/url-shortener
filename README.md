# URL Shortener

Сервис сокращения ссылок на FastAPI, SQLModel, PostgreSQL и Alembic.

Запуск локально:

docker compose up -d
alembic upgrade head
uvicorn app.main:app --reload


Swagger: http://localhost:8000/docs

Тесты:

pip install -r requirements-dev.txt
python -m pytest -v