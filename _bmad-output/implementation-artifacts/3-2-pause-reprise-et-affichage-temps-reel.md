# Story 3.2 : Pause, reprise et affichage temps réel

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a utilisateur,
I want mettre en pause et reprendre mon timer tout en voyant le temps s'écouler,
So that je puisse gérer les interruptions sans perdre ma session.

## Acceptance Criteria

1. **Given** un timer est actif
   **When** l'utilisateur clique sur "Pause"
   **Then** le timer se fige visuellement (le compteur s'arrête)
   **And** la couleur du header timer est atténuée (opacité réduite) pour indiquer la pause
   **And** le bouton "Pause" devient "Reprendre" (icône play)
   **And** l'état pause est persisté dans localStorage (`timer_paused: "true"`, `timer_paused_at: <timestamp>`)
   **And** le temps total de pause est accumulé dans localStorage (`timer_total_paused_ms`)
   **And** côté serveur, un POST `/api/timer/pause` est envoyé pour fiabiliser l'état

2. **Given** un timer est en pause
   **When** l'utilisateur clique sur "Reprendre"
   **Then** le timer reprend depuis où il s'était arrêté (temps de pause exclu du décompte)
   **And** le temps s'affiche en temps réel (update 1x/sec)
   **And** la couleur du header timer redevient normale
   **And** le bouton "Reprendre" redevient "Pause"
   **And** localStorage est mis à jour (`timer_paused: "false"`, `timer_total_paused_ms` incrémenté)
   **And** côté serveur, un POST `/api/timer/resume` est envoyé

3. **Given** un timer est actif et l'utilisateur change d'onglet ou minimise le navigateur
   **When** il revient sur l'app
   **Then** le temps affiché est réconcilié grâce à Page Visibility API
   **And** le timer est précis même après un passage en arrière-plan (NFR13)
   **And** si le timer était en pause, il reste en pause au retour

4. **Given** un timer est actif ou en pause et l'utilisateur recharge la page
   **When** le DOM est prêt
   **Then** l'état pause/actif est restauré depuis localStorage
   **And** l'affichage est correct (temps pause exclu)
   **And** les boutons sont dans le bon état (Pause ou Reprendre)

5. **Given** l'utilisateur n'est pas authentifié
   **When** il tente de mettre en pause ou reprendre un timer
   **Then** il est redirigé vers `/login` (401 + HX-Redirect standard)

## Tasks / Subtasks

- [x] Task 1 : Ajouter le champ `paused_seconds` au modèle TimeEntry (AC: #1, #2)
  - [x] 1.1 Ajouter `paused_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)` dans `app/models/time_entry.py` — cumul total des secondes passées en pause
  - [x]1.2 Ajouter `paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)` — timestamp du dernier passage en pause (NULL si pas en pause)
  - [x]1.3 Créer migration Alembic : `alembic revision --autogenerate -m "add_pause_fields_to_time_entries"`
  - [x]1.4 Appliquer la migration : `alembic upgrade head`

- [x] Task 2 : Ajouter les fonctions pause/resume dans le service timer (AC: #1, #2, #5)
  - [x]2.1 Dans `app/services/timer_service.py`, créer `TimerNotActiveError(ConflictError)` pour le cas où aucun timer n'est actif
  - [x]2.2 Créer `TimerAlreadyPausedError(ConflictError)` pour pause sur un timer déjà en pause
  - [x]2.3 Créer `TimerNotPausedError(ConflictError)` pour resume sur un timer pas en pause
  - [x]2.4 Créer `async def pause_timer(db, user_id) -> TimeEntry` :
    - Récupérer le timer actif (ended_at IS NULL) du user
    - Si aucun timer actif → lever `TimerNotActiveError`
    - Si déjà en pause (paused_at IS NOT NULL) → lever `TimerAlreadyPausedError`
    - Mettre `paused_at = datetime.now(UTC)`
    - Commit + refresh (avec category)
    - Retourner l'entrée
  - [x]2.5 Créer `async def resume_timer(db, user_id) -> TimeEntry` :
    - Récupérer le timer actif (ended_at IS NULL) du user
    - Si aucun timer actif → lever `TimerNotActiveError`
    - Si pas en pause (paused_at IS NULL) → lever `TimerNotPausedError`
    - Calculer `pause_duration = (now - paused_at).total_seconds()`
    - Incrémenter `paused_seconds += pause_duration`
    - Remettre `paused_at = None`
    - Commit + refresh (avec category)
    - Retourner l'entrée

- [x] Task 3 : Créer les endpoints pause/resume dans le routeur timer (AC: #1, #2, #5)
  - [x]3.1 Dans `app/routers/timer.py`, ajouter `POST /api/timer/pause` :
    - `Depends(get_current_user)`, `Depends(get_db)`
    - Appeler `timer_service.pause_timer(db, user.id)`
    - Gérer `TimerNotActiveError` → redirect `/` avec flash warning
    - Gérer `TimerAlreadyPausedError` → redirect `/` avec flash info
    - Retourner le fragment `_timer_display.html` avec `is_paused=True`
  - [x]3.2 Ajouter `POST /api/timer/resume` :
    - Même pattern que pause
    - Appeler `timer_service.resume_timer(db, user.id)`
    - Gérer `TimerNotPausedError` → redirect `/` avec flash info
    - Retourner le fragment `_timer_display.html` avec `is_paused=False`

- [x] Task 4 : Mettre à jour le template `_timer_display.html` (AC: #1, #2, #4)
  - [x]4.1 Ajouter un paramètre template `is_paused` (défaut `False`)
  - [x]4.2 Ajouter un paramètre template `paused_seconds` (défaut `0`)
  - [x]4.3 Rendre le bouton Pause fonctionnel :
    - Si pas en pause : `hx-post="/api/timer/pause"` `hx-target="#timer-container"` avec texte "Pause"
    - Si en pause : `hx-post="/api/timer/resume"` `hx-target="#timer-container"` avec texte "Reprendre"
    - Retirer `disabled` et `btn-disabled opacity-50`
    - Style bouton : `btn btn-sm btn-ghost text-white border-white/30`
  - [x]4.4 Garder le bouton Stop désactivé (placeholder story 3.3)
  - [x]4.5 Quand en pause : ajouter classe `opacity-60` au header + afficher un badge "En pause" sous le temps
  - [x]4.6 Passer les données pause au script inline : `isPaused`, `pausedSeconds`, `pausedAt` pour que le JS puisse restaurer l'état
  - [x]4.7 Mettre à jour l'appel `window.timerApp.startTimer(...)` pour inclure les données pause

- [x] Task 5 : Mettre à jour `timer.js` pour la gestion pause/resume (AC: #1, #2, #3, #4)
  - [x]5.1 Ajouter les clés localStorage : `timer_paused` ("true"/"false"), `timer_paused_at` (timestamp ms), `timer_total_paused_ms` (entier)
  - [x]5.2 Modifier `updateDisplay()` :
    - Si en pause (`timer_paused === "true"`) : ne pas mettre à jour le compteur, afficher le temps figé
    - Si actif : calculer `elapsed = (now - startTime - totalPausedMs) / 1000`
  - [x]5.3 Modifier `showTimerHeader()` pour refléter l'état pause :
    - Si en pause : `opacity-60` sur le header, bouton affiche "Reprendre" avec `hx-post="/api/timer/resume"`
    - Si actif : opacité normale, bouton affiche "Pause" avec `hx-post="/api/timer/pause"`
    - Le bouton Stop reste désactivé (story 3.3)
  - [x]5.4 Ajouter `pauseTimer()` : stocker `timer_paused: "true"`, `timer_paused_at: Date.now()` dans localStorage
  - [x]5.5 Ajouter `resumeTimer()` : calculer durée pause, incrémenter `timer_total_paused_ms`, remettre `timer_paused: "false"`, supprimer `timer_paused_at`
  - [x]5.6 Modifier `restoreTimer()` : lire et restaurer l'état pause depuis localStorage, recalculer le temps correctement en excluant le temps de pause
  - [x]5.7 Modifier le handler Page Visibility API : si en pause, ne pas recalculer ; si actif, recalculer normalement en excluant le temps de pause total
  - [x]5.8 Modifier `startTimer(data)` pour accepter et stocker les données pause initiales (`isPaused`, `pausedSeconds`, `pausedAt`)
  - [x]5.9 Modifier `stopTimerDisplay()` pour aussi nettoyer les nouvelles clés localStorage pause
  - [x]5.10 Exposer `pauseTimer` et `resumeTimer` dans `window.timerApp`

- [x] Task 6 : Mettre à jour `pages.py` pour passer l'état pause au template home (AC: #4)
  - [x]6.1 Dans `GET /`, si un timer actif existe, calculer `is_paused = entry.paused_at is not None` et `paused_seconds = entry.paused_seconds`
  - [x]6.2 Passer `is_paused` et `paused_seconds` au template home pour la restauration correcte du timer

- [x] Task 7 : Tests (AC: #1-#5)
  - [x]7.1 Tests modèle : vérifier champs `paused_seconds` (default 0) et `paused_at` (nullable) sur TimeEntry
  - [x]7.2 Tests service :
    - `pause_timer` succès (timer actif → paused_at rempli)
    - `pause_timer` sans timer actif → `TimerNotActiveError`
    - `pause_timer` timer déjà en pause → `TimerAlreadyPausedError`
    - `resume_timer` succès (paused_at vidé, paused_seconds incrémenté correctement)
    - `resume_timer` sans timer actif → `TimerNotActiveError`
    - `resume_timer` timer pas en pause → `TimerNotPausedError`
    - `resume_timer` accumulation de pause : pause 30s, resume, pause 20s, resume → paused_seconds == 50
  - [x]7.3 Tests route :
    - `POST /api/timer/pause` succès → status 200, fragment HTML retourné
    - `POST /api/timer/pause` non authentifié → 401/redirect
    - `POST /api/timer/pause` sans timer actif → flash warning + redirect
    - `POST /api/timer/pause` timer déjà en pause → flash info + redirect
    - `POST /api/timer/resume` succès → status 200, fragment HTML retourné
    - `POST /api/timer/resume` non authentifié → 401/redirect
    - `POST /api/timer/resume` timer pas en pause → flash info + redirect
  - [x]7.4 Vérifier non-régression : les 231 tests existants passent toujours

## Dev Notes

### Architecture et patterns à suivre

- **Couches** : Router → Service → Model/Schema. Même pattern que story 3.1 et toutes les précédentes.
- **HTMX** : Le POST pause/resume retourne le fragment `_timer_display.html` qui est injecté dans `#timer-container`. Le fragment contient un `<script>` inline qui appelle `window.timerApp.startTimer()` (ou une nouvelle fonction) avec les données mise à jour.
- **Flash** : `flash(response, "warning", "message")` via `app/services/flash_service.py`.
- **Auth** : `Depends(get_current_user)` sur les deux endpoints.
- **DB session** : `Depends(get_db)` pour `AsyncSession`.
- **Redirect HTMX** : `htmx_redirect(request, url)` de `app/routers/helpers.py`.

### Stratégie pause : hybride client + serveur

La pause est gérée des deux côtés :

**Côté client (localStorage)** : Le timer JS gère l'affichage en temps réel. Le `setInterval` reste actif mais `updateDisplay()` ne met pas à jour le compteur si `timer_paused === "true"`. Le temps total de pause est stocké dans `timer_total_paused_ms` pour la réconciliation.

**Côté serveur (DB)** : Les champs `paused_at` et `paused_seconds` sur TimeEntry permettent de connaître l'état exact même si le navigateur est fermé. Le `paused_seconds` sera utilisé par story 3.3 pour calculer `duration_seconds` correctement au stop : `duration = (ended_at - started_at).total_seconds() - paused_seconds`.

### Calcul du temps affiché

```
temps_affiché = (Date.now() - timer_start_time - timer_total_paused_ms) / 1000
```

Si en pause :
```
temps_affiché = (timer_paused_at - timer_start_time - timer_total_paused_ms) / 1000
```

Cela exclut le temps de pause du décompte affiché.

### Modèle TimeEntry — champs à ajouter

Fichier : `app/models/time_entry.py`

```python
paused_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True
)
paused_seconds: Mapped[int] = mapped_column(
    Integer, nullable=False, default=0
)
```

- `paused_at` : timestamp UTC du moment où la pause a été activée. NULL = pas en pause.
- `paused_seconds` : cumul total des secondes passées en pause (incrémenté à chaque resume). Utilisé par story 3.3 pour le calcul de `duration_seconds`.

### Exceptions custom à ajouter

Dans `app/services/timer_service.py` (à côté des exceptions existantes) :

```python
class TimerNotActiveError(ConflictError):
    def __init__(self):
        super().__init__("Aucun timer en cours")

class TimerAlreadyPausedError(ConflictError):
    def __init__(self):
        super().__init__("Le timer est déjà en pause")

class TimerNotPausedError(ConflictError):
    def __init__(self):
        super().__init__("Le timer n'est pas en pause")
```

### Pattern du script inline dans le fragment HTML

Le fragment `_timer_display.html` contient un `<script>` qui appelle le JS global. Pour la pause, le script doit passer l'état :

```html
<script>
    (function() {
        var startTime = new Date({{ started_at | tojson }}).getTime();
        window.timerApp.startTimer({
            entryId: {{ entry_id | tojson }},
            startTime: startTime,
            categoryName: {{ category_name | tojson }},
            categoryEmoji: {{ category_emoji | tojson }},
            categoryColor: {{ category_color | tojson }},
            isPaused: {{ is_paused | tojson }},
            pausedSeconds: {{ paused_seconds | tojson }},
            pausedAt: {{ paused_at | tojson }}
        });
    })();
</script>
```

### localStorage — clés complètes après cette story

| Clé | Type | Description |
|-----|------|-------------|
| `timer_entry_id` | string (UUID) | ID de l'entrée TimeEntry |
| `timer_start_time` | string (timestamp ms) | Début du timer |
| `timer_category_name` | string | Nom de la catégorie |
| `timer_category_emoji` | string | Emoji de la catégorie |
| `timer_category_color` | string (hex) | Couleur de la catégorie |
| `timer_paused` | "true"/"false" | État pause |
| `timer_paused_at` | string (timestamp ms) | Moment de la mise en pause (si en pause) |
| `timer_total_paused_ms` | string (entier) | Cumul total du temps de pause en ms |

### Visual feedback pause (UX-DR17)

- Header timer : ajouter `opacity-60` quand en pause (transition douce `transition-opacity duration-300`)
- Badge "En pause" : petit texte ou badge sous le compteur pour indiquer explicitement l'état
- Bouton toggle : "Pause" → "Reprendre" (pas d'icône complexe, texte clair)
- Le compteur reste affiché mais figé — il ne continue PAS de compter pendant la pause

### Anti-patterns à éviter

- **NE PAS** arrêter le `setInterval` pendant la pause — le garder actif mais ne pas incrémenter le compteur (permet de rester réactif au resume)
- **NE PAS** utiliser un champ booléen `is_paused` en DB — utiliser `paused_at IS NOT NULL` comme indicateur (plus informatif)
- **NE PAS** envoyer le POST pause/resume et attendre la réponse avant de mettre à jour le JS — mettre à jour le localStorage immédiatement (optimistic UI), le serveur confirme ensuite via le fragment retourné
- **NE PAS** modifier le `startTimer(data)` de façon incompatible — les appels existants depuis story 3.1 (sans données pause) doivent toujours fonctionner (valeurs par défaut)
- **NE PAS** oublier de nettoyer les clés localStorage pause dans `stopTimerDisplay()` — sinon état incohérent
- **NE PAS** modifier les tests existants (231 tests) — uniquement ajouter des nouveaux
- **NE PAS** mettre de logique métier dans le routeur — utiliser le service
- **NE PAS** retourner du JSON — retourner un fragment HTML (convention HTMX du projet)
- **NE PAS** utiliser Alpine.js ou autre framework JS — vanilla JS uniquement

### Project Structure Notes

Fichiers à modifier :
- `app/models/time_entry.py` — ajouter `paused_at` et `paused_seconds`
- `app/services/timer_service.py` — ajouter exceptions + fonctions `pause_timer()` et `resume_timer()`
- `app/routers/timer.py` — ajouter endpoints `POST /pause` et `POST /resume`
- `app/templates/components/_timer_display.html` — activer bouton Pause, ajouter état pause, passer données pause au JS
- `app/static/js/timer.js` — gestion complète pause/resume, nouvelles clés localStorage, calcul temps correct
- `app/routers/pages.py` — passer état pause au template home
- `app/templates/pages/home.html` — passer données pause au script de restauration
- `alembic/versions/xxx_add_pause_fields.py` — nouvelle migration
- `tests/test_timer.py` — ajouter tests pause/resume

Fichiers à NE PAS modifier :
- `app/services/category_service.py`
- `app/services/flash_service.py` — réutiliser tel quel
- `app/routers/helpers.py` — réutiliser tel quel
- `app/services/auth_service.py`
- `app/exceptions.py` — les exceptions timer sont dans `timer_service.py`
- `app/models/user.py`, `app/models/category.py` — aucun changement nécessaire

### Previous Story Intelligence (Story 3.1)

- **Boutons désactivés** : Story 3.1 a créé les boutons Pause et Stop comme `btn-disabled opacity-50 disabled` — cette story active le bouton Pause, laisse Stop désactivé pour story 3.3
- **`_timer_display.html`** : Le fragment HTML contient un `<script>` inline qui appelle `window.timerApp.startTimer()` — étendre cet appel avec les données pause
- **`timer.js`** structure : IIFE avec `window.timerApp` exposé globalement, localStorage pour persistance, `setInterval` 1s pour affichage
- **Page Visibility API** : Déjà implémenté dans story 3.1 — modifier le handler pour gérer l'état pause
- **Pattern HTMX** : POST vers `/api/timer/start` retourne fragment dans `#timer-container` — même pattern pour pause/resume
- **Convention tests** : Tests dans `tests/test_timer.py`, classes `TestTimerModels`, `TestTimerSchemas`, `TestTimerService`, `TestTimerRoutes`
- **231 tests actuels** — ne pas régresser, objectif ~250 après cette story
- **`showTimerHeader()`** dans timer.js construit le header dynamiquement via DOM — doit être mis à jour pour l'état pause
- **Index partiel unique** : `ix_time_entries_one_active_per_user` sur `(user_id) WHERE ended_at IS NULL` — un seul timer actif par user au niveau DB

### Git Intelligence

Dernier commit : `c397a2e feat: modèle TimeEntry, démarrage/arrêt du timer et UI (story 3.1)`

Convention commit : `feat: description courte en français (story X.Y)`

Patterns confirmés :
- UUID v7 pour les PKs
- Tailwind CSS 4 + DaisyUI 5 + HTMX 2.0.8 en local
- Flash messages via `flash_service.py`
- Exceptions héritant de `AppException` (ou `ConflictError`/`NotFoundError`)
- Font timer : JetBrains Mono via Google Fonts, classe CSS `.font-timer`

### Testing Standards

- Framework : pytest + pytest-asyncio via `uv run python -m pytest`
- Fixtures dans `tests/conftest.py` : `db_session`, `client`, `authenticated_client`
- Tests modèle et schéma : synchrones (pas de DB nécessaire pour schéma)
- Tests service : async avec `db_session`
- Tests route : async avec `authenticated_client`, header `{"HX-Request": "true"}`
- Nouveau : ajouter les tests dans `tests/test_timer.py` (même fichier que story 3.1)
- Total actuel : 231 tests

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2 — Pause, reprise et affichage temps réel]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture — Timer Implementation (localStorage, Page Visibility API)]
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns — HTMX fragment responses]
- [Source: _bmad-output/planning-artifacts/prd.md#FR18 — Pause timer, FR19 — Reprendre timer, FR21 — Affichage temps réel]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR13 — Timer précis même en arrière-plan]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX-DR5 — Timer Display avec contrôles pause/stop]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX-DR17 — Couleur atténuée pour timer en pause]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey Flow 2 — Tap pause, timer en pause, tap play]
- [Source: _bmad-output/implementation-artifacts/3-1-modele-timeentry-et-demarrage-du-timer.md — previous story]
- [Source: app/static/js/timer.js — code JS actuel avec boutons désactivés]
- [Source: app/services/timer_service.py — service timer actuel (start, get_active)]
- [Source: app/routers/timer.py — routeur timer actuel (POST /start)]
- [Source: app/models/time_entry.py — modèle TimeEntry actuel]
- [Source: app/templates/components/_timer_display.html — fragment HTML actuel]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Migration Alembic nécessitait `server_default='0'` pour `paused_seconds` (données existantes en DB)

### Completion Notes List

- Task 1 : Ajout des champs `paused_at` (DateTime nullable) et `paused_seconds` (Integer default 0) au modèle TimeEntry + migration Alembic appliquée
- Task 2 : Création des 3 exceptions (`TimerNotActiveError`, `TimerAlreadyPausedError`, `TimerNotPausedError`) et des fonctions `pause_timer()` et `resume_timer()` dans `timer_service.py`
- Task 3 : Endpoints `POST /api/timer/pause` et `POST /api/timer/resume` avec gestion d'erreurs et retour du fragment HTML. Refactoring du code commun via `_timer_response()`
- Task 4 : Template `_timer_display.html` mis à jour : bouton Pause fonctionnel (toggle Pause/Reprendre), badge "En pause", opacité réduite, données pause passées au JS
- Task 5 : `timer.js` entièrement mis à jour : nouvelles clés localStorage pause, `updateDisplay()` gère l'état pause, `showTimerHeader()` reflète l'état, fonctions `pauseTimer()`/`resumeTimer()` ajoutées, `restoreTimer()` restaure l'état pause, `stopTimerDisplay()` nettoie les clés pause, `htmx.process()` sur les boutons dynamiques
- Task 6 : `pages.py` passe `is_paused` et `paused_seconds` au template home, `home.html` inclut les données pause dans le script de restauration
- Task 7 : 17 nouveaux tests ajoutés (2 modèle, 7 service dont accumulation, 8 routes). Total : 248 tests, 0 régression

### Change Log

- 2026-03-21 : Implémentation complète de la pause/reprise du timer (story 3.2)

### File List

- app/models/time_entry.py (modifié)
- app/services/timer_service.py (modifié)
- app/routers/timer.py (modifié)
- app/routers/pages.py (modifié)
- app/templates/components/_timer_display.html (modifié)
- app/templates/pages/home.html (modifié)
- app/static/js/timer.js (modifié)
- alembic/versions/60eb965eabc3_add_pause_fields_to_time_entries.py (nouveau)
- tests/test_timer.py (modifié)
