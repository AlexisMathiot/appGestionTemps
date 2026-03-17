# Story 2.2 : Création d'une catégorie

Status: review

## Story

As a utilisateur connecté,
I want créer une catégorie avec un nom, un emoji et une couleur via un modal,
So that je puisse organiser mes activités par thème.

## Acceptance Criteria

1. Le bouton "+" sur l'accueil ouvre un modal de création (`modal modal-bottom sm:modal-middle`) avec les champs : nom (texte), picker emoji, palette couleur
2. L'utilisateur peut saisir un nom (obligatoire, max 100 caractères), sélectionner un emoji et choisir une couleur
3. À la validation ("Créer"), la catégorie est créée en base de données (champs : name, emoji, color, user_id, position auto-incrémenté)
4. Le modal se ferme et la catégorie apparaît sur la grid d'accueil en card DaisyUI (`card card-compact`) avec emoji prominent, nom, temps du jour "0min", couleur personnalisée en border-l-4
5. La grid est responsive : 2 colonnes mobile, 3 tablet, 4 desktop
6. Les touch targets font minimum 44x44px (UX-DR15)
7. Si l'utilisateur ne saisit pas de nom, un message de validation inline s'affiche (422)
8. La soumission du formulaire utilise HTMX — pas de rechargement complet de page

## Tasks / Subtasks

