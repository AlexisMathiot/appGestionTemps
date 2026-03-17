# Story 2.1 : Modèle Category et écran d'accueil avec empty state

Status: review

## Story

As a utilisateur connecté,
I want voir mon écran d'accueil avec un message guide quand je n'ai pas encore de catégories,
So that je sache immédiatement comment commencer à utiliser l'app.

## Acceptance Criteria

1. Le modèle Category existe en base avec migration Alembic : `id` (UUID v7 PK), `user_id` (FK users.id, NOT NULL), `parent_id` (FK categories.id, nullable — self-reference pour sous-catégories), `name` (String 100, NOT NULL), `emoji` (String 10, NOT NULL), `color` (String 7, NOT NULL — hex #RRGGBB), `goal_type` (String 10, nullable — "daily" ou "weekly"), `goal_value` (Integer, nullable — minutes), `position` (Integer, NOT NULL, default 0), `created_at` (DateTime timezone, NOT NULL)
2. Un empty state s'affiche quand l'utilisateur n'a aucune catégorie : message "Créez votre première catégorie" + bouton "+" visible
3. Le résumé jour "Aujourd'hui : 0h 0min" est affiché en header de la page d'accueil
4. La page d'accueil affiche une grid de category cards quand des catégories existent (2 colonnes mobile, 3 tablet, 4 desktop) — card DaisyUI `card card-compact` avec emoji prominent, nom, temps du jour "0min", couleur personnalisée en border ou accent
5. Les données sont isolées par `user_id` — un utilisateur ne voit que ses propres catégories (NFR10)
6. Les touch targets font minimum 44x44px (UX-DR15)
7. Le bouton "+" est toujours visible (empty state ET quand des catégories existent)

## Tasks / Subtasks

- [x] Task 1 : Modèle SQLAlchemy Category (AC: #1)
  - [x] Créer `app/models/category.py` avec le modèle Category (adjacency list self-reference)
  - [x] Ajouter `from app.models.category import Category` dans `alembic/env.py` pour enregistrer le modèle
  - [x] Exporter Category dans `app/models/__init__.py`
  - [x] Générer et vérifier la migration Alembic : `uv run alembic revision --autogenerate -m "create_categories_table"`
  - [x] Vérifier que la migration crée : table `categories`, index sur `user_id`, FK vers `users.id` et self-reference `categories.id`

- [x] Task 2 : Service Category — lecture des catégories (AC: #4, #5)
  - [x] Créer `app/services/category_service.py`
  - [x] Implémenter `get_user_categories(db, user_id) -> list[Category]` — retourne les catégories racines (parent_id IS NULL) triées par `position`, filtrées par `user_id`

- [x] Task 3 : Mettre à jour la route Home (AC: #2, #3, #4, #5, #7)
  - [x] Modifier `app/routers/pages.py` — la route `GET /` charge les catégories de l'utilisateur via `category_service`
  - [x] Passer `categories` et `today_summary` ("0h 0min" en dur — pas de TimeEntry encore) au template

- [x] Task 4 : Templates accueil (AC: #2, #3, #4, #6, #7)
  - [x] Réécrire `app/templates/pages/home.html` avec :
    - Header résumé jour : "Aujourd'hui : 0h 0min"
    - Condition vide → empty state (message + bouton "+")
    - Condition non-vide → grid de category cards + bouton "+"
  - [x] Créer `app/templates/components/_category_card.html` — card DaisyUI `card card-compact` avec emoji (texte 3xl), nom, temps du jour, couleur en `border-l-4` avec `style="border-color: {{ category.color }}"`, min-h 44px
  - [x] Créer `app/templates/components/_category_grid.html` — grid responsive `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3`

- [x] Task 5 : Tests (AC: tous)
  - [x] Créer `tests/test_category_model.py` — test création Category, self-reference parent_id, isolation user_id
  - [x] Créer `tests/test_home.py` — test accueil empty state (pas de catégories), test accueil avec catégories (vérifie la présence des noms/emojis dans le HTML), test isolation user_id
  - [x] Vérifier que tous les tests existants passent toujours (régression)

## Dev Notes

### Architecture & Patterns obligatoires

**Modèle Category — adjacency list self-reference (SQLAlchemy 2.1) :**
```python
# app/models/category.py
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import utcnow


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # #RRGGBB
    goal_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "daily" | "weekly"
    goal_value: Mapped[int | None] = mapped_column(Integer, nullable=True)  # minutes
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Self-referential relationships
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent"
    )
    parent: Mapped["Category | None"] = relationship(
        "Category", back_populates="children", remote_side=[id]
    )
```

**UUID v7** — Le projet utilise `uuid.uuid7` (pas v4). Voir `app/models/user.py` pour le pattern exact. Nécessite Python 3.14+.

**Réutiliser `utcnow`** depuis `app/models/user.py` — NE PAS recréer la fonction.

**Service pattern — réutiliser les patterns de `auth_service.py` :**
```python
# app/services/category_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


async def get_user_categories(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Category]:
    result = await db.execute(
        select(Category)
        .where(Category.user_id == user_id, Category.parent_id.is_(None))
        .order_by(Category.position, Category.created_at)
    )
    return list(result.scalars().all())
```

**Route pattern — réutiliser le pattern de `pages.py` :**
```python
@router.get("/")
async def home(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    categories = await category_service.get_user_categories(db, user.id)
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {
            "active_page": "home",
            "user": user,
            "categories": categories,
            "today_summary": "0h 0min",  # Placeholder — TimeEntry pas encore implémenté
        },
    )
```

**Note :** La route `home` actuelle n'injecte pas `db`. Il faut ajouter `db: AsyncSession = Depends(get_db)` et l'import correspondant.

**Alembic env.py — enregistrer le nouveau modèle :**
Ajouter dans `alembic/env.py` :
```python
from app.models.category import Category  # noqa: F401
```

### Fichiers à créer

| Fichier | Contenu |
|---------|---------|
| `app/models/category.py` | Modèle Category |
| `app/services/category_service.py` | `get_user_categories()` |
| `app/templates/components/_category_card.html` | Card DaisyUI pour une catégorie |
| `app/templates/components/_category_grid.html` | Grid responsive des catégories |
| `tests/test_category_model.py` | Tests modèle Category |
| `tests/test_home.py` | Tests page accueil (empty state + avec catégories) |
| `alembic/versions/*_create_categories_table.py` | Migration auto-générée |

### Fichiers existants à modifier

| Fichier | Modification |
|---------|-------------|
| `app/models/__init__.py` | Ajouter `from app.models.category import Category` |
| `app/routers/pages.py` | Modifier route `home` — ajouter chargement catégories + injection DB |
| `app/templates/pages/home.html` | Remplacer le placeholder par empty state / grid catégories |
| `alembic/env.py` | Ajouter import Category pour l'autogenerate |

### DaisyUI 5 — Composants à utiliser

- **Category Card** : `card card-compact bg-base-100 shadow-sm` — NE PAS utiliser `card-bordered` (DaisyUI 5 applique border par défaut si `--border: 1px` est dans le thème)
- **Grid** : `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3`
- **Bouton "+"** : `btn btn-primary btn-circle` ou `btn btn-primary` avec texte "+" — 44x44px minimum
- **Empty state** : composant custom avec `text-center`, `text-secondary` pour le message

**Couleur personnalisée sur la card** : Utiliser `style="border-left-color: {{ category.color }}"` avec classe `border-l-4` (Tailwind). NE PAS utiliser `style="background-color"` sur la card entière — trop chargé visuellement.

### Navigation actuelle

La navigation utilise une **navbar fixe en haut** (`fixed top-0`), pas un `btm-nav` en bas. Le body a `pt-16` pour compenser. Ne pas modifier la navigation dans cette story.

### Previous Story Intelligence

- **Epic 1 complet (5/5 stories)** — 59 tests passent, lint propre
- **Migration CDN → local terminée** : Tailwind CSS 4 + DaisyUI 5 + HTMX 2.0.8 installés localement. CSS compilé via PostCSS pipeline (`npm run build:css`)
- **Pattern templates DaisyUI 5** : `fieldset` / `label` (pas `form-control` / `label-text`). `input` sans `input-bordered` (border par défaut en DaisyUI 5)
- **Pattern conftest.py** : `db_session` crée/drop tables, `authenticated_client` fixture avec user pré-créé. NullPool obligatoire pour asyncpg en tests
- **Pattern HTMX navigation** : `hx-get`, `hx-push-url="true"`, `hx-target="#app-shell"`, `hx-select="#app-shell"`, `hx-swap="outerHTML"` (voir `_nav.html`)
- **Pattern TemplateResponse** : `templates.TemplateResponse(request, "pages/xxx.html", {...})` — Starlette récent exige `request` comme premier argument
- **Flash messages** : Via `flash_service` et cookie middleware, affiché dans `base.html` via `_alert.html`
- **UUID v7** : Le projet a migré de v4 à v7 (commit c9f2e95). Utiliser `uuid.uuid7` partout
- **utcnow()** : Fonction helper dans `app/models/user.py` — `datetime.now(UTC)`. NE PAS utiliser `datetime.utcnow()` (deprecated Python 3.12+)

### Git Intelligence

Derniers commits pertinents :
- `2d4289c` : Migration CDN → Tailwind CSS 4 + DaisyUI 5 + HTMX 2.0.8 local — les formulaires utilisent `fieldset`/`label`, le thème est dans `input.css`
- `c9f2e95` : Migration UUID v4 → v7 — `uuid.uuid7` dans les modèles
- `26157f0` : Uniformisation flash messages — utiliser `flash_service` pour les messages utilisateur

### Anti-patterns à éviter

- NE PAS utiliser UUID v4 (`uuid.uuid4`) — le projet est sur UUID v7 (`uuid.uuid7`)
- NE PAS utiliser `datetime.utcnow()` — deprecated, utiliser `utcnow()` de `app/models/user.py`
- NE PAS créer une nouvelle instance de `Jinja2Templates` — réutiliser le pattern `templates = Jinja2Templates(directory="app/templates")` existant
- NE PAS retourner du JSON pour l'UI — toujours des fragments HTML (pattern HTMX)
- NE PAS mettre de logique métier dans les routers — utiliser `category_service`
- NE PAS utiliser `form-control` / `label-text` — DaisyUI 5 utilise `fieldset` / `label`
- NE PAS utiliser `input-bordered` — border par défaut en DaisyUI 5
- NE PAS hardcoder les couleurs des catégories — utiliser `style="..."` avec la valeur `category.color` de la DB
- NE PAS ajouter d'endpoint de création de catégorie dans cette story — c'est Story 2.2
- NE PAS implémenter le calcul du temps par catégorie — "0min" en dur, TimeEntry n'existe pas encore (Epic 3)

### Project Structure Notes

- Le modèle Category va dans `app/models/category.py` (1 fichier par table — pattern établi)
- Le service va dans `app/services/category_service.py` (1 fichier par domaine)
- Les templates vont dans `app/templates/components/` avec préfixe `_` pour les fragments HTMX
- Le router `categories.py` n'est PAS nécessaire dans cette story — la route home dans `pages.py` suffit. Le router `/api/categories/*` sera créé en Story 2.2

### Vérifications post-implémentation

1. `uv run alembic upgrade head` — migration s'applique sans erreur
2. `uv run pytest` — tous les tests passent (existants + nouveaux)
3. `uv run ruff check app/ tests/` — lint propre
4. Vérification visuelle : page d'accueil affiche l'empty state pour un utilisateur sans catégories
5. Si CSS manquant après ajout de nouvelles classes Tailwind : `npm run build:css` pour recompiler

### References

- [Source: planning-artifacts/epics.md#Story 2.1] — Acceptance criteria originaux
- [Source: planning-artifacts/architecture.md#Data Architecture] — Modèle Category avec self-reference
- [Source: planning-artifacts/architecture.md#Project Structure] — Organisation fichiers
- [Source: planning-artifacts/ux-design-specification.md#Wireframes] — Écran accueil wireframe
- [Source: planning-artifacts/ux-design-specification.md#UX-DR4] — Category Cards card-compact
- [Source: planning-artifacts/ux-design-specification.md#UX-DR12] — Écran accueil résumé jour + grid + empty state
- [Source: planning-artifacts/ux-design-specification.md#UX-DR14] — Responsive 2/3/4 colonnes
- [Source: planning-artifacts/ux-design-specification.md#UX-DR15] — Touch targets 44x44px
- [Source: implementation-artifacts/tech-spec-migration-cdn-tailwind-daisyui-htmx-local.md] — DaisyUI 5 breaking changes et patterns
- [Source: implementation-artifacts/epic-1-retro-2026-03-17.md] — Enseignements Epic 1
- [Source: planning-artifacts/research/technical-emoji-color-picker-research-2026-03-17.md] — Stockage emoji/couleur (Unicode char + HEX)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun blocage rencontré.

### Completion Notes List

- Modèle Category créé avec adjacency list self-reference (parent_id), UUID v7, utcnow()
- Migration Alembic auto-générée et appliquée — inclut correction timestamps users en timezone=True
- Service `category_service.get_user_categories()` filtre par user_id et parent_id IS NULL, trié par position puis created_at
- Route home mise à jour avec injection DB et chargement des catégories
- Template home avec empty state ("Créez votre première catégorie") et grid responsive de category cards
- Category card avec border-l-4 colorée dynamiquement, emoji 3xl, nom et temps placeholder "0min"
- Bouton "+" toujours visible (empty state ET avec catégories), min 44x44px
- 7 nouveaux tests (4 modèle + 3 intégration home), 102 tests totaux passent, lint propre
- CSS recompilé via `npm run build:css`

### File List

**Fichiers créés :**
- `app/models/category.py`
- `app/services/category_service.py`
- `app/templates/components/_category_card.html`
- `app/templates/components/_category_grid.html`
- `alembic/versions/a1aac92c9f53_create_categories_table.py`
- `tests/test_category_model.py`
- `tests/test_home.py`

**Fichiers modifiés :**
- `app/models/__init__.py` — ajout export Category
- `app/routers/pages.py` — route home avec DB + catégories
- `app/templates/pages/home.html` — réécriture complète (empty state + grid)
- `alembic/env.py` — ajout import Category
- `app/static/css/style.css` — recompilé (nouvelles classes Tailwind)

### Change Log

- 2026-03-17 : Implémentation complète Story 2.1 — Modèle Category, service, templates accueil avec empty state et grid de category cards
