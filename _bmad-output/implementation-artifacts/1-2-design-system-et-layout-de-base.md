# Story 1.2 : Design system et layout de base

Status: done

## Story

As a utilisateur,
I want une interface visuellement cohérente avec une navigation claire entre les sections,
So that je puisse me repérer facilement dans l'application.

## Acceptance Criteria

1. Le template `base.html` intègre Tailwind CSS + DaisyUI avec le thème custom (Primary #3B82F6, Secondary #64748B, Accent #22C55E, Warning #F59E0B, Error #EF4444)
2. La typographie Inter/System est appliquée avec l'échelle d'espacement base 4px
3. Une bottom navigation (`btm-nav` DaisyUI) 3 items (Accueil, Stats, Settings) est visible sur mobile (64px hauteur)
4. La navigation fonctionne avec `hx-push-url` pour l'historique browser
5. Le focus est visible (ring 2px primary color) sur tous les éléments interactifs
6. `prefers-reduced-motion` est respecté
7. Les pages Accueil, Stats et Settings existent en placeholder avec le layout appliqué
8. HTMX est intégré et fonctionnel (chargement CDN ou local)
9. Jinja2 templating est configuré avec FastAPI

## Tasks / Subtasks

- [x] Task 1 : Configuration Tailwind CSS + DaisyUI (AC: #1, #2)
  - [x] Installer Tailwind CSS via CDN dans base.html
  - [x] Intégrer DaisyUI via CDN
  - [x] Configurer le thème custom DaisyUI dans base.html avec les couleurs : primary #3B82F6, secondary #64748B, accent #22C55E, warning #F59E0B, error #EF4444, base-100 #FFFFFF, neutral #1E293B
  - [x] Configurer la typographie : font-family Inter/system-ui pour le corps, JetBrains Mono pour les éléments mono (timer futur)

- [x] Task 2 : Configuration Jinja2 + HTMX (AC: #8, #9)
  - [x] Configurer Jinja2Templates dans app/main.py avec le dossier `app/templates`
  - [x] Intégrer HTMX v2.0.4 via CDN avec SRI dans base.html
  - [x] Créer le router `app/routers/pages.py` pour les pages full-page
  - [x] Enregistrer le router dans app/main.py

- [x] Task 3 : Template base.html (AC: #1, #2, #5, #6)
  - [x] Créer `app/templates/base.html` avec structure HTML5 complète
  - [x] Inclure les meta viewport mobile-first
  - [x] Intégrer Tailwind + DaisyUI + HTMX (CDN)
  - [x] Appliquer le thème custom DaisyUI
  - [x] Ajouter les styles globaux : focus-visible outline 2px primary, prefers-reduced-motion media query
  - [x] Définir les blocs Jinja2 : title, content, head, scripts
  - [x] Intégrer la bottom navigation dans base.html

- [x] Task 4 : Bottom navigation mobile (AC: #3, #4)
  - [x] Créer le composant `app/templates/components/_nav.html`
  - [x] Implémenter `btm-nav` DaisyUI avec 3 items : Accueil (🏠), Stats (📊), Settings (⚙️)
  - [x] Hauteur 64px, fixed en bas de l'écran
  - [x] Ajouter `hx-get` + `hx-push-url="true"` + `hx-target="#main-content"` + `hx-select="#main-content"` sur chaque lien
  - [x] Highlight de l'item actif basé sur l'URL courante

- [x] Task 5 : Pages placeholder (AC: #7)
  - [x] Créer `app/templates/pages/home.html` — extends base.html, contenu placeholder "Accueil — Catégories à venir"
  - [x] Créer `app/templates/pages/stats.html` — extends base.html, contenu placeholder "Statistiques à venir"
  - [x] Créer `app/templates/pages/settings.html` — extends base.html, contenu placeholder "Paramètres à venir"
  - [x] Ajouter les routes GET `/`, `/stats`, `/settings` dans `app/routers/pages.py`
  - [x] Chaque route retourne le template full-page via Jinja2

- [x] Task 6 : Tests et vérification (AC: tous)
  - [x] Tests : GET `/` retourne 200 avec contenu HTML
  - [x] Tests : GET `/stats` retourne 200
  - [x] Tests : GET `/settings` retourne 200
  - [x] Tests : les réponses contiennent les éléments clés (btm-nav, htmx, daisyui, theme, hx-push-url, focus-visible, prefers-reduced-motion)
  - [x] Lancer `ruff check app/ tests/` sans erreur
  - [x] Vérification visuelle restante (http://localhost:8000)

## Dev Notes

### Architecture & Patterns obligatoires

**Rendu Jinja2 + HTMX (source: architecture.md) :**
- Server-side rendering avec Jinja2 templates
- HTMX pour interactivité (fragments HTML, pas JSON)
- Convention réponses : détecter `HX-Request` header pour retourner fragment ou page complète
- Navigation avec `hx-push-url="true"` pour historique browser

**Pattern de route pages (source: architecture.md) :**
```python
# app/routers/pages.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def home(request: Request):
    context = {"request": request, "active_page": "home"}
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("pages/home.html", context, block_name="content")
    return templates.TemplateResponse("pages/home.html", context)
```

**IMPORTANT - Pattern HTMX fragment :** Quand le header `HX-Request` est présent, on peut :
- Option A : Retourner le template complet (HTMX extrait via `hx-select`)
- Option B : Utiliser `block_name` de Jinja2 (si supporté par la version)
- Option C : Créer des templates fragment séparés dans `components/`

Pour la simplicité, utiliser **Option A** avec `hx-select="#main-content"` dans la navigation.

**Template base.html pattern :**
```html
<!DOCTYPE html>
<html lang="fr" data-theme="appgestiontemps">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}appGestionTemps{% endblock %}</title>
    <!-- Tailwind + DaisyUI CDN -->
    <!-- HTMX CDN -->
    <style>
        /* prefers-reduced-motion */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }
        }
        /* Focus visible */
        :focus-visible {
            outline: none;
            ring: 2px;
            ring-color: oklch(var(--p));
        }
    </style>
</head>
<body class="min-h-screen pb-16">
    <main id="main-content" class="px-4 py-4">
        {% block content %}{% endblock %}
    </main>
    {% include "components/_nav.html" %}
    <script src="https://unpkg.com/htmx.org"></script>
</body>
</html>
```

**Bottom nav pattern DaisyUI :**
```html
<div class="btm-nav btm-nav-sm h-16 fixed bottom-0">
  <a hx-get="/" hx-push-url="true" hx-target="#main-content" hx-select="#main-content"
     class="{% if active_page == 'home' %}active{% endif %}">
    <span>🏠</span>
    <span class="btm-nav-label text-xs">Accueil</span>
  </a>
  <!-- Stats, Settings similaires -->
</div>
```

### Palette de couleurs (source: UX Design Specification)

| Rôle | Hex | DaisyUI token |
|------|-----|---------------|
| Primary | #3B82F6 | `--p` |
| Secondary | #64748B | `--s` |
| Accent/Success | #22C55E | `--a` |
| Warning | #F59E0B | `--wa` |
| Error | #EF4444 | `--er` |
| Base (fond) | #FFFFFF | `--b1` |
| Neutral | #1E293B | `--n` |

### Typographie (source: UX Design Specification)

| Élément | Police | Taille | Poids |
|---------|--------|--------|-------|
| H1 | Inter / System | 32px | 700 |
| H2 | Inter / System | 24px | 600 |
| H3 | Inter / System | 20px | 600 |
| Body | Inter / System | 16px | 400 |
| Small | Inter / System | 14px | 400 |
| Caption | Inter / System | 12px | 400 |
| Timer (futur) | JetBrains Mono | 48-64px | 500 |

### Espacement (base 4px)

| Token | Valeur | Usage |
|-------|--------|-------|
| xs | 4px (p-1) | Micro-espacements |
| sm | 8px (p-2) | Entre éléments liés |
| md | 16px (p-4) | Padding standard |
| lg | 24px (p-6) | Entre sections |
| xl | 32px (p-8) | Marges principales |

### Fichiers existants à modifier (de Story 1.1)

- `app/main.py` — ajouter Jinja2Templates config + include router pages
- `app/templates/` — dossier existant mais vide (créé en Story 1.1)
- `app/static/` — dossier existant mais vide

### Previous Story Intelligence (Story 1.1)

- pytest-asyncio nécessite `@pytest_asyncio.fixture` en mode STRICT
- conftest.py a été modifié pour utiliser une base de test séparée (`appgestiontemps_test`)
- alembic/env.py lit DATABASE_URL depuis Pydantic Settings (override du .ini)
- FastAPI monte les fichiers statiques depuis `app/static`

### Anti-patterns à éviter

- NE PAS installer Node.js/npm pour Tailwind — utiliser les CDN pour le MVP (simplicité)
- NE PAS créer de JavaScript custom dans cette story — seulement HTMX via CDN
- NE PAS créer de contenu fonctionnel sur les pages — seulement des placeholders
- NE PAS créer de routes API dans cette story — seulement des pages GET
- NE PAS oublier le `pb-16` ou padding-bottom sur le body pour compenser la bottom nav fixe
- NE PAS oublier `hx-push-url="true"` — essentiel pour le bouton retour du navigateur

### References

- [Source: planning-artifacts/architecture.md#API & Communication Patterns] — HTMX patterns
- [Source: planning-artifacts/architecture.md#Frontend Architecture] — Jinja2 SSR
- [Source: planning-artifacts/architecture.md#Naming Patterns] — Templates: pages/ pour complet, components/ pour fragments
- [Source: planning-artifacts/ux-design-specification.md#Design System Foundation] — Tailwind + DaisyUI
- [Source: planning-artifacts/ux-design-specification.md#Visual Design Foundation] — Couleurs, typo, espacement
- [Source: planning-artifacts/ux-design-specification.md#Design Direction Decision] — Bottom nav 3 items

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- TemplateResponse API changée dans Starlette récent : premier arg est maintenant `request`, puis `name` — corrigé pour supprimer le DeprecationWarning
- DaisyUI v4 CDN + Tailwind CDN utilisés (pas de build Node.js nécessaire pour le MVP)
- HTMX v2.0.4 avec intégrité SRI

### Completion Notes List

- base.html créé avec Tailwind CDN + DaisyUI CDN + HTMX v2.0.4
- Thème custom DaisyUI `appgestiontemps` avec toute la palette couleurs UX spec
- Typographie Inter/system-ui + JetBrains Mono pour mono
- Bottom nav `btm-nav` DaisyUI 3 items avec hx-get/hx-push-url/hx-select
- 3 pages placeholder (home, stats, settings) avec routes dans pages.py
- Focus-visible + prefers-reduced-motion intégrés dans base.html
- Router pages enregistré dans main.py
- 14 nouveaux tests (total 23/23 passent), lint propre

### File List

- app/main.py (modifié — ajout Jinja2Templates + router pages)
- app/routers/pages.py (nouveau)
- app/templates/base.html (nouveau)
- app/templates/components/_nav.html (nouveau)
- app/templates/pages/home.html (nouveau)
- app/templates/pages/stats.html (nouveau)
- app/templates/pages/settings.html (nouveau)
- tests/test_pages.py (nouveau)
