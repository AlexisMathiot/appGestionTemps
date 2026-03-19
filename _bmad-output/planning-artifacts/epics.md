---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - 'planning-artifacts/prd.md'
  - 'planning-artifacts/architecture.md'
  - 'planning-artifacts/ux-design-specification.md'
---

# appGestionTemps - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for appGestionTemps, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Gestion de Compte**
- FR1: L'utilisateur peut créer un compte avec email et mot de passe
- FR2: L'utilisateur peut se connecter à son compte
- FR3: L'utilisateur peut se déconnecter
- FR4: L'utilisateur peut réinitialiser son mot de passe

**Gestion des Catégories**
- FR5: L'utilisateur peut créer une catégorie (thème principal) avec un nom
- FR6: L'utilisateur peut attribuer un emoji à une catégorie
- FR7: L'utilisateur peut attribuer une couleur à une catégorie
- FR8: L'utilisateur peut définir un objectif optionnel pour une catégorie (par jour ou par semaine)
- FR9: L'utilisateur peut modifier une catégorie existante
- FR10: L'utilisateur peut supprimer une catégorie
- FR11: L'utilisateur peut voir la liste de ses catégories
- FR12: L'utilisateur peut créer une sous-catégorie (activité) rattachée à une catégorie parente
- FR13: L'utilisateur peut attribuer un emoji à une sous-catégorie
- FR14: L'utilisateur peut modifier une sous-catégorie
- FR15: L'utilisateur peut supprimer une sous-catégorie
- FR16: L'utilisateur peut voir les sous-catégories d'une catégorie

**Tracking du Temps**
- FR17: L'utilisateur peut démarrer un timer pour une catégorie ou une sous-catégorie
- FR18: L'utilisateur peut mettre en pause un timer en cours
- FR19: L'utilisateur peut reprendre un timer en pause
- FR20: L'utilisateur peut arrêter un timer et enregistrer la session
- FR21: L'utilisateur peut voir le temps écoulé du timer en temps réel
- FR22: L'utilisateur peut ajouter une note à une session (ce qui a été fait, ressenti)
- FR23: L'utilisateur peut créer une entrée de temps manuellement
- FR24: L'utilisateur peut modifier une entrée de temps existante
- FR25: L'utilisateur peut supprimer une entrée de temps

**Visualisation & Statistiques**
- FR26: L'utilisateur peut voir ses statistiques du jour (temps par catégorie)
- FR27: L'utilisateur peut voir ses statistiques de la semaine
- FR28: L'utilisateur peut voir un graphique camembert de répartition du temps
- FR29: L'utilisateur peut voir un heatmap calendrier (style GitHub) de son activité
- FR30: L'utilisateur peut identifier la catégorie où il a passé le plus de temps
- FR31: L'utilisateur peut voir ses statistiques agrégées par catégorie parente
- FR32: L'utilisateur peut voir le détail des statistiques par sous-catégorie

**Gamification & Objectifs**
- FR33: L'utilisateur peut voir ses streaks par catégorie (jours consécutifs)
- FR34: L'utilisateur peut voir sa progression vers ses objectifs définis
- FR35: L'utilisateur peut voir si un objectif est atteint ou non

**Navigation & Interface**
- FR36: L'utilisateur peut accéder rapidement à ses catégories depuis l'écran d'accueil
- FR37: L'utilisateur peut démarrer une session en un minimum d'interactions
- FR38: L'utilisateur peut naviguer entre les sections (accueil, stats, catégories)

### NonFunctional Requirements

**Performance**
- NFR1: Chargement page < 1 seconde
- NFR2: Mise à jour timer en temps réel (1x/sec)
- NFR3: Réponse actions utilisateur < 200ms
- NFR4: Taille page < 500KB
- NFR5: First Contentful Paint < 1s
- NFR6: Time to Interactive < 2s

**Sécurité**
- NFR7: Authentification email + mot de passe hashé (bcrypt)
- NFR8: Sessions avec tokens sécurisés et expiration
- NFR9: HTTPS obligatoire
- NFR10: Données utilisateur isolées par compte
- NFR11: Mot de passe minimum 8 caractères

**Fiabilité**
- NFR12: Aucune perte de données de tracking
- NFR13: Timer précis même si page en arrière-plan
- NFR14: Disponibilité best effort (pas de SLA formel)

**Accessibilité**
- NFR15: Navigation clavier complète
- NFR16: Contraste WCAG AA (4.5:1 minimum)
- NFR17: Labels sur tous les champs de formulaire
- NFR18: Focus visible sur les éléments interactifs

### Additional Requirements

