---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-02-04'
inputDocuments:
  - 'planning-artifacts/prd.md'
  - 'planning-artifacts/ux-design-specification.md'
  - 'brainstorming/brainstorming-session-2026-01-28.md'
workflowType: 'architecture'
project_name: 'appGestionTemps'
user_name: 'Alex'
date: '2026-02-04'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
38 FRs couvrant 6 domaines fonctionnels :
- Authentification (4 FRs) : inscription, connexion, déconnexion, reset password
- Catégories (12 FRs) : CRUD catégories/sous-catégories, emojis, couleurs, objectifs
- Tracking (9 FRs) : timer temps réel, pause/resume, stop, notes, saisie manuelle
- Visualisation (7 FRs) : stats jour/semaine, camembert, heatmap, agrégations
- Gamification (3 FRs) : streaks, progression objectifs, indicateurs
- Navigation (3 FRs) : accès rapide, démarrage 1-tap, navigation sections

**Non-Functional Requirements:**
- Performance : < 1s page load, < 200ms actions, timer 1x/sec
- Sécurité : hash sécurisé, sessions sécurisées, HTTPS obligatoire
- Fiabilité : aucune perte de données tracking, timer précis en arrière-plan
- Accessibilité : WCAG AA, navigation clavier, focus visible

**Scale & Complexity:**
- Primary domain: Full-stack PWA (Python/FastAPI backend + HTMX frontend)
- Complexity level: Low (standard)
- Estimated architectural components: ~8-10 (auth, categories, sessions, timer, stats, heatmap, streaks, PWA)

### Technical Constraints & Dependencies

| Contrainte | Source | Impact |
|------------|--------|--------|
| FastAPI (Python) | PRD Stack | Backend async, Pydantic models |
| PostgreSQL + SQLAlchemy | PRD Stack | ORM, migrations Alembic |
| HTMX + Jinja2 | PRD Stack | Server-side rendering, fragments HTMX |
| Tailwind + DaisyUI | UX Spec | CSS utility-first, composants prêts |
| PWA | PRD Platform | Manifest standalone (Service Worker hors scope MVP) |
| Mobile-first | UX Spec | Responsive design, touch-friendly |

### Cross-Cutting Concerns Identified

1. **Authentication & Authorization** — Sessions cookie-based sur toutes les routes protégées
2. **Timer Precision** — Synchronisation client/serveur, gestion arrière-plan (Page Visibility API)
3. **Data Isolation** — Toutes les données filtrées par user_id
4. **PWA Infrastructure** — Manifest standalone (Service Worker / cache offline hors scope MVP)
5. **Error Handling** — Gestion cohérente des erreurs API et UI
6. **Responsive Layouts** — Breakpoints mobile/tablet/desktop cohérents

## Starter Template Evaluation

### Primary Technology Domain

Full-stack PWA (Python/FastAPI backend + HTMX frontend) basé sur l'analyse des requirements.

### Starter Options Considered

| Option | Stack Match | Maturité | Production-Ready |
|--------|-------------|----------|------------------|
| fastHTMX | Parfait | Faible | Non |
| minimal-fastapi-postgres-template | Partiel (pas HTMX) | Bonne | Oui |
| Full Stack FastAPI (officiel) | React, pas HTMX | Excellente | Oui |
| Structure Custom | Adapté exactement | N/A | Best practices |

### Selected Approach: Structure Custom

**Rationale for Selection:**
- Aucun starter mature ne combine FastAPI + HTMX + sessions cookie-based
- Les templates existants sont orientés API REST + JWT (pas MPA)
- Projet de complexité low → structure simple suffisante
- Meilleure opportunité d'apprentissage FastAPI
- Contrôle total sur l'architecture

**Initialization Command:**

```bash
# Créer projet avec uv (gestionnaire Python moderne)
uv init appGestionTemps
cd appGestionTemps

# Dépendances principales
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic \
    python-dotenv jinja2 python-multipart passlib[bcrypt] itsdangerous

# Dépendances dev
uv add --dev pytest pytest-asyncio httpx ruff mypy
```

### Project Structure

