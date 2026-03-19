---
title: 'Migration CDN vers installation locale Tailwind CSS 4 + DaisyUI 5 + HTMX'
slug: 'migration-cdn-tailwind-daisyui-htmx-local'
created: '2026-03-17'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Tailwind CSS 4', 'DaisyUI 5.5.x', 'HTMX 2.0.8', 'PostCSS', '@tailwindcss/postcss', 'Node.js >= 18', 'npm']
files_to_modify: ['package.json', 'postcss.config.mjs', 'app/static/css/input.css', 'app/templates/base.html', 'app/templates/components/_login_form.html', 'app/templates/components/_register_form.html', 'app/templates/components/_reset_password_form.html', 'app/templates/components/_forgot_password_form.html', 'Dockerfile', '.gitignore']
code_patterns: ['PostCSS pipeline', 'Tailwind 4 @import syntax', 'DaisyUI 5 @plugin "daisyui/theme" syntax', 'FastAPI StaticFiles mount at /static', 'Jinja2 template inheritance via base.html']
test_patterns: ['95 pytest tests existants — aucun changement backend, doivent tous passer']
assignee: 'Charlie (Senior Dev)'
---

# Tech-Spec: Migration CDN vers installation locale Tailwind CSS 4 + DaisyUI 5 + HTMX

**Created:** 2026-03-17
**Assigné à:** Charlie (Senior Dev)

## Overview

### Problem Statement

Le frontend repose entièrement sur des CDN (Tailwind play CDN, DaisyUI 4.12.24 via jsdelivr, HTMX 2.0.4 via unpkg). Il n'y a aucun build pipeline, pas de purge CSS, et une dépendance réseau au runtime. Le Tailwind CDN script n'est pas adapté à la production (pas de tree-shaking, pas de minification optimale). Cette situation bloque la préparation de l'Epic 2.

### Solution

Installer Node.js + npm avec Tailwind CSS 4 + PostCSS + DaisyUI 5 + HTMX 2.0.8 en local. Le CSS est compilé via un pipeline PostCSS, HTMX est copié depuis node_modules vers les fichiers statiques. Les CDN sont remplacés par des fichiers locaux servis par FastAPI.

### Scope

**In Scope :**

- Initialisation `package.json` avec les dépendances frontend
- Pipeline CSS : Tailwind CSS 4 + PostCSS + DaisyUI 5
- Fichier CSS source (`app/static/css/input.css`) avec syntaxe Tailwind 4
- Migration du thème custom oklch vers la syntaxe DaisyUI 5 (`@plugin "daisyui/theme"`)
- Migration des breaking changes classes DaisyUI 4→5 dans les templates
- Migration des formulaires : `form-control` / `label-text` → `fieldset` / `label`
- HTMX 2.0.8 copié en local (`app/static/js/htmx.min.js`)
- Mise à jour `base.html` : remplacer les 3 CDN par fichiers locaux
- Scripts npm `build:css` et `watch:css`
- Mise à jour Dockerfile pour le build CSS
- Mise à jour `.gitignore`

**Out of Scope :**

- Ajout de nouvelles fonctionnalités UI
- Tests E2E (pas de changement fonctionnel, migration transparente)
- Ajout de linting JS / prettier frontend

## Context for Development

### Codebase Patterns

- **Backend** : FastAPI + Jinja2 templates, fichiers statiques servis via `app.mount("/static", StaticFiles(directory="app/static"), name="static")` dans `app/main.py` (ligne 50)
- **Templates** : `app/templates/base.html` est le layout principal, tous les autres templates en héritent via `{% extends "base.html" %}`
- **Thème** : Thème custom `appgestiontemps` défini en CSS variables oklch dans un `<style>` inline dans `base.html` (lignes 24-78)
- **HTMX config** : Configuration `responseHandling` inline dans `base.html` (lignes 101-108) — codes 204, 2xx, 422, 4xx/5xx
- **Structure statique** : `app/static/{css,js,icons}/` existent mais sont vides (`.gitkeep`)
- **Docker** : `Dockerfile` Python 3.14-slim avec `uv`, pas de Node.js actuellement. Pas de multi-stage build.
- **docker-compose.yml** : Ne contient que le service `db` (PostgreSQL). Pas de service app.
- **Package manager Python** : `uv` (pas pip)

### Files to Reference

