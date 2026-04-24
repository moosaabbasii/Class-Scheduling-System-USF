from datetime import datetime
from typing import List

from app.core.exceptions import LockedScheduleError, NotFoundError
from app.models.entities import SemesterSchedule
from app.repositories.schedules import ScheduleRepository
from app.repositories.users import UserRepository


class ScheduleService:
    def __init__(
        self, repository: ScheduleRepository, user_repository: UserRepository
    ) -> None:
        self.repository = repository
        self.user_repository = user_repository

    def list_schedules(self) -> List[SemesterSchedule]:
        return self.repository.list()

    def get_schedule(self, schedule_id: int) -> SemesterSchedule:
        schedule = self.repository.get(schedule_id)
        if not schedule:
            raise NotFoundError(f"Schedule {schedule_id} was not found.")
        return schedule

    def create_schedule(self, payload: dict) -> SemesterSchedule:
        self._validate_user(payload.get("created_by"), "created_by")
        self._validate_user(payload.get("approved_by"), "approved_by")
        approved_at = payload.get("approved_at")
        if payload["status"] in ("approved", "released") and not approved_at:
            approved_at = datetime.utcnow().isoformat(timespec="seconds")
        return self.repository.create(
            name=payload["name"],
            status=payload["status"],
            created_by=payload.get("created_by"),
            approved_by=payload.get("approved_by"),
            approved_at=approved_at,
        )

    def update_schedule(self, schedule_id: int, payload: dict) -> SemesterSchedule:
        self.get_schedule(schedule_id)
        self._validate_user(payload.get("created_by"), "created_by")
        self._validate_user(payload.get("approved_by"), "approved_by")
        updates = dict(payload)
        if updates.get("status") in ("approved", "released") and "approved_at" not in updates:
            updates["approved_at"] = datetime.utcnow().isoformat(timespec="seconds")
        schedule = self.repository.update(schedule_id, updates)
        if not schedule:
            raise NotFoundError(f"Schedule {schedule_id} was not found.")
        return schedule

    def delete_schedule(self, schedule_id: int) -> None:
        self.get_schedule(schedule_id)
        if not self.repository.delete(schedule_id):
            raise NotFoundError(f"Schedule {schedule_id} was not found.")

    def set_lock_state(self, schedule_id: int, locked: bool) -> SemesterSchedule:
        schedule = self.get_schedule(schedule_id)
        if schedule.locked == locked:
            return schedule
        updated = self.repository.update(schedule_id, {"locked": int(locked)})
        if not updated:
            raise NotFoundError(f"Schedule {schedule_id} was not found.")
        return updated

    def ensure_schedule_is_editable(self, schedule_id: int) -> SemesterSchedule:
        schedule = self.get_schedule(schedule_id)
        if schedule.locked:
            raise LockedScheduleError(
                f"Schedule {schedule_id} is locked and cannot be modified."
            )
        return schedule

    def _validate_user(self, user_id: int, field_name: str) -> None:
        if user_id is None:
            return
        if not self.user_repository.get(user_id):
            raise NotFoundError(f"User {user_id} for {field_name} was not found.")
