from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class User:
    id: int
    name: str
    email: str
    role: str
    password_hash: Optional[str] = None


@dataclass
class CatalogCourse:
    id: int
    course_number: str
    title: str


@dataclass
class Room:
    id: int
    room_number: str
    capacity: Optional[int] = None


@dataclass
class Instructor:
    id: int
    name: str
    email: Optional[str] = None


@dataclass
class TeachingAssistant:
    id: int
    name: str
    email: Optional[str] = None
    max_hours: int = 0
    hours: float = 0.0


@dataclass
class SemesterSchedule:
    id: int
    name: str
    locked: bool
    status: str
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: str = ""
    approved_at: Optional[str] = None


@dataclass
class SectionMeeting:
    id: int
    section_id: int
    days: str
    start_time: str
    end_time: str


@dataclass
class SectionTaAssignment:
    ta_id: int
    assigned_hours: float
    ta_name: Optional[str] = None
    ta_email: Optional[str] = None
    max_hours: Optional[int] = None


@dataclass
class CourseSection:
    id: int
    schedule_id: int
    catalog_course_id: int
    crn: int
    level: Optional[str]
    enrollment: int
    start_date: Optional[str]
    end_date: Optional[str]
    room_id: Optional[int]
    instructor_id: Optional[int]
    course_number: Optional[str] = None
    course_title: Optional[str] = None
    room_number: Optional[str] = None
    room_capacity: Optional[int] = None
    instructor_name: Optional[str] = None
    instructor_email: Optional[str] = None
    meetings: List[SectionMeeting] = field(default_factory=list)
    ta_assignments: List[SectionTaAssignment] = field(default_factory=list)


@dataclass
class Issue:
    id: int
    audit_report_id: int
    section_id: Optional[int]
    type: str
    description: str
    status: str
    detected_at: str
    resolved_at: Optional[str] = None


@dataclass
class AuditReport:
    id: int
    schedule_id: int
    generated_by: Optional[int]
    passed: bool
    status: str
    created_at: str
    schedule_name: Optional[str] = None
    generated_by_name: Optional[str] = None
    issues: List[Issue] = field(default_factory=list)


@dataclass
class EnrollmentSemesterStat:
    schedule_id: int
    schedule_name: str
    total_enrollment: Optional[int]
    section_count: int
    near_capacity: bool
    offered: bool
    instructors: List[str] = field(default_factory=list)
    tas: List[str] = field(default_factory=list)


@dataclass
class EnrollmentComparisonCourse:
    catalog_course_id: int
    course_number: str
    course_title: str
    semesters: List[EnrollmentSemesterStat] = field(default_factory=list)
    significant_growth: bool = False
