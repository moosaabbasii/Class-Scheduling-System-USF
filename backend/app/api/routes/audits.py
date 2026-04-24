from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_audit_service, get_authorization_service
from app.api.serializers import audit_report_response
from app.core.exceptions import ValidationError
from app.schemas.audits import (
    AuditReportResponse,
    AuditReportUpdate,
    AuditRunRequest,
    IssueResponse,
    IssueUpdate,
)
from app.services.audits import AuditService
from app.services.authorization import AuthorizationService


router = APIRouter()


@router.get("", response_model=List[AuditReportResponse])
def list_reports(
    schedule_id: Optional[int] = Query(default=None),
    service: AuditService = Depends(get_audit_service),
):
    return [audit_report_response(report) for report in service.list_reports(schedule_id)]


@router.get("/{report_id}", response_model=AuditReportResponse)
def get_report(
    report_id: int,
    service: AuditService = Depends(get_audit_service),
):
    return audit_report_response(service.get_report(report_id))


@router.post("/schedules/{schedule_id}", response_model=AuditReportResponse)
def run_schedule_audit(
    schedule_id: int,
    payload: AuditRunRequest,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: AuditService = Depends(get_audit_service),
):
    authorization_service.ensure_can_finalize(actor_user_id)
    if payload.generated_by is not None and payload.generated_by != actor_user_id:
        raise ValidationError("generated_by must match actor_user_id.")
    report = service.generate_report(schedule_id, actor_user_id)
    return audit_report_response(report)


@router.patch("/{report_id}", response_model=AuditReportResponse)
def update_report(
    report_id: int,
    payload: AuditReportUpdate,
    service: AuditService = Depends(get_audit_service),
):
    report = service.update_report(report_id, payload.model_dump(exclude_unset=True))
    return audit_report_response(report)


@router.patch("/issues/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    service: AuditService = Depends(get_audit_service),
):
    issue = service.update_issue(issue_id, payload.model_dump(exclude_unset=True))
    return IssueResponse(**issue.__dict__)
