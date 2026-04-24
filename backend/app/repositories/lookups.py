from typing import List, Optional

from app.models.entities import CatalogCourse, Instructor, Room, TeachingAssistant
from app.repositories.base import BaseRepository


class CatalogCourseRepository(BaseRepository):
    def list(self) -> List[CatalogCourse]:
        rows = self._fetch_all(
            """
            SELECT id, course_number, title
            FROM catalog_courses
            ORDER BY course_number ASC, title ASC
            """
        )
        return [self._to_entity(row) for row in rows]

    def get(self, course_id: int) -> Optional[CatalogCourse]:
        row = self._fetch_one(
            """
            SELECT id, course_number, title
            FROM catalog_courses
            WHERE id = ?
            """,
            (course_id,),
        )
        return self._to_entity(row) if row else None

    def create(self, course_number: str, title: str) -> CatalogCourse:
        cursor = self._execute(
            """
            INSERT INTO catalog_courses (course_number, title)
            VALUES (?, ?)
            """,
            (course_number, title),
        )
        return self.get(cursor.lastrowid)

    def update(self, course_id: int, payload: dict) -> Optional[CatalogCourse]:
        if not payload:
            return self.get(course_id)
        clause, values = self._build_update_clause(payload)
        values.append(course_id)
        self._execute(f"UPDATE catalog_courses SET {clause} WHERE id = ?", values)
        return self.get(course_id)

    def delete(self, course_id: int) -> bool:
        return self._execute(
            "DELETE FROM catalog_courses WHERE id = ?",
            (course_id,),
        ).rowcount > 0

    @staticmethod
    def _to_entity(row) -> CatalogCourse:
        return CatalogCourse(
            id=row["id"],
            course_number=row["course_number"],
            title=row["title"],
        )


class RoomRepository(BaseRepository):
    def list(self) -> List[Room]:
        rows = self._fetch_all(
            "SELECT id, room_number, capacity FROM rooms ORDER BY room_number ASC"
        )
        return [self._to_entity(row) for row in rows]

    def get(self, room_id: int) -> Optional[Room]:
        row = self._fetch_one(
            "SELECT id, room_number, capacity FROM rooms WHERE id = ?",
            (room_id,),
        )
        return self._to_entity(row) if row else None

    def create(self, room_number: str, capacity: Optional[int]) -> Room:
        cursor = self._execute(
            """
            INSERT INTO rooms (room_number, capacity)
            VALUES (?, ?)
            """,
            (room_number, capacity),
        )
        return self.get(cursor.lastrowid)

    def update(self, room_id: int, payload: dict) -> Optional[Room]:
        if not payload:
            return self.get(room_id)
        clause, values = self._build_update_clause(payload)
        values.append(room_id)
        self._execute(f"UPDATE rooms SET {clause} WHERE id = ?", values)
        return self.get(room_id)

    def delete(self, room_id: int) -> bool:
        return self._execute("DELETE FROM rooms WHERE id = ?", (room_id,)).rowcount > 0

    @staticmethod
    def _to_entity(row) -> Room:
        return Room(
            id=row["id"],
            room_number=row["room_number"],
            capacity=row["capacity"],
        )


class InstructorRepository(BaseRepository):
    def list(self, query: Optional[str] = None, limit: int = 100) -> List[Instructor]:
        normalized_limit = max(1, min(limit, 200))
        if query:
            pattern = f"%{query.strip()}%"
            rows = self._fetch_all(
                """
                SELECT id, name, email
                FROM instructors
                WHERE name LIKE ? OR email LIKE ?
                ORDER BY name ASC
                LIMIT ?
                """,
                (pattern, pattern, normalized_limit),
            )
        else:
            rows = self._fetch_all(
                """
                SELECT id, name, email
                FROM instructors
                ORDER BY name ASC
                LIMIT ?
                """,
                (normalized_limit,),
            )
        return [self._to_entity(row) for row in rows]

    def get(self, instructor_id: int) -> Optional[Instructor]:
        row = self._fetch_one(
            "SELECT id, name, email FROM instructors WHERE id = ?",
            (instructor_id,),
        )
        return self._to_entity(row) if row else None

    def create(self, name: str, email: Optional[str]) -> Instructor:
        cursor = self._execute(
            """
            INSERT INTO instructors (name, email)
            VALUES (?, ?)
            """,
            (name, email),
        )
        return self.get(cursor.lastrowid)

    def update(self, instructor_id: int, payload: dict) -> Optional[Instructor]:
        if not payload:
            return self.get(instructor_id)
        clause, values = self._build_update_clause(payload)
        values.append(instructor_id)
        self._execute(f"UPDATE instructors SET {clause} WHERE id = ?", values)
        return self.get(instructor_id)

    def delete(self, instructor_id: int) -> bool:
        return self._execute(
            "DELETE FROM instructors WHERE id = ?",
            (instructor_id,),
        ).rowcount > 0

    @staticmethod
    def _to_entity(row) -> Instructor:
        return Instructor(id=row["id"], name=row["name"], email=row["email"])


class TeachingAssistantRepository(BaseRepository):
    def list(self) -> List[TeachingAssistant]:
        rows = self._fetch_all(
            "SELECT id, name, email, max_hours FROM tas ORDER BY name ASC"
        )
        return [self._to_entity(row) for row in rows]

    def get(self, ta_id: int) -> Optional[TeachingAssistant]:
        row = self._fetch_one(
            "SELECT id, name, email, max_hours FROM tas WHERE id = ?",
            (ta_id,),
        )
        return self._to_entity(row) if row else None

    def create(
        self, name: str, email: Optional[str], max_hours: int
    ) -> TeachingAssistant:
        cursor = self._execute(
            """
            INSERT INTO tas (name, email, max_hours)
            VALUES (?, ?, ?)
            """,
            (name, email, max_hours),
        )
        return self.get(cursor.lastrowid)

    def update(self, ta_id: int, payload: dict) -> Optional[TeachingAssistant]:
        if not payload:
            return self.get(ta_id)
        clause, values = self._build_update_clause(payload)
        values.append(ta_id)
        self._execute(f"UPDATE tas SET {clause} WHERE id = ?", values)
        return self.get(ta_id)

    def delete(self, ta_id: int) -> bool:
        return self._execute("DELETE FROM tas WHERE id = ?", (ta_id,)).rowcount > 0

    @staticmethod
    def _to_entity(row) -> TeachingAssistant:
        return TeachingAssistant(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            max_hours=row["max_hours"],
        )
