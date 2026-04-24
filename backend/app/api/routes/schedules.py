from typing import List

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import (
    get_audit_service,
    get_authorization_service,
    get_schedule_service,
    get_section_service,
)
from app.api.serializers import audit_report_response, schedule_response, section_response
from app.schemas.audits import AuditReportResponse
from app.schemas.schedules import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from app.schemas.sections import CourseSectionCreate, CourseSectionResponse
from app.services.audits import AuditService
from app.services.authorization import AuthorizationService
from app.services.schedules import ScheduleService
from app.services.sections import SectionService


router = APIRouter()


@router.get("", response_model=List[ScheduleResponse])
def list_schedules(service: ScheduleService = Depends(get_schedule_service)):
    return [schedule_response(item) for item in service.list_schedules()]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int,
    service: ScheduleService = Depends(get_schedule_service),
):
    return schedule_response(service.get_schedule(schedule_id))


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: ScheduleService = Depends(get_schedule_service),
):
    authorization_service.ensure_can_modify(actor_user_id)
    item = service.create_schedule(payload.model_dump())
    return schedule_response(item)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: ScheduleService = Depends(get_schedule_service),
):
    authorization_service.ensure_can_modify(actor_user_id)
    item = service.update_schedule(schedule_id, payload.model_dump(exclude_unset=True))
    return schedule_response(item)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: ScheduleService = Depends(get_schedule_service),
):
    authorization_service.ensure_can_modify(actor_user_id)
    service.delete_schedule(schedule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{schedule_id}/lock", response_model=ScheduleResponse)
def lock_schedule(
    schedule_id: int,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: ScheduleService = Depends(get_schedule_service),
):
    authorization_service.ensure_can_finalize(actor_user_id)
    item = service.set_lock_state(schedule_id, True)
    return schedule_response(item)


@router.post("/{schedule_id}/unlock", response_model=ScheduleResponse)
def unlock_schedule(
    schedule_id: int,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: ScheduleService = Depends(get_schedule_service),
):
    authorization_service.ensure_can_finalize(actor_user_id)
    item = service.set_lock_state(schedule_id, False)
    return schedule_response(item)


@router.post("/{schedule_id}/finalize", response_model=AuditReportResponse)
def finalize_schedule(
    schedule_id: int,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    authorization_service.ensure_can_finalize(actor_user_id)
    report = audit_service.generate_report(schedule_id, actor_user_id)
    return audit_report_response(report)


@router.get("/{schedule_id}/sections", response_model=List[CourseSectionResponse])
def list_schedule_sections(
    schedule_id: int,
    service: SectionService = Depends(get_section_service),
):
    sections = service.list_sections_for_schedule(schedule_id)
    return [section_response(section) for section in sections]


@router.post(
    "/{schedule_id}/sections",
    response_model=CourseSectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule_section(
    schedule_id: int,
    payload: CourseSectionCreate,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: SectionService = Depends(get_section_service),
):
    authorization_service.ensure_can_modify(actor_user_id)
    section = service.create_section(schedule_id, payload.model_dump())
    return section_response(section)
