from app.models.user import User


def test_user_model_has_correct_tablename():
    assert User.__tablename__ == "users"


def test_user_model_has_required_columns():
    column_names = {c.name for c in User.__table__.columns}
    expected = {"id", "email", "password_hash", "created_at", "updated_at"}
    assert expected == column_names


def test_user_id_is_uuid():
    col = User.__table__.columns["id"]
    assert col.primary_key
    assert col.default.arg.__name__ == "uuid4"


def test_user_email_is_unique_and_indexed():
    col = User.__table__.columns["email"]
    assert col.unique
    assert col.index
    assert not col.nullable


def test_user_password_hash_not_nullable():
    col = User.__table__.columns["password_hash"]
    assert not col.nullable
