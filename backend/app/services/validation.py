from datetime import datetime
from typing import List, Optional

from app.core.exceptions import ConflictError, ValidationError
from app.models.entities import CourseSection
from app.repositories.sections import SectionRepository


class ValidationService:
    def __init__(self, section_repository: SectionRepository) -> None:
        self.section_repository = section_repository

    def validate_section(
        self,
        schedule_id: int,
        candidate: dict,
        current_section_id: Optional[int] = None,
    ) -> None:
        self._validate_required_fields(candidate)
        self._validate_duplicate_crn(schedule_id, candidate["crn"], current_section_id)
        self._validate_conflicts(schedule_id, candidate, current_section_id)

    def validate_room_conflicts(
        self,
        schedule_id: int,
        candidate: dict,
        current_section_id: Optional[int] = None,
    ) -> None:
        siblings = self.section_repository.list_by_schedule(schedule_id)
        for sibling in siblings:
            if sibling.id == current_section_id:
                continue
            if self._should_ignore_shared_room_overlap(candidate, sibling):
                continue
            if candidate["room_id"] == sibling.room_id and self._overlaps(
                candidate["meetings"], sibling.meetings
            ):
                raise ConflictError(
                    f"Room {sibling.room_number or sibling.room_id} is already booked "
                    f"for CRN {sibling.crn} at the selected time."
                )

    def _validate_required_fields(self, candidate: dict) -> None:
        if candidate.get("crn") is None:
            raise ValidationError("CRN is required.")
        if candidate.get("room_id") is None:
            raise ValidationError("A room assignment is required.")
        if candidate.get("instructor_id") is None:
            raise ValidationError("An instructor assignment is required.")

    def _validate_duplicate_crn(
        self, schedule_id: int, crn: int, current_section_id: Optional[int]
    ) -> None:
        siblings = self.section_repository.list_by_schedule(schedule_id)
        for sibling in siblings:
            if sibling.id == current_section_id:
                continue
            if sibling.crn == crn:
                raise ConflictError(
                    f"CRN {crn} already exists in schedule {schedule_id}."
                )

    def _validate_conflicts(
        self,
        schedule_id: int,
        candidate: dict,
        current_section_id: Optional[int],
    ) -> None:
        self.validate_room_conflicts(schedule_id, candidate, current_section_id)
        siblings = self.section_repository.list_by_schedule(schedule_id)
        for sibling in siblings:
            if sibling.id == current_section_id:
                continue
            if self._should_ignore_cross_level_instructor_overlap(candidate, sibling):
                continue
            if candidate["instructor_id"] == sibling.instructor_id and self._overlaps(
                candidate["meetings"], sibling.meetings
            ):
                raise ConflictError(
                    f"Instructor {sibling.instructor_name or sibling.instructor_id} is "
                    f"already assigned to CRN {sibling.crn} at the selected time."
                )

    def _overlaps(self, candidate_meetings: List[dict], existing_meetings: List) -> bool:
        for candidate in candidate_meetings:
            for existing in existing_meetings:
                if not set(candidate["days"]) & set(existing.days):
                    continue
                if self._times_overlap(
                    candidate["start_time"],
                    candidate["end_time"],
                    existing.start_time,
                    existing.end_time,
                ):
                    return True
        return False

    @staticmethod
    def _times_overlap(
        left_start: str, left_end: str, right_start: str, right_end: str
    ) -> bool:
        ls = datetime.strptime(left_start, "%H:%M")
        le = datetime.strptime(left_end, "%H:%M")
        rs = datetime.strptime(right_start, "%H:%M")
        re = datetime.strptime(right_end, "%H:%M")
        return max(ls, rs) < min(le, re)

    @staticmethod
    def _should_ignore_cross_level_instructor_overlap(candidate: dict, sibling) -> bool:
        return {candidate.get("level"), getattr(sibling, "level", None)} == {"UG", "GR"}

    @staticmethod
    def _should_ignore_shared_room_overlap(candidate: dict, sibling) -> bool:
        return (
            candidate.get("room_id") == getattr(sibling, "room_id", None)
            and candidate.get("instructor_id") is not None
            and candidate.get("instructor_id") == getattr(sibling, "instructor_id", None)
        )
