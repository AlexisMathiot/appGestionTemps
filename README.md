# appGestionTemps

Application de gestion du temps personnelle (PWA).

## Stack

- **Backend:** FastAPI (Python 3.14), SQLAlchemy async, PostgreSQL
- **Frontend:** HTMX, Jinja2, Tailwind CSS + DaisyUI
- **Infrastructure:** Docker, Alembic

## Démarrage rapide

```bash
# Démarrer avec Docker
docker compose up

# Ou en local
uv sync
uv run uvicorn app.main:app --reload
```

## Développement

```bash
# Tests
uv run pytest

# Lint
uv run ruff check

# Migrations
uv run alembic upgrade head
```