| File | Purpose | Action |
| ---- | ------- | ------ |
| `app/templates/base.html` | Layout principal — 3 CDN + thème inline (lignes 24-78) + HTMX config | Modifier : remplacer CDN, déplacer thème dans input.css |
| `app/templates/components/_nav.html` | Navigation (navbar, btn-ghost) | Aucun breaking change confirmé |
| `app/templates/components/_alert.html` | Alertes flash (alert, alert-{{type}}) | Aucun breaking change confirmé |
| `app/templates/components/_register_form.html` | Formulaire inscription — `input-bordered` + `form-control` + `label-text` | Modifier : supprimer `input-bordered`, migrer form-control → fieldset |
| `app/templates/components/_login_form.html` | Formulaire login — `input-bordered` + `form-control` + `label-text` | Modifier : idem |
| `app/templates/components/_forgot_password_form.html` | Formulaire mot de passe oublié — idem | Modifier : idem |
| `app/templates/components/_reset_password_form.html` | Formulaire reset password — idem | Modifier : idem |
| `app/templates/pages/*.html` | Pages (home, stats, settings, login, register, etc.) | Aucun breaking change |
| `Dockerfile` | Build Docker Python-only | Modifier : multi-stage avec Node.js |
| `.gitignore` | Ignore Python/IDE/Docker | Modifier : ajouter Node.js |
| `app/main.py` (ligne 50) | Static files mount `/static` | Aucun changement requis |

### Technical Decisions

1. **Tailwind CSS 4 + PostCSS** plutôt que Tailwind CLI standalone — plus flexible, écosystème npm standard, permet d'ajouter des plugins PostCSS si besoin
2. **DaisyUI 5** plutôt que rester en v4 — DaisyUI 5 est conçu pour Tailwind 4, plus léger (34 kB CSS), syntaxe `@plugin` native
3. **HTMX 2.0.8** — dernière version stable de la branche 2.x
4. **CSS compilé commité dans le repo** — évite de nécessiter Node.js pour juste lancer l'app en dev Python. Le build CSS est fait explicitement via `npm run build:css`. Le fichier output (`app/static/css/style.css`) est versionné.
5. **HTMX copié en local** — script npm `postinstall` copie le fichier vers `app/static/js/htmx.min.js`. Le fichier est versionné.
6. **Multi-stage Docker build** — stage 1 (Node.js) compile le CSS, stage 2 (Python) copie les assets et lance l'app

### Investigation Results — Breaking Changes DaisyUI 4→5

**Breaking changes confirmés dans le code existant :**

#### 1. `input-bordered` → supprimé (9 occurrences dans 4 fichiers)

| Fichier | Lignes | Occurrences |
| ------- | ------ | ----------- |
| `_login_form.html` | 10, 20 | 2 |
| `_register_form.html` | 10, 25, 40 | 3 |
| `_reset_password_form.html` | 9, 24 | 2 |
| `_forgot_password_form.html` | 24 | 1 |

**Migration :** Supprimer la classe `input-bordered` — en DaisyUI 5, les inputs ont un border par défaut.

#### 2. `form-control` + `label-text` + `label-text-alt` → `fieldset` + `label` (tous les formulaires)

DaisyUI 5 remplace le pattern `form-control` par des éléments HTML sémantiques `fieldset`/`legend`/`label` :

**Avant (DaisyUI 4) :**
```html
<label class="form-control w-full">
  <div class="label">
    <span class="label-text">Name</span>
  </div>
  <input class="input input-bordered" />
  <div class="label">
    <span class="label-text-alt text-error">Error msg</span>
  </div>
</label>
```

**Après (DaisyUI 5) :**
```html
<fieldset class="fieldset">
  <label class="label" for="name">Name</label>
  <input id="name" class="input" />
  <p class="label text-error">Error msg</p>
</fieldset>
```

**Fichiers impactés :** `_login_form.html`, `_register_form.html`, `_reset_password_form.html`, `_forgot_password_form.html`

#### 3. Variables CSS thème : syntaxe complètement changée

**DaisyUI 4 (actuel) :** Variables courtes, valeurs oklch sans `oklch()` :
```css
--p: 62.3% 0.183 264;       /* primary */
--pf: 57% 0.183 264;        /* primary-focus */
--pc: 100% 0 0;             /* primary-content */
--b1: 100% 0 0;             /* base-100 */
--rounded-box: 1rem;
--animation-btn: 0.25s;
```

