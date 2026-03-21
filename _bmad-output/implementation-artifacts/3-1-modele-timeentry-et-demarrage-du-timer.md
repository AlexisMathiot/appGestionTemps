# Story 3.1 : Modèle TimeEntry et démarrage du timer

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a utilisateur,
I want démarrer un timer en tappant sur une catégorie,
So that je puisse tracker mon temps en un minimum d'interactions.

## Acceptance Criteria

1. **Given** l'utilisateur est sur l'accueil avec des catégories
   **When** il tape sur une catégorie (ou sous-catégorie depuis la page détail)
   **Then** le modèle TimeEntry (id UUID v7, user_id FK, category_id FK, started_at DateTime UTC, ended_at nullable, duration_seconds nullable, note nullable, created_at) est créé avec migration Alembic
   **And** une entrée TimeEntry est créée côté serveur (POST /api/timer/start) avec started_at = now()
   **And** le timer démarre côté client (JavaScript setInterval 1s)
   **And** l'état du timer est persisté dans localStorage (timer_active, start_time, entry_id, category_id, category_name, category_emoji, category_color)
   **And** un header sticky affiche le timer actif avec le temps en font mono (JetBrains Mono, 48-64px)
   **And** la catégorie active est visuellement mise en avant (couleur de la catégorie)
   **And** une vibration légère est déclenchée sur mobile (navigator.vibrate)

2. **Given** un timer est déjà actif
   **When** l'utilisateur tape sur une autre catégorie
   **Then** le nouveau timer ne démarre PAS (un seul timer actif à la fois)
   **And** un message flash informe l'utilisateur qu'un timer est déjà en cours

3. **Given** l'utilisateur recharge la page ou navigue entre sections
   **When** le DOM est prêt
   **Then** le timer est réconcilié depuis localStorage (start_time stocké)
   **And** le temps affiché est correct (now - start_time)
   **And** le header sticky timer est restauré

4. **Given** l'utilisateur n'est pas authentifié
   **When** il tente de démarrer un timer
   **Then** il est redirigé vers `/login` (401 + HX-Redirect standard)

