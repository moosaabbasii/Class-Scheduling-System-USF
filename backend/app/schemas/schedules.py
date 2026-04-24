from typing import Literal, Optional

from pydantic import BaseModel


ScheduleStatus = Literal["draft", "review", "approved", "released", "archived"]


class ScheduleCreate(BaseModel):
    name: str
    status: ScheduleStatus = "draft"
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[str] = None


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    locked: Optional[bool] = None
    status: Optional[ScheduleStatus] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    locked: bool
    status: ScheduleStatus
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: str
    approved_at: Optional[str] = None