**DaisyUI 5 (cible) :** Variables sémantiques, valeurs `oklch()` complètes, définies via `@plugin "daisyui/theme"` :
```css
@plugin "daisyui/theme" {
  name: "appgestiontemps";
  default: true;
  color-scheme: light;
  --color-primary: oklch(62.3% 0.183 264);
  --color-primary-content: oklch(100% 0 0);
  --color-base-100: oklch(100% 0 0);
  --radius-box: 1rem;
  --radius-field: 0.5rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

**Mapping complet des variables :**

| DaisyUI 4 | DaisyUI 5 | Valeur actuelle |
| ---------- | --------- | --------------- |
| `--p` | `--color-primary` | `oklch(62.3% 0.183 264)` |
| `--pf` | _(supprimé, auto-calculé)_ | — |
| `--pc` | `--color-primary-content` | `oklch(100% 0 0)` |
| `--s` | `--color-secondary` | `oklch(55.4% 0.023 264)` |
| `--sf` | _(supprimé, auto-calculé)_ | — |
| `--sc` | `--color-secondary-content` | `oklch(100% 0 0)` |
| `--a` | `--color-accent` | `oklch(72.3% 0.195 150)` |
| `--af` | _(supprimé, auto-calculé)_ | — |
| `--ac` | `--color-accent-content` | `oklch(15% 0.02 150)` |
| `--n` | `--color-neutral` | `oklch(27.8% 0.033 266)` |
| `--nf` | _(supprimé, auto-calculé)_ | — |
| `--nc` | `--color-neutral-content` | `oklch(96% 0.005 264)` |
| `--b1` | `--color-base-100` | `oklch(100% 0 0)` |
| `--b2` | `--color-base-200` | `oklch(96.5% 0.006 264)` |
| `--b3` | `--color-base-300` | `oklch(93% 0.011 264)` |
| `--bc` | `--color-base-content` | `oklch(27.8% 0.033 266)` |
| `--in` | `--color-info` | `oklch(62.3% 0.183 264)` |
| `--inc` | `--color-info-content` | `oklch(100% 0 0)` |
| `--su` | `--color-success` | `oklch(72.3% 0.195 150)` |
| `--suc` | `--color-success-content` | `oklch(15% 0.02 150)` |
| `--wa` | `--color-warning` | `oklch(79.5% 0.164 70)` |
| `--wac` | `--color-warning-content` | `oklch(15% 0.02 70)` |
| `--er` | `--color-error` | `oklch(62.8% 0.226 22)` |
| `--erc` | `--color-error-content` | `oklch(100% 0 0)` |
| `--rounded-box` | `--radius-box` | `1rem` |
| `--rounded-btn` | `--radius-field` | `0.5rem` |
| `--rounded-badge` | `--radius-selector` | `1.9rem` |
| `--animation-btn` | _(supprimé)_ | — |
| `--animation-input` | _(supprimé)_ | — |
| `--btn-focus-scale` | _(supprimé)_ | — |
| `--border-btn` | `--border` | `1px` |
| `--tab-border` | _(géré par --border)_ | — |
| `--tab-radius` | _(géré par --radius-field)_ | — |

#### 4. Style `focus-visible` référence `oklch(var(--p))`

Le style global `outline: 2px solid oklch(var(--p));` (ligne 65 de `base.html`) doit être mis à jour car `--p` n'existe plus en DaisyUI 5.

**Migration :** Remplacer par `outline: 2px solid var(--color-primary);` — en DaisyUI 5, les variables contiennent déjà la valeur oklch complète.

**Aucun autre breaking change** — le code n'utilise pas `btm-nav`, `card-compact`, `file-input-bordered`, `avatar-*`, ni `disabled` sur des menu items. Les classes `btn-ghost`, `input-error`, `alert-info/success/error` restent supportées en DaisyUI 5.

## Implementation Plan

### Tasks

- [x] **Task 1 : Initialiser le pipeline Node.js**
  - Fichier : `package.json` (créer à la racine du projet)
  - Action : Créer `package.json` avec :
    - `name`: `appgestiontemps-frontend`
    - `private`: true
    - `devDependencies` : `tailwindcss` (latest v4), `@tailwindcss/postcss` (latest), `postcss` (latest), `postcss-cli` (latest), `daisyui` (latest v5)
    - `dependencies` : `htmx.org` (v2.0.8)
    - `scripts` :
      - `build:css` : `postcss app/static/css/input.css -o app/static/css/style.css --verbose`
      - `watch:css` : `postcss app/static/css/input.css -o app/static/css/style.css --watch --verbose`
      - `postinstall` : `mkdir -p app/static/js && cp node_modules/htmx.org/dist/htmx.min.js app/static/js/htmx.min.js`
  - Notes : Lancer `npm install` après création pour générer `package-lock.json` et copier HTMX. Le `package-lock.json` doit être commité.

- [x] **Task 2 : Configurer PostCSS**
  - Fichier : `postcss.config.mjs` (créer à la racine du projet)
  - Action : Créer le fichier avec le plugin `@tailwindcss/postcss` :
    ```javascript
    export default {
      plugins: {
        "@tailwindcss/postcss": {},
      },
    };
    ```

- [x] **Task 3 : Créer le fichier CSS source avec thème DaisyUI 5**
  - Fichier : `app/static/css/input.css` (créer, remplace le `.gitkeep`)
  - Action : Créer le fichier avec le contenu exact suivant :
    ```css
    @import "tailwindcss";
    @plugin "daisyui";

    /* Scan des templates Jinja2 pour Tailwind (obligatoire — les templates
       sont hors du répertoire de input.css) */
    @source "../../../app/templates";

    /* Fonts custom */
    @theme {
      --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, monospace;
    }

    /* Thème custom appGestionTemps */
    @plugin "daisyui/theme" {
      name: "appgestiontemps";
      default: true;
      color-scheme: light;

      --color-base-100: oklch(100% 0 0);
      --color-base-200: oklch(96.5% 0.006 264);
      --color-base-300: oklch(93% 0.011 264);
      --color-base-content: oklch(27.8% 0.033 266);

      --color-primary: oklch(62.3% 0.183 264);
      --color-primary-content: oklch(100% 0 0);

      --color-secondary: oklch(55.4% 0.023 264);
      --color-secondary-content: oklch(100% 0 0);

      --color-accent: oklch(72.3% 0.195 150);
      --color-accent-content: oklch(15% 0.02 150);

      --color-neutral: oklch(27.8% 0.033 266);
      --color-neutral-content: oklch(96% 0.005 264);

      --color-info: oklch(62.3% 0.183 264);
      --color-info-content: oklch(100% 0 0);

      --color-success: oklch(72.3% 0.195 150);
      --color-success-content: oklch(15% 0.02 150);

      --color-warning: oklch(79.5% 0.164 70);
      --color-warning-content: oklch(15% 0.02 70);

      --color-error: oklch(62.8% 0.226 22);
      --color-error-content: oklch(100% 0 0);

      --radius-selector: 1.9rem;
      --radius-field: 0.5rem;
      --radius-box: 1rem;

      --border: 1px;
      --depth: 1;
      --noise: 0;
    }

    /* Focus visible — ring 2px primary */
    :focus-visible {
      outline: 2px solid var(--color-primary);
      outline-offset: 2px;
    }

    /* Respect prefers-reduced-motion */
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }
    }
    ```
  - Notes : La directive `@source` est **obligatoire** — sans elle, Tailwind ne trouvera pas les classes utilisées dans les templates Jinja2 et le CSS compilé n'aura aucune utility class. Le chemin est relatif à `input.css`.

- [x] **Task 4 : Compiler le CSS et vérifier le build**
  - Action : Lancer `npm run build:css`
  - Vérification : Le fichier `app/static/css/style.css` est généré sans erreurs et contient les utilities Tailwind + composants DaisyUI + thème custom
  - Rollback : Si le build échoue, vérifier les noms de variables dans `input.css` contre la doc DaisyUI 5 (https://daisyui.com/docs/themes/)

- [x] **Task 5 : Migrer les breaking changes DaisyUI 4→5 dans les templates**
  - Fichiers : 4 form templates
  - **Action 5a — Supprimer `input-bordered` (9 occurrences) :**
    - `app/templates/components/_login_form.html` — lignes 10, 20
    - `app/templates/components/_register_form.html` — lignes 10, 25, 40
    - `app/templates/components/_reset_password_form.html` — lignes 9, 24
    - `app/templates/components/_forgot_password_form.html` — ligne 24
  - **Action 5b — Migrer `form-control` / `label-text` → `fieldset` / `label` :**
    - Dans chaque formulaire, remplacer le pattern :
      ```html
      <div class="form-control w-full mb-4">
        <label class="label" for="...">
          <span class="label-text">Label</span>
        </label>
        <input ... />
        {% if errors.get('field') %}
        <label class="label">
          <span class="label-text-alt text-error">{{ errors.field }}</span>
        </label>
        {% endif %}
      </div>
      ```
    - Par le pattern DaisyUI 5 :
      ```html
      <fieldset class="fieldset mb-4">
        <label class="label" for="...">Label</label>
        <input ... />
        {% if errors.get('field') %}
        <p class="label text-error">{{ errors.field }}</p>
        {% endif %}
      </fieldset>
      ```
    - **Attention** : Conserver les attributs `id`, `name`, `value`, `class` des `<input>` inchangés (sauf suppression de `input-bordered`). Conserver la logique Jinja2 conditionnelle pour les erreurs. Conserver `input-error` (toujours supporté en DaisyUI 5).
  - Notes : En DaisyUI 5, les inputs ont un border par défaut. Les classes `form-control`, `label-text`, `label-text-alt` sont dépréciées.

- [x] **Task 6 : Mettre à jour `base.html` — remplacer CDN par fichiers locaux**
  - Fichier : `app/templates/base.html`
  - Actions :
    1. **Supprimer** la ligne 9 : `<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.24/dist/full.min.css" ...>`
    2. **Supprimer** les lignes 10-22 : `<script src="https://cdn.tailwindcss.com">` + bloc `tailwind.config`
    3. **Ajouter** à la place : `<link rel="stylesheet" href="{{ url_for('static', path='css/style.css') }}">`
    4. **Supprimer** le bloc `<style>` complet (lignes 24-78 : thème oklch + focus-visible + prefers-reduced-motion) — tout est désormais dans `input.css` (Task 3)
    5. **Supprimer** la ligne 100 : `<script src="https://unpkg.com/htmx.org@2.0.4" ...>`
    6. **Ajouter** à la place : `<script src="{{ url_for('static', path='js/htmx.min.js') }}"></script>`
    7. **Conserver** le bloc `<script>` de config HTMX `responseHandling` — inchangé
    8. **Supprimer** `data-theme="appgestiontemps"` de la balise `<html>` — le thème est défini comme `default: true` dans `input.css`, DaisyUI 5 l'applique automatiquement
  - Notes : Utiliser `url_for('static', path=...)` pour la résolution des chemins (pattern FastAPI/Jinja2 existant)

