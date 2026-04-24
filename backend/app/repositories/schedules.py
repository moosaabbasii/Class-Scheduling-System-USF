from typing import List, Optional

from app.models.entities import SemesterSchedule
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository):
    def list(self) -> List[SemesterSchedule]:
        rows = self._fetch_all(
            """
            SELECT id, name, locked, status, created_by, approved_by, created_at, approved_at
            FROM semester_schedules
            ORDER BY created_at DESC, id DESC
            """
        )
        return [self._to_entity(row) for row in rows]

    def get(self, schedule_id: int) -> Optional[SemesterSchedule]:
        row = self._fetch_one(
            """
            SELECT id, name, locked, status, created_by, approved_by, created_at, approved_at
            FROM semester_schedules
            WHERE id = ?
            """,
            (schedule_id,),
        )
        return self._to_entity(row) if row else None

    def create(
        self,
        name: str,
        status: str,
        created_by: Optional[int],
        approved_by: Optional[int],
        approved_at: Optional[str],
    ) -> SemesterSchedule:
        cursor = self._execute(
            """
            INSERT INTO semester_schedules (name, status, created_by, approved_by, approved_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, status, created_by, approved_by, approved_at),
        )
        return self.get(cursor.lastrowid)

    def update(self, schedule_id: int, payload: dict) -> Optional[SemesterSchedule]:
        if not payload:
            return self.get(schedule_id)
        clause, values = self._build_update_clause(payload)
        values.append(schedule_id)
        self._execute(f"UPDATE semester_schedules SET {clause} WHERE id = ?", values)
        return self.get(schedule_id)

    def delete(self, schedule_id: int) -> bool:
        return self._execute(
            "DELETE FROM semester_schedules WHERE id = ?",
            (schedule_id,),
        ).rowcount > 0

    @staticmethod
    def _to_entity(row) -> SemesterSchedule:
        return SemesterSchedule(
            id=row["id"],
            name=row["name"],
            locked=bool(row["locked"]),
            status=row["status"],
            created_by=row["created_by"],
            approved_by=row["approved_by"],
            created_at=row["created_at"],
            approved_at=row["approved_at"],
        )
