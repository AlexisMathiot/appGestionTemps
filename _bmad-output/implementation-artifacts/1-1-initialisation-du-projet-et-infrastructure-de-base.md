# Story 1.1 : Initialisation du projet et infrastructure de base

Status: done

## Story

As a développeur,
I want un projet FastAPI initialisé avec la structure définie, les dépendances, Docker, la base de données PostgreSQL et Alembic,
So that j'ai une fondation technique solide pour construire l'application.

## Acceptance Criteria

1. La structure projet complète est créée selon l'architecture définie (app/, templates/, static/, tests/, alembic/)
2. `pyproject.toml` contient toutes les dépendances principales et dev
3. `docker-compose.yml` lance FastAPI (uvicorn) + PostgreSQL et l'app est accessible
4. Alembic est configuré en mode async et connecté à PostgreSQL
5. Une route health-check `GET /health` retourne HTTP 200
6. Le modèle SQLAlchemy `User` (id UUID, email, password_hash, created_at, updated_at) existe avec migration Alembic appliquée
7. La configuration est gérée par variables d'environnement via `.env` + Pydantic Settings
8. `.gitignore`, `.env.example`, et `README.md` minimal sont présents

## Tasks / Subtasks

- [x] Task 1 : Initialisation du projet Python (AC: #1, #2)
  - [x] Créer le projet avec `uv init` dans le répertoire courant
  - [x] Ajouter les dépendances principales dans `pyproject.toml` : fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg, alembic, python-dotenv, jinja2, python-multipart, passlib[bcrypt], itsdangerous
  - [x] Ajouter les dépendances dev : pytest, pytest-asyncio, httpx, ruff, mypy
  - [x] Créer la structure de dossiers complète (voir section Project Structure)

- [x] Task 2 : Configuration de l'application (AC: #7, #8)
  - [x] Créer `app/config.py` avec Pydantic `BaseSettings` : DATABASE_URL, SECRET_KEY, DEBUG, APP_NAME
  - [x] Créer `.env.example` avec les variables documentées
  - [x] Créer `.env` local (gitignored) avec valeurs dev
  - [x] Créer `.gitignore` (Python, .env, __pycache__, .mypy_cache, etc.)

- [x] Task 3 : Setup base de données async (AC: #4, #6)
  - [x] Créer `app/database.py` : engine async (create_async_engine), sessionmaker async, Base declarative
  - [x] Créer `app/models/base.py` : classe Base SQLAlchemy avec convention UUID pour PKs
  - [x] Créer `app/models/user.py` : modèle User (id: UUID v4, email: unique, password_hash, created_at, updated_at)
  - [x] Créer `app/models/__init__.py` : exporter tous les modèles
  - [x] Initialiser Alembic : `alembic init -t async alembic`
  - [x] Configurer `alembic/env.py` pour SQLAlchemy async + import des modèles
  - [x] Configurer `alembic.ini` pour lire DATABASE_URL depuis .env
  - [x] Générer et appliquer la première migration (table `users`)

- [x] Task 4 : Application FastAPI de base (AC: #5)
  - [x] Créer `app/__init__.py`
  - [x] Créer `app/main.py` : instance FastAPI, middleware, montage static files, route `/health`
  - [x] Créer `app/dependencies.py` : dependency `get_db` pour session async
  - [x] Créer `app/exceptions.py` : exceptions custom de base
  - [x] Créer les dossiers vides avec `__init__.py` : schemas/, services/, routers/

- [x] Task 5 : Docker & Docker Compose (AC: #3)
  - [x] Créer `Dockerfile` : image Python 3.14, installation uv, copie projet, uvicorn CMD
  - [x] Créer `docker-compose.yml` : services app (port 8000) + postgres:18 (port 5432), volume persistant, healthcheck
  - [x] Vérifier que `docker compose up` démarre les deux services
  - [x] Vérifier que `/health` retourne 200

- [x] Task 6 : Vérification finale
  - [x] Lancer `ruff check` sans erreur
  - [x] Vérifier la migration Alembic (upgrade head)
  - [x] Confirmer `/health` accessible sur http://localhost:8000/health

## Dev Notes

### Architecture & Patterns obligatoires

**Stack technique exacte :**
- Python 3.12+ avec type hints
- FastAPI en mode async
- SQLAlchemy 2.0 async avec asyncpg (PAS psycopg2)
- Alembic pour migrations (template async)
- Uvicorn comme serveur ASGI

**Conventions de nommage :**
- Tables SQL : snake_case, pluriel (`users`, `categories`, `time_entries`)
- Colonnes : snake_case (`user_id`, `created_at`)
- Foreign keys : `{table_singulier}_id`
- Fichiers Python : snake_case (`time_entry.py`)
- Classes : PascalCase (`TimeEntry`)
- Fonctions/Variables : snake_case (`get_user_stats`)
- Constants : UPPER_SNAKE (`MAX_CATEGORIES`)

**UUID v4 pour toutes les PKs :**
```python
import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**Database async setup pattern :**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**Config pattern (Pydantic Settings) :**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/appgestiontemps"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = True
    APP_NAME: str = "appGestionTemps"

    class Config:
        env_file = ".env"
```

### Project Structure Notes

Structure exacte à créer (source: Architecture document) :

```
appGestionTemps/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── exceptions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── user.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   ├── routers/
│   │   └── __init__.py
│   ├── templates/
│   │   ├── pages/
│   │   └── components/
│   └── static/
│       ├── css/
│       ├── js/
│       └── icons/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── routers/
│   ├── services/
│   └── models/
├── pyproject.toml
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

**IMPORTANT :** Ne PAS créer les fichiers des stories futures (pas de `auth.py`, `categories.py`, etc.). Seuls les fichiers listés ci-dessus sont dans le scope.

### Modèle User (seul modèle de cette story)

```python
# app/models/user.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

### Docker Compose pattern

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/appgestiontemps
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app

  db:
    image: postgres:16
    environment:
      POSTGRES_DB: appgestiontemps
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### Anti-patterns à éviter

- NE PAS utiliser `psycopg2` — utiliser `asyncpg` uniquement
- NE PAS créer de routes auth/categories/timer dans cette story — seulement `/health`
- NE PAS créer les modèles Category ou TimeEntry — seulement User
- NE PAS utiliser `sync_engine` — tout doit être async
- NE PAS mettre de logique métier dans `main.py` — garder minimal
- NE PAS hardcoder les valeurs de config — tout via `.env` + Pydantic Settings
- NE PAS oublier `expire_on_commit=False` sur le sessionmaker async

### References

- [Source: planning-artifacts/architecture.md#Starter Template Evaluation] — Structure custom, commande uv init
- [Source: planning-artifacts/architecture.md#Data Architecture] — UUID v4, modèle User
- [Source: planning-artifacts/architecture.md#Complete Project Directory Structure] — Structure complète
- [Source: planning-artifacts/architecture.md#Naming Patterns] — Conventions de nommage
- [Source: planning-artifacts/architecture.md#Infrastructure & Deployment] — Docker, Uvicorn
- [Source: planning-artifacts/prd.md#Stack Technique] — FastAPI, PostgreSQL, SQLAlchemy

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- PostgreSQL 18 requiert volume mount sur `/var/lib/postgresql` au lieu de `/var/lib/postgresql/data`
- pytest-asyncio en mode STRICT nécessite `@pytest_asyncio.fixture` pour les fixtures async
- Python 3.14.3 compatible avec toutes les dépendances (asyncpg, SQLAlchemy, FastAPI)

### Completion Notes List

- Projet initialisé avec uv, Python 3.14.3
- Structure complète créée selon architecture.md
- Modèle User avec SQLAlchemy 2.0 mapped_column (style moderne)
- Alembic async configuré, migration `create_users_table` générée et appliquée
- FastAPI avec route `/health` fonctionnelle
- Docker Compose avec PostgreSQL 18 + volume corrigé
- 9 tests passent (health check, config, modèle User)
- Ruff lint propre sur app/ et tests/
- Ajout de pydantic-settings (package séparé depuis Pydantic v2)

### File List

- pyproject.toml (nouveau)
- uv.lock (nouveau)
- .python-version (nouveau)
- .gitignore (modifié)
- .env (nouveau, gitignored)
- .env.example (nouveau)
- README.md (nouveau)
- Dockerfile (nouveau)
- docker-compose.yml (nouveau)
- alembic.ini (nouveau)
- app/__init__.py (nouveau)
- app/main.py (nouveau)
- app/config.py (nouveau)
- app/database.py (nouveau)
- app/dependencies.py (nouveau)
- app/exceptions.py (nouveau)
- app/models/__init__.py (nouveau)
- app/models/base.py (nouveau)
- app/models/user.py (nouveau)
- app/schemas/__init__.py (nouveau)
- app/services/__init__.py (nouveau)
- app/routers/__init__.py (nouveau)
- alembic/env.py (nouveau)
- alembic/script.py.mako (nouveau)
- alembic/versions/4e19e7d300ff_create_users_table.py (nouveau)
- tests/__init__.py (nouveau)
- tests/conftest.py (nouveau)
- tests/test_health.py (nouveau)
- tests/test_config.py (nouveau)
- tests/models/__init__.py (nouveau)
- tests/models/test_user.py (nouveau)
- tests/routers/__init__.py (nouveau)
- tests/services/__init__.py (nouveau)
