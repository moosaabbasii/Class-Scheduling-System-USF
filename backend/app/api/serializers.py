from app.models.entities import (
    AuditReport,
    CourseSection,
    EnrollmentComparisonCourse,
    SemesterSchedule,
    User,
)
from app.schemas.analytics import (
    EnrollmentComparisonCourseResponse,
    EnrollmentSemesterStatResponse,
)
from app.schemas.audits import AuditReportResponse, IssueResponse
from app.schemas.exports import (
    ScheduleExportFiltersResponse,
    ScheduleExportPreviewResponse,
)
from app.schemas.lookups import (
    CatalogCourseResponse,
    InstructorResponse,
    RoomResponse,
    TeachingAssistantResponse,
)
from app.schemas.schedules import ScheduleResponse
from app.schemas.sections import (
    CourseSectionResponse,
    SectionMeetingResponse,
    SectionTaAssignmentResponse,
)
from app.schemas.users import UserResponse


def user_response(user: User) -> UserResponse:
    return UserResponse(**user.__dict__)


def schedule_response(schedule: SemesterSchedule) -> ScheduleResponse:
    return ScheduleResponse(**schedule.__dict__)


def catalog_course_response(item) -> CatalogCourseResponse:
    return CatalogCourseResponse(**item.__dict__)


def room_response(item) -> RoomResponse:
    return RoomResponse(**item.__dict__)


def instructor_response(item) -> InstructorResponse:
    return InstructorResponse(**item.__dict__)


def ta_response(item) -> TeachingAssistantResponse:
    return TeachingAssistantResponse(**item.__dict__)


def section_response(section: CourseSection) -> CourseSectionResponse:
    payload = dict(section.__dict__)
    payload["meetings"] = [
        SectionMeetingResponse(**meeting.__dict__) for meeting in section.meetings
    ]
    payload["ta_assignments"] = [
        SectionTaAssignmentResponse(**assignment.__dict__)
        for assignment in section.ta_assignments
    ]
    return CourseSectionResponse(**payload)


def audit_report_response(report: AuditReport) -> AuditReportResponse:
    payload = dict(report.__dict__)
    payload["issues"] = [IssueResponse(**issue.__dict__) for issue in report.issues]
    return AuditReportResponse(**payload)


def enrollment_comparison_response(
    comparison: EnrollmentComparisonCourse,
) -> EnrollmentComparisonCourseResponse:
    payload = dict(comparison.__dict__)
    payload["semesters"] = [
        EnrollmentSemesterStatResponse(**semester.__dict__)
        for semester in comparison.semesters
    ]
    return EnrollmentComparisonCourseResponse(**payload)


def schedule_export_preview_response(payload: dict) -> ScheduleExportPreviewResponse:
    return ScheduleExportPreviewResponse(
        schedule=schedule_response(payload["schedule"]),
        generated_at=payload["generated_at"],
        filters=ScheduleExportFiltersResponse(**payload["filters"]),
        sections=[section_response(section) for section in payload["sections"]],
    )
