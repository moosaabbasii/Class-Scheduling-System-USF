from typing import List

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_user_service
from app.api.serializers import user_response
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services.users import UserService


router = APIRouter()


@router.get("", response_model=List[UserResponse])
def list_users(service: UserService = Depends(get_user_service)):
    return [user_response(user) for user in service.list_users()]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return user_response(service.get_user(user_id))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)):
    user = service.create_user(payload.model_dump())
    return user_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    user = service.update_user(user_id, payload.model_dump(exclude_unset=True))
    return user_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
