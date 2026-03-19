# Story 1.3 : Inscription utilisateur

Status: review

## Story

As a nouvel utilisateur,
I want créer un compte avec mon email et un mot de passe,
So that j'aie un espace personnel pour tracker mon temps.

## Acceptance Criteria

1. La page d'inscription est accessible à `/auth/register` avec un formulaire (email, mot de passe, confirmation mot de passe)
2. Un compte est créé avec le mot de passe hashé (bcrypt via passlib) quand les données sont valides
3. L'utilisateur est automatiquement connecté après inscription (session cookie-based via itsdangerous)
4. L'utilisateur est redirigé vers l'accueil `/` après inscription réussie
5. Un message d'erreur inline s'affiche si l'email est déjà utilisé (HTTP 422)
6. Un message de validation s'affiche si le mot de passe < 8 caractères
7. Un message de validation s'affiche si le mot de passe et la confirmation ne correspondent pas
8. Le formulaire utilise HTMX pour la soumission (hx-post) avec erreurs inline sans rechargement complet

## Tasks / Subtasks

- [x] Task 1 : Schema Pydantic pour l'inscription (AC: #2, #6, #7)
  - [x] Créer `app/schemas/auth.py` avec `RegisterForm` : email (EmailStr), password (min 8 chars), password_confirm
  - [x] Ajouter validation custom : password == password_confirm
  - [x] Ajouter `uv add email-validator` (requis par Pydantic EmailStr)

- [x] Task 2 : Service d'authentification (AC: #2, #3, #5)
  - [x] Créer `app/services/auth_service.py`
  - [x] Implémenter `create_user(db, email, password)` : hash bcrypt directement (pas passlib — incompatible bcrypt 5.0+)
  - [x] Implémenter `get_user_by_email(db, email)` : query async
  - [x] Lever `ConflictError` si email déjà utilisé

