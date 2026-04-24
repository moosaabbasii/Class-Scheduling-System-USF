from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.entities import User
from app.repositories.users import UserRepository


class AuthorizationService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def ensure_authenticated(self, user_id: int) -> User:
        user = self.user_repository.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} was not found.")
        return user

    def ensure_can_modify(self, user_id: int) -> User:
        user = self.ensure_authenticated(user_id)
        if user.role not in {"member", "chair"}:
            raise AuthorizationError("Only committee members can modify schedules.")
        return user

    def ensure_can_finalize(self, user_id: int) -> User:
        user = self.ensure_authenticated(user_id)
        if user.role != "chair":
            raise AuthorizationError("Only a committee chair can generate final audit reports.")
        return user

    def ensure_can_export(self, user_id: int) -> User:
        user = self.ensure_authenticated(user_id)
        if user.role not in {"member", "chair"}:
            raise AuthorizationError("Only committee members can export schedule data.")
        return user
