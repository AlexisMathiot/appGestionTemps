---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
inputDocuments: ['brainstorming-session-2026-01-28.md']
workflowType: 'prd'
workflow: 'edit'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 1
  projectDocs: 0
classification:
  projectType: 'web_app (PWA)'
  domain: 'Productivité personnelle'
  complexity: 'low'
  projectContext: 'greenfield'
  evolutionPrevue: 'Potentiellement public si pertinent'
lastEdited: '2026-02-04'
editHistory:
  - date: '2026-02-04'
    changes: 'Changement stack technique: Go + Gin → FastAPI (Python) + SQLAlchemy'
---

# Product Requirements Document - appGestionTemps

**Author:** Alex
**Date:** 2026-01-28

## Executive Summary

**Projet :** Application de gestion du temps personnelle
**Objectif :** Transformer la relation d'Alex avec son temps en offrant visibilité et structure
**Problème résolu :** Dispersion, manque d'organisation, impression de "tout faire en même temps et rien à la fois"
**Utilisateur cible :** Alex (usage personnel), potentiellement public si pertinent
**Stack technique :** FastAPI (Python), PostgreSQL, SQLAlchemy, HTMX, Tailwind CSS (PWA)
**Approche :** Problem-Solving MVP — dev solo, simplicité assumée

## Success Criteria

### Succès Utilisateur

- **Clarté** : Avoir une vision précise de la répartition de son temps après 1 mois d'utilisation
- **Organisation** : Pouvoir dégager des blocs de temps dédiés à 100% à une activité
- **Régularité** : Maintenir une pratique régulière des activités importantes (chinois, sport, travail freelance)
- **Conscience** : Identifier les patterns de dispersion vs concentration
- **Motivation** : Sentiment de progresser grâce aux streaks et à la visualisation (heatmap)

### Succès Business

**Court terme (personnel, 1-3 mois) :**
- Utilisation quotidienne de l'app par le créateur
- Vision claire de la répartition du temps obtenue

**Moyen terme (si ouverture au public) :**
- Premiers utilisateurs externes testent l'app
- Retours positifs sur l'utilité et la simplicité

### Résultats Mesurables

- **À 1 semaine** : Premières données visibles, patterns émergents
- **À 1 mois** : Évaluation complète — l'app "vaut le coup" ou non
- **Objectifs** : Définis par l'utilisateur dans l'app, pas imposés

## Stack Technique

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| Backend | FastAPI (Python) | Maîtrise Python, apprentissage FastAPI, async natif |
| Base de données | PostgreSQL | Relationnel, expérience existante |
| ORM | SQLAlchemy | ORM Python mature, support async, migrations (Alembic) |
| Frontend | HTMX + Jinja2 templates | Éviter JS complexe, interactivité simple |
| CSS | Tailwind CSS | Productif, responsive |
| Plateforme | PWA | Web + mobile, une seule codebase |
| Auth | Sessions cookie-based | Simple, adapté MPA |

## Product Scope

### MVP - Minimum Viable Product

| Fonctionnalité | Justification |
|----------------|---------------|
| Timer temps réel | Cœur du tracking |
| Saisie manuelle | Flexibilité de saisie |
| Catégories 2 niveaux | Organisation thème → activité |
| Stats jour/semaine | Voir sa répartition |
| Camembert | Visualisation rapide |
| Heatmap GitHub | Motivation + visualisation |
| Streaks | Gamification simple |
| Objectifs par catégorie | Définir ses cibles |
| Auth utilisateur | Base pour évolution |

### Growth Features (Post-MVP)

- Mode Pomodoro personnalisable
- Objectifs avancés (par jour ET par semaine)
- Comparaison période vs période
- Notifications/rappels
- Export données (CSV/JSON)

### Vision (Future)

- Synchronisation multi-appareils
- Badges et niveaux
- Insights automatiques (détection patterns)
- Mode sombre/clair
- Ouverture au public
- App mobile native (si besoin)

## User Journeys

### Parcours 1 : Premier lancement — "Alex configure son espace"

**Scène d'ouverture :**
Alex vient de créer son compte. L'écran est vide, prêt à être configuré. Il sait exactement ce qu'il veut tracker : son travail freelance, son apprentissage du chinois, et son sport.

