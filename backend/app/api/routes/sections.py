from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_authorization_service, get_section_service
from app.api.serializers import section_response
from app.schemas.sections import CourseSectionResponse, CourseSectionUpdate
from app.services.authorization import AuthorizationService
from app.services.sections import SectionService


router = APIRouter()


@router.get("/{section_id}", response_model=CourseSectionResponse)
def get_section(
    section_id: int,
    service: SectionService = Depends(get_section_service),
):
    return section_response(service.get_section(section_id))


@router.patch("/{section_id}", response_model=CourseSectionResponse)
def update_section(
    section_id: int,
    payload: CourseSectionUpdate,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: SectionService = Depends(get_section_service),
):
    authorization_service.ensure_can_modify(actor_user_id)
    section = service.update_section(section_id, payload.model_dump(exclude_unset=True))
    return section_response(section)


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: int,
    actor_user_id: int = Query(...),
    authorization_service: AuthorizationService = Depends(get_authorization_service),
    service: SectionService = Depends(get_section_service),
):
    authorization_service.ensure_can_modify(actor_user_id)
    service.delete_section(section_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
