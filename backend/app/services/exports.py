from datetime import datetime
from typing import Dict, List, Optional

from app.services.analytics import EnrollmentAnalyticsService
from app.services.audits import AuditService
from app.services.schedules import ScheduleService
from app.services.sections import SectionService


class ExportService:
    def __init__(
        self,
        schedule_service: ScheduleService,
        section_service: SectionService,
        audit_service: AuditService,
        analytics_service: EnrollmentAnalyticsService,
    ) -> None:
        self.schedule_service = schedule_service
        self.section_service = section_service
        self.audit_service = audit_service
        self.analytics_service = analytics_service

    def build_schedule_preview(
        self,
        schedule_id: int,
        day: Optional[str] = None,
        room_id: Optional[int] = None,
        instructor_id: Optional[int] = None,
    ) -> Dict[str, object]:
        schedule = self.schedule_service.get_schedule(schedule_id)
        sections = self._filter_sections(
            self.section_service.list_sections_for_schedule(schedule_id),
            day=day,
            room_id=room_id,
            instructor_id=instructor_id,
        )
        return {
            "schedule": schedule,
            "sections": sections,
            "generated_at": self._timestamp(),
            "filters": {
                "day": day,
                "room_id": room_id,
                "instructor_id": instructor_id,
            },
        }

    def export_schedule_pdf(
        self,
        schedule_id: int,
        day: Optional[str] = None,
        room_id: Optional[int] = None,
        instructor_id: Optional[int] = None,
    ) -> tuple[bytes, str]:
        preview = self.build_schedule_preview(
            schedule_id,
            day=day,
            room_id=room_id,
            instructor_id=instructor_id,
        )
        schedule = preview["schedule"]
        lines = [
            f"Schedule: {schedule.name}",
            f"Generated: {preview['generated_at']}",
            "Columns: CRN | Course | Meeting Days/Times | Room | Instructor | Enrollment | TAs",
            "",
        ]
        for section in preview["sections"]:
            lines.extend(self._schedule_section_lines(section))
        if not preview["sections"]:
            lines.append("No sections matched the selected filters.")
        pdf = SimplePdfBuilder().build("Schedule Export", lines)
        filename = f"schedule-{schedule.id}-{self._filename_suffix()}.pdf"
        return pdf, filename

    def export_audit_pdf(self, report_id: int) -> tuple[bytes, str]:
        report = self.audit_service.get_report(report_id)
        grouped = self.audit_service.group_issues_by_type(report)
        lines = [
            f"Audit Report: {report.schedule_name or report.schedule_id}",
            f"Generated: {report.created_at}",
            f"Status: {report.status}",
            "",
        ]
        if not grouped:
            lines.append("No issues found. The selected schedule passed all checks.")
        for issue_type, issues in grouped.items():
            lines.append(f"[{issue_type}]")
            for issue in issues:
                lines.append(
                    f"CRN/Section: {issue.section_id or 'N/A'} | {issue.description}"
                )
            lines.append("")
        pdf = SimplePdfBuilder().build("Audit Export", lines)
        filename = f"audit-{report.id}-{self._filename_suffix()}.pdf"
        return pdf, filename

    def export_comparison_pdf(
        self,
        schedule_ids: List[int],
        subject: Optional[str] = None,
        course_number: Optional[str] = None,
    ) -> tuple[bytes, str]:
        rows = self.analytics_service.compare_enrollment(
            schedule_ids, subject=subject, course_number=course_number
        )
        lines = [
            "Enrollment Comparison",
            f"Generated: {self._timestamp()}",
            "",
        ]
        if not rows:
            lines.append("No courses matched the selected filters.")
        for row in rows:
            growth_flag = " [growth]" if row.significant_growth else ""
            lines.append(f"{row.course_number} - {row.course_title}{growth_flag}")
            for semester in row.semesters:
                enrollment = (
                    str(semester.total_enrollment)
                    if semester.total_enrollment is not None
                    else "Not Offered"
                )
                near_capacity = " near capacity" if semester.near_capacity else ""
                lines.append(
                    f"  {semester.schedule_name}: enrollment={enrollment}, "
                    f"sections={semester.section_count}{near_capacity}"
                )
                if semester.instructors:
                    lines.append(
                        f"    instructors: {', '.join(semester.instructors)}"
                    )
                if semester.tas:
                    lines.append(f"    TAs: {', '.join(semester.tas)}")
            lines.append("")
        pdf = SimplePdfBuilder().build("Enrollment Comparison", lines)
        filename = f"comparison-{self._filename_suffix()}.pdf"
        return pdf, filename

    @staticmethod
    def _filter_sections(
        sections,
        day: Optional[str],
        room_id: Optional[int],
        instructor_id: Optional[int],
    ):
        filtered = []
        normalized_day = day.strip().upper() if day else None
        for section in sections:
            if room_id is not None and section.room_id != room_id:
                continue
            if instructor_id is not None and section.instructor_id != instructor_id:
                continue
            if normalized_day:
                if not any(normalized_day in meeting.days.upper() for meeting in section.meetings):
                    continue
            filtered.append(section)
        return filtered

    @staticmethod
    def _schedule_section_lines(section) -> List[str]:
        meetings = ", ".join(
            f"{meeting.days} {meeting.start_time}-{meeting.end_time}"
            for meeting in section.meetings
        ) or "TBD"
        tas = ", ".join(
            f"{assignment.ta_name or assignment.ta_id} ({assignment.assigned_hours:g}h)"
            for assignment in section.ta_assignments
        ) or "None"
        return [
            f"CRN {section.crn} | {section.course_number} {section.course_title}",
            f"  Meetings: {meetings}",
            f"  Room: {section.room_number or 'TBD'} | Instructor: {section.instructor_name or 'TBD'}",
            f"  Enrollment: {section.enrollment} | TAs: {tas}",
            "",
        ]

    @staticmethod
    def _timestamp() -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    @classmethod
    def _filename_suffix(cls) -> str:
        return cls._timestamp().replace(":", "-")