**Action :**
1. Alex crée sa première catégorie : **Travail** 🔨 — Pas d'objectif particulier, juste tracker les heures
2. Il crée **Chinois** 📚 — Objectif : 15 min/jour OU 2h/semaine (au choix)
3. Il crée **Sport** 💪 — Objectif : 3 sessions/semaine

**Climax :**
Alex voit ses 3 catégories avec leurs emojis et couleurs. Son espace est prêt.

**Résolution :**
En moins de 2 minutes, Alex a un système personnalisé qui reflète ses priorités.

### Parcours 2 : Utilisation quotidienne — "Alex travaille sur un projet"

**Scène d'ouverture :**
Lundi matin. Alex s'assoit pour travailler sur un projet freelance. Il ouvre l'app.

**Action :**
1. Sur l'accueil, il voit ses catégories avec les stats du jour
2. Il tape sur **Travail** → crée une nouvelle carte (session)
3. Il lance le **timer** ▶️
4. Il travaille 2h sur son projet
5. Pause → il **stoppe le timer** ⏹️
6. Il note : "Intégration API client X — 80% terminé"
7. Il **enregistre** la carte

**Climax :**
La carte est sauvegardée. Alex voit son temps de travail du jour augmenter. Le heatmap montre un carré vert pour aujourd'hui.

**Résolution :**
Chaque bloc de temps est capturé avec son contexte.

### Parcours 3 : Fin de semaine — "Alex découvre ses patterns"

**Scène d'ouverture :**
Dimanche soir. Alex veut comprendre comment s'est passée sa semaine.

**Action :**
1. Il ouvre l'onglet **Stats**
2. En premier : la catégorie où il a passé le plus de temps (Travail : 18h)
3. Il voit le **heatmap** — 5 jours actifs cette semaine
4. Il consulte le **camembert** — répartition : 60% travail, 25% chinois, 15% sport
5. Il vérifie ses **streaks** — Chinois : 4 jours consécutifs ✅

**Climax :**
Alex réalise qu'il a fait du chinois 4 jours sur 7 mais seulement 2 sessions de sport.

**Résolution :**
Alex a une vision claire. L'app lui donne le miroir qu'il cherchait.

### Journey Requirements Summary

| Parcours | Fonctionnalités révélées |
|----------|-------------------------|
| Onboarding | Création catégories, emojis/couleurs, objectifs flexibles |
| Usage quotidien | Cartes/sessions, timer, notes par session, stats du jour |
| Consultation stats | Heatmap, camembert, streaks, catégorie principale |

## Technical Architecture

### Project-Type Overview

Application web progressive (PWA) de type MPA avec interactivité HTMX. Orientée mobile-first pour usage quotidien rapide.

### Architecture Decisions

| Aspect | Décision |
|--------|----------|
| Rendu | Server-side (Jinja2 templates) + HTMX pour interactivité |
| État | Côté serveur, sessions utilisateur |
| Timer | Mise à jour client-side (JavaScript minimal) avec sync serveur |
| Offline | Hors scope MVP (pas de Service Worker) |

### Browser Support

- Chrome 90+, Firefox 90+, Safari 14+, Edge 90+
- Pas de support IE11 ou navigateurs legacy

### Responsive Design

- **Mobile-first** : Design pensé pour smartphone d'abord
- **Breakpoints** : Mobile (<768px), Tablet (768-1024px), Desktop (>1024px)
- **Touch-friendly** : Boutons larges, zones de tap généreuses

## Functional Requirements

### Gestion de Compte

- **FR1:** L'utilisateur peut créer un compte avec email et mot de passe
- **FR2:** L'utilisateur peut se connecter à son compte
- **FR3:** L'utilisateur peut se déconnecter
- **FR4:** L'utilisateur peut réinitialiser son mot de passe

### Gestion des Catégories