- [x] Task 3 : Gestion de session (AC: #3)
  - [x] Créer `app/services/session_service.py` (module dédié)
  - [x] Utiliser `itsdangerous.URLSafeTimedSerializer` avec `settings.SECRET_KEY` pour signer le cookie
  - [x] Implémenter `create_session_cookie(user_id)` → retourne le cookie signé
  - [x] Implémenter `get_user_id_from_cookie(cookie_value)` → retourne user_id ou None (max_age 30 jours)
  - [x] Le cookie est httponly, samesite=lax, secure en production

- [x] Task 4 : Router et page d'inscription (AC: #1, #4, #8)
  - [x] Créer `app/routers/auth.py` avec route `GET /auth/register` → affiche le formulaire
  - [x] Ajouter route `POST /auth/register` → traite le formulaire
  - [x] En cas de succès : créer user, set cookie session, redirect 303 vers `/` + header HX-Redirect
  - [x] En cas d'erreur validation : retourner le formulaire avec erreurs inline (422)
  - [x] En cas d'email dupliqué : retourner le formulaire avec message d'erreur (422)
  - [x] Enregistrer le router dans `app/main.py`

- [x] Task 5 : Templates inscription (AC: #1, #8)
  - [x] Créer `app/templates/pages/register.html` — formulaire card DaisyUI centré
  - [x] Le formulaire utilise `hx-post="/auth/register"` avec `hx-swap="outerHTML"` pour erreurs inline
  - [x] Champs input DaisyUI (`input input-bordered`), labels explicites, messages d'erreur sous chaque champ
  - [x] Bouton submit DaisyUI (`btn btn-primary`)
  - [x] Lien vers page de connexion (placeholder pour Story 1.4)

- [x] Task 6 : Tests (AC: tous)
  - [x] Test : GET `/auth/register` retourne 200 avec formulaire HTML
  - [x] Test : POST `/auth/register` avec données valides → crée un user en DB, retourne redirect 303
  - [x] Test : POST `/auth/register` avec email dupliqué → retourne 422 avec message erreur
  - [x] Test : POST `/auth/register` avec mot de passe < 8 chars → retourne erreur validation
  - [x] Test : POST `/auth/register` avec passwords non identiques → retourne erreur
  - [x] Test : le mot de passe est hashé en DB (pas en clair)
  - [x] Test : un cookie de session est set après inscription réussie
  - [x] Test : header HX-Redirect présent après inscription
  - [x] Lancer `ruff check app/ tests/` sans erreur

## Dev Notes

### Architecture & Patterns obligatoires

**Authentication (source: architecture.md) :**
- Sessions cookie-based avec itsdangerous (stateless, pas de Redis)
- Password hashing avec passlib + bcrypt
- CSRF protection : différée pour l'instant — sera ajoutée en Story 1.4 avec le middleware complet

**Pattern auth service :**
```python
# app/services/auth_service.py
from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.exceptions import ConflictError

async def create_user(db: AsyncSession, email: str, password: str) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        raise ConflictError("Un compte avec cet email existe déjà")
    user = User(email=email, password_hash=bcrypt.hash(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
```

**Pattern session cookie (itsdangerous) :**
```python
from itsdangerous import URLSafeTimedSerializer
from app.config import settings

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

def create_session_cookie(user_id: str) -> str:
    return serializer.dumps(str(user_id), salt="session")

def get_user_id_from_cookie(cookie: str, max_age: int = 86400 * 30) -> str | None:
    try:
        return serializer.loads(cookie, salt="session", max_age=max_age)
    except Exception:
        return None
```

**Pattern router auth :**
```python
# app/routers/auth.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db

router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="app/templates")

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "pages/register.html", {})

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate, create user, set cookie, redirect
    ...
```

**Convention HTMX pour formulaires (source: architecture.md) :**
- Success : `RedirectResponse` avec status 303 + header `HX-Redirect` pour HTMX
- Validation error (422) : retourner le formulaire HTML avec erreurs inline
- Le formulaire utilise `hx-post` pour soumission AJAX

**TemplateResponse API (leçon Story 1.2) :**
- Utiliser `TemplateResponse(request, "name.html", context)` (request en premier arg)

### Fichiers existants impactés

- `app/main.py` — ajouter `include_router(auth.router)`
- `app/models/user.py` — déjà créé en Story 1.1 (ne pas modifier)
- `app/exceptions.py` — `ConflictError` déjà défini en Story 1.1
- `app/dependencies.py` — `get_db` déjà défini
- `app/config.py` — `SECRET_KEY` déjà configuré
- `tests/conftest.py` — DB de test séparée déjà configurée, dependency override en place

### Previous Story Intelligence

- **Story 1.1 :** passlib[bcrypt] et itsdangerous déjà dans les dépendances pyproject.toml
- **Story 1.2 :** TemplateResponse prend `request` en 1er arg. DaisyUI v4.12.24 via CDN. Thème oklch custom dans base.html. Navigation dans `#app-shell` avec `hx-swap="outerHTML"`.
- **Review 1.2 :** La nav a été déplacée en haut (navbar fixe top-0). Les liens ont `href` en fallback + `hx-get` pour HTMX. Le thème DaisyUI est défini via CSS variables oklch (pas via JS tailwind.config).
- **conftest.py :** Utilise une DB de test séparée (`appgestiontemps_test`). Le dependency override `get_db` est en place.

### Composants DaisyUI à utiliser

- `input input-bordered` pour les champs de formulaire
- `label` pour les labels
- `btn btn-primary` pour le bouton submit
- `alert alert-error` pour les messages d'erreur
- `card` pour le conteneur du formulaire (centré)

### Anti-patterns à éviter

- NE PAS stocker le mot de passe en clair — toujours hasher avec bcrypt
- NE PAS retourner des messages d'erreur qui révèlent si un email existe (sauf pour le formulaire d'inscription où c'est nécessaire)
- NE PAS utiliser JWT — sessions cookie-based uniquement
- NE PAS créer la page de login dans cette story — seulement un lien placeholder
- NE PAS ajouter de middleware CSRF dans cette story — ce sera fait en Story 1.4
- NE PAS créer de route protégée `get_current_user` dans cette story — ce sera fait en Story 1.4
- NE PAS oublier `await db.commit()` après création du user

### References

- [Source: planning-artifacts/architecture.md#Authentication & Security] — Sessions itsdangerous, passlib+bcrypt
- [Source: planning-artifacts/architecture.md#API & Communication Patterns] — HTMX form submission, error display
- [Source: planning-artifacts/prd.md#Functional Requirements] — FR1: inscription email + mot de passe
- [Source: planning-artifacts/prd.md#Non-Functional Requirements] — NFR7: bcrypt, NFR11: min 8 chars

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- passlib incompatible avec bcrypt 5.0+ (Python 3.14) — remplacé par utilisation directe du package `bcrypt`
- datetime.utcnow() deprecated en Python 3.14 — remplacé par datetime.now(UTC) dans le modèle User
- conftest.py refactoré : NullPool pour éviter "another operation in progress" avec asyncpg, engine créé par test, db_session fixture crée/drop les tables
- Pydantic ValidationError : les erreurs model_validator remontent avec loc vide, mappées sur password_confirm

### Completion Notes List

- Schema RegisterForm avec validation email (EmailStr), password min 8 chars, confirmation match
- Auth service avec hash bcrypt direct (pas passlib), create_user, get_user_by_email
- Session service avec itsdangerous URLSafeTimedSerializer, cookie httponly/samesite/secure
- Router auth : GET/POST /auth/register, erreurs inline 422, redirect 303 + HX-Redirect
- Template register.html : card DaisyUI, formulaire hx-post, erreurs inline par champ
- Modèle User corrigé : DateTime(timezone=True) + datetime.now(UTC)
- conftest.py amélioré : db_session fixture avec NullPool, tables create/drop par test
- 10 nouveaux tests auth (total 33/33 passent), lint propre, 0 warnings

### File List

- app/main.py (modifié — ajout router auth)
- app/schemas/auth.py (nouveau)
- app/services/auth_service.py (nouveau)
- app/services/session_service.py (nouveau)
- app/routers/auth.py (nouveau)
- app/templates/pages/register.html (nouveau)
- app/models/user.py (modifié — DateTime timezone-aware, utcnow fix)
- tests/conftest.py (modifié — db_session fixture, NullPool)
- tests/test_auth.py (nouveau)
- pyproject.toml (modifié — ajout email-validator)
- uv.lock (modifié)
