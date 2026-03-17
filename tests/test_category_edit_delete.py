import uuid

import pytest
from sqlalchemy import select

from app.models.category import Category
from app.services import auth_service, category_service
from app.services.session_service import SESSION_COOKIE_NAME, get_user_id_from_cookie


def _get_user_id(authenticated_client) -> uuid.UUID:
    """Extraire l'user_id depuis le cookie de session du client authentifié."""
    cookie = authenticated_client.cookies.get(SESSION_COOKIE_NAME)
    return uuid.UUID(get_user_id_from_cookie(cookie))


# --- Service tests ---


@pytest.mark.asyncio
async def test_get_category_by_id_found(db_session):
    """get_category_by_id retourne la catégorie quand elle appartient à l'utilisateur."""
    user = await auth_service.create_user(db_session, "svc-get@test.com", "password123")
    cat = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")

    result = await category_service.get_category_by_id(db_session, cat.id, user.id)
    assert result is not None
    assert result.id == cat.id
    assert result.name == "Travail"


@pytest.mark.asyncio
async def test_get_category_by_id_not_found(db_session):
    """get_category_by_id retourne None pour un ID inexistant."""
    user = await auth_service.create_user(db_session, "svc-notfound@test.com", "password123")
    result = await category_service.get_category_by_id(db_session, uuid.uuid4(), user.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_category_by_id_wrong_user(db_session):
    """get_category_by_id retourne None quand la catégorie appartient à un autre utilisateur."""
    user1 = await auth_service.create_user(db_session, "svc-own1@test.com", "password123")
    user2 = await auth_service.create_user(db_session, "svc-own2@test.com", "password123")
    cat = await category_service.create_category(db_session, user1.id, "Travail", "💼", "#FF5733")

    result = await category_service.get_category_by_id(db_session, cat.id, user2.id)
    assert result is None


@pytest.mark.asyncio
async def test_update_category_service(db_session):
    """update_category met à jour tous les champs."""
    user = await auth_service.create_user(db_session, "svc-upd@test.com", "password123")
    cat = await category_service.create_category(db_session, user.id, "Ancien", "💼", "#FF5733")

    updated = await category_service.update_category(
        db_session, cat, "Nouveau", "🏃", "#00FF00",
        goal_type="daily", goal_value=30,
    )

    assert updated.name == "Nouveau"
    assert updated.emoji == "🏃"
    assert updated.color == "#00FF00"
    assert updated.goal_type == "daily"
    assert updated.goal_value == 30


@pytest.mark.asyncio
async def test_update_category_remove_goal(db_session):
    """update_category peut supprimer un objectif existant."""
    user = await auth_service.create_user(db_session, "svc-rmgoal@test.com", "password123")
    cat = await category_service.create_category(
        db_session, user.id, "Sport", "💪", "#FF5733",
        goal_type="daily", goal_value=30,
    )

    updated = await category_service.update_category(
        db_session, cat, "Sport", "💪", "#FF5733",
    )

    assert updated.goal_type is None
    assert updated.goal_value is None


@pytest.mark.asyncio
async def test_delete_category_service(db_session):
    """delete_category supprime la catégorie de la base."""
    user = await auth_service.create_user(db_session, "svc-del@test.com", "password123")
    cat = await category_service.create_category(db_session, user.id, "Suppr", "🗑️", "#FF5733")

    await category_service.delete_category(db_session, cat)

    result = await db_session.execute(select(Category).where(Category.id == cat.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_category_with_children(db_session):
    """delete_category supprime aussi les sous-catégories (enfants)."""
    user = await auth_service.create_user(db_session, "svc-delch@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Parent", "📁", "#FF5733")

    child = Category(
        user_id=user.id, parent_id=parent.id,
        name="Enfant", emoji="📄", color="#00FF00", position=0,
    )
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)

    await category_service.delete_category(db_session, parent)

    result = await db_session.execute(select(Category).where(Category.user_id == user.id))
    remaining = result.scalars().all()
    assert len(remaining) == 0


# --- Router tests ---


@pytest.mark.asyncio
async def test_get_edit_form(authenticated_client, db_session):
    """GET /categories/{id}/edit retourne le formulaire d'édition pré-rempli."""
    user_id = _get_user_id(authenticated_client)
    cat = await category_service.create_category(
        db_session, user_id, "Travail", "💼", "#FF5733",
    )

    response = await authenticated_client.get(
        f"/categories/{cat.id}/edit",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Travail" in response.text
    assert "Enregistrer" in response.text


@pytest.mark.asyncio
async def test_get_edit_form_not_found(authenticated_client):
    """GET /categories/{id}/edit retourne 404 pour une catégorie inexistante."""
    fake_id = uuid.uuid4()
    response = await authenticated_client.get(
        f"/categories/{fake_id}/edit",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_edit_form_other_user(authenticated_client, db_session):
    """GET /categories/{id}/edit retourne 404 pour la catégorie d'un autre utilisateur."""
    other_user = await auth_service.create_user(db_session, "other@test.com", "password123")
    cat = await category_service.create_category(
        db_session, other_user.id, "Autre", "🎮", "#3B82F6",
    )

    response = await authenticated_client.get(
        f"/categories/{cat.id}/edit",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_edit_category_success(authenticated_client, db_session):
    """POST /categories/{id}/edit met à jour la catégorie et redirige."""
    user_id = _get_user_id(authenticated_client)
    cat = await category_service.create_category(
        db_session, user_id, "Ancien", "💼", "#FF5733",
    )

    response = await authenticated_client.post(
        f"/categories/{cat.id}/edit",
        data={"name": "Nouveau", "emoji": "🏃", "color": "#00FF00"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/"

    await db_session.refresh(cat)
    assert cat.name == "Nouveau"
    assert cat.emoji == "🏃"
    assert cat.color == "#00FF00"


@pytest.mark.asyncio
async def test_post_edit_category_with_goal(authenticated_client, db_session):
    """POST /categories/{id}/edit avec objectif met à jour correctement."""
    user_id = _get_user_id(authenticated_client)
    cat = await category_service.create_category(
        db_session, user_id, "Sport", "💪", "#FF5733",
    )

    response = await authenticated_client.post(
        f"/categories/{cat.id}/edit",
        data={
            "name": "Sport", "emoji": "💪", "color": "#FF5733",
            "goal_type": "daily", "goal_value": "30",
        },
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/"

    await db_session.refresh(cat)
    assert cat.goal_type == "daily"
    assert cat.goal_value == 30


@pytest.mark.asyncio
async def test_post_edit_category_validation_error(authenticated_client, db_session):
    """POST /categories/{id}/edit avec données invalides retourne 422."""
    user_id = _get_user_id(authenticated_client)
    cat = await category_service.create_category(
        db_session, user_id, "Travail", "💼", "#FF5733",
    )

    response = await authenticated_client.post(
        f"/categories/{cat.id}/edit",
        data={"name": "", "emoji": "💼", "color": "#FF5733"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 422
    assert "obligatoire" in response.text


@pytest.mark.asyncio
async def test_post_edit_category_invalid_color_422(authenticated_client, db_session):
    """POST /categories/{id}/edit avec couleur invalide retourne 422."""
    user_id = _get_user_id(authenticated_client)
    cat = await category_service.create_category(
        db_session, user_id, "Travail", "💼", "#FF5733",
    )

    response = await authenticated_client.post(
        f"/categories/{cat.id}/edit",
        data={"name": "Travail", "emoji": "💼", "color": "bad"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 422
    assert "#RRGGBB" in response.text


@pytest.mark.asyncio
async def test_post_edit_category_not_found(authenticated_client):
    """POST /categories/{id}/edit retourne 404 pour catégorie inexistante."""
    fake_id = uuid.uuid4()
    response = await authenticated_client.post(
        f"/categories/{fake_id}/edit",
        data={"name": "Test", "emoji": "💼", "color": "#FF5733"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_edit_category_other_user(authenticated_client, db_session):
    """POST /categories/{id}/edit retourne 404 pour la catégorie d'un autre utilisateur."""
    other_user = await auth_service.create_user(db_session, "other-edit@test.com", "password123")
    cat = await category_service.create_category(
        db_session, other_user.id, "Autre", "🎮", "#3B82F6",
    )

    response = await authenticated_client.post(
        f"/categories/{cat.id}/edit",
        data={"name": "Volé", "emoji": "💼", "color": "#FF5733"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_delete_category_success(authenticated_client, db_session):
    """POST /categories/{id}/delete supprime la catégorie et redirige."""
    user_id = _get_user_id(authenticated_client)
    cat = await category_service.create_category(
        db_session, user_id, "Suppr", "🗑️", "#FF5733",
    )

    response = await authenticated_client.post(
        f"/categories/{cat.id}/delete",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/"

    result = await db_session.execute(select(Category).where(Category.id == cat.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_post_delete_category_not_found(authenticated_client):
    """POST /categories/{id}/delete retourne 404 pour catégorie inexistante."""
    fake_id = uuid.uuid4()
    response = await authenticated_client.post(
        f"/categories/{fake_id}/delete",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_delete_category_other_user(authenticated_client, db_session):
    """POST /categories/{id}/delete retourne 404 pour la catégorie d'un autre utilisateur."""
    other_user = await auth_service.create_user(db_session, "other-del@test.com", "password123")
    cat = await category_service.create_category(
        db_session, other_user.id, "Autre", "🎮", "#3B82F6",
    )

    response = await authenticated_client.post(
        f"/categories/{cat.id}/delete",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404
