import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.models.category import Category
from app.schemas.category import SubCategoryCreate
from app.services import auth_service, category_service
from app.services.session_service import SESSION_COOKIE_NAME, get_user_id_from_cookie


def _get_user_id(authenticated_client) -> uuid.UUID:
    """Extraire l'user_id depuis le cookie de session du client authentifié."""
    cookie = authenticated_client.cookies.get(SESSION_COOKIE_NAME)
    return uuid.UUID(get_user_id_from_cookie(cookie))


# --- Schema tests ---


class TestSubCategoryCreateSchema:
    def test_valid_subcategory(self):
        schema = SubCategoryCreate(name="Réunions", emoji="📅")
        assert schema.name == "Réunions"
        assert schema.emoji == "📅"

    def test_name_stripped(self):
        schema = SubCategoryCreate(name="  Réunions  ", emoji="📅")
        assert schema.name == "Réunions"

    def test_name_empty_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            SubCategoryCreate(name="", emoji="📅")
        errors = exc_info.value.errors()
        assert any("obligatoire" in str(e["msg"]) for e in errors)

    def test_name_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            SubCategoryCreate(name="   ", emoji="📅")

    def test_name_max_100(self):
        name_100 = "a" * 100
        schema = SubCategoryCreate(name=name_100, emoji="📅")
        assert schema.name == name_100

    def test_name_over_100_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            SubCategoryCreate(name="a" * 101, emoji="📅")
        errors = exc_info.value.errors()
        assert any("100 caractères" in str(e["msg"]) for e in errors)

    def test_emoji_valid(self):
        schema = SubCategoryCreate(name="Test", emoji="🎯")
        assert schema.emoji == "🎯"

    def test_emoji_over_10_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            SubCategoryCreate(name="Test", emoji="a" * 11)
        errors = exc_info.value.errors()
        assert any("10 caractères" in str(e["msg"]) for e in errors)


# --- Service tests ---


@pytest.mark.asyncio
async def test_get_subcategories_empty(db_session):
    """get_subcategories retourne une liste vide quand il n'y a pas de sous-catégories."""
    user = await auth_service.create_user(db_session, "sub-empty@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")

    subs = await category_service.get_subcategories(db_session, parent.id, user.id)
    assert subs == []


@pytest.mark.asyncio
async def test_get_subcategories_ordered(db_session):
    """get_subcategories retourne les sous-catégories ordonnées par position."""
    user = await auth_service.create_user(db_session, "sub-order@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")

    sub1 = await category_service.create_subcategory(db_session, parent, "Réunions", "📅")
    sub2 = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    subs = await category_service.get_subcategories(db_session, parent.id, user.id)
    assert len(subs) == 2
    assert subs[0].id == sub1.id
    assert subs[1].id == sub2.id


@pytest.mark.asyncio
async def test_create_subcategory_inherits_color(db_session):
    """create_subcategory hérite de la couleur du parent."""
    user = await auth_service.create_user(db_session, "sub-color@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Sport", "💪", "#10B981")

    sub = await category_service.create_subcategory(db_session, parent, "Cardio", "🏃")

    assert sub.color == "#10B981"
    assert sub.parent_id == parent.id
    assert sub.user_id == parent.user_id
    assert sub.goal_type is None
    assert sub.goal_value is None


@pytest.mark.asyncio
async def test_create_subcategory_position_auto_increment(db_session):
    """create_subcategory auto-incrémente la position parmi les frères."""
    user = await auth_service.create_user(db_session, "sub-pos@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")

    sub1 = await category_service.create_subcategory(db_session, parent, "A", "📅")
    sub2 = await category_service.create_subcategory(db_session, parent, "B", "💻")
    sub3 = await category_service.create_subcategory(db_session, parent, "C", "📝")

    assert sub1.position == 0
    assert sub2.position == 1
    assert sub3.position == 2


@pytest.mark.asyncio
async def test_create_subcategory_position_scoped_to_parent(db_session):
    """La position est indépendante entre parents différents."""
    user = await auth_service.create_user(db_session, "sub-scope@test.com", "password123")
    parent1 = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")
    parent2 = await category_service.create_category(db_session, user.id, "Sport", "💪", "#10B981")

    sub1a = await category_service.create_subcategory(db_session, parent1, "Réunions", "📅")
    sub2a = await category_service.create_subcategory(db_session, parent2, "Cardio", "🏃")

    assert sub1a.position == 0
    assert sub2a.position == 0


