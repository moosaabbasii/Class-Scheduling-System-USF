from datetime import datetime
from typing import Iterable

from app.core.exceptions import ValidationError


def calculate_section_weekly_hours(meetings: Iterable[object]) -> float:
    total_minutes = 0
    for meeting in meetings:
        total_minutes += calculate_meeting_weekly_minutes(
            meeting.days,
            meeting.start_time,
            meeting.end_time,
        )
    return round(total_minutes / 60.0, 2)


def calculate_meeting_weekly_minutes(days: str, start_time: str, end_time: str) -> int:
    start = _parse_time(start_time)
    end = _parse_time(end_time)
    minutes = int((end - start).total_seconds() // 60)
    if minutes < 0:
        raise ValidationError("Meeting end_time must be later than start_time.")
    return minutes * _count_days(days)


def _count_days(days: str) -> int:
    normalized = [character for character in days.upper() if character.isalpha()]
    return len(normalized)


def _parse_time(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ValidationError("Times must use HH:MM format.") from exc
