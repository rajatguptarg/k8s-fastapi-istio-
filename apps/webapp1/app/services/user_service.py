from typing import List

from app.models.user import User, UserCreate


class UserService:
    def __init__(self) -> None:
        # naive in-memory storage just for demo
        self._users: list[User] = []
        self._next_id = 1

    def list_users(self) -> List[User]:
        return self._users

    def create_user(self, user_in: UserCreate) -> User:
        user = User(id=self._next_id, name=user_in.name)
        self._users.append(user)
        self._next_id += 1
        return user
