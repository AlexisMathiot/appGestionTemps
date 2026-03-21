# Story 2.5 : Sous-catégories (activités)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a utilisateur,
I want créer des sous-catégories rattachées à une catégorie parente,
So that je puisse détailler mes activités au sein d'un thème.

## Acceptance Criteria

1. **Given** l'utilisateur accède au détail d'une catégorie (tap sur une card)
   **When** la page de détail s'affiche
   **Then** la liste des sous-catégories existantes est affichée avec leurs emojis
   **And** un bouton "Ajouter une sous-catégorie" est visible
   **And** le nom et emoji de la catégorie parente sont affichés en header
   **And** un lien retour vers l'accueil est disponible

2. **Given** l'utilisateur clique sur "Ajouter une sous-catégorie"
   **When** le formulaire de création s'affiche
   **Then** les champs nom + emoji sont disponibles (pas de couleur — héritée du parent)
   **And** pas de champ objectif (les objectifs sont sur la catégorie parente uniquement)

3. **Given** l'utilisateur remplit nom + emoji et valide
   **When** la sous-catégorie est sauvegardée
   **Then** elle apparaît dans la liste des sous-catégories (parent_id = catégorie parente)
   **And** la sous-catégorie hérite de la couleur de la catégorie parente
   **And** un flash message "Sous-catégorie créée" s'affiche

4. **Given** l'utilisateur soumet un formulaire invalide (nom vide)
   **When** la validation échoue
   **Then** le formulaire est ré-affiché avec les erreurs inline (422)
   **And** les valeurs saisies sont préservées

5. **Given** l'utilisateur clique sur le bouton d'édition d'une sous-catégorie
   **When** le formulaire d'édition s'affiche
   **Then** les valeurs nom et emoji sont pré-remplies
   **And** l'utilisateur peut modifier et sauvegarder

6. **Given** l'utilisateur supprime une sous-catégorie
   **When** il confirme la suppression
   **Then** la sous-catégorie est supprimée
   **And** la liste est mise à jour via HTMX
   **And** un flash message "Sous-catégorie supprimée" s'affiche

