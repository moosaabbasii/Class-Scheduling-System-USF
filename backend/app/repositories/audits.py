from typing import List, Optional

from app.models.entities import AuditReport, Issue
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    def list(self, schedule_id: Optional[int] = None) -> List[AuditReport]:
        params = ()
        where_clause = ""
        if schedule_id is not None:
            where_clause = "WHERE ar.schedule_id = ?"
            params = (schedule_id,)
        rows = self._fetch_all(
            f"""
            SELECT
                ar.id,
                ar.schedule_id,
                ar.generated_by,
                ar.passed,
                ar.status,
                ar.created_at,
                ss.name AS schedule_name,
                u.name AS generated_by_name
            FROM audit_reports ar
            JOIN semester_schedules ss ON ss.id = ar.schedule_id
            LEFT JOIN users u ON u.id = ar.generated_by
            {where_clause}
            ORDER BY ar.created_at DESC, ar.id DESC
            """,
            params,
        )
        reports = [self._to_report(row) for row in rows]
        self._attach_issues(reports)
        return reports

    def get(self, report_id: int) -> Optional[AuditReport]:
        row = self._fetch_one(
            """
            SELECT
                ar.id,
                ar.schedule_id,
                ar.generated_by,
                ar.passed,
                ar.status,
                ar.created_at,
                ss.name AS schedule_name,
                u.name AS generated_by_name
            FROM audit_reports ar
            JOIN semester_schedules ss ON ss.id = ar.schedule_id
            LEFT JOIN users u ON u.id = ar.generated_by
            WHERE ar.id = ?
            """,
            (report_id,),
        )
        if not row:
            return None
        report = self._to_report(row)
        self._attach_issues([report])
        return report

    def create_report(
        self, schedule_id: int, generated_by: Optional[int], passed: bool, status: str
    ) -> AuditReport:
        cursor = self._execute(
            """
            INSERT INTO audit_reports (schedule_id, generated_by, passed, status)
            VALUES (?, ?, ?, ?)
            """,
            (schedule_id, generated_by, int(passed), status),
        )
        return self.get(cursor.lastrowid)

    def update_report(self, report_id: int, payload: dict) -> Optional[AuditReport]:
        if not payload:
            return self.get(report_id)
        clause, values = self._build_update_clause(payload)
        values.append(report_id)
        self._execute(f"UPDATE audit_reports SET {clause} WHERE id = ?", values)
        return self.get(report_id)

    def replace_issues(self, report_id: int, issues: List[dict]) -> None:
        self._execute("DELETE FROM issues WHERE audit_report_id = ?", (report_id,))
        if not issues:
            return
        self._executemany(
            """
            INSERT INTO issues (audit_report_id, section_id, type, description, status, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    report_id,
                    item.get("section_id"),
                    item["type"],
                    item["description"],
                    item.get("status", "open"),
                    item.get("resolved_at"),
                )
                for item in issues
            ],
        )

    def get_issue(self, issue_id: int) -> Optional[Issue]:
        row = self._fetch_one(
            """
            SELECT
                id,
                audit_report_id,
                section_id,
                type,
                description,
                status,
                detected_at,
                resolved_at
            FROM issues
            WHERE id = ?
            """,
            (issue_id,),
        )
        return self._to_issue(row) if row else None

    def update_issue(self, issue_id: int, payload: dict) -> Optional[Issue]:
        if not payload:
            return self.get_issue(issue_id)
        clause, values = self._build_update_clause(payload)
        values.append(issue_id)
        self._execute(f"UPDATE issues SET {clause} WHERE id = ?", values)
        return self.get_issue(issue_id)

    def _attach_issues(self, reports: List[AuditReport]) -> None:
        if not reports:
            return
        report_map = {report.id: report for report in reports}
        placeholders = ", ".join("?" for _ in report_map)
        rows = self._fetch_all(
            f"""
            SELECT
                id,
                audit_report_id,
                section_id,
                type,
                description,
                status,
                detected_at,
                resolved_at
            FROM issues
            WHERE audit_report_id IN ({placeholders})
            ORDER BY id ASC
            """,
            tuple(report_map.keys()),
        )
        for row in rows:
            report_map[row["audit_report_id"]].issues.append(self._to_issue(row))

    @staticmethod
    def _to_report(row) -> AuditReport:
        return AuditReport(
            id=row["id"],
            schedule_id=row["schedule_id"],
            generated_by=row["generated_by"],
            passed=bool(row["passed"]),
            status=row["status"],
            created_at=row["created_at"],
            schedule_name=row["schedule_name"],
            generated_by_name=row["generated_by_name"],
        )

    @staticmethod
    def _to_issue(row) -> Issue:
        return Issue(
            id=row["id"],
            audit_report_id=row["audit_report_id"],
            section_id=row["section_id"],
            type=row["type"],
            description=row["description"],
            status=row["status"],
            detected_at=row["detected_at"],
            resolved_at=row["resolved_at"],
        )
