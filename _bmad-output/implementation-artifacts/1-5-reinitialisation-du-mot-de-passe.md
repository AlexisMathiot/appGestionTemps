# Story 1.5 : Réinitialisation du mot de passe

Status: done

## Story

As a utilisateur ayant oublié son mot de passe,
I want pouvoir le réinitialiser via mon email,
So that je puisse retrouver l'accès à mon compte.

## Acceptance Criteria

1. La page "Mot de passe oublié" est accessible à `/auth/forgot-password` avec un champ email
2. Un token de réinitialisation sécurisé est généré via itsdangerous (signé, avec expiration)
3. En mode dev, le lien de réinitialisation est affiché directement sur la page (pas d'envoi d'email)
4. La page de reset `/auth/reset-password/{token}` affiche un formulaire (nouveau mot de passe + confirmation)
5. Le mot de passe est mis à jour en base (bcrypt) quand le token est valide et le nouveau mot de passe conforme
6. L'utilisateur est redirigé vers `/auth/login` avec un message de succès après reset
7. Un token expiré ou invalide affiche un message d'erreur avec un lien pour recommencer
8. Le nouveau mot de passe doit faire minimum 8 caractères
9. Les formulaires utilisent HTMX pour la soumission avec erreurs inline

## Tasks / Subtasks