- [x] Task 1 : Schéma Pydantic pour la création de catégorie (AC: #2, #7)
  - [x] Créer `app/schemas/category.py` avec `CategoryCreate` (name: str min 1 max 100, emoji: str, color: str regex hex)
  - [x] Valider que `color` est un code HEX valide (`#RRGGBB`)
  - [x] Messages de validation en français

- [x] Task 2 : Service — création de catégorie (AC: #3)
  - [x] Ajouter `create_category(db, user_id, name, emoji, color) -> Category` dans `app/services/category_service.py`
  - [x] Calculer `position` auto (max position existante + 1, ou 0 si première catégorie)
  - [x] Retourner la catégorie créée

- [x] Task 3 : Router categories (AC: #1, #3, #7, #8)
  - [x] Créer `app/routers/categories.py` avec le préfixe `/categories`
  - [x] Route `GET /categories/new` → retourne le template du formulaire de création (modal ou page selon HTMX)
  - [x] Route `POST /categories` → valide, crée la catégorie, retourne la grid mise à jour ou redirect vers accueil
  - [x] Enregistrer le router dans `app/main.py`

- [x] Task 4 : Templates — modal et formulaire de création (AC: #1, #2, #6)
  - [x] Créer `app/templates/components/_category_form.html` — formulaire dans un modal DaisyUI avec :
    - Input nom (fieldset/label pattern DaisyUI 5)
    - Sélecteur emoji : grille d'emojis prédéfinis (DIY DaisyUI, ~30 emojis) avec boutons radio visuels
    - Sélecteur couleur : pastilles de couleurs prédéfinies (DIY DaisyUI, 8-12 couleurs) avec boutons radio visuels
    - Bouton "Créer" (`btn btn-primary`)
  - [x] Créer `app/templates/pages/category_new.html` — page wrapper pour le cas non-HTMX
  - [x] Mettre à jour le bouton "+" sur `home.html` pour ouvrir le modal via HTMX

- [x] Task 5 : Réponse HTMX — mise à jour de la grid (AC: #4, #5, #8)
  - [x] Après création réussie : retourner un fragment HTML qui met à jour la grid de catégories sur l'accueil
  - [x] Utiliser `HX-Trigger: closeModal` ou un pattern de redirection HTMX pour fermer le modal et rafraîchir la grid

- [x] Task 6 : Tests (AC: tous)
  - [x] Tests unitaires service : création catégorie, validation position auto, isolation user_id
  - [x] Tests intégration router : POST /categories avec données valides → 200 + catégorie créée, POST sans nom → 422, GET /categories/new → 200
  - [x] Tests régression : vérifier que les tests existants passent toujours (102 tests)

## Dev Notes

### Architecture & Patterns obligatoires

**Pattern de formulaire DaisyUI 5 — réutiliser le pattern auth :**
```python
# app/routers/categories.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/new")
async def new_category(
    request: Request,
    user: User = Depends(get_current_user),
):
    is_htmx = request.headers.get("HX-Request") == "true"
    template = "components/_category_form.html" if is_htmx else "pages/category_new.html"
    return templates.TemplateResponse(request, template, {
        "active_page": "home",
        "user": user,
        "errors": {},
        "form_data": {},
    })

@router.post("")
async def create_category(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    name = form.get("name", "").strip()
    emoji = form.get("emoji", "📁")
    color = form.get("color", "#3B82F6")

    # Validation via Pydantic
    errors = {}
    try:
        CategoryCreate(name=name, emoji=emoji, color=color)
    except ValidationError as e:
        for error in e.errors():
            field = str(error["loc"][-1]) if error["loc"] else "general"
            errors[field] = error["msg"]

    if errors:
        is_htmx = request.headers.get("HX-Request") == "true"
        template = "components/_category_form.html" if is_htmx else "pages/category_new.html"
        return templates.TemplateResponse(request, template, {
            "active_page": "home",
            "user": user,
            "errors": errors,
            "form_data": {"name": name, "emoji": emoji, "color": color},
        }, status_code=422)

    await category_service.create_category(db, user.id, name, emoji, color)

    # Rediriger vers l'accueil pour rafraîchir la grid
    response = _redirect(request, "/")
    flash(response, "success", "Catégorie créée !")
    return response
```

**NE PAS utiliser `Jinja2Templates()` — importer `templates` depuis le module existant.** Vérifier comment `pages.py` et `auth.py` importent `templates` et faire pareil.

**Schéma Pydantic :**
```python
# app/schemas/category.py
import re
from pydantic import BaseModel, field_validator

class CategoryCreate(BaseModel):
    name: str
    emoji: str
    color: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom est obligatoire")
        if len(v) > 100:
            raise ValueError("Le nom ne doit pas dépasser 100 caractères")
        return v

    @field_validator("color")
    @classmethod
    def color_hex_valid(cls, v: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("La couleur doit être au format #RRGGBB")
        return v
```

**Service — ajout `create_category` :**
```python
# Dans app/services/category_service.py (ajouter à l'existant)
async def create_category(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    emoji: str,
    color: str,
) -> Category:
    # Calculer la position (max + 1)
    result = await db.execute(
        select(func.coalesce(func.max(Category.position), -1))
        .where(Category.user_id == user_id, Category.parent_id.is_(None))
    )
    max_position = result.scalar()

    category = Category(
        user_id=user_id,
        name=name,
        emoji=emoji,
        color=color,
        position=max_position + 1,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category
```

**Enregistrement du router dans `main.py` :**
```python
from app.routers import auth, categories, pages

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(categories.router)
```

### Sélecteur Emoji — Approche DIY DaisyUI (0 kB)

Utiliser une grille d'emojis prédéfinis avec des boutons radio stylisés. Pas de librairie externe pour le MVP — l'approche DIY est suffisante pour ~30 emojis de catégorisation.

```html
<!-- Emoji picker DIY -->
<fieldset class="fieldset mb-4">
  <label class="label">Emoji</label>
  <div class="grid grid-cols-6 gap-2">
    {% set emojis = ['💼', '📚', '💪', '🎮', '🎵', '🎨', '🔨', '💻', '📝', '🏃', '🧘', '🍳', '🌱', '🎯', '📊', '🏠', '🚗', '💰', '🎓', '🧹', '📸', '✈️', '🎭', '🏋️', '📱', '🛒', '☕', '🎸', '🐾', '❤️'] %}
    {% for emoji in emojis %}
    <label class="btn btn-ghost btn-sm text-2xl cursor-pointer min-h-[44px] min-w-[44px] {% if form_data.get('emoji') == emoji %}btn-active ring-2 ring-primary{% endif %}">
      <input type="radio" name="emoji" value="{{ emoji }}" class="hidden"
             {% if form_data.get('emoji') == emoji %}checked{% endif %}
             {% if loop.first and not form_data.get('emoji') %}checked{% endif %} />
      {{ emoji }}
    </label>
    {% endfor %}
  </div>
</fieldset>
```

### Sélecteur Couleur — Approche DIY DaisyUI (0 kB)

Pastilles de couleurs prédéfinies avec boutons radio visuels. Palette alignée avec le design system de l'app.

```html
<!-- Color picker DIY -->
<fieldset class="fieldset mb-4">
  <label class="label">Couleur</label>
  <div class="flex gap-2 flex-wrap">
    {% set colors = [
      ('#EF4444', 'Rouge'), ('#F59E0B', 'Ambre'), ('#10B981', 'Émeraude'),
      ('#3B82F6', 'Bleu'), ('#8B5CF6', 'Violet'), ('#EC4899', 'Rose'),
      ('#14B8A6', 'Turquoise'), ('#F97316', 'Orange'), ('#6366F1', 'Indigo'),
      ('#84CC16', 'Citron vert'), ('#06B6D4', 'Cyan'), ('#78716C', 'Gris')
    ] %}
    {% for hex, label in colors %}
    <label class="cursor-pointer" title="{{ label }}">
      <input type="radio" name="color" value="{{ hex }}" class="hidden peer"
             {% if form_data.get('color') == hex %}checked{% endif %}
             {% if loop.first and not form_data.get('color') %}checked{% endif %} />
      <span class="block w-8 h-8 rounded-full border-2 border-transparent peer-checked:ring-2 peer-checked:ring-primary peer-checked:ring-offset-2 min-w-[44px] min-h-[44px] flex items-center justify-center"
            style="background-color: {{ hex }}"></span>
    </label>
    {% endfor %}
  </div>
</fieldset>
```

### Pattern Modal DaisyUI 5

```html
<!-- Modal de création dans home.html ou chargé via HTMX -->
<dialog id="create-category-modal" class="modal modal-bottom sm:modal-middle">
  <div class="modal-box">
    <h3 class="text-lg font-bold mb-4">Nouvelle catégorie</h3>
    <form method="dialog">
      <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
    </form>
    {% include "components/_category_form.html" %}
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

**Ouverture du modal** : Le bouton "+" sur home.html doit appeler `document.getElementById('create-category-modal').showModal()` via un onclick, ou charger le contenu via HTMX puis ouvrir le modal.

**Pattern recommandé** : Inclure le modal vide dans `home.html`, charger le formulaire via `hx-get="/categories/new"` dans le modal-box, puis ouvrir avec `showModal()`. Alternative plus simple : inclure le formulaire statiquement dans `home.html` et ouvrir/fermer le modal côté client.

### Pattern HTMX pour fermeture modal + refresh grid

Après la création réussie, deux approches :

**Approche 1 — Redirect (recommandée, plus simple) :**
- POST /categories → crée la catégorie → flash "Catégorie créée !" → redirect vers `/`
- La page d'accueil recharge avec la nouvelle catégorie dans la grid
- Utiliser le pattern `_redirect()` existant dans `auth.py`

**Approche 2 — Swap HTMX (plus fluide mais plus complexe) :**
- POST /categories → crée la catégorie → retourne un fragment `_category_grid.html` mis à jour
- Header `HX-Trigger: closeModal` pour fermer le dialog côté client
- Script JS : `document.addEventListener('closeModal', () => document.getElementById('create-category-modal').close())`

**Choisir l'approche 1 pour le MVP** — simplicité et cohérence avec les patterns auth existants.

### Helpers existants à réutiliser

- `_redirect(request, url)` depuis `app/routers/auth.py` — extraire vers un helper partagé OU copier le pattern
- `flash(response, level, message)` depuis `app/services/flash_service.py`
- `get_current_user` et `get_db` depuis `app/dependencies.py`
- `templates` import — vérifier comment `pages.py` l'importe (probablement `from app.main import templates` ou via un module dédié)

**IMPORTANT :** Vérifier où `templates` (instance de `Jinja2Templates`) est défini. Dans `pages.py` et `auth.py`, il est probablement instancié localement ou importé. Ne pas créer une nouvelle instance — réutiliser l'existante.

### Fichiers à créer

| Fichier | Contenu |
|---------|---------|
| `app/schemas/category.py` | `CategoryCreate` (Pydantic validation) |
| `app/routers/categories.py` | Routes `GET /categories/new`, `POST /categories` |
| `app/templates/components/_category_form.html` | Formulaire création catégorie (nom, emoji picker, color picker) |
| `app/templates/pages/category_new.html` | Page wrapper pour le formulaire (fallback non-HTMX) |
| `tests/test_category_creation.py` | Tests création catégorie (service + router) |

### Fichiers existants à modifier

| Fichier | Modification |
|---------|-------------|
| `app/services/category_service.py` | Ajouter `create_category()` |
| `app/main.py` | Ajouter `app.include_router(categories.router)` |
| `app/templates/pages/home.html` | Ajouter le modal de création + mettre à jour le bouton "+" pour l'ouvrir |
| `app/static/css/style.css` | Recompiler après ajout de nouvelles classes Tailwind (`npm run build:css`) |

### DaisyUI 5 — Rappels critiques

- Utiliser `fieldset` / `label` (PAS `form-control` / `label-text`)
- `input` sans `input-bordered` (border par défaut en DaisyUI 5)
- `modal modal-bottom sm:modal-middle` pour le modal
- `card card-compact bg-base-100 shadow-sm` pour les cards (PAS `card-bordered`)
- Les classes d'erreur : `input-error` sur l'input, `text-error` sur le message

### Anti-patterns à éviter

- NE PAS utiliser UUID v4 (`uuid.uuid4`) — le projet utilise UUID v7 (`uuid.uuid7`)
- NE PAS utiliser `datetime.utcnow()` — deprecated, utiliser `utcnow()` de `app/models/user.py`
- NE PAS créer une nouvelle instance de `Jinja2Templates` — réutiliser l'existante
- NE PAS retourner du JSON pour l'UI — toujours des fragments HTML (pattern HTMX)
- NE PAS mettre de logique métier dans les routers — utiliser `category_service`
- NE PAS utiliser `form-control` / `label-text` / `input-bordered` — DaisyUI 5 a changé
- NE PAS ajouter d'endpoint de modification/suppression de catégorie — c'est Story 2.4
- NE PAS ajouter l'objectif optionnel (goal_type, goal_value) au formulaire — c'est Story 2.3
- NE PAS installer de librairie externe (Coloris, emoji-picker-element) — l'approche DIY est suffisante pour le MVP
- NE PAS implémenter le calcul du temps par catégorie — "0min" en dur (TimeEntry n'existe pas encore)

### Previous Story Intelligence

- **Story 2.1 terminée (review)** — 102 tests passent, lint propre
- Le modèle Category existe déjà avec tous les champs nécessaires (name, emoji, color, goal_type, goal_value, position)
- Le service `get_user_categories()` existe — on ajoute `create_category()` au même fichier
- La page home affiche déjà l'empty state et la grid de catégories
- Le bouton "+" existe déjà et pointe vers `/categories/new` via HTMX
- `_category_card.html` et `_category_grid.html` existent — pas besoin de les modifier
- Le modèle Category a un `@validates("color")` qui vérifie le format HEX — la validation côté service existe déjà

### Git Intelligence

Derniers commits pertinents :
- `77ebff5` : Story 2.1 — modèle Category, écran d'accueil avec empty state et grid
- `2d4289c` : Migration CDN → Tailwind CSS 4 + DaisyUI 5 + HTMX 2.0.8 local
- `c9f2e95` : Migration UUID v4 → v7

### Navigation actuelle

La navigation utilise une **navbar fixe en haut** (`fixed top-0`), pas un `btm-nav` en bas. Le body a `pt-16` pour compenser. Ne pas modifier la navigation dans cette story.

### Vérifications post-implémentation

1. `uv run pytest` — tous les tests passent (existants + nouveaux)
2. `uv run ruff check app/ tests/` — lint propre
3. `npm run build:css` — recompiler le CSS si nouvelles classes Tailwind utilisées
4. Vérification visuelle : le bouton "+" ouvre le modal, le formulaire fonctionne, la catégorie apparaît dans la grid après création
5. Tester la validation : soumettre sans nom → message d'erreur inline

### Project Structure Notes

- Le router `categories.py` va dans `app/routers/` (1 fichier par domaine — pattern établi)
- Le schéma `category.py` va dans `app/schemas/` (miroir des routers)
- Les templates de formulaire vont dans `app/templates/components/` avec préfixe `_`
- La page wrapper va dans `app/templates/pages/`

### References

- [Source: planning-artifacts/epics.md#Story 2.2] — Acceptance criteria originaux
- [Source: planning-artifacts/architecture.md#API Patterns] — Convention réponses HTMX (200 → fragment, 422 → form errors)
- [Source: planning-artifacts/architecture.md#Route Boundaries] — `/api/categories/*` auth required
- [Source: planning-artifacts/architecture.md#Naming Patterns] — snake_case endpoints, PascalCase classes
- [Source: planning-artifacts/ux-design-specification.md#UX-DR10] — Modal création catégorie (modal-bottom sm:modal-middle)
- [Source: planning-artifacts/ux-design-specification.md#UX-DR4] — Category Cards (card card-compact)
- [Source: planning-artifacts/ux-design-specification.md#UX-DR14] — Responsive 2/3/4 colonnes
- [Source: planning-artifacts/ux-design-specification.md#UX-DR15] — Touch targets 44x44px
- [Source: planning-artifacts/research/technical-emoji-color-picker-research-2026-03-17.md] — Recherche technique emoji/color picker
- [Source: implementation-artifacts/2-1-modele-category-et-ecran-daccueil-avec-empty-state.md] — Story précédente, patterns établis

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Régression corrigée : `home.html` inclut `_category_form.html` qui nécessite `errors` et `form_data` dans le contexte — ajouté ces variables dans `pages.py:home()`
- Lint : imports inutilisés nettoyés dans `test_category_creation.py`

### Completion Notes List

- Task 1 : Schéma `CategoryCreate` créé avec validators name (non-vide, max 100 chars) et color (regex #RRGGBB), messages en français. 11 tests unitaires.
- Task 2 : Service `create_category()` ajouté avec calcul auto de position (max+1 par user). 3 tests.
- Task 3 : Router `/categories` avec GET `/new` (form) et POST `/` (création + redirect). Enregistré dans main.py.
- Task 4 : Modal DaisyUI 5 (`modal-bottom sm:modal-middle`) avec emoji picker DIY (30 emojis, grille 6 cols) et color picker DIY (12 couleurs pastilles). Touch targets 44x44px. Page wrapper non-HTMX créée.
- Task 5 : Pattern Approche 1 (redirect) — POST crée → flash "Catégorie créée !" → redirect `/` → page recharge avec nouvelle catégorie dans la grid.
- Task 6 : 22 nouveaux tests (11 schéma, 3 service, 8 router). 124 tests au total, tous passent. Lint propre.

### Change Log

- 2026-03-17 : Implémentation complète de la story 2.2 — création de catégorie via modal

### File List

- `app/schemas/category.py` (nouveau) — Schéma Pydantic CategoryCreate
- `app/routers/categories.py` (nouveau) — Router categories avec GET /new et POST /
- `app/templates/components/_category_form.html` (nouveau) — Formulaire création catégorie (modal)
- `app/templates/pages/category_new.html` (nouveau) — Page wrapper non-HTMX
- `tests/test_category_creation.py` (nouveau) — 22 tests (schéma, service, router)
- `app/services/category_service.py` (modifié) — Ajout create_category()
- `app/main.py` (modifié) — Ajout categories router
- `app/routers/pages.py` (modifié) — Ajout errors/form_data au contexte home
- `app/templates/pages/home.html` (modifié) — Modal de création + bouton "+" ouvre le modal
- `app/static/css/style.css` (modifié) — Recompilé avec nouvelles classes Tailwind