class SimplePdfBuilder:
    def build(self, title: str, lines: List[str]) -> bytes:
        page_lines = self._paginate([title, ""] + lines)
        objects: List[str] = []
        font_object_id = 3
        content_object_ids = []
        page_object_ids = []
        next_object_id = 4

        for page in page_lines:
            page_object_ids.append(next_object_id)
            content_object_ids.append(next_object_id + 1)
            next_object_id += 2

        kids = " ".join(f"{object_id} 0 R" for object_id in page_object_ids)
        objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        objects.append(
            f"2 0 obj\n<< /Type /Pages /Count {len(page_object_ids)} /Kids [{kids}] >>\nendobj\n"
        )
        objects.append(
            "3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        )

        for page_object_id, content_object_id, page in zip(
            page_object_ids, content_object_ids, page_lines
        ):
            stream = self._page_stream(page)
            objects.append(
                f"{page_object_id} 0 obj\n"
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> "
                f"/Contents {content_object_id} 0 R >>\nendobj\n"
            )
            objects.append(
                f"{content_object_id} 0 obj\n<< /Length {len(stream.encode('latin-1'))} >>\n"
                f"stream\n{stream}\nendstream\nendobj\n"
            )

        output = "%PDF-1.4\n"
        offsets = [0]
        for item in objects:
            offsets.append(len(output.encode("latin-1")))
            output += item

        xref_offset = len(output.encode("latin-1"))
        output += f"xref\n0 {len(objects) + 1}\n"
        output += "0000000000 65535 f \n"
        for offset in offsets[1:]:
            output += f"{offset:010d} 00000 n \n"
        output += (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n"
            f"{xref_offset}\n%%EOF"
        )
        return output.encode("latin-1")

    @staticmethod
    def _paginate(lines: List[str], page_size: int = 40) -> List[List[str]]:
        pages = []
        for start in range(0, max(1, len(lines)), page_size):
            pages.append(lines[start : start + page_size])
        return pages or [[]]

    def _page_stream(self, lines: List[str]) -> str:
        commands = ["BT", "/F1 12 Tf", "14 TL", "50 760 Td"]
        for index, line in enumerate(lines):
            if index > 0:
                commands.append("T*")
            commands.append(f"({self._escape(line)}) Tj")
        commands.append("ET")
        return "\n".join(commands)

    @staticmethod
    def _escape(value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
