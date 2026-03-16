# Story 1.4 : Connexion et déconnexion

Status: done

## Story

As a utilisateur existant,
I want me connecter à mon compte et me déconnecter,
So that j'accède à mes données en toute sécurité.

## Acceptance Criteria

1. La page de connexion est accessible à `/auth/login` avec un formulaire (email, mot de passe)
2. Une session cookie sécurisée est créée quand les identifiants sont corrects
3. L'utilisateur est redirigé vers l'accueil `/` après connexion réussie
4. Un message d'erreur générique s'affiche si les identifiants sont incorrects (pas de fuite d'info : ne pas distinguer "email inconnu" vs "mauvais mot de passe")
5. L'utilisateur peut se déconnecter via un bouton/lien qui détruit la session et redirige vers `/auth/login`
6. Un utilisateur non connecté qui accède à une route protégée est redirigé vers `/auth/login` (avec `HX-Redirect` pour HTMX)
7. Une dependency `get_current_user` est disponible pour protéger les routes
8. Les pages existantes (accueil, stats, settings) sont protégées par authentification
9. Le formulaire de login utilise HTMX pour la soumission avec erreurs inline

## Tasks / Subtasks

- [x] Task 1 : Schema Pydantic pour le login (AC: #1)
  - [x] Ajouter `LoginForm` dans `app/schemas/auth.py` : email (EmailStr), password (str)

- [x] Task 2 : Fonction authenticate_user dans auth_service (AC: #2, #4)
  - [x] Ajouter `authenticate_user(db, email, password)` dans `app/services/auth_service.py`
  - [x] Vérifier email existe, puis vérifier mot de passe avec `verify_password`
  - [x] Retourner le User si valide, None sinon

- [x] Task 3 : Dependency get_current_user (AC: #6, #7)
  - [x] Créer `get_current_user` dans `app/dependencies.py`
  - [x] Lire le cookie session, extraire user_id via `get_user_id_from_cookie`
  - [x] Charger le User depuis la DB
  - [x] Si pas de cookie ou user invalide : raise `AuthenticationRequired` exception
  - [x] Exception handler dans main.py : HTMX → `HX-Redirect`, normal → RedirectResponse 303

- [x] Task 4 : Routes login et logout (AC: #1, #2, #3, #5, #9)
  - [x] Ajouter `GET /auth/login` → affiche le formulaire
  - [x] Ajouter `POST /auth/login` → authentifie, set cookie, redirect `/` + HX-Redirect
  - [x] En cas d'erreur : formulaire avec message générique "Email ou mot de passe incorrect"
  - [x] Ajouter `POST /auth/logout` → supprimer cookie, redirect `/auth/login` + HX-Redirect
  - [x] Helper `_set_session_cookie` factorisé entre register et login

- [x] Task 5 : Templates login (AC: #1, #9)
  - [x] Créer `app/templates/pages/login.html` — card DaisyUI centré
  - [x] Créer `app/templates/components/_login_form.html` — fragment pour HTMX swap
  - [x] Formulaire `hx-post="/auth/login"` avec erreur alert DaisyUI globale
  - [x] Lien vers inscription `/auth/register`

- [x] Task 6 : Protéger les pages existantes (AC: #6, #8)
  - [x] Ajouter `Depends(get_current_user)` sur `/`, `/stats`, `/settings`
  - [x] Passer `user` au template context
  - [x] Ajouter bouton "Déconnexion" dans la navigation

- [x] Task 7 : Tests (AC: tous)
  - [x] Test : GET `/auth/login` retourne 200 avec formulaire
  - [x] Test : POST `/auth/login` avec identifiants valides → redirect 303 + cookie + HX-Redirect
  - [x] Test : POST `/auth/login` avec identifiants invalides → 422 + message erreur générique
  - [x] Test : message d'erreur identique pour email inconnu et mauvais mot de passe
  - [x] Test : POST `/auth/logout` → cookie supprimé, redirect vers login + HX-Redirect
  - [x] Test : GET `/` sans session → redirect 303 vers login
  - [x] Test : GET `/stats` sans session → redirect 303
  - [x] Test : GET `/` avec session valide → 200
  - [x] Test : HTMX request sans auth → header HX-Redirect
  - [x] Tests pages existants mis à jour avec `authenticated_client` fixture
  - [x] Lancer `ruff check app/ tests/` sans erreur

## Dev Notes

### Architecture & Patterns obligatoires

**Dependency get_current_user (source: architecture.md) :**
```python
# app/dependencies.py
from fastapi import Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.session_service import SESSION_COOKIE_NAME, get_user_id_from_cookie
from app.models.user import User

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        return _redirect_to_login(request)
    user_id = get_user_id_from_cookie(cookie)
    if not user_id:
        return _redirect_to_login(request)
    # Load user from DB
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return _redirect_to_login(request)
    return user
```

**IMPORTANT — Redirect pattern pour auth :**
La dependency `get_current_user` ne peut pas retourner une RedirectResponse directement (FastAPI l'attend comme un User). Il faut plutôt lever une exception custom qui sera catchée par un exception handler.

Pattern recommandé :
```python
class AuthenticationRequired(Exception):
    def __init__(self, redirect_url: str = "/auth/login"):
        self.redirect_url = redirect_url

# Exception handler dans main.py
@app.exception_handler(AuthenticationRequired)
async def auth_required_handler(request: Request, exc: AuthenticationRequired):
    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = exc.redirect_url
        return response
    return RedirectResponse(url=exc.redirect_url, status_code=303)
```

**Convention HTMX pour auth (source: architecture.md) :**
- Auth error (401) : `HX-Redirect: /auth/login` header
- Les requêtes HTMX ne suivent pas les redirects HTTP classiques → utiliser `HX-Redirect`

**Formulaire login — message d'erreur générique (sécurité) :**
- NE PAS distinguer "email inconnu" de "mauvais mot de passe"
- Toujours afficher : "Email ou mot de passe incorrect"

**Pattern logout :**
```python
@router.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    response.headers["HX-Redirect"] = "/auth/login"
    return response
```

### Fichiers existants à modifier

- `app/routers/auth.py` — ajouter routes login/logout
- `app/services/auth_service.py` — ajouter `authenticate_user`
- `app/schemas/auth.py` — ajouter `LoginForm`
- `app/dependencies.py` — ajouter `get_current_user`
- `app/exceptions.py` — ajouter `AuthenticationRequired`
- `app/main.py` — ajouter exception handler pour `AuthenticationRequired`
- `app/routers/pages.py` — ajouter `Depends(get_current_user)` sur toutes les routes
- `app/templates/components/_nav.html` — ajouter bouton déconnexion

### Previous Story Intelligence

- **Story 1.3 :** auth_service.py a déjà `get_user_by_email`, `verify_password`, `hash_password`, `create_user`. session_service.py a `create_session_cookie`, `get_user_id_from_cookie`, `SESSION_COOKIE_NAME`, `SESSION_MAX_AGE`. Le router auth.py utilise le pattern `is_htmx` pour choisir le template d'erreur (fragment vs page complète). Le cookie est set avec httponly, samesite=lax, secure conditionnel.
- **Story 1.2 :** La nav est dans `_nav.html`, incluse dans `#app-shell`. Le swap HTMX utilise `hx-target="#app-shell" hx-select="#app-shell" hx-swap="outerHTML"`. Les liens nav ont `href` en fallback.
- **Review 1.3 :** Le formulaire register a été séparé en `_register_form.html` (composant) inclus dans `register.html` (page). Le router détecte `HX-Request` pour choisir le bon template.
- **conftest.py :** NullPool engine, db_session fixture crée/drop tables par test, client dépend de db_session.

### Anti-patterns à éviter

- NE PAS distinguer "email inconnu" de "mauvais mot de passe" dans les messages d'erreur
- NE PAS utiliser HTTPException(401) seul — les redirections doivent fonctionner avec HTMX
- NE PAS oublier `HX-Redirect` header pour les requêtes HTMX qui nécessitent un redirect
- NE PAS supprimer la route `/health` — elle doit rester non protégée
- NE PAS protéger les routes `/auth/*` — elles doivent rester accessibles sans session

### References

- [Source: planning-artifacts/architecture.md#Authentication & Security] — Sessions cookie-based, dependency injection get_current_user
- [Source: planning-artifacts/architecture.md#API & Communication Patterns] — HX-Redirect pour auth errors
- [Source: planning-artifacts/architecture.md#Route Boundaries] — `/auth/*` non protégé, `/`, `/stats`, `/settings` protégés
- [Source: planning-artifacts/prd.md#Functional Requirements] — FR2: connexion, FR3: déconnexion

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- AuthenticationRequired exception pattern fonctionne bien avec exception_handler dans main.py — évite le problème de dependency qui ne peut pas retourner une Response
- HTMX ne suit pas les redirects HTTP classiques → HX-Redirect header essentiel
- Helper `_set_session_cookie` factorisé pour éviter duplication entre register et login

### Completion Notes List

- LoginForm schema ajouté dans schemas/auth.py
- authenticate_user ajouté dans auth_service (retourne None si invalide, pas d'exception)
- get_current_user dependency dans dependencies.py avec AuthenticationRequired exception
- Exception handler dans main.py : gère HTMX (HX-Redirect) et normal (RedirectResponse 303)
- Routes login (GET/POST) et logout (POST) ajoutées dans auth router
- Templates login.html + _login_form.html avec message d'erreur générique (sécurité)
- Pages protégées : /, /stats, /settings nécessitent auth. /health et /auth/* restent publics
- Bouton Déconnexion ajouté dans la navbar
- conftest.py : fixture `authenticated_client` avec user pré-créé et cookie session
- Tests pages mis à jour pour utiliser authenticated_client
- 15 nouveaux tests login/logout (total 48/48 passent), lint propre

### File List

- app/main.py (modifié — ajout exception handler AuthenticationRequired)
- app/exceptions.py (modifié — ajout AuthenticationRequired)
- app/dependencies.py (modifié — ajout get_current_user)
- app/schemas/auth.py (modifié — ajout LoginForm)
- app/services/auth_service.py (modifié — ajout authenticate_user)
- app/routers/auth.py (modifié — ajout login/logout routes, helper _set_session_cookie)
- app/routers/pages.py (modifié — ajout Depends(get_current_user), user en context)
- app/templates/pages/login.html (nouveau)
- app/templates/components/_login_form.html (nouveau)
- app/templates/components/_nav.html (modifié — ajout bouton Déconnexion)
- tests/conftest.py (modifié — ajout fixture authenticated_client)
- tests/test_pages.py (modifié — utilise authenticated_client)
- tests/test_login.py (nouveau)
