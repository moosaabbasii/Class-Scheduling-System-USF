from hashlib import sha256
from typing import List

from app.core.exceptions import NotFoundError
from app.models.entities import User
from app.repositories.users import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def list_users(self) -> List[User]:
        return self.repository.list()

    def get_user(self, user_id: int) -> User:
        user = self.repository.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} was not found.")
        return user

    def create_user(self, payload: dict) -> User:
        password_hash = self._hash_password(payload.get("password"))
        return self.repository.create(
            name=payload["name"],
            email=payload["email"],
            role=payload["role"],
            password_hash=password_hash,
        )

    def update_user(self, user_id: int, payload: dict) -> User:
        self.get_user(user_id)
        updates = dict(payload)
        if "password" in updates:
            updates["password_hash"] = self._hash_password(updates.pop("password"))
        user = self.repository.update(user_id, updates)
        if not user:
            raise NotFoundError(f"User {user_id} was not found.")
        return user

    def delete_user(self, user_id: int) -> None:
        self.get_user(user_id)
        if not self.repository.delete(user_id):
            raise NotFoundError(f"User {user_id} was not found.")

    @staticmethod
    def _hash_password(password: str) -> str:
        if not password:
            return ""
        return sha256(password.encode("utf-8")).hexdigest()