5. **Given** l'utilisateur tente de démarrer un timer sur une catégorie qui ne lui appartient pas
   **When** la requête est traitée
   **Then** une erreur 404 est retournée (pas de fuite d'information)

## Tasks / Subtasks

- [x] Task 1 : Créer le modèle TimeEntry (AC: #1)
  - [x] 1.1 Créer `app/models/time_entry.py` avec : id (UUID v7, PK), user_id (FK users.id, CASCADE), category_id (FK categories.id, SET NULL), started_at (DateTime UTC, non-null), ended_at (DateTime UTC, nullable), duration_seconds (Integer, nullable), note (Text, nullable), created_at (DateTime UTC, default utcnow)
  - [x] 1.2 Index composite sur (user_id, started_at DESC) pour requêtes stats futures
  - [x] 1.3 Index sur category_id pour les jointures
  - [x] 1.4 Exporter dans `app/models/__init__.py`
  - [x] 1.5 Créer migration Alembic : `alembic revision --autogenerate -m "create_time_entries_table"`
  - [x] 1.6 Vérifier et appliquer la migration : `alembic upgrade head`

- [x] Task 2 : Créer le schéma Pydantic TimerStart (AC: #1, #5)
  - [x] 2.1 Créer `app/schemas/time_entry.py` avec `TimerStartRequest(BaseModel)` : category_id (UUID, obligatoire)
  - [x] 2.2 Créer `TimerStartResponse(BaseModel)` : entry_id (UUID), category_id (UUID), category_name (str), category_emoji (str), category_color (str), started_at (datetime)

- [x] Task 3 : Créer le service timer (AC: #1, #2, #5)
  - [x] 3.1 Créer `app/services/timer_service.py`
  - [x] 3.2 `start_timer(db, user_id, category_id) -> TimeEntry` : vérifier que la catégorie appartient au user, vérifier qu'aucun timer actif (ended_at IS NULL pour ce user), créer TimeEntry avec started_at=now
  - [x] 3.3 `get_active_timer(db, user_id) -> TimeEntry | None` : retourner l'entrée avec ended_at IS NULL pour ce user, eager load category
  - [x] 3.4 Lever une exception custom `TimerAlreadyActiveError` si un timer est déjà actif (AC: #2)

- [x] Task 4 : Créer le routeur timer (AC: #1, #2, #4, #5)
  - [x] 4.1 Créer `app/routers/timer.py` avec prefix `/api/timer`
  - [x] 4.2 `POST /api/timer/start` : parser category_id depuis le formulaire, appeler `start_timer()`, retourner le fragment `_timer_display.html` (pour HTMX)
  - [x] 4.3 Gérer `TimerAlreadyActiveError` → flash message "Un timer est déjà en cours" + redirect (AC: #2)
  - [x] 4.4 Enregistrer le routeur dans `app/main.py` : `app.include_router(timer.router)`

- [x] Task 5 : Créer le JavaScript timer client-side (AC: #1, #3)
  - [x] 5.1 Créer `app/static/js/timer.js`
  - [x] 5.2 Fonctions : `startTimer(entryId, startTime, categoryName, categoryEmoji, categoryColor)`, `stopTimerDisplay()`, `formatTime(seconds) -> "HH:MM:SS"`, `restoreTimer()`
  - [x] 5.3 `startTimer` : sauver dans localStorage, démarrer setInterval 1s, mettre à jour l'affichage, montrer le header sticky
  - [x] 5.4 `restoreTimer` : vérifier localStorage au chargement, réconcilier temps (Date.now() - start_time), relancer l'affichage
  - [x] 5.5 Déclencher vibration légère au démarrage : `navigator.vibrate && navigator.vibrate(50)`
  - [x] 5.6 Inclure le script dans `base.html` : `<script src="/static/js/timer.js" defer></script>`

- [x] Task 6 : Créer les templates timer (AC: #1, #3)
  - [x] 6.1 Créer `app/templates/components/_timer_display.html` : header sticky avec emoji + nom catégorie + temps HH:MM:SS (font JetBrains Mono 48px) + boutons Pause/Stop (Pause et Stop seront implémentés stories 3.2/3.3 — mettre des boutons désactivés ou placeholder)
  - [x] 6.2 Intégrer le timer sticky dans `base.html` : un div `#timer-container` en haut du body (avant le contenu) qui sera rempli dynamiquement
  - [x] 6.3 Style : couleur de fond basée sur la catégorie active, contraste WCAG AA

- [x] Task 7 : Modifier l'accueil pour déclencher le timer au tap (AC: #1, #2)
  - [x] 7.1 Modifier `app/templates/components/_category_card.html` : le tap sur une card envoie `hx-post="/api/timer/start"` avec `hx-vals='{"category_id": "{{ category.id }}"}'`
  - [x] 7.2 ATTENTION : la card a actuellement `hx-get="/categories/{{ category.id }}"` pour naviguer vers le détail. Il faut changer le comportement : **tap = démarrer timer**, un bouton/icône séparé pour aller au détail (ou long-press, ou bouton "...")
  - [x] 7.3 Mettre à jour `_category_card.html` : `hx-post="/api/timer/start"` avec `hx-target="#timer-container"` pour injecter le fragment timer
  - [x] 7.4 Inclure un attribut `hx-vals` avec `category_id` dans le POST
  - [x] 7.5 Si timer déjà actif, la réponse du serveur doit être un flash message (pas de nouveau timer)

- [x] Task 8 : Gérer le démarrage timer depuis la page détail catégorie (AC: #1)
  - [x] 8.1 Ajouter un bouton "Démarrer le timer" sur `category_detail.html` qui POST vers `/api/timer/start` avec le category_id
  - [x] 8.2 Ajouter des boutons de démarrage timer sur chaque sous-catégorie dans `_subcategory_list.html` (icône play)
  - [x] 8.3 Même pattern HTMX que pour les cards d'accueil

- [x] Task 9 : Mettre à jour la home pour afficher le timer actif (AC: #3)
  - [x] 9.1 Dans `app/routers/pages.py` GET `/` : appeler `get_active_timer(db, user.id)` et passer au template
  - [x] 9.2 Dans `home.html` : si timer actif, inclure `_timer_display.html` + trigger JS `restoreTimer()` avec les données du timer
  - [x] 9.3 Le header sticky doit être visible sur TOUTES les pages quand un timer est actif — intégrer dans `base.html`

- [x] Task 10 : Tests (AC: #1-#5)
  - [x] 10.1 Tests modèle : vérifier création TimeEntry, contraintes FK, index, nullable fields
  - [x] 10.2 Tests schéma : TimerStartRequest validation (category_id obligatoire, format UUID)
  - [x] 10.3 Tests service : start_timer succès, start_timer catégorie inexistante (404), start_timer catégorie autre user (404), start_timer timer déjà actif (erreur), get_active_timer avec/sans timer actif
  - [x] 10.4 Tests route : POST /api/timer/start succès (vérifier status code, TimeEntry créée en base, réponse HTML), POST /api/timer/start timer déjà actif (flash message), POST /api/timer/start non authentifié (401/redirect), POST /api/timer/start catégorie invalide (404)
  - [x] 10.5 Vérifier non-régression : les 181 tests existants passent toujours (201 total)

## Dev Notes

### Architecture et patterns à suivre

- **Couches** : Router → Service → Model/Schema. Même pattern que toutes les stories précédentes.
- **HTMX** : Pattern existant = `hx-post` / `hx-get` avec `hx-target="#app-shell"` et `hx-select="#app-shell"` pour full page swap. Pour le timer, utiliser `hx-target="#timer-container"` pour injecter uniquement le fragment timer sans recharger toute la page.
- **Redirect** : `htmx_redirect(request, url)` du module `app/routers/helpers.py`.
- **Flash** : `flash(response, "success", "message")` du module `app/services/flash_service.py`.
- **Auth** : `Depends(get_current_user)` sur tous les endpoints timer.
- **DB session** : `Depends(get_db)` pour obtenir l'AsyncSession.

### Modèle TimeEntry — à créer

Fichier : `app/models/time_entry.py`

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relations
    user = relationship("User", back_populates="time_entries")
    category = relationship("Category", back_populates="time_entries")

    __table_args__ = (
        Index("ix_time_entries_user_started", "user_id", "started_at"),
        Index("ix_time_entries_category", "category_id"),
    )
```

**IMPORTANT** : Ajouter `time_entries` relationship dans `User` et `Category` models :
- `app/models/user.py` : `time_entries = relationship("TimeEntry", back_populates="user", cascade="all, delete-orphan")`
- `app/models/category.py` : `time_entries = relationship("TimeEntry", back_populates="category")`

### Schéma Pydantic

Fichier : `app/schemas/time_entry.py`

```python
from pydantic import BaseModel
import uuid
from datetime import datetime


class TimerStartRequest(BaseModel):
    category_id: uuid.UUID
```

Pas besoin de schéma de réponse complexe — la réponse est un fragment HTML (pas JSON).

### Service Timer

Fichier : `app/services/timer_service.py`

Pattern identique aux services existants : fonctions async, premier argument `db: AsyncSession`.

```python
async def get_active_timer(db: AsyncSession, user_id: uuid.UUID) -> TimeEntry | None:
    result = await db.execute(
        select(TimeEntry)
        .options(selectinload(TimeEntry.category))
        .where(TimeEntry.user_id == user_id, TimeEntry.ended_at.is_(None))
    )
    return result.scalar_one_or_none()

async def start_timer(db: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID) -> TimeEntry:
    # 1. Vérifier catégorie appartient au user
    category = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    category = category.scalar_one_or_none()
    if not category:
        raise CategoryNotFoundError()

    # 2. Vérifier pas de timer actif
    active = await get_active_timer(db, user_id)
    if active:
        raise TimerAlreadyActiveError()

    # 3. Créer l'entrée
    entry = TimeEntry(
        user_id=user_id,
        category_id=category_id,
        started_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry, attribute_names=["category"])
    return entry
```

**Exceptions custom** : Créer `TimerAlreadyActiveError` et `CategoryNotFoundError` dans `app/exceptions.py` (si pas déjà existant) ou dans le service directement.

### Routeur Timer

Fichier : `app/routers/timer.py`

```python
router = APIRouter(prefix="/api/timer", tags=["timer"])

@router.post("/start")
async def start_timer_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    form = await request.form()
    category_id = form.get("category_id")
    # Valider UUID...
    try:
        entry = await timer_service.start_timer(db, user.id, uuid.UUID(category_id))
    except TimerAlreadyActiveError:
        # Flash + redirect ou re-render
        ...
    except CategoryNotFoundError:
        raise HTTPException(status_code=404)
    # Retourner fragment HTML _timer_display.html
```

### JavaScript Timer — client-side

Fichier : `app/static/js/timer.js`

Fonctionnalités requises :
- **localStorage keys** : `timer_entry_id`, `timer_start_time` (ISO string ou timestamp ms), `timer_category_name`, `timer_category_emoji`, `timer_category_color`
- **setInterval** : 1x/sec, met à jour le DOM `#timer-time`
- **formatTime(totalSeconds)** : `HH:MM:SS` avec padding zéro
- **restoreTimer()** : appelé au DOMContentLoaded, vérifie localStorage, réconcilie temps, relance affichage
- **startTimer(data)** : appelé après POST réussi, sauve localStorage, démarre interval
- **stopTimerDisplay()** : supprime localStorage, arrête interval, masque header (sera appelé par story 3.3)
- **Page Visibility API** : écouter `visibilitychange`, recalculer le temps quand la page redevient visible (évite le drift si setInterval est throttled en background)
- **Vibration** : `navigator.vibrate && navigator.vibrate(50)` au démarrage

**HTMX integration** : Après le POST /api/timer/start réussi, le serveur retourne un fragment HTML. Utiliser l'événement HTMX `htmx:afterSwap` ou un `<script>` inline dans le fragment pour appeler `startTimer()` avec les données.

### Changement de comportement de la card catégorie — DÉCISION CRITIQUE

La card catégorie (`_category_card.html`) navigue actuellement vers `/categories/{id}` (page détail). Pour le timer, le tap doit démarrer le timer (FR37 : démarrer en minimum d'interactions).

**Approche recommandée** :
- **Tap sur la card** = démarrer le timer (POST /api/timer/start)
- **Bouton icône ">" ou "détails"** sur la card = naviguer vers le détail catégorie
- Garder le `event.stopPropagation()` sur les boutons éditer/supprimer/détail
- Si un timer est déjà actif, le tap sur une autre card affiche un flash message

Alternative si la navigation détail est jugée plus importante : utiliser un **bouton play** sur la card pour démarrer le timer, et garder le tap pour le détail. Choisir avec l'utilisateur si besoin.

### category_id FK — SET NULL justification

`ondelete="SET NULL"` sur category_id pour préserver l'historique de tracking même si une catégorie est supprimée. Les entrées de temps orphelines resteront consultables (affichage "Catégorie supprimée").

### Timer sticky — intégration base.html

Ajouter dans `base.html` un conteneur pour le timer :
```html
<div id="timer-container">
  <!-- Rempli dynamiquement par HTMX ou JS -->
</div>
```

Ce conteneur est AVANT `#app-shell` pour rester visible pendant la navigation HTMX. Le fragment `_timer_display.html` est injecté dedans.

### Anti-patterns à éviter

- **NE PAS** utiliser JSON pour la réponse timer — retourner un fragment HTML (convention HTMX du projet)
- **NE PAS** stocker le timer côté serveur avec polling (pas de `hx-trigger="every 1s"` pour le compteur) — le compteur est 100% client-side via JavaScript
- **NE PAS** permettre plusieurs timers simultanés — un seul timer actif par utilisateur
- **NE PAS** utiliser Alpine.js ou un framework JS — vanilla JS inline
- **NE PAS** utiliser la méthode HTTP DELETE — utiliser POST (convention formulaires HTML du projet)
- **NE PAS** oublier le Page Visibility API — sans lui, le timer drift en arrière-plan
- **NE PAS** modifier les tests existants (210 tests) — uniquement ajouter des nouveaux
- **NE PAS** mettre de logique métier dans le routeur — utiliser le service
- **NE PAS** oublier d'exporter le modèle TimeEntry dans `app/models/__init__.py`
- **NE PAS** oublier d'ajouter les relationships `time_entries` dans User et Category
- **NE PAS** oublier d'enregistrer le routeur timer dans `main.py`

### Project Structure Notes

Fichiers à créer :
- `app/models/time_entry.py` — modèle TimeEntry
- `app/schemas/time_entry.py` — schéma TimerStartRequest
- `app/services/timer_service.py` — service timer (start, get_active)
- `app/routers/timer.py` — routeur API timer
- `app/static/js/timer.js` — JavaScript timer client-side
- `app/templates/components/_timer_display.html` — fragment header sticky timer
- `alembic/versions/xxx_create_time_entries_table.py` — migration Alembic
- `tests/test_timer.py` — tests pour le timer

Fichiers à modifier :
- `app/models/__init__.py` — exporter TimeEntry
- `app/models/user.py` — ajouter relationship `time_entries`
- `app/models/category.py` — ajouter relationship `time_entries`
- `app/main.py` — enregistrer `timer.router`
- `app/templates/base.html` — ajouter `#timer-container` + script timer.js
- `app/templates/components/_category_card.html` — changer tap → POST /api/timer/start (+ bouton séparé pour détail)
- `app/templates/pages/category_detail.html` — ajouter bouton "Démarrer timer"
- `app/templates/components/_subcategory_list.html` — ajouter bouton play par sous-catégorie
- `app/routers/pages.py` — passer le timer actif au template home

Fichiers à NE PAS modifier :
- `app/services/category_service.py` — ne pas toucher
- `app/services/flash_service.py` — réutiliser tel quel
- `app/routers/helpers.py` — réutiliser tel quel
- `app/services/auth_service.py` — ne pas toucher
- `app/services/session_service.py` — ne pas toucher

### Previous Story Intelligence (Story 2.5)

- Pattern form + validation 422 est bien rodé — le réutiliser pour le formulaire timer
- La convention de commit est : `feat: description courte en français (story X.Y)`
- 210 tests actuels — ne pas régresser
- Le pattern `_parse_category_form()` centralise le parsing — créer un équivalent pour le timer
- Le modal DaisyUI est utilisé pour confirmations — réutiliser pour le modal post-session (story 3.3)
- `stopPropagation()` est critique sur les boutons dans les cards cliquables — l'appliquer au nouveau bouton détail
- Story 2.5 note : "le timer pourra cibler indifféremment une catégorie ou une sous-catégorie sans modification du modèle TimeEntry" — category_id FK vers `categories` couvre les deux cas

### Git Intelligence

Derniers commits :
- `dbebeab` fix: propager la couleur parent aux sous-catégories lors de la modification (code review story 2.5)
- `a6484f2` feat: sous-catégories CRUD + artifacts de planification BMAD (story 2.5)
- `3b268e7` feat: modification et suppression de catégorie + correctifs code review (story 2.4)

Convention : `feat: description courte en français (story X.Y)`

Patterns de code confirmés :
- UUID v7 (pas v4) — commit `c9f2e95` a migré de v4 à v7
- Tailwind CSS 4 + DaisyUI 5 + HTMX 2.0.8 en local (commit `2d4289c`)
- Flash messages uniformisés (commit `26157f0`)

### Testing Standards

- Framework : pytest + pytest-asyncio
- Fixtures dans `tests/conftest.py` : `db_session`, `client`, `authenticated_client`
- Tests schéma : synchrones, pas de DB
- Tests service : async avec `db_session`
- Tests route : async avec `authenticated_client`
- Header HTMX : `{"HX-Request": "true"}`
- Nouveau fichier test : `tests/test_timer.py`
- Total actuel : 210 tests — objectif > 230 après cette story

### Dépendances techniques vérifiées

- **SQLAlchemy 2.0 async** : déjà installé et configuré
- **asyncpg** : driver PostgreSQL async, en place
- **Alembic** : migrations configurées, 2 migrations existantes (users, categories)
- **JetBrains Mono** : mentionné dans l'UX spec pour le timer — vérifier s'il est déjà chargé dans base.html, sinon l'ajouter (via CDN Google Fonts ou fichier local)
- **Page Visibility API** : natif browser, pas de dépendance externe
- **localStorage** : natif browser, pas de dépendance externe
- **navigator.vibrate** : natif browser (mobile), pas de dépendance externe

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture — TimeEntry model]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture — Timer Implementation]
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/prd.md#FR17-FR21 — Tracking du Temps]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Écran 2 Timer Actif]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Experience Mechanics]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Composants DaisyUI mappés — Timer Display = stat + custom mono font]
- [Source: _bmad-output/implementation-artifacts/2-5-sous-categories-activites.md — previous story]
- [Source: app/models/category.py — modèle Category avec parent_id]
- [Source: app/routers/categories.py — routeur existant, pattern à suivre]
- [Source: app/dependencies.py — get_current_user, get_db]
- [Source: app/main.py — enregistrement des routeurs]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- expire_all() is sync, not async — fixed in test

### Completion Notes List

- Task 1: Modèle TimeEntry créé avec UUID v7, FK CASCADE (user) et SET NULL (category), index composites, relationships ajoutées dans User et Category, migration Alembic générée et appliquée
- Task 2: Schéma TimerStartRequest créé (pas besoin de TimerStartResponse — la réponse est un fragment HTML)
- Task 3: Service timer avec start_timer et get_active_timer, exceptions custom TimerAlreadyActiveError et CategoryNotFoundError héritant de AppException
- Task 4: Routeur timer POST /api/timer/start avec gestion des erreurs, enregistré dans main.py
- Task 5: timer.js vanilla JS avec startTimer, stopTimerDisplay, restoreTimer, formatTime, Page Visibility API, vibration, et intégration HTMX (htmx:afterSettle)
- Task 6: Template _timer_display.html avec header sticky, font mono, couleur dynamique, boutons Pause/Stop désactivés (placeholder stories 3.2/3.3)
- Task 7: Card catégorie modifiée — tap = démarrer timer (hx-post), nouveau bouton chevron ">" pour naviguer vers le détail avec stopPropagation
- Task 8: Bouton "Timer" ajouté sur category_detail.html, boutons play ajoutés sur chaque sous-catégorie dans _subcategory_list.html
- Task 9: pages.py passe active_timer au template home, home.html inclut un script de restauration timer si actif, timer-container dans base.html avant app-shell
- Task 10: 20 tests ajoutés (4 modèle, 3 schéma, 6 service, 7 route), 201 tests totaux, 0 régression

### File List

Fichiers créés :
- app/models/time_entry.py
- app/schemas/time_entry.py
- app/services/timer_service.py
- app/routers/timer.py
- app/static/js/timer.js
- app/templates/components/_timer_display.html
- alembic/versions/789469fc36c6_create_time_entries_table.py
- tests/test_timer.py

Fichiers modifiés :
- app/models/__init__.py (export TimeEntry)
- app/models/user.py (relationship time_entries)
- app/models/category.py (relationship time_entries)
- app/main.py (include timer.router)
- app/templates/base.html (timer-container div + timer.js script)
- app/templates/components/_category_card.html (tap = timer, bouton détail séparé)
- app/templates/pages/category_detail.html (bouton "Timer")
- app/templates/components/_subcategory_list.html (boutons play)
- app/routers/pages.py (active_timer dans context home)
- app/templates/pages/home.html (script restauration timer)
- alembic/env.py (import TimeEntry)

### Change Log

- 2026-03-20 : Implémentation complète story 3.1 — Modèle TimeEntry, service timer, routeur API, JavaScript client-side, templates, intégration accueil et détail catégorie, 20 tests ajoutés