- [x] **Task 7 : Mettre à jour `.gitignore`**
  - Fichier : `.gitignore`
  - Action : Ajouter une section Node.js :
    ```
    # Node.js
    node_modules/
    ```
  - Notes : Ne PAS ignorer `app/static/css/style.css`, `app/static/js/htmx.min.js`, ni `package-lock.json` — ils sont commités (décisions techniques #4 et #5)

- [x] **Task 8 : Mettre à jour le Dockerfile avec multi-stage build**
  - Fichier : `Dockerfile`
  - Action : Remplacer le Dockerfile actuel par un multi-stage build :
    - **Stage 1 (`frontend`)** : Image `node:22-slim`
      - `WORKDIR /frontend`
      - Copier `package.json` et `package-lock.json`
      - `RUN mkdir -p app/static/js app/static/css`
      - `RUN npm ci` (install deps + postinstall copie HTMX)
      - Copier `postcss.config.mjs` et `app/static/css/input.css`
      - Copier `app/templates/` (nécessaire pour que Tailwind détecte les classes via `@source`)
      - `RUN npm run build:css`
    - **Stage 2 (`app`)** : Image `python:3.14-slim` (existant)
      - Copier `uv` depuis `ghcr.io/astral-sh/uv:latest`
      - Copier `pyproject.toml`, `uv.lock`, `RUN uv sync --frozen --no-dev`
      - Copier le code applicatif
      - `COPY --from=frontend /frontend/app/static/css/style.css app/static/css/style.css`
      - `COPY --from=frontend /frontend/app/static/js/htmx.min.js app/static/js/htmx.min.js`
      - `CMD` inchangé
  - Notes : Le multi-stage évite d'installer Node.js dans l'image finale Python. Il faut copier `app/templates/` dans le stage frontend pour que `@source` fonctionne et que Tailwind génère les bonnes classes.

- [x] **Task 9 : Vérification visuelle et tests**
  - Actions :
    1. Lancer l'app en local (`uv run uvicorn app.main:app --reload`)
    2. Vérifier visuellement toutes les pages : home, login, register, forgot-password, reset-password, settings, stats
    3. Vérifier que le thème custom (couleurs, fonts, focus ring) est identique
    4. Vérifier que les formulaires ont bien un border sur les inputs (sans la classe `input-bordered`)
    5. Vérifier que les labels de formulaire s'affichent correctement avec la nouvelle structure `fieldset`/`label`
    6. Vérifier que les messages d'erreur de validation inline s'affichent toujours en rouge
    7. Lancer `uv run pytest` — les 95 tests doivent passer
    8. Tester le build Docker : `docker build -t appgestiontemps .` puis `docker run -p 8000:8000 appgestiontemps`

### Acceptance Criteria

- [ ] **AC 1 :** Given le projet cloné, when `npm install` est exécuté, then les dépendances sont installées et `app/static/js/htmx.min.js` est copié automatiquement (via postinstall)
- [ ] **AC 2 :** Given les dépendances installées, when `npm run build:css` est exécuté, then `app/static/css/style.css` est généré sans erreurs et contient le CSS compilé (Tailwind utilities + DaisyUI components + thème custom)
- [ ] **AC 3 :** Given les dépendances installées, when `npm run watch:css` est exécuté, then le CSS est recompilé automatiquement à chaque modification de `input.css`
- [ ] **AC 4 :** Given l'app lancée en local, when on navigue sur toutes les pages (home, login, register, forgot-password, reset-password, settings, stats), then le rendu visuel est équivalent à l'ancien (mêmes couleurs, fonts, spacings, composants DaisyUI fonctionnels)
- [ ] **AC 5 :** Given l'app lancée en local, when on inspecte les sources HTML, then aucune référence CDN (jsdelivr, unpkg, cdn.tailwindcss.com) n'est présente
- [ ] **AC 6 :** Given l'app lancée en local, when on inspecte les sources HTML, then les fichiers CSS et JS sont servis depuis `/static/css/style.css` et `/static/js/htmx.min.js`
- [ ] **AC 7 :** Given les formulaires (login, register, reset-password, forgot-password), when on les affiche, then les inputs ont un border visible et la structure utilise `fieldset`/`label` (DaisyUI 5)
- [ ] **AC 8 :** Given les formulaires avec validation, when on soumet un formulaire invalide, then les messages d'erreur inline s'affichent en rouge sous les champs concernés
- [ ] **AC 9 :** Given la suite de tests existante, when `uv run pytest` est exécuté, then les 95 tests passent sans échec
- [ ] **AC 10 :** Given le Dockerfile mis à jour, when `docker build -t appgestiontemps .` est exécuté, then l'image est construite avec le CSS compilé et HTMX copié via multi-stage build

## Additional Context

### Dependencies

- **Node.js >= 18 LTS** — requis pour npm et le build CSS
- **npm** — inclus avec Node.js
- **Packages npm :**
  - `tailwindcss` v4 (latest) — framework CSS
  - `@tailwindcss/postcss` (latest) — plugin PostCSS pour Tailwind 4
  - `postcss` (latest) — processeur CSS
  - `postcss-cli` (latest) — CLI pour exécuter PostCSS
  - `daisyui` v5 (latest) — composants DaisyUI
  - `htmx.org` v2.0.8 — librairie HTMX
- **Aucune dépendance Python ajoutée**

### Testing Strategy

- **Tests existants (95 pytest)** : Doivent tous passer sans modification — cette migration n'impacte aucun code backend
- **Vérification visuelle** : Comparer manuellement chaque page avant/après migration (couleurs, fonts, spacings, composants, formulaires, validation inline)
- **Build pipeline** : Vérifier que `npm run build:css` produit un CSS fonctionnel contenant les utilities et composants attendus
- **Docker** : Vérifier que `docker build` fonctionne avec le multi-stage build
- **Pas de tests E2E ajoutés** — hors scope

### Notes

- **`watch:css` limitation** : `postcss-cli --watch` ne surveille que `input.css`, pas les templates. Si un dev ajoute une nouvelle classe Tailwind dans un template, il faut relancer `npm run build:css` manuellement. C'est une limitation connue de postcss-cli. Alternative future : utiliser `@tailwindcss/cli` avec `--watch` natif.
- **Rollback** : En cas de problème, `git revert` du commit de migration restaure l'état CDN. Commiter la migration en un seul commit atomique pour faciliter le rollback.
- **`package-lock.json`** : Doit être commité pour garantir la reproductibilité des builds (`npm ci` l'exige).
- **Source rétro Epic 1 :** `_bmad-output/implementation-artifacts/epic-1-retro-2026-03-17.md`
- **Référence doc DaisyUI 5 thèmes :** https://daisyui.com/docs/themes/
- **Référence doc DaisyUI 5 upgrade :** https://daisyui.com/docs/upgrade/
