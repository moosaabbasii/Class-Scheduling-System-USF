from typing import List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.models.entities import CatalogCourse, Instructor, Room, TeachingAssistant
from app.repositories.lookups import (
    CatalogCourseRepository,
    InstructorRepository,
    RoomRepository,
    TeachingAssistantRepository,
)
from app.repositories.schedules import ScheduleRepository
from app.repositories.sections import SectionRepository


class CatalogCourseService:
    def __init__(self, repository: CatalogCourseRepository) -> None:
        self.repository = repository

    def list_items(self) -> List[CatalogCourse]:
        return self.repository.list()

    def get_item(self, item_id: int) -> CatalogCourse:
        item = self.repository.get(item_id)
        if not item:
            raise NotFoundError(f"Catalog course {item_id} was not found.")
        return item

    def create_item(self, payload: dict) -> CatalogCourse:
        return self.repository.create(
            course_number=payload["course_number"],
            title=payload["title"],
        )

    def update_item(self, item_id: int, payload: dict) -> CatalogCourse:
        self.get_item(item_id)
        item = self.repository.update(item_id, payload)
        if not item:
            raise NotFoundError(f"Catalog course {item_id} was not found.")
        return item

    def delete_item(self, item_id: int) -> None:
        self.get_item(item_id)
        if not self.repository.delete(item_id):
            raise NotFoundError(f"Catalog course {item_id} was not found.")


class RoomService:
    def __init__(self, repository: RoomRepository) -> None:
        self.repository = repository

    def list_items(self) -> List[Room]:
        return self.repository.list()

    def get_item(self, item_id: int) -> Room:
        item = self.repository.get(item_id)
        if not item:
            raise NotFoundError(f"Room {item_id} was not found.")
        return item

    def create_item(self, payload: dict) -> Room:
        self._validate_capacity(payload.get("capacity"))
        return self.repository.create(
            room_number=payload["room_number"],
            capacity=payload.get("capacity"),
        )

    def update_item(self, item_id: int, payload: dict) -> Room:
        self.get_item(item_id)
        self._validate_capacity(payload.get("capacity"))
        item = self.repository.update(item_id, payload)
        if not item:
            raise NotFoundError(f"Room {item_id} was not found.")
        return item

    def delete_item(self, item_id: int) -> None:
        self.get_item(item_id)
        if not self.repository.delete(item_id):
            raise NotFoundError(f"Room {item_id} was not found.")

    @staticmethod
    def _validate_capacity(capacity: int) -> None:
        if capacity is not None and capacity < 0:
            raise ValidationError("Room capacity cannot be negative.")


class InstructorService:
    def __init__(self, repository: InstructorRepository) -> None:
        self.repository = repository

    def list_items(self, query: str = "", limit: int = 100) -> List[Instructor]:
        return self.repository.list(query=query, limit=limit)

    def get_item(self, item_id: int) -> Instructor:
        item = self.repository.get(item_id)
        if not item:
            raise NotFoundError(f"Instructor {item_id} was not found.")
        return item

    def create_item(self, payload: dict) -> Instructor:
        return self.repository.create(name=payload["name"], email=payload.get("email"))

    def update_item(self, item_id: int, payload: dict) -> Instructor:
        self.get_item(item_id)
        item = self.repository.update(item_id, payload)
        if not item:
            raise NotFoundError(f"Instructor {item_id} was not found.")
        return item

    def delete_item(self, item_id: int) -> None:
        self.get_item(item_id)
        if not self.repository.delete(item_id):
            raise NotFoundError(f"Instructor {item_id} was not found.")


class TeachingAssistantService:
    def __init__(
        self,
        repository: TeachingAssistantRepository,
        section_repository: SectionRepository,
        schedule_repository: ScheduleRepository,
    ) -> None:
        self.repository = repository
        self.section_repository = section_repository
        self.schedule_repository = schedule_repository

    def list_items(self, schedule_id: Optional[int] = None) -> List[TeachingAssistant]:
        items = self.repository.list()
        return self._attach_hours(items, schedule_id=schedule_id)

    def get_item(
        self, item_id: int, schedule_id: Optional[int] = None
    ) -> TeachingAssistant:
        item = self.repository.get(item_id)
        if not item:
            raise NotFoundError(f"TA {item_id} was not found.")
        return self._attach_hours([item], schedule_id=schedule_id)[0]

    def create_item(self, payload: dict) -> TeachingAssistant:
        self._validate_max_hours(payload["max_hours"])
        return self.repository.create(
            name=payload["name"],
            email=payload.get("email"),
            max_hours=payload["max_hours"],
        )

    def update_item(self, item_id: int, payload: dict) -> TeachingAssistant:
        self.get_item(item_id)
        if "max_hours" in payload:
            self._validate_max_hours(payload["max_hours"])
        item = self.repository.update(item_id, payload)
        if not item:
            raise NotFoundError(f"TA {item_id} was not found.")
        return item

    def delete_item(self, item_id: int) -> None:
        self.get_item(item_id)
        if not self.repository.delete(item_id):
            raise NotFoundError(f"TA {item_id} was not found.")

    @staticmethod
    def _validate_max_hours(max_hours: int) -> None:
        if max_hours < 0:
            raise ValidationError("TA max_hours cannot be negative.")

    def _attach_hours(
        self, items: List[TeachingAssistant], schedule_id: Optional[int]
    ) -> List[TeachingAssistant]:
        if schedule_id is None:
            for item in items:
                item.hours = 0.0
            return items

        if not self.schedule_repository.get(schedule_id):
            raise NotFoundError(f"Schedule {schedule_id} was not found.")

        hours_by_ta = {}
        for section in self.section_repository.list_by_schedule(schedule_id):
            for assignment in section.ta_assignments:
                hours_by_ta[assignment.ta_id] = (
                    hours_by_ta.get(assignment.ta_id, 0.0) + assignment.assigned_hours
                )

        for item in items:
            item.hours = round(hours_by_ta.get(item.id, 0.0), 2)
        return items
