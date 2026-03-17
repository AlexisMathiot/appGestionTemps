# Story 2.4 : Modification et suppression de catégorie

Status: review

## Story

As a utilisateur,
I want modifier ou supprimer une catégorie existante,
So that je puisse ajuster mon organisation au fil du temps.

## Acceptance Criteria

1. **Given** l'utilisateur a des catégories existantes
   **When** il clique sur le bouton d'édition d'une catégorie
   **Then** un modal d'édition s'ouvre avec les valeurs actuelles pré-remplies (nom, emoji, couleur, objectif)

2. **Given** l'utilisateur modifie une catégorie et valide
   **When** les changements sont sauvegardés
   **Then** la card est mise à jour via HTMX (fragment swap sur la grid entière)
   **And** les entrées de temps existantes restent liées (pas de suppression cascade sur TimeEntry)
   **And** un flash message "Catégorie modifiée" s'affiche

3. **Given** l'utilisateur soumet le formulaire d'édition avec des données invalides
   **When** la validation échoue
   **Then** le formulaire est ré-affiché avec les erreurs inline (422)
   **And** les valeurs saisies sont préservées

4. **Given** l'utilisateur clique sur le bouton de suppression d'une catégorie
   **When** le modal de confirmation apparaît
   **Then** un message demande "Supprimer cette catégorie ?" avec le nom de la catégorie
   **And** deux boutons sont visibles : "Annuler" et "Supprimer"

5. **Given** l'utilisateur confirme la suppression
   **When** la catégorie est supprimée
   **Then** la catégorie et ses sous-catégories (enfants par parent_id) sont supprimées
   **And** la grid d'accueil est mise à jour (rechargement via HTMX)
   **And** un flash message "Catégorie supprimée" s'affiche

