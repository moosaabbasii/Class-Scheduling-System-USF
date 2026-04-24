import argparse
import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


MAIN_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_to_index(col: str) -> int:
    index = 0
    for char in col:
        if char.isalpha():
            index = index * 26 + (ord(char.upper()) - 64)
    return index - 1


def read_first_sheet_rows(xlsx_path: Path) -> List[Dict[str, str]]:
    with zipfile.ZipFile(xlsx_path) as archive:
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", MAIN_NS):
                parts = [text.text or "" for text in item.findall(".//m:t", MAIN_NS)]
                shared_strings.append("".join(parts))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
        }
        first_sheet = workbook.find("m:sheets/m:sheet", MAIN_NS)
        if first_sheet is None:
            return []
        rid = first_sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rel_map[rid]
        sheet_xml = ET.fromstring(archive.read(f"xl/{target}"))

        matrix: List[List[str]] = []
        for row in sheet_xml.findall("m:sheetData/m:row", MAIN_NS):
            values: Dict[int, str] = {}
            for cell in row.findall("m:c", MAIN_NS):
                reference = cell.attrib.get("r", "")
                col = "".join(ch for ch in reference if ch.isalpha())
                idx = col_to_index(col)
                cell_type = cell.attrib.get("t")
                value_node = cell.find("m:v", MAIN_NS)
                inline_node = cell.find("m:is", MAIN_NS)
                value = ""
                if cell_type == "s" and value_node is not None and value_node.text is not None:
                    value = shared_strings[int(value_node.text)]
                elif cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(
                        text.text or "" for text in inline_node.findall(".//m:t", MAIN_NS)
                    )
                elif value_node is not None and value_node.text is not None:
                    value = value_node.text
                values[idx] = value
            if values:
                max_col = max(values.keys())
                row_values = [""] * (max_col + 1)
                for idx, value in values.items():
                    row_values[idx] = value
                matrix.append(row_values)

    if not matrix:
        return []
    header = [item.strip() for item in matrix[0]]
    rows: List[Dict[str, str]] = []
    for row in matrix[1:]:
        padded = row + [""] * max(0, len(header) - len(row))
        record = {}
        for idx, key in enumerate(header):
            if key:
                record[key] = (padded[idx] or "").strip()
        rows.append(record)
    return rows


def parse_int(value: str) -> Optional[int]:
    value = (value or "").strip()
    if not value:
        return None
    if not re.fullmatch(r"\d+", value):
        return None
    return int(value)