@pytest.mark.asyncio
async def test_get_subcategory_by_id_found(db_session):
    """get_subcategory_by_id retourne la sous-catégorie si elle appartient à l'utilisateur."""
    user = await auth_service.create_user(db_session, "sub-getid@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    result = await category_service.get_subcategory_by_id(db_session, sub.id, user.id)
    assert result is not None
    assert result.id == sub.id
    assert result.name == "Code"


@pytest.mark.asyncio
async def test_get_subcategory_by_id_not_found(db_session):
    """get_subcategory_by_id retourne None pour un ID inexistant."""
    user = await auth_service.create_user(db_session, "sub-nf@test.com", "password123")
    result = await category_service.get_subcategory_by_id(db_session, uuid.uuid4(), user.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_subcategory_by_id_wrong_user(db_session):
    """get_subcategory_by_id retourne None pour un autre utilisateur."""
    user1 = await auth_service.create_user(db_session, "sub-own1@test.com", "password123")
    user2 = await auth_service.create_user(db_session, "sub-own2@test.com", "password123")
    parent = await category_service.create_category(db_session, user1.id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    result = await category_service.get_subcategory_by_id(db_session, sub.id, user2.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_subcategory_by_id_does_not_return_root(db_session):
    """get_subcategory_by_id ne retourne PAS une catégorie racine (parent_id IS NULL)."""
    user = await auth_service.create_user(db_session, "sub-noroot@test.com", "password123")
    root = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")

    result = await category_service.get_subcategory_by_id(db_session, root.id, user.id)
    assert result is None


@pytest.mark.asyncio
async def test_update_subcategory(db_session):
    """update_subcategory met à jour nom et emoji."""
    user = await auth_service.create_user(db_session, "sub-upd@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Ancien", "📅")

    updated = await category_service.update_subcategory(db_session, sub, "Nouveau", "🎯")

    assert updated.name == "Nouveau"
    assert updated.emoji == "🎯"
    # Color should remain unchanged
    assert updated.color == "#FF5733"


@pytest.mark.asyncio
async def test_delete_subcategory(db_session):
    """delete_subcategory supprime la sous-catégorie."""
    user = await auth_service.create_user(db_session, "sub-del@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Suppr", "🗑️")

    await category_service.delete_subcategory(db_session, sub)

    result = await db_session.execute(select(Category).where(Category.id == sub.id))
    assert result.scalar_one_or_none() is None

    # Parent should still exist
    result = await db_session.execute(select(Category).where(Category.id == parent.id))
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_delete_parent_cascades_subcategories(db_session):
    """Test de non-régression : la suppression d'une catégorie parente supprime ses sous-catégories."""
    user = await auth_service.create_user(db_session, "sub-cascade@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Parent", "📁", "#FF5733")

    sub1 = await category_service.create_subcategory(db_session, parent, "Enfant1", "📄")
    sub2 = await category_service.create_subcategory(db_session, parent, "Enfant2", "📄")

    await category_service.delete_category(db_session, parent)

    result = await db_session.execute(select(Category).where(Category.user_id == user.id))
    remaining = result.scalars().all()
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test_update_parent_color_propagates_to_subcategories(db_session):
    """Modifier la couleur d'une catégorie parente propage aux sous-catégories."""
    user = await auth_service.create_user(db_session, "sub-color-prop@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Sport", "🏃", "#FF5733")
    sub1 = await category_service.create_subcategory(db_session, parent, "Course", "🏃‍♂️")
    sub2 = await category_service.create_subcategory(db_session, parent, "Natation", "🏊")

    assert sub1.color == "#FF5733"
    assert sub2.color == "#FF5733"

    await category_service.update_category(db_session, parent, "Sport", "🏃", "#0000FF")

    await db_session.refresh(sub1)
    await db_session.refresh(sub2)
    assert sub1.color == "#0000FF"
    assert sub2.color == "#0000FF"


@pytest.mark.asyncio
async def test_get_subcategories_user_isolation(db_session):
    """get_subcategories ne retourne pas les sous-catégories d'un autre utilisateur."""
    user1 = await auth_service.create_user(db_session, "sub-iso1@test.com", "password123")
    user2 = await auth_service.create_user(db_session, "sub-iso2@test.com", "password123")
    parent1 = await category_service.create_category(db_session, user1.id, "Travail", "💼", "#FF5733")
    await category_service.create_subcategory(db_session, parent1, "Code", "💻")

    subs = await category_service.get_subcategories(db_session, parent1.id, user2.id)
    assert subs == []


# --- Router tests ---


@pytest.mark.asyncio
async def test_get_category_detail_page(authenticated_client, db_session):
    """GET /categories/{id} retourne la page de détail avec la liste des sous-catégories."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    await category_service.create_subcategory(db_session, parent, "Réunions", "📅")

    response = await authenticated_client.get(
        f"/categories/{parent.id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Travail" in response.text
    assert "Réunions" in response.text
    assert "Sous-catégories" in response.text


@pytest.mark.asyncio
async def test_get_category_detail_empty_state(authenticated_client, db_session):
    """GET /categories/{id} affiche l'empty state quand il n'y a pas de sous-catégories."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")

    response = await authenticated_client.get(
        f"/categories/{parent.id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Aucune sous-catégorie" in response.text


@pytest.mark.asyncio
async def test_get_category_detail_not_found(authenticated_client):
    """GET /categories/{id} retourne 404 pour une catégorie inexistante."""
    fake_id = uuid.uuid4()
    response = await authenticated_client.get(
        f"/categories/{fake_id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_category_detail_other_user(authenticated_client, db_session):
    """GET /categories/{id} retourne 404 pour la catégorie d'un autre utilisateur."""
    other_user = await auth_service.create_user(db_session, "other-detail@test.com", "password123")
    parent = await category_service.create_category(db_session, other_user.id, "Autre", "🎮", "#3B82F6")

    response = await authenticated_client.get(
        f"/categories/{parent.id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_create_subcategory_success(authenticated_client, db_session):
    """POST /categories/{id}/subcategories crée la sous-catégorie et redirige."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories",
        data={"name": "Réunions", "emoji": "📅"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == f"/categories/{parent.id}"

    subs = await category_service.get_subcategories(db_session, parent.id, user_id)
    assert len(subs) == 1
    assert subs[0].name == "Réunions"
    assert subs[0].color == "#FF5733"


@pytest.mark.asyncio
async def test_post_create_subcategory_validation_error(authenticated_client, db_session):
    """POST /categories/{id}/subcategories avec nom vide retourne 422."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories",
        data={"name": "", "emoji": "📅"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 422
    assert "obligatoire" in response.text


@pytest.mark.asyncio
async def test_post_create_subcategory_parent_not_found(authenticated_client):
    """POST /categories/{id}/subcategories retourne 404 pour catégorie parente inexistante."""
    fake_id = uuid.uuid4()
    response = await authenticated_client.post(
        f"/categories/{fake_id}/subcategories",
        data={"name": "Test", "emoji": "📅"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_create_subcategory_other_user(authenticated_client, db_session):
    """POST /categories/{id}/subcategories retourne 404 pour catégorie d'un autre utilisateur."""
    other_user = await auth_service.create_user(db_session, "other-sub-create@test.com", "password123")
    parent = await category_service.create_category(db_session, other_user.id, "Autre", "🎮", "#3B82F6")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories",
        data={"name": "Hack", "emoji": "💀"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_edit_subcategory_form(authenticated_client, db_session):
    """GET /categories/{id}/subcategories/{sub_id}/edit retourne le formulaire pré-rempli."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    response = await authenticated_client.get(
        f"/categories/{parent.id}/subcategories/{sub.id}/edit",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Code" in response.text
    assert "Enregistrer" in response.text


@pytest.mark.asyncio
async def test_get_edit_subcategory_form_not_found(authenticated_client, db_session):
    """GET /categories/{id}/subcategories/{sub_id}/edit retourne 404 pour sous-catégorie inexistante."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")

    response = await authenticated_client.get(
        f"/categories/{parent.id}/subcategories/{uuid.uuid4()}/edit",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_edit_subcategory_form_wrong_parent(authenticated_client, db_session):
    """GET edit retourne 404 si la sous-catégorie n'appartient pas au parent dans l'URL."""
    user_id = _get_user_id(authenticated_client)
    parent1 = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    parent2 = await category_service.create_category(db_session, user_id, "Sport", "💪", "#10B981")
    sub = await category_service.create_subcategory(db_session, parent1, "Code", "💻")

    # Try to access sub via parent2 — should fail
    response = await authenticated_client.get(
        f"/categories/{parent2.id}/subcategories/{sub.id}/edit",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_edit_subcategory_success(authenticated_client, db_session):
    """POST /categories/{id}/subcategories/{sub_id}/edit met à jour la sous-catégorie."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Ancien", "📅")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{sub.id}/edit",
        data={"name": "Nouveau", "emoji": "🎯"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == f"/categories/{parent.id}"

    await db_session.refresh(sub)
    assert sub.name == "Nouveau"
    assert sub.emoji == "🎯"


@pytest.mark.asyncio
async def test_post_edit_subcategory_validation_error(authenticated_client, db_session):
    """POST /categories/{id}/subcategories/{sub_id}/edit avec nom vide retourne 422."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{sub.id}/edit",
        data={"name": "", "emoji": "💻"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 422
    assert "obligatoire" in response.text


@pytest.mark.asyncio
async def test_post_edit_subcategory_not_found(authenticated_client, db_session):
    """POST edit retourne 404 pour sous-catégorie inexistante."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{uuid.uuid4()}/edit",
        data={"name": "Test", "emoji": "📅"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_edit_subcategory_wrong_parent(authenticated_client, db_session):
    """POST edit retourne 404 si sous-catégorie n'appartient pas au parent dans l'URL."""
    user_id = _get_user_id(authenticated_client)
    parent1 = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    parent2 = await category_service.create_category(db_session, user_id, "Sport", "💪", "#10B981")
    sub = await category_service.create_subcategory(db_session, parent1, "Code", "💻")

    response = await authenticated_client.post(
        f"/categories/{parent2.id}/subcategories/{sub.id}/edit",
        data={"name": "Hack", "emoji": "💀"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_delete_subcategory_success(authenticated_client, db_session):
    """POST /categories/{id}/subcategories/{sub_id}/delete supprime et redirige."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Suppr", "🗑️")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{sub.id}/delete",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == f"/categories/{parent.id}"

    result = await db_session.execute(select(Category).where(Category.id == sub.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_post_delete_subcategory_not_found(authenticated_client, db_session):
    """POST delete retourne 404 pour sous-catégorie inexistante."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{uuid.uuid4()}/delete",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_delete_subcategory_wrong_parent(authenticated_client, db_session):
    """POST delete retourne 404 si sous-catégorie n'appartient pas au parent dans l'URL."""
    user_id = _get_user_id(authenticated_client)
    parent1 = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    parent2 = await category_service.create_category(db_session, user_id, "Sport", "💪", "#10B981")
    sub = await category_service.create_subcategory(db_session, parent1, "Code", "💻")

    response = await authenticated_client.post(
        f"/categories/{parent2.id}/subcategories/{sub.id}/delete",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_delete_subcategory_other_user(authenticated_client, db_session):
    """POST delete retourne 404 pour la sous-catégorie d'un autre utilisateur."""
    other_user = await auth_service.create_user(db_session, "other-sub-del@test.com", "password123")
    parent = await category_service.create_category(db_session, other_user.id, "Autre", "🎮", "#3B82F6")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{sub.id}/delete",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_create_sub_subcategory_via_route(authenticated_client, db_session):
    """POST /categories/{subcategory_id}/subcategories retourne 404 — 2 niveaux max."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    response = await authenticated_client.post(
        f"/categories/{sub.id}/subcategories",
        data={"name": "Sub-sub", "emoji": "🔴"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_create_sub_subcategory_via_service(db_session):
    """create_subcategory lève ValueError si le parent est déjà une sous-catégorie."""
    from app.services import auth_service

    user = await auth_service.create_user(db_session, "subsub-svc@test.com", "password123")
    parent = await category_service.create_category(db_session, user.id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    with pytest.raises(ValueError, match="2 levels max"):
        await category_service.create_subcategory(db_session, sub, "Sub-sub", "🔴")


@pytest.mark.asyncio
async def test_empty_emoji_rejected(self=None):
    """SubCategoryCreate rejette un emoji vide."""
    with pytest.raises(ValidationError, match="obligatoire"):
        SubCategoryCreate(name="Test", emoji="")


@pytest.mark.asyncio
async def test_flash_message_on_create(authenticated_client, db_session):
    """La création d'une sous-catégorie set le flash cookie."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories",
        data={"name": "Test", "emoji": "📅"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert "flash" in response.cookies


@pytest.mark.asyncio
async def test_flash_message_on_edit(authenticated_client, db_session):
    """La modification d'une sous-catégorie set le flash cookie."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Code", "💻")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{sub.id}/edit",
        data={"name": "Nouveau", "emoji": "🎯"},
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert "flash" in response.cookies


@pytest.mark.asyncio
async def test_flash_message_on_delete(authenticated_client, db_session):
    """La suppression d'une sous-catégorie set le flash cookie."""
    user_id = _get_user_id(authenticated_client)
    parent = await category_service.create_category(db_session, user_id, "Travail", "💼", "#FF5733")
    sub = await category_service.create_subcategory(db_session, parent, "Suppr", "🗑️")

    response = await authenticated_client.post(
        f"/categories/{parent.id}/subcategories/{sub.id}/delete",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert "flash" in response.cookies