6. **Given** l'utilisateur tente de modifier/supprimer une catégorie qui ne lui appartient pas
   **When** la requête est traitée
   **Then** une erreur 404 est retournée (pas de fuite d'information)

7. **Given** l'utilisateur ne peut modifier/supprimer que ses propres catégories racines (parent_id IS NULL)
   **When** il accède à l'édition
   **Then** seules les catégories racines sont éditables/supprimables (les sous-catégories seront gérées dans story 2.5)

## Tasks / Subtasks

- [x] Task 1 : Ajouter boutons éditer/supprimer sur `_category_card.html` (AC: #1, #4)
  - [x] 1.1 Ajouter un bouton icône "éditer" (crayon) sur la card — ouvre le modal d'édition
  - [x] 1.2 Ajouter un bouton icône "supprimer" (poubelle) sur la card — ouvre le modal de confirmation
  - [x] 1.3 Les boutons doivent être discrets mais accessibles (min 44x44px touch target)
  - [x] 1.4 Stopper la propagation du clic (les boutons sont dans la card cliquable)

- [x] Task 2 : Créer le schéma `CategoryUpdate` dans `app/schemas/category.py` (AC: #2, #3)
  - [x] 2.1 Même champs que `CategoryCreate` : name, emoji, color, goal_type, goal_value
  - [x] 2.2 Réutiliser les mêmes validators (ou hériter/factoriser)
  - [x] 2.3 Messages d'erreur en français

- [x] Task 3 : Ajouter `update_category()` et `delete_category()` dans `app/services/category_service.py` (AC: #2, #5, #6)
  - [x] 3.1 `get_category_by_id(db, category_id, user_id) -> Category | None` — query filtrée par user_id
  - [x] 3.2 `update_category(db, category, name, emoji, color, goal_type, goal_value) -> Category` — met à jour les champs, commit, refresh
  - [x] 3.3 `delete_category(db, category) -> None` — supprime la catégorie ; les enfants (sous-catégories) doivent aussi être supprimés (query DELETE WHERE parent_id = category.id puis delete category)

- [x] Task 4 : Ajouter les endpoints dans `app/routers/categories.py` (AC: #1, #2, #3, #5, #6)
  - [x] 4.1 `GET /categories/{category_id}/edit` — retourne le formulaire d'édition pré-rempli (fragment HTMX ou page complète)
  - [x] 4.2 `POST /categories/{category_id}/edit` — valide et met à jour la catégorie, redirect vers accueil
  - [x] 4.3 `POST /categories/{category_id}/delete` — supprime la catégorie après vérification propriétaire, redirect vers accueil
  - [x] 4.4 Vérifier `category.user_id == user.id` dans chaque endpoint, retourner 404 sinon
  - [x] 4.5 Utiliser `htmx_redirect(request, "/")` + `flash()` pour les redirections réussies

- [x] Task 5 : Créer/adapter les templates (AC: #1, #3, #4)
  - [x] 5.1 Créer `_category_edit_form.html` — réutiliser la structure de `_category_form.html` mais avec : action vers `/categories/{id}/edit`, valeurs pré-remplies, bouton "Enregistrer" au lieu de "Créer"
  - [x] 5.2 Créer `_category_delete_confirm.html` — modal de confirmation avec nom catégorie, boutons Annuler/Supprimer
  - [x] 5.3 Ajouter les modals d'édition et suppression dans `pages/home.html` (un par catégorie, ou un seul modal dynamique chargé via HTMX)

- [x] Task 6 : Tests (AC: #1-#7)
  - [x] 6.1 Tests service : get_category_by_id (trouvée, pas trouvée, autre user), update_category, delete_category (avec enfants)
  - [x] 6.2 Tests route : GET edit form, POST edit succès, POST edit validation error 422, POST delete succès, POST delete catégorie inexistante, POST delete catégorie autre user
  - [x] 6.3 Tests schéma : CategoryUpdate validation (si séparé de CategoryCreate)

## Dev Notes

### Architecture et patterns à suivre

- **Couches** : Router → Service → Model/Schema. Même pattern que stories 2.2 et 2.3.
- **HTMX** : Pattern existant = `hx-post` / `hx-get` avec `hx-target="#app-shell"` et `hx-select="#app-shell"` pour full page swap. Utiliser le même pattern.
- **Redirect** : `htmx_redirect(request, "/")` du module `app/routers/helpers.py` — retourne `HX-Redirect` pour HTMX, `RedirectResponse(status_code=303)` pour normal.
- **Flash** : `flash(response, "success", "message")` du module `app/services/flash_service.py`.
- **Erreurs** : Validation Pydantic → 422 avec re-render formulaire + erreurs inline. Pattern existant dans `POST /categories`.

### Modèle Category existant — PAS de migration nécessaire

Le modèle `app/models/category.py` possède déjà tous les champs nécessaires. La relation `children` existe (self-referential via `parent_id`). **Pas de modification du modèle ni de migration Alembic.**

Champs du modèle :
```
id (UUID v7), user_id (FK → users.id), parent_id (FK → categories.id, nullable),
name (String 100), emoji (String 10), color (String 7, #RRGGBB),
goal_type (String, nullable), goal_value (Integer, nullable),
position (Integer), created_at (DateTime UTC)
```

Contraintes CHECK en base :
- `ck_categories_goal_consistency` : `(goal_type IS NULL) = (goal_value IS NULL)`
- `ck_categories_goal_value_positive` : `goal_value > 0`

### Schéma Pydantic — `CategoryUpdate`

Fichier : `app/schemas/category.py`

`CategoryUpdate` peut être identique à `CategoryCreate` (mêmes champs et validations). Option recommandée : soit hériter de `CategoryCreate`, soit simplement réutiliser le même schéma sous un alias. Les deux approches sont acceptables — le plus simple est de réutiliser `CategoryCreate` directement puisque les champs et validations sont identiques.

### Service — nouvelles fonctions requises

Fichier : `app/services/category_service.py`

Fonctions à ajouter :

```python
async def get_category_by_id(db: AsyncSession, category_id: UUID, user_id: UUID) -> Category | None:
    """Retourne la catégorie si elle appartient à l'utilisateur, sinon None."""
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    return result.scalar_one_or_none()

async def update_category(db: AsyncSession, category: Category, name: str, emoji: str, color: str,
                          goal_type: str | None = None, goal_value: int | None = None) -> Category:
    """Met à jour les champs de la catégorie."""
    category.name = name
    category.emoji = emoji
    category.color = color
    category.goal_type = goal_type
    category.goal_value = goal_value
    await db.commit()
    await db.refresh(category)
    return category

async def delete_category(db: AsyncSession, category: Category) -> None:
    """Supprime la catégorie et ses sous-catégories."""
    # Supprimer les enfants d'abord (sous-catégories)
    await db.execute(delete(Category).where(Category.parent_id == category.id))
    await db.delete(category)
    await db.commit()
```

**Note** : Pas besoin d'advisory lock pour update/delete (pas de calcul de position).

### Routeur — endpoints à ajouter

Fichier : `app/routers/categories.py`

3 nouveaux endpoints :

1. **`GET /categories/{category_id}/edit`** — Retourne le formulaire d'édition pré-rempli
   - Charger la catégorie via `get_category_by_id(db, category_id, user.id)`
   - Si None → 404
   - Retourner le template `_category_edit_form.html` avec les valeurs pré-remplies dans `form_data`

2. **`POST /categories/{category_id}/edit`** — Traiter la modification
   - Charger la catégorie → 404 si absente
   - Parser le formulaire, valider via `CategoryCreate` (réutiliser le schéma)
   - Si erreur validation → 422 avec formulaire ré-affiché
   - Sinon → `update_category()`, `htmx_redirect("/")`, `flash("Catégorie modifiée")`

3. **`POST /categories/{category_id}/delete`** — Supprimer
   - Charger la catégorie → 404 si absente
   - `delete_category()`, `htmx_redirect("/")`, `flash("Catégorie supprimée")`

**Pattern category_id** : Utiliser `category_id: UUID` dans la signature FastAPI. FastAPI parse automatiquement les UUID depuis l'URL.

### Templates — édition

Fichier : `app/templates/components/_category_edit_form.html`

Réutiliser la structure exacte de `_category_form.html` avec ces différences :
- Action du formulaire : `hx-post="/categories/{{ category.id }}/edit"`
- Valeurs pré-remplies dans les champs (name, emoji sélectionné, couleur sélectionnée)
- Toggle objectif coché si `category.goal_type` est défini, section visible, valeurs pré-remplies
- Bouton "Enregistrer" au lieu de "Créer"
- Titre "Modifier la catégorie" au lieu de "Nouvelle catégorie"

### Templates — confirmation suppression

Fichier : `app/templates/components/_category_delete_confirm.html`

Modal DaisyUI simple :
```html
<dialog id="delete-modal-{{ category.id }}" class="modal modal-bottom sm:modal-middle">
  <div class="modal-box">
    <h3 class="text-lg font-bold">Supprimer cette catégorie ?</h3>
    <p class="py-4">{{ category.emoji }} {{ category.name }} sera supprimée définitivement.</p>
    <div class="modal-action">
      <form method="dialog"><button class="btn">Annuler</button></form>
      <form hx-post="/categories/{{ category.id }}/delete" hx-target="#app-shell" hx-select="#app-shell">
        <button class="btn btn-error">Supprimer</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>
```

### Templates — boutons sur la card

Fichier : `app/templates/components/_category_card.html`

Ajouter des boutons éditer/supprimer dans la card. Attention : la card entière est cliquable (`hx-get`). Les boutons doivent utiliser `onclick="event.stopPropagation()"` pour ne pas déclencher le clic de la card.

Approche recommandée : ajouter une zone d'action en haut à droite de la card :
```html
<div class="absolute top-1 right-1 flex gap-1">
  <button onclick="event.stopPropagation(); document.getElementById('edit-modal-{{ category.id }}').showModal()"
          class="btn btn-ghost btn-xs min-h-[44px] min-w-[44px]" aria-label="Modifier {{ category.name }}">
    ✏️
  </button>
  <button onclick="event.stopPropagation(); document.getElementById('delete-modal-{{ category.id }}').showModal()"
          class="btn btn-ghost btn-xs min-h-[44px] min-w-[44px]" aria-label="Supprimer {{ category.name }}">
    🗑️
  </button>
</div>
```

### Intégration dans home.html

Fichier : `app/templates/pages/home.html`

Pour chaque catégorie, il faut un modal d'édition et un modal de suppression. Deux approches :

**Approche A (recommandée — simple)** : Inclure les modals dans la boucle `for category in categories` de `home.html`, après la grid. Chaque catégorie génère son edit-modal et son delete-modal. C'est simple et fonctionne bien avec peu de catégories (usage personnel).

**Approche B (optimisée)** : Un seul modal générique, et les boutons chargent le contenu du formulaire via HTMX (`hx-get="/categories/{id}/edit"` → insère le formulaire dans le modal). Plus complexe mais évite la duplication HTML.

**Choix** : Approche A car le nombre de catégories sera faible (< 20) et c'est cohérent avec le pattern du modal de création déjà en place.

Le modal d'édition doit charger le formulaire pré-rempli. Deux options :
- **Option 1** : Le formulaire est rendu côté serveur au chargement de la page (comme le modal de création) → simple mais charge le HTML pour chaque catégorie
- **Option 2** : Le bouton édit fait un `hx-get="/categories/{id}/edit"` qui retourne le formulaire, injecté dans un modal → plus léger au chargement initial

**Choix** : Option 2 (chargement HTMX) pour le formulaire d'édition car il contient beaucoup de HTML (picker emoji, couleurs). Le modal de suppression reste statique (peu de HTML).

Flow pour l'édition :
1. Clic bouton éditer → ouvre un modal vide + déclenche `hx-get="/categories/{id}/edit"` → injecte le formulaire dans le modal
2. Soumission formulaire → `hx-post="/categories/{id}/edit"` → redirect ou re-render

### Suppression en cascade des sous-catégories

La story mentionne "la catégorie et ses sous-catégories sont supprimées". Le modèle utilise `parent_id` (self-reference). Il faut explicitement supprimer les enfants avant le parent. Pour le MVP, une suppression en un niveau suffit (pas de récursion nécessaire car les sous-catégories ne peuvent pas avoir d'enfants dans le design actuel).

**Note** : Les `TimeEntry` ne seront pas encore liées aux catégories (Epic 3). Mais préparer le code pour ne PAS cascade-delete les entrées de temps — quand elles existeront, il faudra décider de la stratégie (soft-delete, rattachement, etc.). Pour l'instant, la suppression simple suffit.

### Anti-patterns à éviter

- **NE PAS** créer de migration Alembic — le modèle est complet
- **NE PAS** modifier `app/models/category.py`
- **NE PAS** utiliser `DELETE` HTTP method — utiliser `POST /categories/{id}/delete` car les formulaires HTML ne supportent que GET/POST
- **NE PAS** oublier de vérifier `category.user_id == user.id` — toujours filtrer par user
- **NE PAS** permettre l'édition/suppression des sous-catégories ici (story 2.5)
- **NE PAS** utiliser Alpine.js ou framework JS — vanilla JS inline suffit
- **NE PAS** oublier `event.stopPropagation()` sur les boutons dans la card cliquable

### Project Structure Notes

Fichiers à créer :
- `app/templates/components/_category_edit_form.html` — formulaire d'édition
- `app/templates/components/_category_delete_confirm.html` — modal de confirmation suppression

Fichiers à modifier :
- `app/schemas/category.py` — ajouter `CategoryUpdate` (ou réutiliser `CategoryCreate`)
- `app/services/category_service.py` — ajouter get_category_by_id, update_category, delete_category
- `app/routers/categories.py` — ajouter GET edit, POST edit, POST delete
- `app/templates/components/_category_card.html` — ajouter boutons éditer/supprimer
- `app/templates/pages/home.html` — ajouter modals (édition HTMX + suppression statique)
- `tests/test_category_creation.py` — ou créer `tests/test_category_edit_delete.py`

Fichiers à NE PAS modifier :
- `app/models/category.py` — déjà complet
- `alembic/` — aucune migration nécessaire
- `app/templates/components/_category_grid.html` — pas de changement
- `app/templates/components/_category_form.html` — garder pour la création (ne pas modifier)

### Previous Story Intelligence (Story 2.3)

- Le pattern form + validation 422 fonctionne bien — le réutiliser
- Les tests couvrent 148 cas — maintenir ou dépasser cette couverture
- Le toggle objectif (show/hide avec disabled) fonctionne — réutiliser dans le formulaire d'édition
- La convention de commit est `feat: description en français (story X.Y)`
- Le schéma `CategoryCreate` dans `app/schemas/category.py` contient toute la validation nécessaire (name, emoji, color, goal_type, goal_value avec model_validator)

### Git Intelligence

Derniers commits :
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
- Nouveau fichier test recommandé : `tests/test_category_edit_delete.py` pour séparer clairement les tests

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Écran 4 : Modal Création Catégorie]
- [Source: app/models/category.py — modèle avec tous les champs]
- [Source: app/schemas/category.py — schéma CategoryCreate réutilisable]
- [Source: app/routers/categories.py — routeur existant à étendre]
- [Source: app/services/category_service.py — service existant à étendre]
- [Source: app/routers/helpers.py — htmx_redirect utilitaire]
- [Source: app/services/flash_service.py — flash messages]
- [Source: _bmad-output/implementation-artifacts/2-3-objectif-optionnel-sur-une-categorie.md — story précédente]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun problème de debug significatif. Le seul ajustement a été l'extraction du user_id dans les tests : remplacement de `import jwt` par `get_user_id_from_cookie` d'itsdangerous.

### Completion Notes List

- **Task 1** : Boutons ✏️ et 🗑️ ajoutés en position absolue (top-right) sur la card. `event.stopPropagation()` + `event.preventDefault()` pour éviter le clic de la card. Le bouton édit charge le formulaire via `hx-get` puis ouvre le modal via `hx-on::after-request`. Touch targets 44x44px respectés.
- **Task 2** : `CategoryUpdate = CategoryCreate` (alias simple, mêmes champs et validations).
- **Task 3** : 3 nouvelles fonctions dans le service — `get_category_by_id` (filtré par user_id), `update_category`, `delete_category` (avec suppression enfants via DELETE WHERE parent_id).
- **Task 4** : 3 endpoints — `GET /{id}/edit` (formulaire pré-rempli), `POST /{id}/edit` (validation + update), `POST /{id}/delete`. Tous vérifient ownership via `get_category_by_id` → 404 si pas propriétaire.
- **Task 5** : `_category_edit_form.html` (réutilise la structure du form de création, valeurs pré-remplies, bouton "Enregistrer"), `_category_delete_confirm.html` (modal DaisyUI de confirmation). Modals intégrés dans `home.html` via boucle for (Approche A). Le formulaire d'édition est chargé dynamiquement via HTMX (Option 2).
- **Task 6** : 19 tests dans `test_category_edit_delete.py` — 7 tests service (get/update/delete + enfants), 12 tests route (GET form, POST edit succès/erreur/404/autre user, POST delete succès/404/autre user). Suite complète : 167 tests, 0 échecs.

### File List

Fichiers créés :
- `app/templates/components/_category_edit_form.html`
- `app/templates/components/_category_delete_confirm.html`
- `tests/test_category_edit_delete.py`

Fichiers modifiés :
- `app/schemas/category.py` — ajout alias `CategoryUpdate`
- `app/services/category_service.py` — ajout `get_category_by_id`, `update_category`, `delete_category`
- `app/routers/categories.py` — ajout endpoints GET/POST edit, POST delete
- `app/templates/components/_category_card.html` — ajout boutons éditer/supprimer
- `app/templates/pages/home.html` — ajout modals édition et suppression

### Change Log

- 2026-03-17 : Implémentation complète story 2.4 — modification et suppression de catégorie (19 nouveaux tests, 167 total)
