from collections import defaultdict
from datetime import datetime
from itertools import combinations
from typing import Dict, List, Optional

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.entities import AuditReport, CourseSection
from app.repositories.audits import AuditRepository
from app.repositories.users import UserRepository
from app.services.schedules import ScheduleService
from app.services.sections import SectionService


class AuditService:
    VALID_MEETING_DAYS = set("MTWRFSU")
    EARLIEST_REASONABLE_START = datetime.strptime("07:00", "%H:%M")
    LATEST_REASONABLE_END = datetime.strptime("22:00", "%H:%M")
    MAX_REASONABLE_DURATION_HOURS = 6

    def __init__(
        self,
        repository: AuditRepository,
        schedule_service: ScheduleService,
        section_service: SectionService,
        user_repository: UserRepository,
    ) -> None:
        self.repository = repository
        self.schedule_service = schedule_service
        self.section_service = section_service
        self.user_repository = user_repository

    def list_reports(self, schedule_id: int = None) -> List[AuditReport]:
        if schedule_id is not None:
            self.schedule_service.get_schedule(schedule_id)
        return self.repository.list(schedule_id=schedule_id)

    def get_report(self, report_id: int) -> AuditReport:
        report = self.repository.get(report_id)
        if not report:
            raise NotFoundError(f"Audit report {report_id} was not found.")
        return report

    def generate_report(self, schedule_id: int, generated_by: int = None) -> AuditReport:
        schedule = self.schedule_service.get_schedule(schedule_id)
        if schedule.status == "released":
            raise ValidationError("Released schedules cannot be audited again.")
        if generated_by is not None:
            user = self.user_repository.get(generated_by)
            if not user:
                raise NotFoundError(f"User {generated_by} was not found.")
            if user.role != "chair":
                raise AuthorizationError(
                    "Only a committee chair can generate an audit report."
                )

        sections = self.section_service.list_sections_for_schedule(schedule_id)
        if not sections:
            raise ValidationError(
                "The selected semester has no class information to check."
            )
        issues = self._build_issues(sections)
        passed = len(issues) == 0
        report_status = "cleared" if passed else "open"
        report = self.repository.create_report(
            schedule_id=schedule_id,
            generated_by=generated_by,
            passed=passed,
            status=report_status,
        )
        self.repository.replace_issues(report.id, issues)
        return self.get_report(report.id)

    def update_report(self, report_id: int, payload: dict) -> AuditReport:
        self.get_report(report_id)
        report = self.repository.update_report(report_id, payload)
        if not report:
            raise NotFoundError(f"Audit report {report_id} was not found.")
        return report

    def update_issue(self, issue_id: int, payload: dict):
        issue = self.repository.get_issue(issue_id)
        if not issue:
            raise NotFoundError(f"Issue {issue_id} was not found.")
        updates = dict(payload)
        if updates.get("status") == "resolved" and "resolved_at" not in updates:
            updates["resolved_at"] = datetime.utcnow().isoformat(timespec="seconds")
        if updates.get("status") == "open":
            updates["resolved_at"] = None
        updated = self.repository.update_issue(issue_id, updates)
        if not updated:
            raise NotFoundError(f"Issue {issue_id} was not found.")
        return updated

    def _build_issues(self, sections: List[CourseSection]) -> List[Dict[str, object]]:
        issues: List[Dict[str, object]] = []
        issues.extend(self._duplicate_crn_issues(sections))
        issues.extend(self._invalid_crn_issues(sections))
        issues.extend(self._missing_resource_issues(sections))
        issues.extend(self._date_range_issues(sections))
        issues.extend(self._meeting_data_issues(sections))
        issues.extend(self._section_meeting_conflicts(sections))
        issues.extend(self._capacity_issues(sections))
        issues.extend(self._room_conflicts(sections))
        issues.extend(self._instructor_conflicts(sections))
        issues.extend(self._ta_overallocation_issues(sections))
        return issues

    @staticmethod
    def group_issues_by_type(report: AuditReport) -> Dict[str, List]:
        grouped = defaultdict(list)
        for issue in report.issues:
            grouped[issue.type].append(issue)
        return dict(grouped)

    @staticmethod
    def _duplicate_crn_issues(sections: List[CourseSection]) -> List[Dict[str, object]]:
        issues = []
        grouped = defaultdict(list)
        for section in sections:
            grouped[section.crn].append(section)
        for crn, siblings in grouped.items():
            if len(siblings) < 2:
                continue
            titles = ", ".join(
                section.course_title or section.course_number or f"section {section.id}"
                for section in siblings
            )
            issues.append(
                {
                    "section_id": siblings[0].id,
                    "type": "duplicate_crn",
                    "description": f"CRN {crn} is duplicated across: {titles}.",
                }
            )
        return issues

    @staticmethod
    def _invalid_crn_issues(sections: List[CourseSection]) -> List[Dict[str, object]]:
        issues = []
        for section in sections:
            if 10000 <= section.crn <= 99999:
                continue
            issues.append(
                {
                    "section_id": section.id,
                    "type": "invalid_crn",
                    "description": (
                        f"Section {section.id} uses CRN {section.crn}, which is outside the "
                        "expected 5-digit range."
                    ),
                }
            )
        return issues

    @staticmethod
    def _missing_resource_issues(sections: List[CourseSection]) -> List[Dict[str, object]]:
        issues = []
        for section in sections:
            if not section.room_id:
                issues.append(
                    {
                        "section_id": section.id,
                        "type": "missing_room",
                        "description": f"Section CRN {section.crn} has no room assigned.",
                    }
                )
            if not section.instructor_id:
                issues.append(
                    {
                        "section_id": section.id,
                        "type": "missing_instructor",
                        "description": (
                            f"Section CRN {section.crn} has no instructor assigned."
                        ),
                    }
                )
            if not section.meetings:
                issues.append(
                    {
                        "section_id": section.id,
                        "type": "missing_meetings",
                        "description": (
                            f"Section CRN {section.crn} has no meeting times configured."
                        ),
                    }
                )
        return issues

    @staticmethod
    def _date_range_issues(sections: List[CourseSection]) -> List[Dict[str, object]]:
        issues = []
        for section in sections:
            if not section.start_date or not section.end_date:
                continue
            try:
                start = datetime.strptime(section.start_date, "%Y-%m-%d")
                end = datetime.strptime(section.end_date, "%Y-%m-%d")
            except ValueError:
                issues.append(
                    {
                        "section_id": section.id,
                        "type": "invalid_date_format",
                        "description": (
                            f"Section CRN {section.crn} has dates that do not use YYYY-MM-DD."
                        ),
                    }
                )
                continue
            if end < start:
                issues.append(
                    {
                        "section_id": section.id,
                        "type": "invalid_date_range",
                        "description": (
                            f"Section CRN {section.crn} ends before it starts "
                            f"({section.start_date} to {section.end_date})."
                        ),
                    }
                )
        return issues

    def _meeting_data_issues(self, sections: List[CourseSection]) -> List[Dict[str, object]]:
        issues = []
        for section in sections:
            for index, meeting in enumerate(section.meetings, start=1):
                prefix = f"Section CRN {section.crn} meeting {index}"
                days = (meeting.days or "").strip().upper()
                invalid_days = sorted(
                    {day for day in days if day not in self.VALID_MEETING_DAYS}
                )

                if not days:
                    issues.append(
                        {
                            "section_id": section.id,
                            "type": "invalid_meeting_days",
                            "description": f"{prefix} has no meeting days listed.",
                        }
                    )
                elif invalid_days:
                    issues.append(
                        {
                            "section_id": section.id,
                            "type": "invalid_meeting_days",
                            "description": (
                                f"{prefix} uses unsupported day codes: "
                                f"{', '.join(invalid_days)}."
                            ),
                        }
                    )

                start = self._parse_time(meeting.start_time)
                end = self._parse_time(meeting.end_time)
                if start is None or end is None:
                    issues.append(
                        {
                            "section_id": section.id,
                            "type": "invalid_meeting_time_format",
                            "description": (
                                f"{prefix} has invalid time values "
                                f"({meeting.start_time} - {meeting.end_time})."
                            ),
                        }
                    )
                    continue

                if start >= end:
                    issues.append(
                        {
                            "section_id": section.id,
                            "type": "invalid_meeting_range",
                            "description": (
                                f"{prefix} starts at {meeting.start_time} but ends at "
                                f"{meeting.end_time}."
                            ),
                        }
                    )
                    continue

                duration_hours = (end - start).total_seconds() / 3600
                if duration_hours > self.MAX_REASONABLE_DURATION_HOURS:
                    issues.append(
                        {
                            "section_id": section.id,
                            "type": "unreasonable_meeting_duration",
                            "description": (
                                f"{prefix} lasts {duration_hours:g} hours, which should be "
                                "reviewed."
                            ),
                        }
                    )

                if (
                    start < self.EARLIEST_REASONABLE_START
                    or end > self.LATEST_REASONABLE_END
                ):
                    issues.append(
                        {
                            "section_id": section.id,
                            "type": "unreasonable_meeting_hours",
                            "description": (
                                f"{prefix} runs {meeting.start_time}-{meeting.end_time}, which "
                                "falls outside the normal audit window of 07:00-22:00."
                            ),
                        }
                    )
        return issues

    def _section_meeting_conflicts(
        self, sections: List[CourseSection]
    ) -> List[Dict[str, object]]:
        issues = []
        for section in sections:
            for left, right in combinations(section.meetings, 2):
                overlap = self._meetings_overlap(
                    left.days,
                    left.start_time,
                    left.end_time,
                    right.days,
                    right.start_time,
                    right.end_time,
                )
                if not overlap:
                    continue
                issue_type = (
                    "duplicate_meeting_slot"
                    if self._is_same_meeting_slot(
                        left.days,
                        left.start_time,
                        left.end_time,
                        right.days,
                        right.start_time,
                        right.end_time,
                    )
                    else "section_meeting_conflict"
                )
                issues.append(
                    {
                        "section_id": section.id,
                        "type": issue_type,
                        "description": (
                            f"Section CRN {section.crn} contains overlapping meeting entries "
                            f"({left.days} {left.start_time}-{left.end_time} and "
                            f"{right.days} {right.start_time}-{right.end_time})."
                        ),
                    }
                )
        return issues

    @staticmethod
    def _capacity_issues(sections: List[CourseSection]) -> List[Dict[str, object]]:
        issues = []
        for section in sections:
            if section.room_capacity is None:
                continue
            if section.enrollment > section.room_capacity:
                issues.append(
                    {
                        "section_id": section.id,
                        "type": "room_capacity",
                        "description": (
                            f"Section CRN {section.crn} enrollment {section.enrollment} "
                            f"exceeds room capacity {section.room_capacity}."
                        ),
                    }
                )
        return issues

    def _room_conflicts(self, sections: List[CourseSection]) -> List[Dict[str, object]]:
        room_sections = defaultdict(list)
        for section in sections:
            if section.room_id:
                room_sections[section.room_id].append(section)

        issues = []
        for siblings in room_sections.values():
            for left, right in combinations(siblings, 2):
                if self._should_ignore_shared_room_overlap(left, right):
                    continue
                if self._sections_overlap(left, right):
                    issues.append(
                        {
                            "section_id": left.id,
                            "type": "room_conflict",
                            "description": (
                                f"Sections CRN {left.crn} and CRN {right.crn} overlap "
                                f"in room {left.room_number}."
                            ),
                        }
                    )
        return issues

    @staticmethod
    def _should_ignore_shared_room_overlap(
        left: CourseSection, right: CourseSection
    ) -> bool:
        return (
            left.room_id == right.room_id
            and left.instructor_id is not None
            and left.instructor_id == right.instructor_id
        )

    def _instructor_conflicts(
        self, sections: List[CourseSection]
    ) -> List[Dict[str, object]]:
        instructor_sections = defaultdict(list)
        for section in sections:
            if section.instructor_id:
                instructor_sections[section.instructor_id].append(section)

        issues = []
        for siblings in instructor_sections.values():
            for left, right in combinations(siblings, 2):
                if self._should_ignore_cross_level_instructor_overlap(left, right):
                    continue
                if self._sections_overlap(left, right):
                    issues.append(
                        {
                            "section_id": left.id,
                            "type": "instructor_conflict",
                            "description": (
                                f"Instructor {left.instructor_name} is double-booked "
                                f"for CRN {left.crn} and CRN {right.crn}."
                            ),
                        }
                    )
        return issues

    @staticmethod
    def _should_ignore_cross_level_instructor_overlap(
        left: CourseSection, right: CourseSection
    ) -> bool:
        return {left.level, right.level} == {"UG", "GR"}

    @staticmethod
    def _ta_overallocation_issues(
        sections: List[CourseSection],
    ) -> List[Dict[str, object]]:
        totals = defaultdict(int)
        ta_names = {}
        ta_limits = {}
        for section in sections:
            for assignment in section.ta_assignments:
                totals[assignment.ta_id] += assignment.assigned_hours
                ta_names[assignment.ta_id] = assignment.ta_name or f"TA {assignment.ta_id}"
                ta_limits[assignment.ta_id] = assignment.max_hours or 0

        issues = []
        for ta_id, total in totals.items():
            if total > ta_limits[ta_id]:
                issues.append(
                    {
                        "section_id": None,
                        "type": "ta_overallocated",
                        "description": (
                            f"{ta_names[ta_id]} is assigned {total:g} hours, exceeding the "
                            f"limit of {ta_limits[ta_id]:g}."
                        ),
                    }
                )
        return issues

    def _sections_overlap(self, left: CourseSection, right: CourseSection) -> bool:
        for left_meeting in left.meetings:
            for right_meeting in right.meetings:
                if self._meetings_overlap(
                    left_meeting.days,
                    left_meeting.start_time,
                    left_meeting.end_time,
                    right_meeting.days,
                    right_meeting.start_time,
                    right_meeting.end_time,
                ):
                    return True
        return False

    def _meetings_overlap(
        self,
        left_days: str,
        left_start: str,
        left_end: str,
        right_days: str,
        right_start: str,
        right_end: str,
    ) -> bool:
        if not set((left_days or "").upper()) & set((right_days or "").upper()):
            return False
        return self._times_overlap(left_start, left_end, right_start, right_end)

    @staticmethod
    def _parse_time(value: str) -> Optional[datetime]:
        try:
            return datetime.strptime(value, "%H:%M")
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _times_overlap(
        left_start: str, left_end: str, right_start: str, right_end: str
    ) -> bool:
        ls = AuditService._parse_time(left_start)
        le = AuditService._parse_time(left_end)
        rs = AuditService._parse_time(right_start)
        re = AuditService._parse_time(right_end)
        if None in (ls, le, rs, re):
            return False
        return max(ls, rs) < min(le, re)

    @staticmethod
    def _is_same_meeting_slot(
        left_days: str,
        left_start: str,
        left_end: str,
        right_days: str,
        right_start: str,
        right_end: str,
    ) -> bool:
        return (
            (left_days or "").upper() == (right_days or "").upper()
            and left_start == right_start
            and left_end == right_end
        )
