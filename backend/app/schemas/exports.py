from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.schedules import ScheduleResponse
from app.schemas.sections import CourseSectionResponse


class ScheduleExportFiltersResponse(BaseModel):
    day: Optional[str] = None
    room_id: Optional[int] = None
    instructor_id: Optional[int] = None


class ScheduleExportPreviewResponse(BaseModel):
    schedule: ScheduleResponse
    generated_at: str
    filters: ScheduleExportFiltersResponse
    sections: List[CourseSectionResponse] = Field(default_factory=list)
