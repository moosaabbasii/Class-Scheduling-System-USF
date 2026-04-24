from typing import Dict, List, Optional

from app.models.entities import CourseSection, SectionMeeting, SectionTaAssignment
from app.repositories.base import BaseRepository
from app.services.hours import calculate_section_weekly_hours


class SectionRepository(BaseRepository):
    def list_by_schedule(self, schedule_id: int) -> List[CourseSection]:
        rows = self._fetch_all(
            """
            SELECT
                cs.id,
                cs.schedule_id,
                cs.catalog_course_id,
                cs.crn,
                cs.level,
                cs.enrollment,
                cs.start_date,
                cs.end_date,
                cs.room_id,
                cs.instructor_id,
                cc.course_number,
                cc.title AS course_title,
                r.room_number,
                r.capacity AS room_capacity,
                i.name AS instructor_name,
                i.email AS instructor_email
            FROM course_sections cs
            JOIN catalog_courses cc ON cc.id = cs.catalog_course_id
            LEFT JOIN rooms r ON r.id = cs.room_id
            LEFT JOIN instructors i ON i.id = cs.instructor_id
            WHERE cs.schedule_id = ?
            ORDER BY cs.crn ASC, cs.id ASC
            """,
            (schedule_id,),
        )
        sections = [self._to_entity(row) for row in rows]
        self._attach_related_data(sections)
        return sections

    def get(self, section_id: int) -> Optional[CourseSection]:
        row = self._fetch_one(
            """
            SELECT
                cs.id,
                cs.schedule_id,
                cs.catalog_course_id,
                cs.crn,
                cs.level,
                cs.enrollment,
                cs.start_date,
                cs.end_date,
                cs.room_id,
                cs.instructor_id,
                cc.course_number,
                cc.title AS course_title,
                r.room_number,
                r.capacity AS room_capacity,
                i.name AS instructor_name,
                i.email AS instructor_email
            FROM course_sections cs
            JOIN catalog_courses cc ON cc.id = cs.catalog_course_id
            LEFT JOIN rooms r ON r.id = cs.room_id
            LEFT JOIN instructors i ON i.id = cs.instructor_id
            WHERE cs.id = ?
            """,
            (section_id,),
        )
        if not row:
            return None
        section = self._to_entity(row)
        self._attach_related_data([section])
        return section

    def create(self, payload: dict) -> CourseSection:
        cursor = self._execute(
            """
            INSERT INTO course_sections (
                schedule_id,
                catalog_course_id,
                crn,
                level,
                enrollment,
                start_date,
                end_date,
                room_id,
                instructor_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["schedule_id"],
                payload["catalog_course_id"],
                payload["crn"],
                payload.get("level"),
                payload.get("enrollment", 0),
                payload.get("start_date"),
                payload.get("end_date"),
                payload.get("room_id"),
                payload.get("instructor_id"),
            ),
        )
        section_id = cursor.lastrowid
        self.replace_meetings(section_id, payload.get("meetings", []))
        self.replace_ta_assignments(section_id, payload.get("ta_assignments", []))
        return self.get(section_id)

    def update(self, section_id: int, payload: dict) -> Optional[CourseSection]:
        section_fields = {
            key: value
            for key, value in payload.items()
            if key not in ("meetings", "ta_assignments")
        }
        if section_fields:
            clause, values = self._build_update_clause(section_fields)
            values.append(section_id)
            self._execute(f"UPDATE course_sections SET {clause} WHERE id = ?", values)

        if "meetings" in payload:
            self.replace_meetings(section_id, payload["meetings"])
        if "ta_assignments" in payload:
            self.replace_ta_assignments(section_id, payload["ta_assignments"])
        return self.get(section_id)

    def delete(self, section_id: int) -> bool:
        return self._execute(
            "DELETE FROM course_sections WHERE id = ?",
            (section_id,),
        ).rowcount > 0

    def replace_meetings(self, section_id: int, meetings: List[dict]) -> None:
        self._execute("DELETE FROM section_meetings WHERE section_id = ?", (section_id,))
        if not meetings:
            return
        self._executemany(
            """
            INSERT INTO section_meetings (section_id, days, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    section_id,
                    item["days"],
                    item["start_time"],
                    item["end_time"],
                )
                for item in meetings
            ],
        )

    def replace_ta_assignments(self, section_id: int, assignments: List[dict]) -> None:
        self._execute("DELETE FROM section_tas WHERE section_id = ?", (section_id,))
        if not assignments:
            return
        self._executemany(
            """
            INSERT INTO section_tas (section_id, ta_id, assigned_hours)
            VALUES (?, ?, ?)
            """,
            [
                (
                    section_id,
                    item["ta_id"],
                    0,
                )
                for item in assignments
            ],
        )

    def _attach_related_data(self, sections: List[CourseSection]) -> None:
        if not sections:
            return
        section_map: Dict[int, CourseSection] = {section.id: section for section in sections}
        placeholders = ", ".join("?" for _ in section_map)
        section_ids = tuple(section_map.keys())

        meeting_rows = self._fetch_all(
            f"""
            SELECT id, section_id, days, start_time, end_time
            FROM section_meetings
            WHERE section_id IN ({placeholders})
            ORDER BY start_time ASC, end_time ASC, id ASC
            """,
            section_ids,
        )
        for row in meeting_rows:
            section_map[row["section_id"]].meetings.append(
                SectionMeeting(
                    id=row["id"],
                    section_id=row["section_id"],
                    days=row["days"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                )
            )
        section_hours = {
            section_id: calculate_section_weekly_hours(section.meetings)
            for section_id, section in section_map.items()
        }

        ta_rows = self._fetch_all(
            f"""
            SELECT
                st.section_id,
                st.ta_id,
                t.name AS ta_name,
                t.email AS ta_email,
                t.max_hours
            FROM section_tas st
            JOIN tas t ON t.id = st.ta_id
            WHERE st.section_id IN ({placeholders})
            ORDER BY t.name ASC, st.ta_id ASC
            """,
            section_ids,
        )
        for row in ta_rows:
            section_map[row["section_id"]].ta_assignments.append(
                SectionTaAssignment(
                    ta_id=row["ta_id"],
                    assigned_hours=section_hours[row["section_id"]],
                    ta_name=row["ta_name"],
                    ta_email=row["ta_email"],
                    max_hours=row["max_hours"],
                )
            )

    @staticmethod
    def _to_entity(row) -> CourseSection:
        return CourseSection(
            id=row["id"],
            schedule_id=row["schedule_id"],
            catalog_course_id=row["catalog_course_id"],
            crn=row["crn"],
            level=row["level"],
            enrollment=row["enrollment"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            room_id=row["room_id"],
            instructor_id=row["instructor_id"],
            course_number=row["course_number"],
            course_title=row["course_title"],
            room_number=row["room_number"],
            room_capacity=row["room_capacity"],
            instructor_name=row["instructor_name"],
            instructor_email=row["instructor_email"],
        )
