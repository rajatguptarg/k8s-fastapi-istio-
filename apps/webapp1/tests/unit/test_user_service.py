from app.models.user import UserCreate
from app.services.user_service import UserService


def test_create_user_assigns_incrementing_ids() -> None:
    service = UserService()

    first = service.create_user(UserCreate(name="Alice"))
    second = service.create_user(UserCreate(name="Bob"))

    assert first.id == 1
    assert first.name == "Alice"
    assert second.id == 2
    assert second.name == "Bob"


def test_list_users_returns_created_users_in_order() -> None:
    service = UserService()
    service.create_user(UserCreate(name="Alice"))
    service.create_user(UserCreate(name="Bob"))

    users = service.list_users()
    assert [user.model_dump() for user in users] == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
