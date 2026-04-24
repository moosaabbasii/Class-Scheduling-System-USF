from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import get_authorization_service, get_export_service
from app.api.serializers import schedule_export_preview_response
from app.schemas.exports import ScheduleExportPreviewResponse
from app.services.authorization import AuthorizationService
from app.services.exports import ExportService


router = APIRouter()


@router.get("/schedules/preview", response_model=ScheduleExportPreviewResponse)
def get_schedule_preview(
    schedule_id: int = Query(...),
    actor_user_id: int = Query(...),
    day: Optional[str] = Query(default=None),
    room_id: Optional[int] = Query(default=None),
    instructor_id: Optional[int] = Query(default=None),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    export_service: ExportService = Depends(get_export_service),
):
    authorization_service.ensure_can_export(actor_user_id)
    preview = export_service.build_schedule_preview(
        schedule_id,
        day=day,
        room_id=room_id,
        instructor_id=instructor_id,
    )
    return schedule_export_preview_response(preview)


@router.get("/schedules/pdf")
def export_schedule_pdf(
    schedule_id: int = Query(...),
    actor_user_id: int = Query(...),
    day: Optional[str] = Query(default=None),
    room_id: Optional[int] = Query(default=None),
    instructor_id: Optional[int] = Query(default=None),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    export_service: ExportService = Depends(get_export_service),
):
    authorization_service.ensure_can_export(actor_user_id)
    pdf, filename = export_service.export_schedule_pdf(
        schedule_id,
        day=day,
        room_id=room_id,
        instructor_id=instructor_id,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/audits/{report_id}/pdf")
def export_audit_pdf(
    report_id: int,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    export_service: ExportService = Depends(get_export_service),
):
    authorization_service.ensure_can_export(actor_user_id)
    pdf, filename = export_service.export_audit_pdf(report_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/analytics/enrollment-comparison/pdf")
def export_comparison_pdf(
    schedule_ids: List[int] = Query(...),
    actor_user_id: int = Query(...),
    subject: Optional[str] = Query(default=None),
    course_number: Optional[str] = Query(default=None),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    export_service: ExportService = Depends(get_export_service),
):
    authorization_service.ensure_can_export(actor_user_id)
    pdf, filename = export_service.export_comparison_pdf(
        schedule_ids,
        subject=subject,
        course_number=course_number,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
