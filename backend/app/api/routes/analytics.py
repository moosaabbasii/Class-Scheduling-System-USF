from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_analytics_service, get_authorization_service
from app.api.serializers import enrollment_comparison_response
from app.schemas.analytics import EnrollmentComparisonCourseResponse
from app.services.analytics import EnrollmentAnalyticsService
from app.services.authorization import AuthorizationService


router = APIRouter()


@router.get("/enrollment-comparison", response_model=List[EnrollmentComparisonCourseResponse])
def compare_enrollment(
    schedule_ids: List[int] = Query(...),
    actor_user_id: int = Query(...),
    subject: Optional[str] = Query(default=None),
    course_number: Optional[str] = Query(default=None),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    analytics_service: EnrollmentAnalyticsService = Depends(get_analytics_service),
):
    authorization_service.ensure_can_modify(actor_user_id)
    rows = analytics_service.compare_enrollment(
        schedule_ids,
        subject=subject,
        course_number=course_number,
    )
    return [enrollment_comparison_response(row) for row in rows]
