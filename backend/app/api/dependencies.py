from fastapi import Depends

from app.core.config import settings
from app.db.connection import DatabaseManager, DatabaseSession
from app.repositories.audits import AuditRepository
from app.repositories.lookups import (
    CatalogCourseRepository,
    InstructorRepository,
    RoomRepository,
    TeachingAssistantRepository,
)
from app.repositories.schedules import ScheduleRepository
from app.repositories.sections import SectionRepository
from app.repositories.users import UserRepository
from app.services.audits import AuditService
from app.services.authorization import AuthorizationService
from app.services.exports import ExportService
from app.services.lookups import (
    CatalogCourseService,
    InstructorService,
    RoomService,
    TeachingAssistantService,
)
from app.services.analytics import EnrollmentAnalyticsService
from app.services.schedules import ScheduleService
from app.services.sections import SectionService
from app.services.users import UserService
from app.services.validation import ValidationService


database_manager = DatabaseManager(settings.database_path)


def get_db_session():
    with database_manager.session() as session:
        yield session


def get_user_service(
    session: DatabaseSession = Depends(get_db_session),
) -> UserService:
    return UserService(UserRepository(session))


def get_catalog_course_service(
    session: DatabaseSession = Depends(get_db_session),
) -> CatalogCourseService:
    return CatalogCourseService(CatalogCourseRepository(session))


def get_room_service(
    session: DatabaseSession = Depends(get_db_session),
) -> RoomService:
    return RoomService(RoomRepository(session))


def get_instructor_service(
    session: DatabaseSession = Depends(get_db_session),
) -> InstructorService:
    return InstructorService(InstructorRepository(session))


def get_ta_service(
    session: DatabaseSession = Depends(get_db_session),
) -> TeachingAssistantService:
    return TeachingAssistantService(
        repository=TeachingAssistantRepository(session),
        section_repository=SectionRepository(session),
        schedule_repository=ScheduleRepository(session),
    )


def get_schedule_service(
    session: DatabaseSession = Depends(get_db_session),
) -> ScheduleService:
    return ScheduleService(
        repository=ScheduleRepository(session),
        user_repository=UserRepository(session),
    )


def get_authorization_service(
    session: DatabaseSession = Depends(get_db_session),
) -> AuthorizationService:
    return AuthorizationService(UserRepository(session))


def get_section_service(
    session: DatabaseSession = Depends(get_db_session),
) -> SectionService:
    schedule_service = ScheduleService(
        repository=ScheduleRepository(session),
        user_repository=UserRepository(session),
    )
    return SectionService(
        repository=SectionRepository(session),
        schedule_service=schedule_service,
        catalog_repository=CatalogCourseRepository(session),
        room_repository=RoomRepository(session),
        instructor_repository=InstructorRepository(session),
        ta_repository=TeachingAssistantRepository(session),
        validation_service=ValidationService(SectionRepository(session)),
    )


def get_audit_service(
    session: DatabaseSession = Depends(get_db_session),
) -> AuditService:
    schedule_service = ScheduleService(
        repository=ScheduleRepository(session),
        user_repository=UserRepository(session),
    )
    section_service = SectionService(
        repository=SectionRepository(session),
        schedule_service=schedule_service,
        catalog_repository=CatalogCourseRepository(session),
        room_repository=RoomRepository(session),
        instructor_repository=InstructorRepository(session),
        ta_repository=TeachingAssistantRepository(session),
        validation_service=ValidationService(SectionRepository(session)),
    )
    return AuditService(
        repository=AuditRepository(session),
        schedule_service=schedule_service,
        section_service=section_service,
        user_repository=UserRepository(session),
    )


def get_analytics_service(
    session: DatabaseSession = Depends(get_db_session),
) -> EnrollmentAnalyticsService:
    return EnrollmentAnalyticsService(SectionRepository(session), ScheduleRepository(session))


def get_export_service(
    session: DatabaseSession = Depends(get_db_session),
) -> ExportService:
    schedule_service = ScheduleService(
        repository=ScheduleRepository(session),
        user_repository=UserRepository(session),
    )
    section_service = SectionService(
        repository=SectionRepository(session),
        schedule_service=schedule_service,
        catalog_repository=CatalogCourseRepository(session),
        room_repository=RoomRepository(session),
        instructor_repository=InstructorRepository(session),
        ta_repository=TeachingAssistantRepository(session),
        validation_service=ValidationService(SectionRepository(session)),
    )
    audit_service = AuditService(
        repository=AuditRepository(session),
        schedule_service=schedule_service,
        section_service=section_service,
        user_repository=UserRepository(session),
    )
    analytics_service = EnrollmentAnalyticsService(
        SectionRepository(session), ScheduleRepository(session)
    )
    return ExportService(
        schedule_service=schedule_service,
        section_service=section_service,
        audit_service=audit_service,
        analytics_service=analytics_service,
    )
