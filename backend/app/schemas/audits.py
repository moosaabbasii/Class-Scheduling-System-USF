from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AuditRunRequest(BaseModel):
    generated_by: Optional[int] = None


class AuditReportUpdate(BaseModel):
    status: Optional[Literal["open", "cleared", "approved"]] = None
    passed: Optional[bool] = None


class IssueUpdate(BaseModel):
    status: Optional[Literal["open", "resolved"]] = None
    resolved_at: Optional[str] = None


class IssueResponse(BaseModel):
    id: int
    audit_report_id: int
    section_id: Optional[int] = None
    type: str
    description: str
    status: Literal["open", "resolved"]
    detected_at: str
    resolved_at: Optional[str] = None


class AuditReportResponse(BaseModel):
    id: int
    schedule_id: int
    generated_by: Optional[int] = None
    passed: bool
    status: Literal["open", "cleared", "approved"]
    created_at: str
    schedule_name: Optional[str] = None
    generated_by_name: Optional[str] = None
    issues: List[IssueResponse] = Field(default_factory=list)
