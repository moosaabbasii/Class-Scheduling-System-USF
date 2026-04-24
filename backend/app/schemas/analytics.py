from typing import List, Optional

from pydantic import BaseModel, Field


class EnrollmentSemesterStatResponse(BaseModel):
    schedule_id: int
    schedule_name: str
    total_enrollment: Optional[int] = None
    section_count: int
    near_capacity: bool
    offered: bool
    instructors: List[str] = Field(default_factory=list)
    tas: List[str] = Field(default_factory=list)


class EnrollmentComparisonCourseResponse(BaseModel):
    catalog_course_id: int
    course_number: str
    course_title: str
    semesters: List[EnrollmentSemesterStatResponse] = Field(default_factory=list)
    significant_growth: bool