**Infrastructure & Setup (Architecture)**
- Structure projet custom FastAPI + HTMX + SQLAlchemy async (pas de starter template existant)
- Initialisation avec uv (gestionnaire Python moderne) + dépendances définies
- Docker + docker-compose pour dev/prod parity
- GitHub Actions pour CI/CD (tests + lint automatiques)
- Configuration par .env files (dev, test, prod)
- Alembic pour migrations de base de données

**Data Architecture**
- UUID v4 pour toutes les clés primaires (sécurité, pas d'énumération)
- Modèle de données : User → Category (self-reference pour sous-catégories) → TimeEntry
- SQLAlchemy 2.0 async avec asyncpg

**Authentication & Security**
- Sessions cookie-based avec itsdangerous (stateless, pas de Redis)
- Password hashing avec passlib + bcrypt
- CSRF protection via middleware + tokens
- Dependency injection `get_current_user` sur toutes les routes protégées

**API & Communication Patterns**
- Server-side rendering Jinja2 + HTMX fragments pour interactivité
- Convention réponses HTMX : 200 → HTML fragment, 422 → form errors, 401 → HX-Redirect login, 500 → toast
- Timer client-side : JavaScript minimal (setInterval 1s), localStorage pour persistance, Page Visibility API

**PWA**
- Service Worker avec Workbox
- Cache-first pour assets, network-first pour API
- Manifest standalone, theme colors
- Banner "Mode hors-ligne" pour UX offline

**Conventions & Patterns**
- Nommage : snake_case Python, PascalCase classes, underscore prefix pour fragments HTMX
- Organisation : 1 fichier par domaine (router, model, service)
- Business logic dans services, jamais dans routers
- HTML fragments en réponse, jamais JSON brut pour UI

### UX Design Requirements

- UX-DR1: Implémentation du design system Tailwind CSS + DaisyUI avec thème custom (palette: Primary #3B82F6, Secondary #64748B, Accent/Success #22C55E, Warning #F59E0B, Error #EF4444)
- UX-DR2: Système typographique avec Inter/System fonts pour le texte et JetBrains Mono pour le timer (48-64px)
- UX-DR3: Échelle d'espacement base 4px (xs:4px, sm:8px, md:16px, lg:24px, xl:32px, 2xl:48px)
- UX-DR4: Category Cards — composant carte DaisyUI (`card card-compact`) avec emoji prominent, nom, temps du jour, couleur personnalisée, grid 2 colonnes mobile
- UX-DR5: Timer Display — composant `stat` DaisyUI avec font mono grande taille (01:23:45), header sticky quand actif, contrôles pause/stop
- UX-DR6: Bottom Navigation — `btm-nav` DaisyUI 3 items (Accueil, Stats, Settings), 64px hauteur
- UX-DR7: Heatmap calendrier custom style GitHub — 52 semaines visibles, dégradé gris → vert, affichage jours L-M-M-J-V-S-D
- UX-DR8: Graphique camembert pour répartition du temps par catégorie avec couleurs par catégorie
- UX-DR9: Streak badges — `badge badge-accent` DaisyUI avec icône flamme, liste des streaks actifs par catégorie
- UX-DR10: Modal création catégorie — `modal modal-bottom sm:modal-middle` avec champs nom, picker emoji, palette couleur, toggle objectif optionnel
- UX-DR11: Modal note post-session — affiche catégorie + durée, textarea optionnel, boutons "Passer" et "Enregistrer"
- UX-DR12: Écran accueil — résumé jour en header, grid catégories, bouton "+" pour ajouter catégorie, empty state avec message guide
- UX-DR13: Écran stats — tabs période (Jour/Semaine/Mois), barres de progression par catégorie, heatmap, camembert, streaks
- UX-DR14: Responsive design — Mobile 2 colonnes, Tablet 3 colonnes, Desktop 4 colonnes pour grid catégories + layout 2 panneaux
- UX-DR15: Touch targets minimum 44x44px, zones de tap généreuses pour usage mobile
- UX-DR16: Focus visible (ring 2px primary color), support `prefers-reduced-motion`
- UX-DR17: Feedback interactions — vibration légère au démarrage timer (mobile), animation succès à l'enregistrement, couleur atténuée pour timer en pause
- UX-DR18: Saisie manuelle de temps — formulaire avec sélection catégorie, date/heure début/fin, note optionnelle

### FR Coverage Map

- FR1: Epic 1 — Création de compte (email + mot de passe)
- FR2: Epic 1 — Connexion au compte
- FR3: Epic 1 — Déconnexion
- FR4: Epic 1 — Réinitialisation mot de passe
- FR5: Epic 2 — Création catégorie avec nom
- FR6: Epic 2 — Attribution emoji à catégorie
- FR7: Epic 2 — Attribution couleur à catégorie
- FR8: Epic 2 — Objectif optionnel par catégorie (jour/semaine)
- FR9: Epic 2 — Modification catégorie
- FR10: Epic 2 — Suppression catégorie
- FR11: Epic 2 — Liste des catégories
- FR12: Epic 2 — Création sous-catégorie
- FR13: Epic 2 — Attribution emoji à sous-catégorie
- FR14: Epic 2 — Modification sous-catégorie
- FR15: Epic 2 — Suppression sous-catégorie
- FR16: Epic 2 — Liste sous-catégories d'une catégorie
- FR17: Epic 3 — Démarrer timer pour catégorie/sous-catégorie
- FR18: Epic 3 — Pause timer
- FR19: Epic 3 — Reprendre timer
- FR20: Epic 3 — Arrêter timer et enregistrer session
- FR21: Epic 3 — Affichage temps réel du timer
- FR22: Epic 3 — Ajouter note à une session
- FR23: Epic 3 — Saisie manuelle entrée de temps
- FR24: Epic 3 — Modification entrée de temps
- FR25: Epic 3 — Suppression entrée de temps
- FR26: Epic 4 — Statistiques du jour
- FR27: Epic 4 — Statistiques de la semaine
- FR28: Epic 4 — Graphique camembert répartition
- FR29: Epic 4 — Heatmap calendrier style GitHub
- FR30: Epic 4 — Catégorie principale identifiée
- FR31: Epic 4 — Stats agrégées par catégorie parente
- FR32: Epic 4 — Détail stats par sous-catégorie
- FR33: Epic 5 — Streaks par catégorie
- FR34: Epic 5 — Progression vers objectifs
- FR35: Epic 5 — Indicateur objectif atteint/non atteint
- FR36: Epic 1 — Accès rapide catégories depuis accueil
- FR37: Epic 3 — Démarrage session en minimum d'interactions
- FR38: Epic 1 — Navigation entre sections

## Epic List

### Epic 1 : Authentification & Fondations de l'App
L'utilisateur peut créer un compte, se connecter, et naviguer dans l'application avec le layout de base en place.
**FRs couverts :** FR1, FR2, FR3, FR4, FR36, FR38
**UX-DRs :** UX-DR1, UX-DR2, UX-DR3, UX-DR6, UX-DR16
**Inclut :** Setup projet (structure, deps, Docker, DB, Alembic), design system DaisyUI, layout de base avec bottom nav, auth complète (register, login, logout, reset password), CSRF protection, sessions cookie-based.

### Epic 2 : Gestion des Catégories
L'utilisateur peut créer, personnaliser et organiser ses catégories d'activités avec emojis, couleurs, objectifs et sous-catégories.
**FRs couverts :** FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16
**UX-DRs :** UX-DR4, UX-DR10, UX-DR12, UX-DR14, UX-DR15
**Dépendances :** Epic 1 (auth + layout)

### Epic 3 : Tracking du Temps
L'utilisateur peut tracker son temps via un timer temps réel (start/pause/stop en 1 tap) ou par saisie manuelle, avec notes optionnelles par session.
**FRs couverts :** FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR37
**UX-DRs :** UX-DR5, UX-DR11, UX-DR17, UX-DR18
**Dépendances :** Epic 1 (auth), Epic 2 (catégories)

### Epic 4 : Statistiques & Visualisations
L'utilisateur peut consulter ses statistiques jour/semaine, voir la répartition via camembert, suivre son activité sur un heatmap GitHub-style, et explorer les détails par catégorie et sous-catégorie.
**FRs couverts :** FR26, FR27, FR28, FR29, FR30, FR31, FR32
**UX-DRs :** UX-DR7, UX-DR8, UX-DR13
**Dépendances :** Epic 1 (auth), Epic 2 (catégories), Epic 3 (time entries)

### Epic 5 : Gamification & Objectifs
L'utilisateur peut voir ses streaks par catégorie (jours consécutifs), suivre sa progression vers ses objectifs définis, et savoir si un objectif est atteint.
**FRs couverts :** FR33, FR34, FR35
**UX-DRs :** UX-DR9
**Dépendances :** Epic 1 (auth), Epic 2 (catégories + objectifs), Epic 3 (time entries)

### Epic 6 : PWA & Expérience Mobile Optimisée
L'utilisateur peut installer l'app sur son téléphone, bénéficier d'un mode hors-ligne basique avec cache des données, et d'une expérience mobile native optimisée.
**FRs couverts :** Aucun FR direct — couvre les exigences Architecture PWA et NFRs performance/fiabilité
**Inclut :** Service Worker (Workbox), manifest standalone, cache strategies (cache-first assets, network-first API), banner offline, optimisation performance (FCP < 1s, TTI < 2s)

## Epic 1 : Authentification & Fondations de l'App

L'utilisateur peut créer un compte, se connecter, et naviguer dans l'application avec le layout de base en place.

### Story 1.1 : Initialisation du projet et infrastructure de base

As a développeur,
I want un projet FastAPI initialisé avec la structure définie, les dépendances, Docker, la base de données PostgreSQL et Alembic,
So that j'ai une fondation technique solide pour construire l'application.

**Acceptance Criteria:**

**Given** le dépôt est vide
**When** le script d'initialisation est exécuté
**Then** la structure projet complète est créée (app/, templates/, static/, tests/, alembic/)
**And** pyproject.toml contient toutes les dépendances (FastAPI, SQLAlchemy, asyncpg, Alembic, etc.)
**And** docker-compose.yml lance FastAPI + PostgreSQL
**And** Alembic est configuré et connecté à la base
**And** une route health-check `/health` retourne 200
**And** le modèle User (id UUID, email, password_hash, created_at, updated_at) est créé avec migration Alembic

### Story 1.2 : Design system et layout de base

As a utilisateur,
I want une interface visuellement cohérente avec une navigation claire entre les sections,
So that je puisse me repérer facilement dans l'application.

**Acceptance Criteria:**

**Given** le projet est initialisé
**When** l'utilisateur accède à l'application
**Then** le template base.html intègre Tailwind CSS + DaisyUI avec le thème custom (Primary #3B82F6, Accent #22C55E, etc.)
**And** la typographie Inter/System est appliquée avec l'échelle d'espacement base 4px
**And** une bottom navigation (`btm-nav`) 3 items (Accueil, Stats, Settings) est visible sur mobile (64px hauteur)
**And** la navigation fonctionne avec `hx-push-url` pour l'historique browser
**And** le focus est visible (ring 2px primary) sur tous les éléments interactifs
**And** `prefers-reduced-motion` est respecté
**And** les pages Accueil, Stats et Settings existent en placeholder

### Story 1.3 : Inscription utilisateur

As a nouvel utilisateur,
I want créer un compte avec mon email et un mot de passe,
So that j'aie un espace personnel pour tracker mon temps.

**Acceptance Criteria:**

**Given** l'utilisateur est sur la page d'inscription
**When** il saisit un email valide et un mot de passe (min 8 caractères)
**Then** le compte est créé avec le mot de passe hashé (bcrypt)
**And** l'utilisateur est automatiquement connecté (session cookie-based via itsdangerous)
**And** il est redirigé vers l'accueil

**Given** l'utilisateur saisit un email déjà utilisé
**When** il soumet le formulaire
**Then** un message d'erreur inline s'affiche (422)

**Given** l'utilisateur saisit un mot de passe < 8 caractères
**When** il soumet le formulaire
**Then** un message de validation s'affiche

### Story 1.4 : Connexion et déconnexion

As a utilisateur existant,
I want me connecter à mon compte et me déconnecter,
So that j'accède à mes données en toute sécurité.

**Acceptance Criteria:**

**Given** l'utilisateur est sur la page de connexion
**When** il saisit email + mot de passe corrects
**Then** une session cookie sécurisée est créée
**And** il est redirigé vers l'accueil
**And** la protection CSRF est active sur tous les formulaires

**Given** l'utilisateur saisit des identifiants incorrects
**When** il soumet le formulaire
**Then** un message d'erreur générique s'affiche (pas de fuite d'info)

**Given** l'utilisateur est connecté
**When** il clique sur "Déconnexion"
**Then** la session est détruite et il est redirigé vers la page de connexion

**Given** l'utilisateur n'est pas connecté
**When** il accède à une route protégée
**Then** il est redirigé vers `/login` (HX-Redirect pour requêtes HTMX)

### Story 1.5 : Réinitialisation du mot de passe

As a utilisateur ayant oublié son mot de passe,
I want pouvoir le réinitialiser via mon email,
So that je puisse retrouver l'accès à mon compte.

**Acceptance Criteria:**

**Given** l'utilisateur est sur la page de réinitialisation
**When** il saisit son email
**Then** un token de réinitialisation sécurisé est généré
**And** un email est envoyé avec un lien de réinitialisation (ou affiché en dev)

**Given** l'utilisateur clique sur le lien valide
**When** il saisit un nouveau mot de passe (min 8 caractères)
**Then** le mot de passe est mis à jour (bcrypt)
**And** il est redirigé vers la page de connexion

**Given** le token a expiré ou est invalide
**When** l'utilisateur accède au lien
**Then** un message d'erreur s'affiche avec possibilité de recommencer

## Epic 2 : Gestion des Catégories

L'utilisateur peut créer, personnaliser et organiser ses catégories d'activités avec emojis, couleurs, objectifs et sous-catégories.

### Story 2.1 : Modèle Category et écran d'accueil avec empty state

As a utilisateur connecté,
I want voir mon écran d'accueil avec un message guide quand je n'ai pas encore de catégories,
So that je sache immédiatement comment commencer à utiliser l'app.

**Acceptance Criteria:**

**Given** l'utilisateur est connecté et n'a aucune catégorie
**When** il accède à l'accueil
**Then** le modèle Category (id UUID, user_id, parent_id nullable, name, emoji, color, goal_type, goal_value, position, created_at) existe avec migration Alembic
**And** un empty state s'affiche avec le message "Créez votre première catégorie"
**And** un bouton "+" est visible pour ajouter une catégorie
**And** le résumé jour "Aujourd'hui: 0h 0min" est affiché en header
**And** les données sont isolées par user_id (NFR10)

### Story 2.2 : Création d'une catégorie

As a utilisateur,
I want créer une catégorie avec un nom, un emoji et une couleur,
So that je puisse organiser mes activités par thème.

**Acceptance Criteria:**

**Given** l'utilisateur clique sur le bouton "+"
**When** le modal de création s'ouvre (`modal modal-bottom sm:modal-middle`)
**Then** le formulaire contient les champs : nom, picker emoji, palette couleur

**Given** l'utilisateur remplit nom + emoji + couleur et valide
**When** il clique sur "Créer"
**Then** la catégorie est créée en base de données
**And** le modal se ferme
**And** la catégorie apparaît sur la grid d'accueil en card DaisyUI (`card card-compact`) avec emoji prominent
**And** la grid est en 2 colonnes sur mobile, 3 sur tablet, 4 sur desktop
**And** les touch targets font minimum 44x44px

**Given** l'utilisateur ne saisit pas de nom
**When** il soumet le formulaire
**Then** un message de validation inline s'affiche

### Story 2.3 : Objectif optionnel sur une catégorie

As a utilisateur,
I want définir un objectif optionnel sur une catégorie (par jour ou par semaine),
So that je puisse me fixer des cibles de temps.

**Acceptance Criteria:**

**Given** l'utilisateur est dans le modal de création de catégorie
**When** il active le toggle "Définir un objectif"
**Then** un sélecteur apparaît : type (par jour / par semaine) + valeur (durée)

**Given** l'utilisateur crée une catégorie avec objectif "15 min/jour"
**When** la catégorie est sauvegardée
**Then** l'objectif est stocké en base (goal_type, goal_value)
**And** l'objectif est affiché sur la card de la catégorie

**Given** l'utilisateur ne définit pas d'objectif
**When** il crée la catégorie
**Then** goal_type et goal_value sont null
**And** aucun indicateur d'objectif n'est affiché sur la card

### Story 2.4 : Modification et suppression de catégorie

As a utilisateur,
I want modifier ou supprimer une catégorie existante,
So that je puisse ajuster mon organisation au fil du temps.

**Acceptance Criteria:**

**Given** l'utilisateur a des catégories existantes
**When** il accède aux options d'une catégorie (tap long ou bouton éditer)
**Then** il peut modifier le nom, l'emoji, la couleur et l'objectif

**Given** l'utilisateur modifie une catégorie et valide
**When** les changements sont sauvegardés
**Then** la card est mise à jour via HTMX (fragment swap)
**And** les entrées de temps existantes restent liées

**Given** l'utilisateur supprime une catégorie
**When** il confirme la suppression
**Then** la catégorie et ses sous-catégories sont supprimées
**And** la grid d'accueil est mise à jour
**And** une confirmation est demandée avant suppression (modal de confirmation)

### Story 2.5 : Sous-catégories (activités)

As a utilisateur,
I want créer des sous-catégories rattachées à une catégorie parente,
So that je puisse détailler mes activités au sein d'un thème.

**Acceptance Criteria:**

**Given** l'utilisateur accède au détail d'une catégorie
**When** il clique sur "Ajouter une sous-catégorie"
**Then** un formulaire permet de saisir nom + emoji pour la sous-catégorie

**Given** l'utilisateur crée une sous-catégorie
**When** elle est sauvegardée
**Then** elle apparaît dans la liste des sous-catégories de la catégorie parente (parent_id renseigné)
**And** la sous-catégorie hérite de la couleur de la catégorie parente

**Given** l'utilisateur a des sous-catégories
**When** il consulte une catégorie
**Then** la liste des sous-catégories est affichée avec leurs emojis

**Given** l'utilisateur modifie ou supprime une sous-catégorie
**When** l'action est confirmée
**Then** la modification/suppression est effectuée
**And** la liste est mise à jour via HTMX

## Epic 3 : Tracking du Temps

L'utilisateur peut tracker son temps via un timer temps réel (start/pause/stop en 1 tap) ou par saisie manuelle, avec notes optionnelles par session.

### Story 3.1 : Modèle TimeEntry et démarrage du timer

As a utilisateur,
I want démarrer un timer en tappant sur une catégorie,
So that je puisse tracker mon temps en un minimum d'interactions.

**Acceptance Criteria:**

**Given** l'utilisateur est sur l'accueil avec des catégories
**When** il tape sur une catégorie
**Then** le modèle TimeEntry (id UUID, user_id, category_id, started_at, ended_at nullable, duration_seconds nullable, note nullable, created_at) est créé avec migration Alembic
**And** une entrée TimeEntry est créée côté serveur (POST /api/timer/start) avec started_at = now
**And** le timer démarre côté client (JavaScript setInterval 1s)
**And** l'état du timer est persisté dans localStorage (timer_active, start_time, category_id)
**And** un header sticky affiche le timer actif avec le temps en font mono (JetBrains Mono, 48-64px)
**And** la catégorie active est visuellement mise en avant (couleur)
**And** une vibration légère est déclenchée sur mobile

### Story 3.2 : Pause, reprise et affichage temps réel

As a utilisateur,
I want mettre en pause et reprendre mon timer tout en voyant le temps s'écouler,
So that je puisse gérer les interruptions sans perdre ma session.

**Acceptance Criteria:**

**Given** un timer est actif
**When** l'utilisateur clique sur "Pause"
**Then** le timer se fige visuellement
**And** la couleur du timer est atténuée pour indiquer la pause
**And** l'état est mis à jour dans localStorage

**Given** un timer est en pause
**When** l'utilisateur clique sur "Play"
**Then** le timer reprend depuis où il s'était arrêté
**And** le temps s'affiche en temps réel (update 1x/sec)

**Given** un timer est actif et l'utilisateur change d'onglet
**When** il revient sur l'app
**Then** le temps affiché est réconcilié grâce à Page Visibility API
**And** le timer est précis même après un passage en arrière-plan (NFR13)

### Story 3.3 : Arrêt du timer et enregistrement avec note

As a utilisateur,
I want arrêter mon timer et optionnellement ajouter une note à ma session,
So that je puisse capturer le contexte de mon travail.

**Acceptance Criteria:**

**Given** un timer est actif (ou en pause)
**When** l'utilisateur clique sur "Stop"
**Then** le timer s'arrête
**And** un modal s'affiche ("Session terminée") avec catégorie, durée, et textarea pour note optionnelle

**Given** le modal post-session est affiché
**When** l'utilisateur clique sur "Enregistrer" (avec ou sans note)
**Then** l'entrée TimeEntry est mise à jour côté serveur (ended_at, duration_seconds, note)
**And** le modal se ferme
**And** le header sticky timer disparaît
**And** le résumé du jour sur l'accueil est mis à jour
**And** localStorage est nettoyé

**Given** le modal post-session est affiché
**When** l'utilisateur clique sur "Passer"
**Then** la session est enregistrée sans note
**And** le comportement est identique à "Enregistrer"

### Story 3.4 : Saisie manuelle d'une entrée de temps

As a utilisateur,
I want ajouter manuellement une entrée de temps passée,
So that je puisse rattraper du temps non tracké en live.

**Acceptance Criteria:**

**Given** l'utilisateur accède à la saisie manuelle
**When** le formulaire s'affiche
**Then** il contient : sélection catégorie/sous-catégorie, date, heure début, heure fin, note optionnelle

**Given** l'utilisateur remplit le formulaire avec des données valides
**When** il soumet
**Then** une entrée TimeEntry est créée avec les valeurs saisies
**And** duration_seconds est calculé automatiquement (fin - début)
**And** les statistiques sont mises à jour

**Given** l'utilisateur saisit une heure de fin antérieure à l'heure de début
**When** il soumet le formulaire
**Then** un message de validation s'affiche

### Story 3.5 : Modification et suppression d'entrées de temps

As a utilisateur,
I want modifier ou supprimer une entrée de temps existante,
So that je puisse corriger des erreurs de saisie.

**Acceptance Criteria:**

**Given** l'utilisateur consulte l'historique de ses sessions (sur l'écran timer ou accueil)
**When** il sélectionne une entrée
**Then** il peut modifier la catégorie, les horaires et la note

**Given** l'utilisateur modifie une entrée et valide
**When** les changements sont sauvegardés
**Then** duration_seconds est recalculé
**And** l'affichage est mis à jour via HTMX

**Given** l'utilisateur supprime une entrée
**When** il confirme la suppression
**Then** l'entrée est supprimée de la base
**And** les statistiques du jour sont recalculées
**And** l'affichage est mis à jour

## Epic 4 : Statistiques & Visualisations

L'utilisateur peut consulter ses statistiques jour/semaine, voir la répartition via camembert, suivre son activité sur un heatmap GitHub-style, et explorer les détails par catégorie et sous-catégorie.

### Story 4.1 : Statistiques jour et semaine avec barres de progression

As a utilisateur,
I want voir mes statistiques du jour et de la semaine avec le temps par catégorie,
So that je comprenne rapidement comment j'ai réparti mon temps.

**Acceptance Criteria:**

**Given** l'utilisateur accède à l'onglet Stats
**When** la page s'affiche
**Then** des tabs période (Jour / Semaine / Mois) sont disponibles (`tabs tabs-boxed`)
**And** le total du temps est affiché ("Cette semaine: 23h 15min")

**Given** l'utilisateur sélectionne "Jour"
**When** les stats se chargent
**Then** le temps par catégorie parente est affiché avec barres de progression (`progress progress-primary`)
**And** la catégorie avec le plus de temps est identifiée visuellement (FR30)

**Given** l'utilisateur sélectionne "Semaine"
**When** les stats se chargent
**Then** le temps agrégé par catégorie parente est affiché (FR31)
**And** les barres de progression reflètent les proportions

**Given** l'utilisateur tape sur une catégorie dans les stats
**When** le détail s'ouvre
**Then** les sous-catégories sont affichées avec leurs temps individuels (FR32)

### Story 4.2 : Graphique camembert de répartition

As a utilisateur,
I want voir un graphique camembert de la répartition de mon temps,
So that j'aie une vue visuelle immédiate de mes proportions.

**Acceptance Criteria:**

**Given** l'utilisateur est sur l'écran Stats
**When** la section camembert s'affiche
**Then** un graphique camembert montre la répartition par catégorie
**And** chaque segment utilise la couleur de la catégorie
**And** les pourcentages sont affichés
**And** la légende liste les catégories avec emoji + pourcentage

**Given** l'utilisateur n'a aucune donnée pour la période
**When** la section camembert s'affiche
**Then** un message "Aucune donnée pour cette période" est affiché

**Given** l'utilisateur change la période (Jour/Semaine/Mois)
**When** le camembert se met à jour
**Then** les proportions reflètent la période sélectionnée

### Story 4.3 : Heatmap calendrier style GitHub

As a utilisateur,
I want voir un heatmap calendrier de mon activité sur l'année,
So that je visualise ma régularité et ma progression au fil du temps.

**Acceptance Criteria:**

**Given** l'utilisateur est sur l'écran Stats
**When** la section heatmap s'affiche
**Then** un calendrier de 52 semaines est affiché en grille (style GitHub)
**And** les jours de la semaine (L-M-M-J-V-S-D) sont affichés en labels
**And** chaque carré représente un jour avec un dégradé gris → vert selon l'intensité d'activité

**Given** l'utilisateur a tracké du temps un jour donné
**When** le heatmap s'affiche
**Then** le carré de ce jour est coloré en vert (intensité proportionnelle au temps total)

**Given** l'utilisateur n'a pas d'activité un jour donné
**When** le heatmap s'affiche
**Then** le carré est gris clair

**Given** l'utilisateur survole ou tape un carré du heatmap
**When** l'interaction se produit
**Then** une infobulle affiche la date et le temps total de ce jour

## Epic 5 : Gamification & Objectifs

L'utilisateur peut voir ses streaks par catégorie (jours consécutifs), suivre sa progression vers ses objectifs définis, et savoir si un objectif est atteint.

### Story 5.1 : Streaks par catégorie

As a utilisateur,
I want voir mes streaks (jours consécutifs d'activité) par catégorie,
So that je sois motivé à maintenir ma régularité.

**Acceptance Criteria:**

**Given** l'utilisateur est sur l'écran Stats
**When** la section Streaks s'affiche
**Then** une liste des streaks actifs par catégorie est affichée
**And** chaque streak est affiché avec un badge DaisyUI (`badge badge-accent`) + icône flamme
**And** le nombre de jours consécutifs est indiqué

**Given** l'utilisateur a tracké du temps dans "Chinois" 4 jours consécutifs
**When** les streaks sont calculés
**Then** "Chinois: 4 jours" est affiché avec l'icône flamme

**Given** l'utilisateur n'a pas tracké une catégorie hier
**When** les streaks sont calculés
**Then** le streak de cette catégorie est remis à 0
**And** le message reste neutre (pas de culpabilité, pas de "streak perdu")

**Given** l'utilisateur n'a aucun streak actif
**When** la section s'affiche
**Then** un message encourageant s'affiche ("Commencez à tracker pour voir vos streaks")

### Story 5.2 : Progression vers les objectifs

As a utilisateur,
I want voir ma progression vers les objectifs définis sur mes catégories,
So that je sache où j'en suis par rapport à mes cibles.

**Acceptance Criteria:**

**Given** l'utilisateur a des catégories avec objectifs définis
**When** il consulte l'accueil ou les stats
**Then** un indicateur de progression est visible sur chaque catégorie ayant un objectif
**And** la progression est exprimée en pourcentage (temps tracké / objectif)

**Given** une catégorie a un objectif "15 min/jour" et l'utilisateur a tracké 10 min aujourd'hui
**When** la progression s'affiche
**Then** l'indicateur montre 67% (10/15)
**And** une barre de progression ou indicateur visuel reflète l'avancement

**Given** une catégorie a un objectif "2h/semaine" et l'utilisateur a tracké 2h30
**When** la progression s'affiche
**Then** l'objectif est marqué comme atteint (FR35)
**And** un indicateur visuel de succès est affiché (couleur accent/vert)

**Given** une catégorie n'a pas d'objectif défini
**When** l'affichage se construit
**Then** aucun indicateur de progression n'est affiché pour cette catégorie

## Epic 6 : PWA & Expérience Mobile Optimisée

L'utilisateur peut installer l'app sur son téléphone, bénéficier d'un mode hors-ligne basique avec cache des données, et d'une expérience mobile native optimisée.

### Story 6.1 : Manifest PWA et installation

As a utilisateur,
I want installer l'application sur mon téléphone comme une app native,
So that j'y accède rapidement depuis mon écran d'accueil.

**Acceptance Criteria:**

**Given** l'utilisateur accède à l'app depuis un navigateur mobile
**When** les critères PWA sont remplis
**Then** un fichier `manifest.json` est configuré (name, short_name, icons, start_url, display: standalone, theme_color, background_color)
**And** les icônes sont disponibles en plusieurs tailles (192x192, 512x512)
**And** le navigateur propose l'installation ("Ajouter à l'écran d'accueil")

**Given** l'utilisateur installe la PWA
**When** il l'ouvre depuis l'écran d'accueil
**Then** l'app se lance en mode standalone (sans barre d'adresse)
**And** les couleurs du thème sont appliquées (status bar)

### Story 6.2 : Service Worker et cache offline

As a utilisateur,
I want que l'app fonctionne en mode dégradé quand je n'ai pas de connexion,
So that je puisse au moins consulter mes données récentes.

**Acceptance Criteria:**

**Given** l'app est chargée pour la première fois
**When** le Service Worker (Workbox) s'installe
**Then** les assets statiques (CSS, JS, images, fonts) sont mis en cache (cache-first strategy)
**And** les pages HTML sont cachées pour consultation offline

**Given** l'utilisateur perd sa connexion
**When** il ouvre l'app
**Then** les pages cachées sont servies depuis le cache
**And** un banner "Mode hors-ligne" s'affiche clairement
**And** les requêtes API utilisent network-first avec fallback sur le cache

**Given** l'utilisateur retrouve sa connexion
**When** l'app détecte le retour en ligne
**Then** le banner offline disparaît
**And** les données sont synchronisées avec le serveur

### Story 6.3 : Optimisation performance

As a utilisateur,
I want que l'app se charge rapidement et soit réactive,
So that mon expérience soit fluide au quotidien.

**Acceptance Criteria:**

**Given** l'utilisateur accède à l'app
**When** la page se charge
**Then** le First Contentful Paint est < 1 seconde (NFR5)
**And** le Time to Interactive est < 2 secondes (NFR6)
**And** la taille totale de la page est < 500KB (NFR4)

**Given** l'utilisateur interagit avec l'app (tap, navigation)
**When** une action est déclenchée
**Then** la réponse est perçue en < 200ms (NFR3)
**And** les fragments HTMX se chargent sans flash visuel

**Given** les assets sont déjà en cache (visite suivante)
**When** l'utilisateur ouvre l'app
**Then** le chargement est quasi-instantané grâce au cache Service Worker