```
appGestionTemps/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, middleware, routes
│   ├── config.py            # Settings (Pydantic)
│   ├── database.py          # SQLAlchemy setup
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── category.py
│   │   └── time_entry.py
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # Routes par domaine
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── categories.py
│   │   ├── timer.py
│   │   └── stats.py
│   ├── services/            # Business logic
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── components/      # HTMX fragments
│   │   └── pages/
│   └── static/              # CSS, JS minimal
├── alembic/                 # Migrations
├── tests/
├── alembic.ini
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

### Architectural Decisions Provided

| Aspect | Décision |
|--------|----------|
| Language & Runtime | Python 3.12+, type hints, async/await |
| Database | SQLAlchemy 2.0 async, asyncpg, Alembic |
| Authentication | Sessions cookie-based (itsdangerous), passlib+bcrypt |
| Frontend | Jinja2 SSR, HTMX, Tailwind CSS + DaisyUI |
| Code Quality | Ruff, Mypy, Pytest async |

**Note:** L'initialisation du projet avec cette structure sera la première story d'implémentation.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Data model (User, Category, TimeEntry)
- Authentication (sessions cookie-based)
- Timer sync strategy (client JS + server reconciliation)

**Important Decisions (Shape Architecture):**
- HTMX patterns pour interactivité
- PWA service worker strategy
- Error handling standards

**Deferred Decisions (Post-MVP):**
- Caching (Redis si besoin perf)
- Rate limiting (si ouverture public)
- Hosting platform (à décider au déploiement)

### Data Architecture

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Database | PostgreSQL + asyncpg | Requis PRD, async performant |
| ORM | SQLAlchemy 2.0 async | Type-safe, migrations Alembic |
| Caching | Aucun (MVP) | Simplicité, usage solo suffisant |
| UUIDs | UUID v4 pour PKs | Sécurité, pas d'énumération |

**Data Model:**

```
User (id, email, password_hash, created_at, updated_at)
  │
  ├── Category (id, user_id, parent_id, name, emoji, color, goal_type, goal_value, position, created_at)
  │     │
  │     └── [self-reference pour sous-catégories]
  │
  └── TimeEntry (id, user_id, category_id, started_at, ended_at, duration_seconds, note, created_at)
