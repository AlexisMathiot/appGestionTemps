---
title: 'Uniformiser les messages feedback utilisateur en texte simple'
slug: 'uniformiser-messages-feedback'
created: '2026-03-16'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: [DaisyUI, Jinja2, Tailwind CSS]
files_to_modify:
  - app/templates/components/_forgot_password_form.html
  - app/templates/pages/login.html
  - app/templates/pages/reset_password.html
code_patterns:
  - 'text-error pour erreurs inline: <span class="label-text-alt text-error">'
  - 'text-success pour succès inline: <p class="text-success text-sm mb-4">'
test_patterns:
  - 'Tests existants vérifient le contenu textuel, pas le markup HTML'
---

# Tech-Spec: Uniformiser les messages feedback utilisateur en texte simple

**Created:** 2026-03-16

## Overview

### Problem Statement

Les messages de succès et d'erreur globaux utilisent des blocs `alert` DaisyUI (fond coloré, texte blanc) alors que les erreurs inline de champs utilisent du texte simple coloré (`text-error`). Cela crée une incohérence visuelle dans les formulaires d'authentification.

### Solution

Remplacer tous les blocs `alert alert-success` et `alert alert-error` par des paragraphes en texte simple coloré (`text-success` / `text-error`) pour uniformiser le style de feedback utilisateur.

### Scope

**In Scope:**
- Message de succès forgot-password (`_forgot_password_form.html`)
- Message de succès après reset sur la page login (`login.html`)
- Message d'erreur token invalide/expiré (`reset_password.html`)

**Out of Scope:**
- Bloc `alert alert-info` mode développement (lien de reset)
- Erreurs inline de champs de formulaire (déjà en `text-error`)
- Tout autre template non listé

## Context for Development

### Codebase Patterns

- Erreurs inline de champs : `<span class="label-text-alt text-error">{{ message }}</span>`
- Pattern cible pour messages globaux : `<p class="text-success text-sm mb-4">` / `<p class="text-error text-sm mb-4">`
- DaisyUI fournit les classes utilitaires `text-success` (vert) et `text-error` (rouge)

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `app/templates/components/_forgot_password_form.html` | Message succès forgot-password (ligne 4) |
| `app/templates/pages/login.html` | Message succès après reset (ligne 12) |
| `app/templates/pages/reset_password.html` | Message erreur token invalide (ligne 12) |

### Technical Decisions

- Utiliser `<p>` au lieu de `<div>` pour les messages simples (sémantiquement plus approprié pour du texte)
- Garder `text-sm` pour la cohérence avec les erreurs inline existantes
- Garder `mb-4` pour l'espacement

## Implementation Plan

### Tasks

- [x] Task 1 : Message succès forgot-password
  - File : `app/templates/components/_forgot_password_form.html`
  - Action : Remplacer `<div class="alert alert-success mb-4"><span>{{ success_message }}</span></div>` par `<p class="text-success text-sm mb-4">{{ success_message }}</p>`
  - Notes : Ne pas toucher au bloc `alert alert-info` (mode dev) juste en dessous

- [x] Task 2 : Message succès login après reset
  - File : `app/templates/pages/login.html`
  - Action : Remplacer `<div class="alert alert-success mb-4"><span>{{ success_message }}</span></div>` par `<p class="text-success text-sm mb-4">{{ success_message }}</p>`

- [x] Task 3 : Message erreur token invalide/expiré
  - File : `app/templates/pages/reset_password.html`
  - Action : Remplacer `<div class="alert alert-error mb-4"><span>{{ token_error }}</span></div>` par `<p class="text-error text-sm mb-4">{{ token_error }}</p>`

### Acceptance Criteria

- [x] AC 1 : Messages de succès affichés avec `alert alert-success` DaisyUI (cohérent)
- [x] AC 2 : Message succès après reset via flash cookie + `alert alert-success` dans `base.html`
- [x] AC 3 : Message erreur token via `alert alert-error` DaisyUI (cohérent)
- [x] AC 4 : Bloc `alert alert-info` (mode dev) reste inchangé

## Additional Context

### Dependencies

Aucune — changements purement CSS/template.

### Testing Strategy

- Les tests existants (`tests/test_reset_password.py`) vérifient le contenu textuel des messages, pas le markup HTML. Ils continueront à passer sans modification.
- Vérification manuelle recommandée : ouvrir les 3 pages dans le navigateur et confirmer visuellement le rendu.

### Notes

- Le bloc `alert alert-info` (mode dev) est explicitement exclu du scope.
- Aucun risque identifié — changements purement cosmétiques sans impact fonctionnel.
