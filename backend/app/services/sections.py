from datetime import datetime
import random
from typing import List

from app.core.exceptions import NotFoundError, ValidationError
from app.models.entities import CourseSection
from app.repositories.lookups import (
    CatalogCourseRepository,
    InstructorRepository,
    RoomRepository,
    TeachingAssistantRepository,
)
from app.repositories.sections import SectionRepository
from app.services.schedules import ScheduleService
from app.services.validation import ValidationService


class SectionService:
    def __init__(
        self,
        repository: SectionRepository,
        schedule_service: ScheduleService,
        catalog_repository: CatalogCourseRepository,
        room_repository: RoomRepository,
        instructor_repository: InstructorRepository,
        ta_repository: TeachingAssistantRepository,
        validation_service: ValidationService,
    ) -> None:
        self.repository = repository
        self.schedule_service = schedule_service
        self.catalog_repository = catalog_repository
        self.room_repository = room_repository
        self.instructor_repository = instructor_repository
        self.ta_repository = ta_repository
        self.validation_service = validation_service

    def list_sections_for_schedule(self, schedule_id: int) -> List[CourseSection]:
        self.schedule_service.get_schedule(schedule_id)
        return self.repository.list_by_schedule(schedule_id)

    def get_section(self, section_id: int) -> CourseSection:
        section = self.repository.get(section_id)
        if not section:
            raise NotFoundError(f"Section {section_id} was not found.")
        return section

    def create_section(self, schedule_id: int, payload: dict) -> CourseSection:
        self.schedule_service.ensure_schedule_is_editable(schedule_id)
        prepared = dict(payload)
        prepared["schedule_id"] = schedule_id
        if prepared.get("crn") is None:
            prepared["crn"] = self._generate_unique_crn(schedule_id)
        self._validate_payload(prepared, validation_schedule_id=schedule_id)
        return self.repository.create(prepared)

    def update_section(self, section_id: int, payload: dict) -> CourseSection:
        section = self.get_section(section_id)
        self.schedule_service.ensure_schedule_is_editable(section.schedule_id)
        prepared = dict(payload)
        if "schedule_id" in prepared and prepared["schedule_id"] != section.schedule_id:
            self.schedule_service.ensure_schedule_is_editable(prepared["schedule_id"])
        validation_schedule_id = prepared.get("schedule_id", section.schedule_id)
        merged_payload = self._merge_section_with_updates(section, prepared)
        self._validate_payload(
            prepared,
            partial=True,
            validation_schedule_id=validation_schedule_id,
            merged_payload=merged_payload,
            current_section_id=section_id,
        )
        updated = self.repository.update(section_id, prepared)
        if not updated:
            raise NotFoundError(f"Section {section_id} was not found.")
        return updated

    def delete_section(self, section_id: int) -> None:
        section = self.get_section(section_id)
        self.schedule_service.ensure_schedule_is_editable(section.schedule_id)
        if not self.repository.delete(section_id):
            raise NotFoundError(f"Section {section_id} was not found.")

    def _validate_payload(
        self,
        payload: dict,
        partial: bool = False,
        validation_schedule_id: int = None,
        merged_payload: dict = None,
        current_section_id: int = None,
    ) -> None:
        if not partial or "schedule_id" in payload:
            self.schedule_service.get_schedule(payload["schedule_id"])
        if not partial or "catalog_course_id" in payload:
            if not self.catalog_repository.get(payload["catalog_course_id"]):
                raise NotFoundError(
                    f"Catalog course {payload['catalog_course_id']} was not found."
                )
        if "room_id" in payload and payload["room_id"] is not None:
            if not self.room_repository.get(payload["room_id"]):
                raise NotFoundError(f"Room {payload['room_id']} was not found.")
        if "instructor_id" in payload and payload["instructor_id"] is not None:
            if not self.instructor_repository.get(payload["instructor_id"]):
                raise NotFoundError(
                    f"Instructor {payload['instructor_id']} was not found."
                )
        if "enrollment" in payload and payload["enrollment"] < 0:
            raise ValidationError("Enrollment cannot be negative.")
        if "meetings" in payload:
            self._validate_meetings(payload["meetings"])
        if "ta_assignments" in payload:
            self._validate_ta_assignments(payload["ta_assignments"])
        candidate = merged_payload or payload
        self._validate_date_range(candidate.get("start_date"), candidate.get("end_date"))
        target_schedule = self.schedule_service.get_schedule(
            validation_schedule_id or candidate["schedule_id"]
        )
        if target_schedule.status == "draft":
            if candidate.get("room_id") is not None and candidate.get("meetings"):
                self.validation_service.validate_room_conflicts(
                    schedule_id=target_schedule.id,
                    candidate=candidate,
                    current_section_id=current_section_id,
                )
            return
        self.validation_service.validate_section(
            schedule_id=target_schedule.id,
            candidate=candidate,
            current_section_id=current_section_id,
        )

    def _validate_meetings(self, meetings: List[dict]) -> None:
        for meeting in meetings:
            start = self._parse_time(meeting["start_time"])
            end = self._parse_time(meeting["end_time"])
            if start >= end:
                raise ValidationError(
                    "Meeting start_time must be earlier than end_time."
                )
            if not meeting["days"].strip():
                raise ValidationError("Meeting days cannot be empty.")

    def _validate_ta_assignments(self, assignments: List[dict]) -> None:
        seen_ids = set()
        for assignment in assignments:
            ta_id = assignment["ta_id"]
            if ta_id in seen_ids:
                raise ValidationError("Duplicate TA assignments are not allowed.")
            seen_ids.add(ta_id)
            if not self.ta_repository.get(ta_id):
                raise NotFoundError(f"TA {ta_id} was not found.")

    @staticmethod
    def _parse_time(value: str) -> datetime:
        try:
            return datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValidationError("Times must use HH:MM format.") from exc

    @staticmethod
    def _validate_date_range(start_date: str, end_date: str) -> None:
        if not start_date or not end_date:
            return
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValidationError("Dates must use YYYY-MM-DD format.") from exc
        if end < start:
            raise ValidationError("end_date cannot be earlier than start_date.")

    def _generate_unique_crn(self, schedule_id: int) -> int:
        existing_crns = {
            section.crn for section in self.repository.list_by_schedule(schedule_id)
        }

        for _ in range(1000):
            candidate = random.randint(10000, 99999)
            if candidate not in existing_crns:
                return candidate

        raise ValidationError("Unable to generate a unique CRN for this schedule.")

    @staticmethod
    def _merge_section_with_updates(section: CourseSection, updates: dict) -> dict:
        meetings = updates.get(
            "meetings",
            [
                {
                    "days": meeting.days,
                    "start_time": meeting.start_time,
                    "end_time": meeting.end_time,
                }
                for meeting in section.meetings
            ],
        )
        ta_assignments = updates.get(
            "ta_assignments",
            [
                {
                    "ta_id": assignment.ta_id,
                }
                for assignment in section.ta_assignments
            ],
        )
        return {
            "schedule_id": updates.get("schedule_id", section.schedule_id),
            "catalog_course_id": updates.get(
                "catalog_course_id", section.catalog_course_id
            ),
            "crn": updates.get("crn", section.crn),
            "level": updates.get("level", section.level),
            "enrollment": updates.get("enrollment", section.enrollment),
            "start_date": updates.get("start_date", section.start_date),
            "end_date": updates.get("end_date", section.end_date),
            "room_id": updates.get("room_id", section.room_id),
            "instructor_id": updates.get("instructor_id", section.instructor_id),
            "meetings": meetings,
            "ta_assignments": ta_assignments,
        }