def parse_date(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_meeting_range(value: str) -> Tuple[Optional[str], Optional[str]]:
    text = (value or "").strip()
    if not text or "TBA" in text.upper():
        return None, None
    parts = [part.strip() for part in text.split("-")]
    if len(parts) != 2:
        return None, None
    start = parse_clock(parts[0])
    end = parse_clock(parts[1])
    return start, end


def parse_clock(value: str) -> Optional[str]:
    text = (value or "").strip().upper().replace(".", "")
    candidates = ["%I:%M %p", "%I %p"]
    for fmt in candidates:
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None


def normalize_room(value: str) -> Optional[str]:
    room = (value or "").strip()
    if not room:
        return None
    if "TBA" in room.upper():
        return None
    return room


def get_row_value(row: Dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return ""


def parse_ta_block(
    names_block: str,
    emails_block: str,
    default_hours: int = 0,
) -> List[Dict[str, object]]:
    name_lines = [line.strip() for line in (names_block or "").splitlines() if line.strip()]
    email_lines = [line.strip() for line in (emails_block or "").splitlines() if line.strip()]
    results = []
    for idx, line in enumerate(name_lines):
        if re.match(r"^see\b", line, re.IGNORECASE):
            continue
        match = re.match(r"^(.*?)\s*\((\d+)\)\s*$", line)
        if match:
            name = match.group(1).strip()
            hours = int(match.group(2))
        else:
            name = line
            hours = default_hours
        email = email_lines[idx] if idx < len(email_lines) and "@" in email_lines[idx] else None
        results.append({"name": name, "email": email, "hours": hours})
    return results


class Importer:
    def __init__(self, db_path: Path, schedule_name: str, schedule_status: str) -> None:
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.ensure_ta_capacity_column()
        self.schedule_name = schedule_name
        self.schedule_status = schedule_status
        self.course_cache: Dict[Tuple[str, str], int] = {}
        self.room_cache: Dict[str, int] = {}
        self.instructor_cache: Dict[str, int] = {}
        self.ta_cache: Dict[str, int] = {}
        self.stats = {
            "rows_seen": 0,
            "rows_imported": 0,
            "rows_skipped": 0,
            "courses_created": 0,
            "rooms_created": 0,
            "instructors_created": 0,
            "tas_created": 0,
            "sections_created": 0,
            "sections_updated": 0,
            "meetings_created": 0,
            "section_ta_links_created": 0,
        }

    def ensure_ta_capacity_column(self) -> None:
        columns = [
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(tas)").fetchall()
        ]
        if "max_hours" in columns:
            return
        self.conn.execute("ALTER TABLE tas ADD COLUMN max_hours INTEGER DEFAULT 0")
        if "hours" in columns:
            self.conn.execute("UPDATE tas SET max_hours = COALESCE(hours, 0)")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def run(self, rows: List[Dict[str, str]]) -> Dict[str, int]:
        schedule_id = self.get_or_create_schedule(self.schedule_name, self.schedule_status)
        for row in rows:
            self.stats["rows_seen"] += 1
            crn = parse_int(get_row_value(row, "CRN"))
            if crn is None:
                self.stats["rows_skipped"] += 1
                continue

            subject = get_row_value(row, "SUBJ").strip()
            number = get_row_value(row, "CRSE NUMB", "CRSE_NUMB").strip()
            title = get_row_value(row, "CRSE TITLE", "CRSE_TITLE").strip()
            if not subject or not number or not title:
                self.stats["rows_skipped"] += 1
                continue

            course_number = f"{subject} {number}"
            level = get_row_value(row, "CRSE LEVL", "CRSE_LEVL").strip() or None
            enrollment = parse_int(get_row_value(row, "ENROLLMENT")) or 0
            start_date = parse_date(get_row_value(row, "START DATE"))
            end_date = parse_date(get_row_value(row, "END DATE"))
            room_number = normalize_room(get_row_value(row, "MEETING ROOM", "MEETING_ROOM"))
            meeting_days = get_row_value(row, "MEETING DAYS", "MEETING_DAYS").strip().upper()
            start_time, end_time = parse_meeting_range(
                get_row_value(row, "MEETING TIMES1", "MEETING TIMES", "MEETING_TIMES")
            )
            instructor_name = get_row_value(row, "INSTRUCTOR").strip() or None
            instructor_email = get_row_value(row, "INSTRUCTOR EMAIL").strip() or None

            catalog_course_id = self.get_or_create_catalog_course(course_number, title)
            room_id = self.get_or_create_room(room_number) if room_number else None
            instructor_id = (
                self.get_or_create_instructor(instructor_name, instructor_email)
                if instructor_name
                else None
            )

            section_id, created = self.upsert_section(
                schedule_id=schedule_id,
                catalog_course_id=catalog_course_id,
                crn=crn,
                level=level,
                enrollment=enrollment,
                start_date=start_date,
                end_date=end_date,
                room_id=room_id,
                instructor_id=instructor_id,
            )
            if created:
                self.stats["sections_created"] += 1
            else:
                self.stats["sections_updated"] += 1

            self.replace_meetings(section_id, meeting_days, start_time, end_time)

            ug_hours_hint = parse_int(get_row_value(row, "UG Hours")) or 0
            grad_hours_hint = parse_int(get_row_value(row, "Grad Hours")) or 0
            ug_tas = parse_ta_block(
                get_row_value(row, "UGTAs", "UGTA(s)"),
                get_row_value(row, "UGTA Emails"),
                default_hours=ug_hours_hint,
            )
            grad_tas = parse_ta_block(
                get_row_value(row, "Grad TAS", "Grad TAs", "Graduate TA(s)"),
                get_row_value(row, "Grad TA Emails"),
                default_hours=grad_hours_hint,
            )
            self.replace_section_tas(section_id, ug_tas + grad_tas)

            self.stats["rows_imported"] += 1

        self.conn.commit()
        return self.stats

    def get_or_create_schedule(self, name: str, status: str) -> int:
        row = self.conn.execute(
            "SELECT id FROM semester_schedules WHERE name = ?",
            (name,),
        ).fetchone()
        if row:
            return int(row["id"])
        cursor = self.conn.execute(
            "INSERT INTO semester_schedules (name, status, locked) VALUES (?, ?, 0)",
            (name, status),
        )
        return int(cursor.lastrowid)

    def get_or_create_catalog_course(self, course_number: str, title: str) -> int:
        key = (course_number, title)
        if key in self.course_cache:
            return self.course_cache[key]
        row = self.conn.execute(
            "SELECT id FROM catalog_courses WHERE course_number = ? AND title = ?",
            (course_number, title),
        ).fetchone()
        if row:
            course_id = int(row["id"])
        else:
            cursor = self.conn.execute(
                "INSERT INTO catalog_courses (course_number, title) VALUES (?, ?)",
                (course_number, title),
            )
            course_id = int(cursor.lastrowid)
            self.stats["courses_created"] += 1
        self.course_cache[key] = course_id
        return course_id

    def get_or_create_room(self, room_number: str) -> int:
        if room_number in self.room_cache:
            return self.room_cache[room_number]
        row = self.conn.execute(
            "SELECT id FROM rooms WHERE room_number = ?",
            (room_number,),
        ).fetchone()
        if row:
            room_id = int(row["id"])
        else:
            cursor = self.conn.execute(
                "INSERT INTO rooms (room_number) VALUES (?)",
                (room_number,),
            )
            room_id = int(cursor.lastrowid)
            self.stats["rooms_created"] += 1
        self.room_cache[room_number] = room_id
        return room_id

    def get_or_create_instructor(self, name: str, email: Optional[str]) -> int:
        cache_key = (email or f"name:{name}").strip().lower()
        if cache_key in self.instructor_cache:
            return self.instructor_cache[cache_key]
        row = None
        if email:
            row = self.conn.execute(
                "SELECT id, email FROM instructors WHERE email = ?",
                (email,),
            ).fetchone()
        if row is None:
            row = self.conn.execute(
                "SELECT id, email FROM instructors WHERE name = ?",
                (name,),
            ).fetchone()
        if row:
            instructor_id = int(row["id"])
            if email and not row["email"]:
                self.conn.execute(
                    "UPDATE instructors SET email = ? WHERE id = ?",
                    (email, instructor_id),
                )
        else:
            cursor = self.conn.execute(
                "INSERT INTO instructors (name, email) VALUES (?, ?)",
                (name, email),
            )
            instructor_id = int(cursor.lastrowid)
            self.stats["instructors_created"] += 1
        self.instructor_cache[cache_key] = instructor_id
        return instructor_id

    def get_or_create_ta(self, name: str, email: Optional[str], hours_hint: int) -> int:
        cache_key = (email or f"name:{name}").strip().lower()
        if cache_key in self.ta_cache:
            ta_id = self.ta_cache[cache_key]
            self.conn.execute(
                "UPDATE tas SET max_hours = CASE WHEN max_hours < ? THEN ? ELSE max_hours END WHERE id = ?",
                (hours_hint, hours_hint, ta_id),
            )
            return ta_id

        row = None
        if email:
            row = self.conn.execute(
                "SELECT id, email, max_hours FROM tas WHERE email = ?",
                (email,),
            ).fetchone()
        if row is None:
            row = self.conn.execute(
                "SELECT id, email, max_hours FROM tas WHERE name = ?",
                (name,),
            ).fetchone()
        if row:
            ta_id = int(row["id"])
            updates = []
            values: List[object] = []
            if email and not row["email"]:
                updates.append("email = ?")
                values.append(email)
            if int(row["max_hours"]) < hours_hint:
                updates.append("max_hours = ?")
                values.append(hours_hint)
            if updates:
                values.append(ta_id)
                self.conn.execute(
                    f"UPDATE tas SET {', '.join(updates)} WHERE id = ?",
                    values,
                )
        else:
            cursor = self.conn.execute(
                "INSERT INTO tas (name, email, max_hours) VALUES (?, ?, ?)",
                (name, email, max(0, hours_hint)),
            )
            ta_id = int(cursor.lastrowid)
            self.stats["tas_created"] += 1

        self.ta_cache[cache_key] = ta_id
        return ta_id

    def upsert_section(
        self,
        schedule_id: int,
        catalog_course_id: int,
        crn: int,
        level: Optional[str],
        enrollment: int,
        start_date: Optional[str],
        end_date: Optional[str],
        room_id: Optional[int],
        instructor_id: Optional[int],
    ) -> Tuple[int, bool]:
        row = self.conn.execute(
            "SELECT id FROM course_sections WHERE schedule_id = ? AND crn = ?",
            (schedule_id, crn),
        ).fetchone()
        if row:
            section_id = int(row["id"])
            self.conn.execute(
                """
                UPDATE course_sections
                SET catalog_course_id = ?, level = ?, enrollment = ?, start_date = ?, end_date = ?, room_id = ?, instructor_id = ?
                WHERE id = ?
                """,
                (
                    catalog_course_id,
                    level,
                    enrollment,
                    start_date,
                    end_date,
                    room_id,
                    instructor_id,
                    section_id,
                ),
            )
            return section_id, False

        cursor = self.conn.execute(
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                schedule_id,
                catalog_course_id,
                crn,
                level,
                enrollment,
                start_date,
                end_date,
                room_id,
                instructor_id,
            ),
        )
        return int(cursor.lastrowid), True

    def replace_meetings(
        self,
        section_id: int,
        days: str,
        start_time: Optional[str],
        end_time: Optional[str],
    ) -> None:
        self.conn.execute("DELETE FROM section_meetings WHERE section_id = ?", (section_id,))
        if not days or not start_time or not end_time:
            return
        self.conn.execute(
            """
            INSERT INTO section_meetings (section_id, days, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            (section_id, days, start_time, end_time),
        )
        self.stats["meetings_created"] += 1

    def replace_section_tas(self, section_id: int, ta_entries: List[Dict[str, object]]) -> None:
        self.conn.execute("DELETE FROM section_tas WHERE section_id = ?", (section_id,))
        for ta_entry in ta_entries:
            name = (ta_entry.get("name") or "").strip()
            if not name:
                continue
            email = ta_entry.get("email")
            assigned_hours = int(ta_entry.get("hours") or 0)
            ta_id = self.get_or_create_ta(name=name, email=email, hours_hint=assigned_hours)
            self.conn.execute(
                """
                INSERT OR REPLACE INTO section_tas (section_id, ta_id, assigned_hours)
                VALUES (?, ?, ?)
                """,
                (section_id, ta_id, max(0, assigned_hours)),
            )
            self.stats["section_ta_links_created"] += 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import Bellini schedule data from XLSX into SQLite.")
    parser.add_argument("--db", default="database.sqlite", help="Path to SQLite database.")
    parser.add_argument(
        "--xlsx",
        default="app/data/Bellini Classes F25.xlsx",
        help="Path to input XLSX file.",
    )
    parser.add_argument("--schedule-name", default="F25", help="Target schedule name.")
    parser.add_argument("--schedule-status", default="draft", help="Target schedule status.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    db_path = Path(args.db)
    xlsx_path = Path(args.xlsx)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Workbook not found: {xlsx_path}")

    rows = read_first_sheet_rows(xlsx_path)
    importer = Importer(db_path=db_path, schedule_name=args.schedule_name, schedule_status=args.schedule_status)
    try:
        stats = importer.run(rows)
    finally:
        importer.close()

    print("Import complete.")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
