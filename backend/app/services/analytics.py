from typing import Dict, List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.models.entities import EnrollmentComparisonCourse, EnrollmentSemesterStat
from app.repositories.schedules import ScheduleRepository
from app.repositories.sections import SectionRepository


class EnrollmentAnalyticsService:
    def __init__(
        self,
        section_repository: SectionRepository,
        schedule_repository: ScheduleRepository,
    ) -> None:
        self.section_repository = section_repository
        self.schedule_repository = schedule_repository

    def compare_enrollment(
        self,
        schedule_ids: List[int],
        subject: Optional[str] = None,
        course_number: Optional[str] = None,
    ) -> List[EnrollmentComparisonCourse]:
        unique_schedule_ids = list(dict.fromkeys(schedule_ids))
        if len(unique_schedule_ids) < 2:
            raise ValidationError("At least two semesters are required for comparison.")

        schedules = []
        for schedule_id in unique_schedule_ids:
            schedule = self.schedule_repository.get(schedule_id)
            if not schedule:
                raise NotFoundError(f"Schedule {schedule_id} was not found.")
            schedules.append(schedule)

        course_map: Dict[int, EnrollmentComparisonCourse] = {}
        schedule_stats: Dict[int, Dict[int, EnrollmentSemesterStat]] = {}

        for schedule in schedules:
            sections = self.section_repository.list_by_schedule(schedule.id)
            for section in sections:
                if not self._matches_filters(section.course_number, subject, course_number):
                    continue
                course = course_map.setdefault(
                    section.catalog_course_id,
                    EnrollmentComparisonCourse(
                        catalog_course_id=section.catalog_course_id,
                        course_number=section.course_number or "",
                        course_title=section.course_title or "",
                    ),
                )
                stats_by_schedule = schedule_stats.setdefault(section.catalog_course_id, {})
                stats = stats_by_schedule.setdefault(
                    schedule.id,
                    EnrollmentSemesterStat(
                        schedule_id=schedule.id,
                        schedule_name=schedule.name,
                        total_enrollment=0,
                        section_count=0,
                        near_capacity=False,
                        offered=True,
                    ),
                )
                stats.total_enrollment = (stats.total_enrollment or 0) + section.enrollment
                stats.section_count += 1
                stats.near_capacity = stats.near_capacity or self._is_near_capacity(section)
                self._append_unique(stats.instructors, section.instructor_name)
                for assignment in section.ta_assignments:
                    self._append_unique(stats.tas, assignment.ta_name)

        results: List[EnrollmentComparisonCourse] = []
        for course_id, course in sorted(course_map.items(), key=self._course_sort_key):
            stats_by_schedule = schedule_stats.get(course_id, {})
            course.semesters = []
            for schedule in schedules:
                stat = stats_by_schedule.get(schedule.id)
                if not stat:
                    stat = EnrollmentSemesterStat(
                        schedule_id=schedule.id,
                        schedule_name=schedule.name,
                        total_enrollment=None,
                        section_count=0,
                        near_capacity=False,
                        offered=False,
                    )
                else:
                    stat.instructors.sort()
                    stat.tas.sort()
                course.semesters.append(stat)
            course.significant_growth = self._has_significant_growth(course.semesters)
            results.append(course)
        return results

    @staticmethod
    def _matches_filters(
        course_number_value: Optional[str],
        subject: Optional[str],
        course_number: Optional[str],
    ) -> bool:
        if not course_number_value:
            return False
        normalized = course_number_value.strip().lower()
        if subject:
            if not normalized.startswith(subject.strip().lower()):
                return False
        if course_number:
            if course_number.strip().lower() not in normalized:
                return False
        return True

    @staticmethod
    def _is_near_capacity(section) -> bool:
        if not section.room_capacity:
            return False
        return section.enrollment >= max(1, int(section.room_capacity * 0.9))

    @staticmethod
    def _append_unique(values: List[str], value: Optional[str]) -> None:
        if value and value not in values:
            values.append(value)

    @staticmethod
    def _has_significant_growth(semesters: List[EnrollmentSemesterStat]) -> bool:
        offered = [item.total_enrollment for item in semesters if item.offered and item.total_enrollment is not None]
        if len(offered) < 2:
            return False
        first = offered[0]
        last = offered[-1]
        if first == 0:
            return last >= 10
        return last >= first * 1.2 and (last - first) >= 10

    @staticmethod
    def _course_sort_key(item):
        _, course = item
        return (course.course_number, course.course_title)