7. **Given** l'utilisateur tente de manipuler une sous-catégorie qui ne lui appartient pas
   **When** la requête est traitée
   **Then** une erreur 404 est retournée (pas de fuite d'information)

## Tasks / Subtasks

- [x] Task 1 : Créer le schéma `SubCategoryCreate` dans `app/schemas/category.py` (AC: #2, #4)
  - [x] 1.1 Champs : `name` (str, 1-100, obligatoire, strip), `emoji` (str, max 10)
  - [x] 1.2 Réutiliser les validators `validate_name` et `validate_emoji` de `CategoryCreate`
  - [x] 1.3 Pas de champs color, goal_type, goal_value (hérités/absents)

- [x] Task 2 : Ajouter les fonctions service pour sous-catégories dans `app/services/category_service.py` (AC: #1, #3, #5, #6, #7)
  - [x] 2.1 `get_subcategories(db, parent_id, user_id) -> list[Category]` — retourne les enfants ordonnés par position puis created_at
  - [x] 2.2 `create_subcategory(db, parent: Category, name, emoji) -> Category` — crée avec parent_id=parent.id, user_id=parent.user_id, color=parent.color, goal_type=None, goal_value=None, position auto-incrémentée (scoped au parent_id)
  - [x] 2.3 `get_subcategory_by_id(db, subcategory_id, user_id) -> Category | None` — query filtrée par user_id ET parent_id IS NOT NULL
  - [x] 2.4 `update_subcategory(db, subcategory, name, emoji) -> Category` — met à jour uniquement nom et emoji
  - [x] 2.5 `delete_subcategory(db, subcategory) -> None` — supprime la sous-catégorie (pas d'enfants à cascade car 2 niveaux max)

- [x] Task 3 : Créer la page de détail catégorie et ajouter les endpoints sous-catégories dans `app/routers/categories.py` (AC: #1-#7)
  - [x] 3.1 `GET /categories/{category_id}` — page de détail avec liste des sous-catégories + formulaire de création
  - [x] 3.2 `POST /categories/{category_id}/subcategories` — créer une sous-catégorie
  - [x] 3.3 `GET /categories/{category_id}/subcategories/{sub_id}/edit` — formulaire d'édition pré-rempli
  - [x] 3.4 `POST /categories/{category_id}/subcategories/{sub_id}/edit` — modifier la sous-catégorie
  - [x] 3.5 `POST /categories/{category_id}/subcategories/{sub_id}/delete` — supprimer la sous-catégorie
  - [x] 3.6 Tous les endpoints vérifient : catégorie parente appartient à l'utilisateur, sous-catégorie a bien parent_id == category_id

- [x] Task 4 : Créer les templates (AC: #1-#6)
  - [x] 4.1 `app/templates/pages/category_detail.html` — page de détail catégorie avec header (emoji + nom parent + couleur), liste des sous-catégories, bouton "Ajouter"
  - [x] 4.2 `app/templates/components/_subcategory_list.html` — liste des sous-catégories avec emoji, nom, boutons éditer/supprimer
  - [x] 4.3 `app/templates/components/_subcategory_form.html` — formulaire création (modal ou inline) : nom + emoji uniquement
  - [x] 4.4 `app/templates/components/_subcategory_edit_form.html` — formulaire édition pré-rempli
  - [x] 4.5 `app/templates/components/_subcategory_delete_confirm.html` — modal de confirmation suppression
  - [x] 4.6 Empty state : "Aucune sous-catégorie. Ajoutez-en une pour détailler vos activités."

- [x] Task 5 : Mettre à jour la navigation — rendre la card catégorie cliquable vers le détail (AC: #1)
  - [x] 5.1 Modifier `_category_card.html` : le tap sur la card navigue vers `/categories/{id}` (page de détail)
  - [x] 5.2 S'assurer que les boutons éditer/supprimer continuent à `stopPropagation()` (déjà en place)
  - [x] 5.3 Le lien utilise `hx-get` + `hx-push-url` pour navigation HTMX avec historique

- [x] Task 6 : Tests (AC: #1-#7)
  - [x] 6.1 Tests schéma : SubCategoryCreate validation (nom vide, nom trop long, emoji valide)
  - [x] 6.2 Tests service : get_subcategories, create_subcategory (position, héritage couleur), get_subcategory_by_id, update_subcategory, delete_subcategory, isolation user
  - [x] 6.3 Tests route : GET detail page, POST create succès/422, GET edit form, POST edit succès/422, POST delete succès/404, isolation user/parent
  - [x] 6.4 Vérifier que la suppression d'une catégorie parente (story 2.4) supprime toujours ses sous-catégories — test de non-régression

## Dev Notes

### Architecture et patterns à suivre

- **Couches** : Router → Service → Model/Schema. Même pattern que stories 2.2–2.4.
- **HTMX** : Pattern existant = `hx-post` / `hx-get` avec `hx-target="#app-shell"` et `hx-select="#app-shell"` pour full page swap. Utiliser le même pattern.
- **Redirect** : `htmx_redirect(request, url)` du module `app/routers/helpers.py` — retourne `HX-Redirect` pour HTMX, `RedirectResponse(status_code=303)` pour normal.
- **Flash** : `flash(response, "success", "message")` du module `app/services/flash_service.py`.
- **Erreurs** : Validation Pydantic → 422 avec re-render formulaire + erreurs inline. Pattern existant dans `POST /categories`.
- **Formulaire parsing** : Réutiliser le pattern de `_parse_category_form()` dans `app/routers/categories.py` mais adapté aux sous-catégories (moins de champs).

### Modèle Category existant — PAS de migration nécessaire

Le modèle `app/models/category.py` possède **déjà** toute la structure pour les sous-catégories :
- `parent_id: Mapped[uuid.UUID | None]` — FK vers categories.id avec `ondelete="SET NULL"`
- `children: Mapped[list["Category"]]` — relation one-to-many
- `parent: Mapped["Category | None"]` — relation many-to-one avec `remote_side=[id]`

Champs du modèle :
```
id (UUID v7), user_id (FK → users.id), parent_id (FK → categories.id, nullable),
name (String 100), emoji (String 10), color (String 7, #RRGGBB),
goal_type (String, nullable), goal_value (Integer, nullable),
position (Integer), created_at (DateTime UTC)
```

**Aucune migration Alembic nécessaire.**

### Schéma Pydantic — `SubCategoryCreate`

Fichier : `app/schemas/category.py`

Nouveau schéma simplifié (pas de color, pas de goal) :
```python
class SubCategoryCreate(BaseModel):
    name: str
    emoji: str

    # Réutiliser les validators existants de CategoryCreate :
    # validate_name (strip, non-vide, max 100)
    # validate_emoji (max 10 chars)
```

Option : utiliser une classe de base commune avec `CategoryCreate` pour factoriser les validators `name` et `emoji`, ou simplement dupliquer ces 2 validators simples.

### Service — nouvelles fonctions requises

Fichier : `app/services/category_service.py`

**ATTENTION** — `get_category_by_id()` existant filtre `parent_id IS NULL` (lignes ~dans le service). Il faudra :
- **Ne PAS modifier** `get_category_by_id()` — il est utilisé par les endpoints de catégories racines (stories 2.4)
- **Créer** `get_subcategory_by_id(db, sub_id, user_id)` qui filtre `parent_id IS NOT NULL` pour les sous-catégories

Pour `create_subcategory()`, adapter le pattern de position auto-incrémentée :
- L'advisory lock actuel utilise `user_id` comme scope → adapter pour utiliser `parent_id` comme scope supplémentaire
- La position doit être calculée parmi les enfants du même parent : `SELECT MAX(position) FROM categories WHERE parent_id = :parent_id`

```python
async def create_subcategory(db: AsyncSession, parent: Category, name: str, emoji: str) -> Category:
    # Advisory lock scoped to parent_id for position calculation
    await db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"),
                     {"lock_id": parent.id.int & 0x7FFFFFFFFFFFFFFF})
    result = await db.execute(
        select(func.coalesce(func.max(Category.position), -1) + 1)
        .where(Category.parent_id == parent.id)
    )
    next_position = result.scalar()
    subcategory = Category(
        user_id=parent.user_id,
        parent_id=parent.id,
        name=name,
        emoji=emoji,
        color=parent.color,  # Héritage couleur parent
        goal_type=None,
        goal_value=None,
        position=next_position,
    )
    db.add(subcategory)
    await db.commit()
    await db.refresh(subcategory)
    return subcategory
```

### Routeur — endpoints à ajouter

Fichier : `app/routers/categories.py`

5 nouveaux endpoints + 1 page de détail :

1. **`GET /categories/{category_id}`** — Page de détail catégorie
   - Charger la catégorie racine via `get_category_by_id(db, category_id, user.id)` → 404 si absente
   - Charger les sous-catégories via `get_subcategories(db, category_id, user.id)`
   - Rendre `pages/category_detail.html`

2. **`POST /categories/{category_id}/subcategories`** — Créer sous-catégorie
   - Charger la catégorie parente → 404 si absente
   - Parser formulaire, valider via `SubCategoryCreate`
   - Si erreur → 422 avec re-render
   - Sinon → `create_subcategory()`, redirect vers `/categories/{category_id}`, flash "Sous-catégorie créée"

3. **`GET /categories/{category_id}/subcategories/{sub_id}/edit`** — Formulaire édition
   - Vérifier catégorie parente + sous-catégorie → 404 si absent
   - Vérifier `subcategory.parent_id == category_id`
   - Rendre template `_subcategory_edit_form.html`

4. **`POST /categories/{category_id}/subcategories/{sub_id}/edit`** — Modifier
   - Mêmes vérifications + valider + `update_subcategory()`
   - Redirect vers `/categories/{category_id}`, flash "Sous-catégorie modifiée"

5. **`POST /categories/{category_id}/subcategories/{sub_id}/delete`** — Supprimer
   - Mêmes vérifications + `delete_subcategory()`
   - Redirect vers `/categories/{category_id}`, flash "Sous-catégorie supprimée"

**Pattern URL** : Les sous-catégories sont nestées sous la catégorie parente dans l'URL pour garantir la cohérence parent-enfant.

### Templates — page de détail

Fichier : `app/templates/pages/category_detail.html`

Structure :
```html
{% extends "base.html" %}
{% block content %}
<div class="p-4 max-w-lg mx-auto">
  <!-- Header avec retour -->
  <a hx-get="/" hx-target="#app-shell" hx-select="#app-shell" hx-push-url="/"
     class="btn btn-ghost btn-sm mb-4">← Accueil</a>

  <!-- Catégorie parente -->
  <div class="flex items-center gap-3 mb-6" style="border-left: 4px solid {{ category.color }}; padding-left: 12px;">
    <span class="text-3xl">{{ category.emoji }}</span>
    <h1 class="text-xl font-bold">{{ category.name }}</h1>
  </div>

  <!-- Sous-catégories -->
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-lg font-semibold">Sous-catégories</h2>
    <button onclick="document.getElementById('subcategory-create-modal').showModal()"
            class="btn btn-primary btn-sm">+ Ajouter</button>
  </div>

  {% include "components/_subcategory_list.html" %}

  <!-- Modal création -->
  <!-- Modal(s) suppression -->
</div>
{% endblock %}
```

### Templates — liste des sous-catégories

Fichier : `app/templates/components/_subcategory_list.html`

- Afficher chaque sous-catégorie avec emoji + nom
- Boutons éditer/supprimer par sous-catégorie (même pattern que cards parentes)
- Empty state si aucune sous-catégorie
- Style liste simple (pas de grid — ce sont des éléments secondaires)
- Couleur héritée du parent visible (bordure ou badge)

### Templates — formulaire sous-catégorie

Fichier : `app/templates/components/_subcategory_form.html`

Formulaire simplifié :
- Champ nom (input text, obligatoire)
- Picker emoji (réutiliser le même composant que `_category_form.html`)
- Pas de couleur, pas d'objectif
- Bouton "Créer"
- `hx-post="/categories/{{ category.id }}/subcategories"` + `hx-target="#app-shell"` + `hx-select="#app-shell"`

### Navigation — card cliquable vers détail

Fichier : `app/templates/components/_category_card.html`

La card est actuellement cliquable mais n'a pas de destination définie (pas de `hx-get` sur la card elle-même dans le code actuel — les boutons éditer/supprimer ouvrent des modals). Il faut :
- Ajouter `hx-get="/categories/{{ category.id }}"` sur la card
- Ajouter `hx-target="#app-shell"` + `hx-select="#app-shell"` + `hx-push-url="/categories/{{ category.id }}"`
- Les boutons éditer/supprimer ont déjà `event.stopPropagation()` — vérifier que ça fonctionne toujours

### Suppression cascade — vérification non-régression

La story 2.4 a implémenté la suppression des sous-catégories quand une catégorie parente est supprimée :
```python
await db.execute(delete(Category).where(Category.parent_id == category.id))
```
Ajouter un test de non-régression : créer une catégorie avec des sous-catégories, supprimer la catégorie parente, vérifier que les sous-catégories sont bien supprimées.

### Anti-patterns à éviter

- **NE PAS** créer de migration Alembic — le modèle est complet
- **NE PAS** modifier `app/models/category.py` — déjà prêt
- **NE PAS** modifier `get_category_by_id()` existant — créer `get_subcategory_by_id()` à la place
- **NE PAS** permettre les sous-sous-catégories (2 niveaux max) — vérifier que `parent_id` du parent est NULL
- **NE PAS** ajouter de couleur ou objectif aux sous-catégories — elles héritent du parent
- **NE PAS** utiliser Alpine.js ou framework JS — vanilla JS inline suffit
- **NE PAS** oublier `event.stopPropagation()` sur les boutons dans les éléments cliquables
- **NE PAS** utiliser `DELETE` HTTP method — utiliser `POST /delete` (formulaires HTML = GET/POST)
- **NE PAS** oublier la double vérification : catégorie parente appartient au user ET sous-catégorie a le bon parent_id

### Project Structure Notes

Fichiers à créer :
- `app/templates/pages/category_detail.html` — page de détail catégorie
- `app/templates/components/_subcategory_list.html` — liste des sous-catégories
- `app/templates/components/_subcategory_form.html` — formulaire création sous-catégorie
- `app/templates/components/_subcategory_edit_form.html` — formulaire édition
- `app/templates/components/_subcategory_delete_confirm.html` — modal confirmation suppression
- `tests/test_subcategories.py` — tests dédiés sous-catégories

Fichiers à modifier :
- `app/schemas/category.py` — ajouter `SubCategoryCreate`
- `app/services/category_service.py` — ajouter fonctions sous-catégories
- `app/routers/categories.py` — ajouter endpoints sous-catégories + page détail
- `app/templates/components/_category_card.html` — rendre la card cliquable vers `/categories/{id}`

Fichiers à NE PAS modifier :
- `app/models/category.py` — déjà complet
- `alembic/` — aucune migration nécessaire
- `app/templates/components/_category_form.html` — garder pour la création de catégories racines
- `app/templates/components/_category_edit_form.html` — garder pour l'édition de catégories racines
- `app/services/flash_service.py` — réutiliser tel quel
- `app/routers/helpers.py` — réutiliser tel quel

### Previous Story Intelligence (Story 2.4)

- Le pattern form + validation 422 est bien rodé — le réutiliser
- `CategoryUpdate = CategoryCreate` (alias simple) fonctionne — faire pareil si pertinent
- Les tests couvrent 167 cas au total — maintenir ou dépasser
- La suppression cascade des enfants fonctionne via `DELETE WHERE parent_id = category.id`
- Le modal d'édition est chargé dynamiquement via HTMX (Option 2) — bon pattern à réutiliser
- Convention de commit : `feat: description courte en français (story X.Y)`
- Le pattern `_parse_category_form()` dans le routeur centralise le parsing/validation — créer un équivalent `_parse_subcategory_form()` pour les sous-catégories

### Git Intelligence

Derniers commits :
- `3b268e7` feat: modification et suppression de catégorie + correctifs code review (story 2.4)
- `d704e71` feat: création de catégorie via modal + correctifs code review (story 2.2)
- `77ebff5` feat: modèle Category, écran d'accueil avec empty state et grid (story 2.1)
- `2d4289c` feat: migration CDN vers Tailwind CSS 4 + DaisyUI 5 + HTMX 2.0.8 en local

Convention : `feat: description courte en français (story X.Y)`

### Testing Standards

- Framework : pytest + pytest-asyncio
- Fixtures dans `tests/conftest.py` : `db_session`, `client`, `authenticated_client`
- Tests schéma : synchrones, pas de DB
- Tests service : async avec `db_session`
- Tests route : async avec `authenticated_client`
- Header HTMX : `{"HX-Request": "true"}` pour tester les réponses HTMX
- Vérifier status codes, contenu HTML, état en base
- Nouveau fichier test : `tests/test_subcategories.py` (séparé des tests catégories)
- Total actuel : 167 tests — objectif > 180 après cette story

### Epic 3 Impact — préparer le terrain

L'Epic 3 (Tracking du Temps) utilisera les sous-catégories : `FR17: L'utilisateur peut démarrer un timer pour une catégorie ou une sous-catégorie`. Le modèle `TimeEntry` a un `category_id` FK vers `categories`. Les sous-catégories étant dans la même table, le timer pourra cibler indifféremment une catégorie ou une sous-catégorie sans modification du modèle TimeEntry.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — self-reference pour sous-catégories]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns]
- [Source: _bmad-output/planning-artifacts/prd.md#FR12-FR16 — sous-catégories]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design Direction]
- [Source: app/models/category.py — modèle avec parent_id, children, parent relations]
- [Source: app/schemas/category.py — schéma CategoryCreate avec validators réutilisables]
- [Source: app/routers/categories.py — routeur existant à étendre]
- [Source: app/services/category_service.py — service existant, get_category_by_id filtre parent_id IS NULL]
- [Source: _bmad-output/implementation-artifacts/2-4-modification-et-suppression-de-categorie.md — story précédente]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun problème rencontré. Tous les tests ont passé du premier coup.

### Completion Notes List

- Task 1 : Schéma `SubCategoryCreate` créé avec validators `name` et `emoji` identiques à `CategoryCreate`. Alias `SubCategoryUpdate = SubCategoryCreate` ajouté.
- Task 2 : 5 fonctions service ajoutées — `get_subcategories`, `create_subcategory` (avec advisory lock scoped au parent_id), `get_subcategory_by_id` (filtre parent_id IS NOT NULL), `update_subcategory`, `delete_subcategory`.
- Task 3 : 6 endpoints ajoutés — page de détail catégorie, CRUD sous-catégories. Double vérification user + parent_id sur tous les endpoints. Pattern `_parse_subcategory_form()` créé.
- Task 4 : 5 templates créés — page de détail, liste sous-catégories, formulaire création, formulaire édition, modal suppression. Empty state inclus.
- Task 5 : La card catégorie avait déjà les attributs HTMX nécessaires (hx-get, hx-push-url, hx-target, hx-select, stopPropagation). Aucune modification nécessaire.
- Task 6 : 43 tests créés dans `tests/test_subcategories.py` — 8 tests schéma, 13 tests service, 22 tests route. Test de non-régression cascade inclus. Total suite : 210 tests, 0 régression.

### Change Log

- 2026-03-17 : Implémentation complète story 2.5 — sous-catégories (activités). 43 nouveaux tests, 210 tests total.

### File List

Fichiers créés :
- `app/templates/pages/category_detail.html`
- `app/templates/components/_subcategory_list.html`
- `app/templates/components/_subcategory_form.html`
- `app/templates/components/_subcategory_edit_form.html`
- `app/templates/components/_subcategory_delete_confirm.html`
- `tests/test_subcategories.py`

Fichiers modifiés :
- `app/schemas/category.py`
- `app/services/category_service.py`
- `app/routers/categories.py`