```

### Authentication & Security

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Session storage | Signed cookies (itsdangerous) | Stateless, simple, pas de Redis |
| Password hashing | passlib + bcrypt | Standard industrie |
| CSRF protection | Middleware + tokens | Protection forms POST |
| Rate limiting | Différé post-MVP | Usage personnel initial |
| HTTPS | Obligatoire production | Requis NFR |

### API & Communication Patterns

| Pattern | Implementation |
|---------|----------------|
| Server rendering | Jinja2 templates, full pages |
| Partial updates | HTMX fragments (`hx-swap="innerHTML"`) |
| Form submission | `hx-post` avec `hx-target` pour feedback |
| Timer polling | `hx-trigger="every 1s"` sur timer display |
| Navigation | `hx-push-url="true"` pour historique browser |
| Error display | HTTP 422 → inline errors, toasts pour autres |

**HTMX Response Convention:**
- Success: Return HTML fragment
- Validation error (422): Return form with errors
- Auth error (401): `HX-Redirect: /login`
- Server error (500): Return toast component

### Frontend Architecture

**Timer Implementation:**

| Aspect | Décision |
|--------|----------|
| Client display | JavaScript minimal (setInterval 1s) |
| State persistence | localStorage (timer_active, start_time, category_id) |
| Server sync | POST /timer/start, POST /timer/stop |
| Page reload | Réconciliation depuis localStorage + server |
| Background tabs | Page Visibility API pour précision |

**PWA Configuration:**

| Aspect | Décision |
|--------|----------|
| Manifest | standalone display, theme colors, icônes multi-tailles |
| Service Worker | ~~Hors scope MVP~~ (Workbox envisageable post-MVP) |
| Offline | ~~Hors scope MVP~~ |

### Infrastructure & Deployment

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Containerization | Docker + docker-compose | Dev/prod parity |
| Web server | Uvicorn | FastAPI standard, async |
| Hosting | Différé | À décider au déploiement |
| CI/CD | GitHub Actions | Tests + lint automatiques |
| Environments | .env files | dev, test, prod configs |

### Decision Impact Analysis

**Implementation Sequence:**
1. Project setup (structure, deps, config)
2. Database models + Alembic migrations
3. Auth (register, login, sessions)
4. Categories CRUD
5. Timer + TimeEntry
6. Stats & visualizations
7. PWA (service worker, manifest)

**Cross-Component Dependencies:**
- Auth → requis avant toute route protégée
- Categories → requis avant TimeEntry
- TimeEntry → requis avant Stats
- PWA → peut être ajouté incrementally

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Database (SQLAlchemy):**
- Tables: snake_case, pluriel (`users`, `categories`, `time_entries`)
- Colonnes: snake_case (`user_id`, `created_at`)
- Foreign keys: `{table_singulier}_id`
- Index: `ix_{table}_{column}`

**API (FastAPI Routes):**
- Endpoints: snake_case, pluriel (`/api/categories`)
- Route params: snake_case (`{category_id}`)
- Actions custom: verbe-nom (`/api/timer/start`)

**Code Python:**
- Fichiers: snake_case (`time_entry.py`)
- Classes: PascalCase (`TimeEntry`)
- Fonctions/Variables: snake_case (`get_user_stats`)
- Constants: UPPER_SNAKE (`MAX_CATEGORIES`)

**Templates Jinja2:**
- Pages: snake_case (`category_list.html`)
- Components HTMX: underscore prefix (`_timer_display.html`)

### Structure Patterns

**Router Organization:** Un fichier par domaine fonctionnel
**Model Organization:** Un fichier par table SQLAlchemy
**Schema Organization:** Miroir des routers (Pydantic)
**Service Organization:** Business logic séparée des routers
**Template Organization:** `pages/` pour complet, `components/` pour fragments HTMX
**Test Organization:** Miroir de `app/` dans `tests/`

### Format Patterns

**HTMX Responses:**
- Success: HTML fragment (200)
- Validation error: Form avec erreurs inline (422)
- Auth error: `HX-Redirect: /login` header (401)
- Server error: Toast component (500)

**Pydantic Naming:** `{Model}{Action}` (CategoryCreate, CategoryResponse)

**Dates:** ISO 8601 en API, UTC en DB, format local en affichage

### Process Patterns

**Auth:** Dependency injection `get_current_user` sur routes protégées
**Errors:** Exceptions custom → HTTPException dans services
**Loading:** `hx-indicator` avec DaisyUI loading spinner
**CSRF:** Token dans forms, vérifié par middleware

### Enforcement Guidelines

**Tous les agents IA DOIVENT:**
1. Suivre les conventions de nommage définies ci-dessus
2. Placer les fichiers dans les dossiers appropriés selon la structure
3. Utiliser les patterns HTMX pour toutes les interactions
4. Implémenter l'auth via dependency injection
5. Retourner des fragments HTML, jamais de JSON brut (sauf cas explicite)

**Anti-Patterns à éviter:**
- JSON responses pour UI (utiliser HTML fragments)
- Logique métier dans les routers (utiliser services)
- Queries SQL dans les routers (utiliser repositories/services)
- Nommage camelCase en Python
- Templates sans underscore prefix pour fragments

## Project Structure & Boundaries

### Complete Project Directory Structure

```
appGestionTemps/
├── README.md
├── pyproject.toml
├── alembic.ini
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml
│
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
│   │   ├── user.py
│   │   ├── category.py
│   │   └── time_entry.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── category.py
│   │   ├── time_entry.py
│   │   └── stats.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── category_service.py
│   │   ├── timer_service.py
│   │   └── stats_service.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── pages.py
│   │   ├── categories.py
│   │   ├── timer.py
│   │   └── stats.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth_layout.html
│   │   ├── pages/
│   │   │   ├── home.html
│   │   │   ├── stats.html
│   │   │   ├── settings.html
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── components/
│   │       ├── _category_card.html
│   │       ├── _category_grid.html
│   │       ├── _category_form.html
│   │       ├── _timer_display.html
│   │       ├── _timer_controls.html
│   │       ├── _session_note_modal.html
│   │       ├── _stats_summary.html
│   │       ├── _heatmap.html
│   │       ├── _pie_chart.html
│   │       ├── _streak_list.html
│   │       ├── _toast.html
│   │       └── _nav.html
│   └── static/
│       ├── css/app.css
│       ├── js/timer.js
│       ├── js/app.js
│       ├── icons/
│       ├── manifest.json
│       └── sw.js
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
└── tests/
    ├── conftest.py
    ├── routers/
    ├── services/
    └── models/
