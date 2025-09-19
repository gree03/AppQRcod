from __future__ import annotations

from datetime import date
from typing import Iterable, List, Sequence

from .repositories import ScheduleData

DAY_INDEX_TO_NAME = {
    0: "ПОНЕДЕЛЬНИК",
    1: "ВТОРНИК",
    2: "СРЕДА",
    3: "ЧЕТВЕРГ",
    4: "ПЯТНИЦА",
    5: "СУББОТА",
    6: "ВОСКРЕСЕНЬЕ",
}

DAY_ALIASES = {name.lower(): name for name in DAY_INDEX_TO_NAME.values()}


def get_day_name_for_date(target_date: date) -> str:
    """Return the uppercase Russian day name for the provided date."""
    return DAY_INDEX_TO_NAME[target_date.weekday()]


def pretty_day_name(day: str) -> str:
    """Return the day name with capitalised first letter."""
    normalized = normalize_day_name(day)
    return normalized.capitalize()


def normalize_day_name(day: str) -> str:
    key = day.strip().lower()
    if key not in DAY_ALIASES:
        raise KeyError(f"Неизвестный день недели: {day}")
    return DAY_ALIASES[key]


def calculate_week_number(current_week: int, base_date: date, target_date: date) -> int:
    """Return academic week number for the target date based on the current week."""
    days_diff = (target_date - base_date).days
    if days_diff <= 0:
        return current_week

    week_offset = (base_date.weekday() + days_diff) // 7
    return current_week + week_offset


def format_weeks(weeks: Iterable[int]) -> str:
    numbers = sorted(set(int(week) for week in weeks))
    if not numbers:
        return "—"

    ranges = []
    start = prev = numbers[0]
    for week in numbers[1:]:
        if week == prev + 1:
            prev = week
            continue
        ranges.append((start, prev))
        start = prev = week
    ranges.append((start, prev))

    parts = []
    for start, end in ranges:
        if start == end:
            parts.append(str(start))
        else:
            parts.append(f"{start}–{end}")
    return ", ".join(parts)


def parse_weeks(value: str, *, min_week: int = 1, max_week: int = 30) -> List[int]:
    cleaned = value.replace(";", ",").replace(" ", "")
    if not cleaned:
        raise ValueError("Строка с неделями не должна быть пустой.")

    result: List[int] = []
    for chunk in cleaned.split(","):
        if not chunk:
            continue
        if "-" in chunk or "–" in chunk:
            parts: Sequence[str] = chunk.replace("–", "-").split("-", maxsplit=1)
            if len(parts) != 2:
                raise ValueError(f"Неверный диапазон недель: {chunk}")
            start, end = (int(part) for part in parts)
            if start > end:
                raise ValueError(f"Начало диапазона больше конца: {chunk}")
            result.extend(range(start, end + 1))
        else:
            result.append(int(chunk))

    filtered = sorted(set(result))
    if any(week < min_week or week > max_week for week in filtered):
        raise ValueError("Указаны недели вне допустимого диапазона.")
    return filtered


def format_schedule_day(
    day: str,
    week_number: int | None,
    schedule: ScheduleData,
    *,
    show_all_when_week_missing: bool = False,
) -> str:
    normalized_day = normalize_day_name(day)
    events = schedule.get(normalized_day, [])

    if week_number is None and show_all_when_week_missing:
        filtered_events = events
    elif week_number is None:
        filtered_events = []
    else:
        filtered_events = [
            event for event in events if week_number in event.get("weeks", [])
        ]

    title = pretty_day_name(normalized_day)
    if week_number is None:
        header = f"Расписание на {title} (номер учебной недели не определён):"
    else:
        header = f"Расписание на {title}, {week_number} учебная неделя:"

    if not filtered_events:
        if week_number is None and not show_all_when_week_missing:
            return header + "\nНет данных для отображения без номера недели."
        return header + "\nПар нет."

    lines = [header]
    for index, lesson in enumerate(filtered_events, start=1):
        group = lesson.get("group")
        subject_line = f"{index}. {lesson['time']} — {lesson['subject']}"
        if group:
            subject_line += f" ({group})"

        details = []
        room = lesson.get("room")
        if room:
            details.append(f"ауд. {room}")
        teacher = lesson.get("teacher")
        if teacher:
            details.append(teacher)

        lines.append(subject_line)
        if details:
            lines.append("    " + ", ".join(details))
        lines.append(f"    Недели: {format_weeks(lesson.get('weeks', []))}")

    return "\n".join(lines)


__all__ = [
    "calculate_week_number",
    "format_schedule_day",
    "format_weeks",
    "get_day_name_for_date",
    "normalize_day_name",
    "parse_weeks",
    "pretty_day_name",
]