- **FR5:** L'utilisateur peut créer une catégorie (thème principal) avec un nom
- **FR6:** L'utilisateur peut attribuer un emoji à une catégorie
- **FR7:** L'utilisateur peut attribuer une couleur à une catégorie
- **FR8:** L'utilisateur peut définir un objectif optionnel pour une catégorie (par jour ou par semaine)
- **FR9:** L'utilisateur peut modifier une catégorie existante
- **FR10:** L'utilisateur peut supprimer une catégorie
- **FR11:** L'utilisateur peut voir la liste de ses catégories
- **FR12:** L'utilisateur peut créer une sous-catégorie (activité) rattachée à une catégorie parente
- **FR13:** L'utilisateur peut attribuer un emoji à une sous-catégorie
- **FR14:** L'utilisateur peut modifier une sous-catégorie
- **FR15:** L'utilisateur peut supprimer une sous-catégorie
- **FR16:** L'utilisateur peut voir les sous-catégories d'une catégorie

### Tracking du Temps

- **FR17:** L'utilisateur peut démarrer un timer pour une catégorie ou une sous-catégorie
- **FR18:** L'utilisateur peut mettre en pause un timer en cours
- **FR19:** L'utilisateur peut reprendre un timer en pause
- **FR20:** L'utilisateur peut arrêter un timer et enregistrer la session
- **FR21:** L'utilisateur peut voir le temps écoulé du timer en temps réel
- **FR22:** L'utilisateur peut ajouter une note à une session (ce qui a été fait, ressenti)
- **FR23:** L'utilisateur peut créer une entrée de temps manuellement
- **FR24:** L'utilisateur peut modifier une entrée de temps existante
- **FR25:** L'utilisateur peut supprimer une entrée de temps

### Visualisation & Statistiques

- **FR26:** L'utilisateur peut voir ses statistiques du jour (temps par catégorie)
- **FR27:** L'utilisateur peut voir ses statistiques de la semaine
- **FR28:** L'utilisateur peut voir un graphique camembert de répartition du temps
- **FR29:** L'utilisateur peut voir un heatmap calendrier (style GitHub) de son activité
- **FR30:** L'utilisateur peut identifier la catégorie où il a passé le plus de temps
- **FR31:** L'utilisateur peut voir ses statistiques agrégées par catégorie parente
- **FR32:** L'utilisateur peut voir le détail des statistiques par sous-catégorie

### Gamification & Objectifs

- **FR33:** L'utilisateur peut voir ses streaks par catégorie (jours consécutifs)
- **FR34:** L'utilisateur peut voir sa progression vers ses objectifs définis
- **FR35:** L'utilisateur peut voir si un objectif est atteint ou non

### Navigation & Interface

- **FR36:** L'utilisateur peut accéder rapidement à ses catégories depuis l'écran d'accueil
- **FR37:** L'utilisateur peut démarrer une session en un minimum d'interactions
- **FR38:** L'utilisateur peut naviguer entre les sections (accueil, stats, catégories)

## Non-Functional Requirements

### Performance

| Critère | Exigence |
|---------|----------|
| Chargement page | < 1 seconde |
| Mise à jour timer | En temps réel (1x/sec) |
| Réponse actions utilisateur | < 200ms |
| Taille page | < 500KB |
| First Contentful Paint | < 1s |
| Time to Interactive | < 2s |

### Sécurité

| Critère | Exigence |
|---------|----------|
| Authentification | Email + mot de passe hashé (bcrypt) |
| Sessions | Tokens sécurisés, expiration |
| HTTPS | Obligatoire |
| Données utilisateur | Isolées par compte |
| Mot de passe | Minimum 8 caractères |

### Fiabilité

| Critère | Exigence |
|---------|----------|
| Données de tracking | Aucune perte |
| Timer | Précis même si page en arrière-plan |
| Disponibilité | Best effort (pas de SLA formel) |

### Accessibilité

- Navigation clavier complète
- Contraste WCAG AA (4.5:1 minimum)
- Labels sur tous les champs de formulaire
- Focus visible sur les éléments interactifs

## Risk Mitigation Strategy

| Risque | Stratégie |
|--------|-----------|
| Technique | Stack simple (Go+HTMX), pas de sur-ingénierie |
| Motivation | MVP minimal pour livrer vite, itérer ensuite |
| Scope creep | Liste MVP figée, tout le reste = post-MVP |
