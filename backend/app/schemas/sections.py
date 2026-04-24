from typing import List, Optional

from pydantic import BaseModel, Field


class SectionMeetingInput(BaseModel):
    days: str
    start_time: str
    end_time: str


class SectionMeetingResponse(SectionMeetingInput):
    id: int
    section_id: int


class SectionTaAssignmentInput(BaseModel):
    ta_id: int


class SectionTaAssignmentResponse(SectionTaAssignmentInput):
    assigned_hours: float
    ta_name: Optional[str] = None
    ta_email: Optional[str] = None
    max_hours: Optional[int] = None


class CourseSectionCreate(BaseModel):
    catalog_course_id: int
    crn: Optional[int] = None
    level: Optional[str] = None
    enrollment: int = Field(default=0, ge=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    room_id: Optional[int] = None
    instructor_id: Optional[int] = None
    meetings: List[SectionMeetingInput] = Field(default_factory=list)
    ta_assignments: List[SectionTaAssignmentInput] = Field(default_factory=list)


class CourseSectionUpdate(BaseModel):
    schedule_id: Optional[int] = None
    catalog_course_id: Optional[int] = None
    crn: Optional[int] = None
    level: Optional[str] = None
    enrollment: Optional[int] = Field(default=None, ge=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    room_id: Optional[int] = None
    instructor_id: Optional[int] = None
    meetings: Optional[List[SectionMeetingInput]] = None
    ta_assignments: Optional[List[SectionTaAssignmentInput]] = None


class CourseSectionResponse(BaseModel):
    id: int
    schedule_id: int
    catalog_course_id: int
    crn: int
    level: Optional[str] = None
    enrollment: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    room_id: Optional[int] = None
    instructor_id: Optional[int] = None
    course_number: Optional[str] = None
    course_title: Optional[str] = None
    room_number: Optional[str] = None
    room_capacity: Optional[int] = None
    instructor_name: Optional[str] = None
    instructor_email: Optional[str] = None
    meetings: List[SectionMeetingResponse] = Field(default_factory=list)
    ta_assignments: List[SectionTaAssignmentResponse] = Field(default_factory=list)