```

### Architectural Boundaries

**Route Boundaries:**

| Route Pattern | Type | Auth Required |
|---------------|------|---------------|
| `/auth/*` | Full pages | Non |
| `/api/categories/*` | HTMX fragments | Oui |
| `/api/timer/*` | HTMX fragments | Oui |
| `/api/stats/*` | HTMX fragments | Oui |
| `/`, `/stats`, `/settings` | Full pages | Oui |
| `/static/*` | Assets | Non |

**Layer Boundaries:**
- **Routers**: HTTP handling, template rendering, pas de business logic
- **Services**: Business logic, data access, pas de HTTP concerns
- **Models**: Data structure, relationships, pas de logic
- **Schemas**: Validation, serialization

### Requirements to Structure Mapping

| FR Category | Primary Files |
|-------------|---------------|
| Auth (FR1-4) | `routers/auth.py`, `services/auth_service.py`, `models/user.py` |
| Categories (FR5-16) | `routers/categories.py`, `services/category_service.py`, `models/category.py` |
| Timer (FR17-25) | `routers/timer.py`, `services/timer_service.py`, `models/time_entry.py`, `static/js/timer.js` |
| Stats (FR26-32) | `routers/stats.py`, `services/stats_service.py`, `components/_heatmap.html` |
| Gamification (FR33-35) | `services/stats_service.py`, `components/_streak_list.html` |
| Navigation (FR36-38) | `routers/pages.py`, `base.html`, `components/_nav.html` |

### Data Flow

```
Request → Router → Dependency (auth) → Service → SQLAlchemy → DB
                                         ↓
Response ← Jinja2 Template ← Service Response
```

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** Toutes les technologies choisies fonctionnent ensemble sans conflit.
- FastAPI + SQLAlchemy 2.0 async ✅
- HTMX + Jinja2 SSR ✅
- Tailwind + DaisyUI ✅
- Sessions cookies + itsdangerous ✅

**Pattern Consistency:** Les patterns d'implémentation supportent les décisions architecturales.

**Structure Alignment:** La structure projet respecte les boundaries et supporte tous les patterns définis.

### Requirements Coverage Validation ✅

**Functional Requirements:** 38/38 FRs couverts par l'architecture
**Non-Functional Requirements:** Tous les NFRs addressés (performance, sécurité, accessibilité)

### Implementation Readiness Validation ✅

**Decision Completeness:** Toutes les décisions critiques documentées avec rationale
**Structure Completeness:** Structure complète avec tous les fichiers et dossiers
**Pattern Completeness:** Conventions de nommage, patterns de communication, gestion d'erreurs documentés

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (Low)
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns (HTMX) specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Stack simple et cohérent (FastAPI + HTMX)
- Patterns clairs pour agents IA
- Structure projet complète et mappée aux FRs
- Pas de sur-ingénierie (adapté dev solo)

**Areas for Future Enhancement:**
- Logging strategy (à définir à l'implémentation)
- Monitoring/observability (post-MVP)
- Hosting decision (différé)

### Implementation Handoff

**AI Agent Guidelines:**
- Suivre toutes les décisions architecturales exactement comme documentées
- Utiliser les patterns d'implémentation de manière consistante
- Respecter la structure projet et les boundaries
- Référer à ce document pour toutes les questions architecturales

**First Implementation Priority:**
```bash
uv init appGestionTemps && cd appGestionTemps
uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic python-dotenv jinja2 python-multipart passlib[bcrypt] itsdangerous
```

