# Story 2.3 : Objectif optionnel sur une catégorie

Status: review

## Story

As a utilisateur,
I want définir un objectif optionnel sur une catégorie (par jour ou par semaine),
So that je puisse me fixer des cibles de temps.

## Acceptance Criteria

1. **Given** l'utilisateur est dans le modal de création de catégorie
   **When** il active le toggle "Définir un objectif"
   **Then** un sélecteur apparaît : type (par jour / par semaine) + valeur (durée en minutes)

2. **Given** l'utilisateur crée une catégorie avec objectif "15 min/jour"
   **When** la catégorie est sauvegardée
   **Then** l'objectif est stocké en base (goal_type="daily", goal_value=15)
   **And** l'objectif est affiché sur la card de la catégorie

3. **Given** l'utilisateur ne définit pas d'objectif
   **When** il crée la catégorie
   **Then** goal_type et goal_value sont null
   **And** aucun indicateur d'objectif n'est affiché sur la card

4. **Given** l'utilisateur active l'objectif puis le désactive avant de soumettre
   **When** il crée la catégorie
   **Then** goal_type et goal_value sont null (les champs masqués ne sont pas envoyés)

## Tasks / Subtasks

- [x] Task 1 : Étendre le schéma Pydantic `CategoryCreate` (AC: #1, #2, #3)
  - [x] 1.1 Ajouter `goal_type: str | None = None` avec validation ("daily" ou "weekly" ou None)
  - [x] 1.2 Ajouter `goal_value: int | None = None` avec validation (> 0, ≤ 1440 min si daily, ≤ 10080 si weekly)
  - [x] 1.3 Ajouter `model_validator` pour cohérence : les deux doivent être présents ensemble ou absents ensemble
  - [x] 1.4 Messages d'erreur en français

- [x] Task 2 : Mettre à jour le routeur `POST /categories` (AC: #2, #3)
  - [x] 2.1 Extraire `goal_type` et `goal_value` du formulaire
  - [x] 2.2 Passer les valeurs validées à `category_service.create_category()`
  - [x] 2.3 Inclure `goal_type` et `goal_value` dans `form_data` pour re-render en cas d'erreur 422

- [x] Task 3 : Étendre `category_service.create_category()` (AC: #2, #3)
  - [x] 3.1 Ajouter paramètres `goal_type: str | None = None` et `goal_value: int | None = None`
  - [x] 3.2 Passer ces valeurs au constructeur `Category(...)`

- [x] Task 4 : Ajouter le toggle objectif dans `_category_form.html` (AC: #1, #4)
  - [x] 4.1 Ajouter une checkbox DaisyUI `toggle` labellée "Définir un objectif"
  - [x] 4.2 Section conditionnelle (show/hide JS vanilla) contenant :
    - Select `goal_type` : "Par jour" / "Par semaine"
    - Input number `goal_value` : placeholder "Minutes", min=1
  - [x] 4.3 Quand le toggle est décoché, les inputs `goal_type` et `goal_value` doivent être `disabled` (non envoyés dans le formulaire)
  - [x] 4.4 Préserver l'état form_data en cas de re-render (erreur 422)

- [x] Task 5 : Afficher l'objectif sur `_category_card.html` (AC: #2, #3)
  - [x] 5.1 Si `category.goal_type` et `category.goal_value` existent, afficher une ligne sous le temps (ex: "🎯 15min/jour")
  - [x] 5.2 Si pas d'objectif, ne rien afficher de plus

- [x] Task 6 : Tests (AC: #1, #2, #3, #4)
  - [x] 6.1 Tests schéma : goal_type/goal_value valides, invalides, cohérence, bornes
  - [x] 6.2 Tests service : création avec objectif, sans objectif
  - [x] 6.3 Tests route : POST avec objectif, POST sans objectif, POST avec toggle désactivé, validation errors
  - [x] 6.4 Tests modèle : contraintes CHECK existantes (ck_categories_goal_consistency, ck_categories_goal_value_positive)

## Dev Notes

### Architecture et patterns à suivre

- **Couches** : Router → Service → Model/Schema. Même pattern que story 2.2.
- **Validation** : Pydantic v2 `field_validator` + `model_validator` dans `app/schemas/category.py`
- **Erreurs français** : Tous les messages ValidationError en français (pattern existant)
- **HTMX** : Le formulaire utilise `hx-post="/categories"` avec `hx-target="#app-shell"` et `hx-select="#app-shell"` — ne pas modifier ce pattern
- **Redirect** : `_redirect(request, "/")` avec `HX-Redirect` pour HTMX, 303 pour normal

### Modèle Category existant — PAS de migration nécessaire

Le modèle `app/models/category.py` possède **déjà** les champs :
```python
goal_type: Mapped[str | None]   # "daily" | "weekly"
goal_value: Mapped[int | None]  # minutes
```

Avec les contraintes CHECK en base :
- `ck_categories_goal_consistency` : `(goal_type IS NULL) = (goal_value IS NULL)`
- `ck_categories_goal_value_positive` : `goal_value > 0`

**Pas besoin de migration Alembic. Pas besoin de toucher au modèle.**

### Schéma Pydantic — modifications requises

Fichier : `app/schemas/category.py`

Le schéma `CategoryCreate` actuel ne contient que `name`, `emoji`, `color`. Ajouter :
```python
goal_type: str | None = None
goal_value: int | None = None
```

Validations à implémenter :
- `goal_type` : doit être `"daily"`, `"weekly"`, ou `None`
- `goal_value` : entier > 0, ou `None`
- **Cohérence** (model_validator) : les deux champs doivent être ensemble (`None`/`None`) ou ensemble définis. Si un seul est fourni → erreur.
- **Conversion** : si `goal_value` arrive en string vide (formulaire HTML), le traiter comme `None`

### Service — modifications minimales

Fichier : `app/services/category_service.py`

Ajouter les paramètres `goal_type` et `goal_value` à la signature de `create_category()` et les passer au constructeur `Category(...)`. Le modèle et les contraintes CHECK gèrent la cohérence en base.

### Routeur — modifications requises

Fichier : `app/routers/categories.py`

Dans `create_category()` :
- Extraire `goal_type = form.get("goal_type") or None` et `goal_value`
- Convertir `goal_value` en `int` si présent (formulaire envoie des strings), sinon `None`
- Passer au schéma `CategoryCreate(name=..., emoji=..., color=..., goal_type=..., goal_value=...)`
- Inclure dans `form_data` dict pour re-render 422

### Template formulaire — toggle show/hide

Fichier : `app/templates/components/_category_form.html`

Ajouter **après** le fieldset couleur et **avant** `modal-action` :

1. **Checkbox toggle** DaisyUI : `<input type="checkbox" class="toggle toggle-primary">` avec label "Définir un objectif"
2. **Section conditionnelle** (masquée par défaut) :
   - `<select name="goal_type">` avec options "Par jour" (value="daily") et "Par semaine" (value="weekly")
   - `<input type="number" name="goal_value" min="1" placeholder="Minutes">`
3. **JS vanilla inline** (pas de fichier séparé) : toggle la visibilité de la section et `disabled` sur les inputs quand décoché

Pattern show/hide recommandé :
```html
<script>
document.getElementById('goal-toggle').addEventListener('change', function() {
    const section = document.getElementById('goal-section');
    const inputs = section.querySelectorAll('input, select');
    section.classList.toggle('hidden', !this.checked);
    inputs.forEach(el => el.disabled = !this.checked);
});
</script>
```

**IMPORTANT** : Quand les inputs sont `disabled`, le navigateur ne les envoie PAS dans le FormData. Cela garantit que `goal_type` et `goal_value` sont absents quand le toggle est off → le schéma Pydantic les recevra comme `None`.

### Template card — affichage objectif

Fichier : `app/templates/components/_category_card.html`

Ajouter sous la ligne temps (`<p class="text-xs text-secondary">0min</p>`) :
```html
{% if category.goal_type and category.goal_value %}
<p class="text-xs text-accent">🎯 {{ category.goal_value }}min/{{ "jour" if category.goal_type == "daily" else "semaine" }}</p>
{% endif %}
```

### Préservation de l'état formulaire (re-render 422)

Dans le routeur, `form_data` doit inclure :
```python
"goal_enabled": bool(goal_type),  # pour re-cocher le toggle
"goal_type": goal_type,
"goal_value": goal_value,
```

Dans le template, si `form_data.get('goal_enabled')` :
- La checkbox toggle doit être `checked`
- La section goal doit être visible (pas `hidden`)
- Les inputs goal ne doivent pas être `disabled`
- Les valeurs `goal_type` et `goal_value` doivent être restaurées

### Anti-patterns à éviter

- **NE PAS** créer de migration Alembic — les champs existent déjà en base
- **NE PAS** modifier `app/models/category.py` — le modèle est complet
- **NE PAS** utiliser un framework JS ou Alpine.js — vanilla JS inline suffit
- **NE PAS** envoyer `goal_type`/`goal_value` quand le toggle est off — utiliser `disabled` sur les inputs
- **NE PAS** ajouter de librairie pour le time picker — un simple input number en minutes suffit pour le MVP
- **NE PAS** oublier de convertir les strings vides du formulaire en `None` dans le routeur

### Project Structure Notes

Fichiers à modifier :
- `app/schemas/category.py` — ajouter goal_type, goal_value + validators
- `app/services/category_service.py` — ajouter paramètres goal_type, goal_value
- `app/routers/categories.py` — extraire et passer les champs objectif
- `app/templates/components/_category_form.html` — toggle + section objectif
- `app/templates/components/_category_card.html` — affichage objectif sur card
- `tests/test_category_creation.py` — nouveaux tests objectif

Fichiers à NE PAS modifier :
- `app/models/category.py` — déjà complet
- `alembic/` — aucune migration nécessaire
- `app/templates/pages/home.html` — pas de changement nécessaire
- `app/templates/components/_category_grid.html` — pas de changement nécessaire

### Previous Story Intelligence (Story 2.2)

- Pattern form validation : `CategoryCreate` schema avec `field_validator`, erreurs en français, re-render 422 avec `form_data` et `errors`
- Pattern HTMX form : `hx-post`, `hx-target="#app-shell"`, `hx-select="#app-shell"`, `hx-swap="outerHTML"` — fonctionne bien, ne pas changer
- Le modal DaisyUI 5 utilise `<dialog>` natif avec `showModal()` — OK
- Advisory lock dans `create_category` pour position — déjà en place
- 124 tests passent au dernier commit — maintenir cette base

### Git Intelligence

Derniers commits :
- `d704e71` feat: création de catégorie via modal + correctifs code review (story 2.2)
- `77ebff5` feat: modèle Category, écran d'accueil avec empty state et grid (story 2.1)
- `2d4289c` feat: migration CDN vers Tailwind CSS 4 + DaisyUI 5 + HTMX 2.0.8 en local

Convention commit : `feat: description courte en français (story X.Y)`

### Testing Standards

- Framework : pytest + pytest-asyncio
- Fixtures : `db_session`, `client`, `authenticated_client` dans `tests/conftest.py`
- Organisation : tests schéma (sync), tests service (async avec db), tests route (async avec client)
- Assertions : vérifier status code, contenu réponse, état base de données
- Pattern HTMX : ajouter header `{"HX-Request": "true"}` pour tester les réponses HTMX

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Écran 4 : Modal Création Catégorie]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns]
- [Source: app/models/category.py — modèle avec goal_type/goal_value existants]
- [Source: app/schemas/category.py — schéma à étendre]
- [Source: app/routers/categories.py — routeur à modifier]
- [Source: app/services/category_service.py — service à étendre]
- [Source: app/templates/components/_category_form.html — formulaire à modifier]
- [Source: app/templates/components/_category_card.html — card à modifier]
- [Source: _bmad-output/implementation-artifacts/2-2-creation-dune-categorie.md — story précédente]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

Aucun problème rencontré.

### Completion Notes List

- Task 1 : Schéma Pydantic étendu avec `goal_type`, `goal_value`, `field_validator`, `model_validator` (cohérence, bornes daily/weekly, coercition string vide → None). Messages en français.
- Task 2 : Routeur mis à jour pour extraire les champs objectif du formulaire, les passer au schéma, et inclure `goal_enabled`/`goal_type`/`goal_value` dans `form_data` pour re-render 422.
- Task 3 : Service étendu avec paramètres `goal_type` et `goal_value` passés au constructeur `Category(...)`.
- Task 4 : Template formulaire avec toggle DaisyUI, section conditionnelle show/hide, inputs disabled quand toggle off, préservation état 422.
- Task 5 : Template card affiche "🎯 Xmin/jour" ou "🎯 Xmin/semaine" si objectif défini.
- Task 6 : 24 nouveaux tests ajoutés (schéma: 14, service: 2, route: 6, contraintes DB: 2). Total suite: 148 tests, 0 échec.

### Change Log

- 2026-03-17 : Implémentation story 2.3 — objectif optionnel sur catégorie (6 tasks, 24 nouveaux tests)

### File List

- app/schemas/category.py (modifié)
- app/services/category_service.py (modifié)
- app/routers/categories.py (modifié)
- app/templates/components/_category_form.html (modifié)
- app/templates/components/_category_card.html (modifié)
- tests/test_category_creation.py (modifié)