- [x] Task 1 : Token de réinitialisation (AC: #2)
  - [x] Ajouter `create_reset_token(email)` dans `app/services/session_service.py` — salt "password-reset", max_age 1h
  - [x] Ajouter `verify_reset_token(token)` → retourne l'email ou None si expiré/invalide

- [x] Task 2 : Service update password (AC: #5)
  - [x] Ajouter `update_password(db, user, new_password)` dans `app/services/auth_service.py`

- [x] Task 3 : Schema Pydantic pour reset (AC: #8)
  - [x] Ajouter `ForgotPasswordForm` dans `app/schemas/auth.py`
  - [x] Ajouter `ResetPasswordForm` avec validation password min 8 + confirmation match

- [x] Task 4 : Routes forgot/reset password (AC: #1, #3, #4, #5, #6, #7)
  - [x] `GET /auth/forgot-password` → formulaire email
  - [x] `POST /auth/forgot-password` → génère token, affiche lien en mode dev, même message si email inconnu
  - [x] `GET /auth/reset-password/{token}` → vérifie token, affiche formulaire ou erreur
  - [x] `POST /auth/reset-password/{token}` → valide, update DB, redirect login

- [x] Task 5 : Templates (AC: #1, #3, #9)
  - [x] Créer forgot_password.html + _forgot_password_form.html
  - [x] Créer reset_password.html + _reset_password_form.html
  - [x] Lien reset affiché en alert info (mode dev)
  - [x] Lien "Mot de passe oublié ?" ajouté sur le formulaire login

- [x] Task 6 : Tests (AC: tous)
  - [x] 11 tests reset password + 1 test lien forgot sur login page
  - [x] Total 59/59 tests passent, lint propre

## Dev Notes

### Architecture & Patterns obligatoires

**Token de reset (itsdangerous) — réutiliser le même serializer que les sessions :**
```python
# app/services/session_service.py
RESET_TOKEN_MAX_AGE = 3600  # 1 heure

def create_reset_token(email: str) -> str:
    return _serializer.dumps(email, salt="password-reset")

def verify_reset_token(token: str) -> str | None:
    try:
        return _serializer.loads(token, salt="password-reset", max_age=RESET_TOKEN_MAX_AGE)
    except Exception:
        return None
```

**Update password pattern :**
```python
# app/services/auth_service.py
async def update_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    await db.commit()
```

**Sécurité — même message pour email connu et inconnu :**
Toujours afficher "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé." que l'email existe ou non.

**Mode dev — afficher le lien au lieu d'envoyer un email :**
```python
if settings.DEBUG:
    reset_url = f"{request.base_url}auth/reset-password/{token}"
    # Afficher dans une alert info sur la page
```

**Helper `_redirect` déjà disponible** dans `app/routers/auth.py` — réutiliser pour les redirections HTMX/normal.

**Pattern validation — réutiliser le pattern de register :**
`ResetPasswordForm` peut reprendre le même pattern que `RegisterForm` (password min 8 + confirmation match) sans le champ email.

### Fichiers existants à modifier

- `app/services/session_service.py` — ajouter `create_reset_token`, `verify_reset_token`
- `app/services/auth_service.py` — ajouter `update_password`
- `app/schemas/auth.py` — ajouter `ForgotPasswordForm`, `ResetPasswordForm`
- `app/routers/auth.py` — ajouter 4 routes forgot/reset password
- `app/templates/pages/login.html` ou `_login_form.html` — ajouter lien "Mot de passe oublié ?"

### Previous Story Intelligence

- **Story 1.4 :** `_redirect(request, url)` helper gère HTMX vs normal redirect. `_set_session_cookie` et `_delete_session_cookie` helpers. Pattern `is_htmx` pour choisir template fragment vs page complète. `authenticate_user` avec timing-safe dummy hash. Exception handler `AuthenticationRequired` dans main.py.
- **Story 1.3 :** bcrypt direct (pas passlib). Pydantic `RegisterForm` avec `field_validator` + `model_validator`. `ValidationError` parsing avec `error["loc"]`.
- **conftest.py :** NullPool engine, `db_session` crée/drop tables, `authenticated_client` fixture avec user pré-créé.
- **session_service.py :** `_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)` — le même serializer peut être réutilisé avec un salt différent pour les tokens de reset.

### Anti-patterns à éviter

- NE PAS révéler si un email existe via le message de forgot-password
- NE PAS implémenter l'envoi d'email réel — en mode dev, afficher le lien sur la page
- NE PAS réutiliser le salt "session" pour les tokens de reset — utiliser un salt dédié "password-reset"
- NE PAS permettre de réutiliser un token après reset — le token expire naturellement (1h)
- NE PAS oublier de valider le token AVANT d'afficher le formulaire de reset
- NE PAS connecter automatiquement après reset — rediriger vers login

### References

- [Source: planning-artifacts/prd.md#Functional Requirements] — FR4: réinitialisation mot de passe
- [Source: planning-artifacts/architecture.md#Authentication & Security] — itsdangerous, bcrypt
- [Source: planning-artifacts/prd.md#Non-Functional Requirements] — NFR11: min 8 caractères

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (1M context)

### Debug Log References

- Réutilisation du même `_serializer` (itsdangerous) avec un salt "password-reset" différent de "session"
- Token signé contient l'email (pas le user_id) pour lookup DB au moment du reset

### Completion Notes List

- Token reset via itsdangerous avec salt dédié, expiration 1h
- update_password dans auth_service (bcrypt hash + commit)
- Schemas ForgotPasswordForm et ResetPasswordForm ajoutés
- 4 routes : GET/POST forgot-password + GET/POST reset-password/{token}
- Sécurité : même message que l'email existe ou non sur forgot-password
- Mode dev : lien de reset affiché dans une alert info
- Token invalide/expiré : message d'erreur + lien pour recommencer
- Lien "Mot de passe oublié ?" ajouté sur le formulaire login
- 11 nouveaux tests (total 59/59 passent), lint propre

### File List

- app/services/session_service.py (modifié — ajout create_reset_token, verify_reset_token)
- app/services/auth_service.py (modifié — ajout update_password)
- app/schemas/auth.py (modifié — ajout ForgotPasswordForm, ResetPasswordForm)
- app/routers/auth.py (modifié — ajout 4 routes forgot/reset password)
- app/templates/pages/forgot_password.html (nouveau)
- app/templates/components/_forgot_password_form.html (nouveau)
- app/templates/pages/reset_password.html (nouveau)
- app/templates/components/_reset_password_form.html (nouveau)
- app/templates/components/_login_form.html (modifié — ajout lien "Mot de passe oublié ?")
- tests/test_reset_password.py (nouveau)
