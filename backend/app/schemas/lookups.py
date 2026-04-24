from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CatalogCourseCreate(BaseModel):
    course_number: str
    title: str


class CatalogCourseUpdate(BaseModel):
    course_number: Optional[str] = None
    title: Optional[str] = None


class CatalogCourseResponse(BaseModel):
    id: int
    course_number: str
    title: str


class RoomCreate(BaseModel):
    room_number: str
    capacity: Optional[int] = Field(default=None, ge=0)


class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    capacity: Optional[int] = Field(default=None, ge=0)


class RoomResponse(BaseModel):
    id: int
    room_number: str
    capacity: Optional[int] = None


class InstructorCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None


class InstructorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class InstructorResponse(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None


class TeachingAssistantCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    max_hours: int = Field(default=0, ge=0)


class TeachingAssistantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    max_hours: Optional[int] = Field(default=None, ge=0)


class TeachingAssistantResponse(BaseModel):
    id: int
    name: str
    email: Optional[EmailStr] = None
    max_hours: int
    hours: float
