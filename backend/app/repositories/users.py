from typing import List, Optional

from app.models.entities import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def list(self) -> List[User]:
        rows = self._fetch_all(
            "SELECT id, name, email, password_hash, role FROM users ORDER BY name ASC"
        )
        return [self._to_entity(row) for row in rows]

    def get(self, user_id: int) -> Optional[User]:
        row = self._fetch_one(
            "SELECT id, name, email, password_hash, role FROM users WHERE id = ?",
            (user_id,),
        )
        return self._to_entity(row) if row else None

    def create(
        self, name: str, email: str, role: str, password_hash: Optional[str]
    ) -> User:
        cursor = self._execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, password_hash, role),
        )
        return self.get(cursor.lastrowid)

    def update(self, user_id: int, payload: dict) -> Optional[User]:
        if not payload:
            return self.get(user_id)
        clause, values = self._build_update_clause(payload)
        values.append(user_id)
        self._execute(f"UPDATE users SET {clause} WHERE id = ?", values)
        return self.get(user_id)

    def delete(self, user_id: int) -> bool:
        cursor = self._execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _to_entity(row) -> User:
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
        )
