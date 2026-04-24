from typing import List

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import (
    get_catalog_course_service,
    get_instructor_service,
    get_room_service,
    get_ta_service,
)
from app.api.serializers import (
    catalog_course_response,
    instructor_response,
    room_response,
    ta_response,
)
from app.schemas.lookups import (
    CatalogCourseCreate,
    CatalogCourseResponse,
    CatalogCourseUpdate,
    InstructorCreate,
    InstructorResponse,
    InstructorUpdate,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
    TeachingAssistantCreate,
    TeachingAssistantResponse,
    TeachingAssistantUpdate,
)
from app.services.lookups import (
    CatalogCourseService,
    InstructorService,
    RoomService,
    TeachingAssistantService,
)


catalog_router = APIRouter()
room_router = APIRouter()
instructor_router = APIRouter()
ta_router = APIRouter()


@catalog_router.get("", response_model=List[CatalogCourseResponse])
def list_catalog_courses(
    service: CatalogCourseService = Depends(get_catalog_course_service),
):
    return [catalog_course_response(item) for item in service.list_items()]


@catalog_router.get("/{item_id}", response_model=CatalogCourseResponse)
def get_catalog_course(
    item_id: int,
    service: CatalogCourseService = Depends(get_catalog_course_service),
):
    return catalog_course_response(service.get_item(item_id))


@catalog_router.post(
    "",
    response_model=CatalogCourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_catalog_course(
    payload: CatalogCourseCreate,
    service: CatalogCourseService = Depends(get_catalog_course_service),
):
    item = service.create_item(payload.model_dump())
    return catalog_course_response(item)


@catalog_router.patch("/{item_id}", response_model=CatalogCourseResponse)
def update_catalog_course(
    item_id: int,
    payload: CatalogCourseUpdate,
    service: CatalogCourseService = Depends(get_catalog_course_service),
):
    item = service.update_item(item_id, payload.model_dump(exclude_unset=True))
    return catalog_course_response(item)


@catalog_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalog_course(
    item_id: int,
    service: CatalogCourseService = Depends(get_catalog_course_service),
):
    service.delete_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@room_router.get("", response_model=List[RoomResponse])
def list_rooms(service: RoomService = Depends(get_room_service)):
    return [room_response(item) for item in service.list_items()]


@room_router.get("/{item_id}", response_model=RoomResponse)
def get_room(item_id: int, service: RoomService = Depends(get_room_service)):
    return room_response(service.get_item(item_id))


@room_router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, service: RoomService = Depends(get_room_service)):
    item = service.create_item(payload.model_dump())
    return room_response(item)


@room_router.patch("/{item_id}", response_model=RoomResponse)
def update_room(
    item_id: int,
    payload: RoomUpdate,
    service: RoomService = Depends(get_room_service),
):
    item = service.update_item(item_id, payload.model_dump(exclude_unset=True))
    return room_response(item)


@room_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(item_id: int, service: RoomService = Depends(get_room_service)):
    service.delete_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@instructor_router.get("", response_model=List[InstructorResponse])
def list_instructors(
    query: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=200),
    service: InstructorService = Depends(get_instructor_service),
):
    return [instructor_response(item) for item in service.list_items(query=query, limit=limit)]


@instructor_router.get("/{item_id}", response_model=InstructorResponse)
def get_instructor(
    item_id: int,
    service: InstructorService = Depends(get_instructor_service),
):
    return instructor_response(service.get_item(item_id))


@instructor_router.post(
    "", response_model=InstructorResponse, status_code=status.HTTP_201_CREATED
)
def create_instructor(
    payload: InstructorCreate,
    service: InstructorService = Depends(get_instructor_service),
):
    item = service.create_item(payload.model_dump())
    return instructor_response(item)


@instructor_router.patch("/{item_id}", response_model=InstructorResponse)
def update_instructor(
    item_id: int,
    payload: InstructorUpdate,
    service: InstructorService = Depends(get_instructor_service),
):
    item = service.update_item(item_id, payload.model_dump(exclude_unset=True))
    return instructor_response(item)


@instructor_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instructor(
    item_id: int,
    service: InstructorService = Depends(get_instructor_service),
):
    service.delete_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@ta_router.get("", response_model=List[TeachingAssistantResponse])
def list_tas(
    schedule_id: int | None = Query(default=None),
    service: TeachingAssistantService = Depends(get_ta_service),
):
    return [ta_response(item) for item in service.list_items(schedule_id=schedule_id)]


@ta_router.get("/{item_id}", response_model=TeachingAssistantResponse)
def get_ta(
    item_id: int,
    schedule_id: int | None = Query(default=None),
    service: TeachingAssistantService = Depends(get_ta_service),
):
    return ta_response(service.get_item(item_id, schedule_id=schedule_id))


@ta_router.post(
    "",
    response_model=TeachingAssistantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ta(
    payload: TeachingAssistantCreate,
    service: TeachingAssistantService = Depends(get_ta_service),
):
    item = service.create_item(payload.model_dump())
    return ta_response(item)


@ta_router.patch("/{item_id}", response_model=TeachingAssistantResponse)
def update_ta(
    item_id: int,
    payload: TeachingAssistantUpdate,
    service: TeachingAssistantService = Depends(get_ta_service),
):
    item = service.update_item(item_id, payload.model_dump(exclude_unset=True))
    return ta_response(item)


@ta_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ta(
    item_id: int,
    service: TeachingAssistantService = Depends(get_ta_service),
):
    service.delete_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
