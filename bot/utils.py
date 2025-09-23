from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from html import escape
from typing import Any, Iterable, List, Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen

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

ACADEMIC_YEAR_START_MONTH = 9
ACADEMIC_YEAR_START_DAY = 1

_LESSON_INDENT = "\u00A0" * 2
_WEEK_SOURCE_URL = (
    "https://www.bsau.ru/obrazovanie/raspisanie/?FAKULTET=1257&NAPR=48&KURS=3"
    "&LEVEL_EDUCATION=165&FORM_EDUCATION=169"
)
_WEEK_NUMBER_PATTERN = re.compile(r"<span\s+id=\"info33\"[^>]*><b>(\d+)</b>", re.IGNORECASE)
_WEEK_CACHE_TTL = timedelta(minutes=30)
_week_cache: dict[str, Any] = {"timestamp": None, "value": None}
_logger = logging.getLogger(__name__)


def _fetch_week_number_from_site(timeout: float = 10.0) -> int:
    request = Request(
        _WEEK_SOURCE_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ScheduleBot/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:  # nosec B310 - trusted source
        raw_body = response.read()
        encoding = response.headers.get_content_charset() if response.headers else None

    try:
        html_text = raw_body.decode(encoding or "utf-8", errors="ignore")
    except LookupError:
        html_text = raw_body.decode("utf-8", errors="ignore")

    match = _WEEK_NUMBER_PATTERN.search(html_text)
    if not match:
        raise ValueError("Не удалось найти номер учебной недели на странице БГАУ.")

    return int(match.group(1))


def get_remote_week_number(force: bool = False) -> int | None:
    now = datetime.now()
    cached_value = _week_cache.get("value")
    cached_timestamp = _week_cache.get("timestamp")
    if (
        not force
        and isinstance(cached_timestamp, datetime)
        and now - cached_timestamp <= _WEEK_CACHE_TTL
    ):
        return cached_value

    try:
        value = _fetch_week_number_from_site()
    except (URLError, ValueError, OSError) as exc:
        if cached_value is not None:
            _logger.warning(
                "Не удалось обновить номер учебной недели: %s. Использую кэш %s.",
                exc,
                cached_value,
            )
            return cached_value
        _logger.warning("Не удалось получить номер учебной недели: %s", exc)
        return None

    _week_cache["timestamp"] = now
    _week_cache["value"] = value
    return value


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


def get_academic_year_start(target_date: date) -> date:
    """Return the first Monday of the academic year for the provided date."""
    year = target_date.year
    start_candidate = date(year, ACADEMIC_YEAR_START_MONTH, ACADEMIC_YEAR_START_DAY)
    if target_date < start_candidate:
        year -= 1
        start_candidate = date(year, ACADEMIC_YEAR_START_MONTH, ACADEMIC_YEAR_START_DAY)

    weekday = start_candidate.weekday()
    offset = (7 - weekday) % 7
    return start_candidate + timedelta(days=offset)


def _calculate_week_number_from_september(target_date: date) -> int:
    """Return the academic week number counting from the first Monday of September."""
    start = get_academic_year_start(target_date)
    if target_date < start:
        return 1

    days_passed = (target_date - start).days
    return days_passed // 7 + 1


def get_academic_week_number(target_date: date) -> int:
    """Return the academic week number using the BGAU website as a reference."""

    today = date.today()
    current_week_local = _calculate_week_number_from_september(today)
    target_week_local = _calculate_week_number_from_september(target_date)

    remote_week = get_remote_week_number()
    if remote_week is None:
        return target_week_local

    delta = target_week_local - current_week_local
    calculated = remote_week + delta
    return max(1, calculated)


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


def _week_phrase(week_number: int | None) -> str:
    if week_number is None:
        return "номер учебной недели не определён"
    return f"{week_number}-я учебная неделя"


def _filter_events_for_week(
    events: list[dict[str, Any]],
    week_number: int | None,
    *,
    show_all_when_week_missing: bool = False,
) -> list[dict[str, Any]]:
    if week_number is None:
        return events if show_all_when_week_missing else []
    return [event for event in events if week_number in event.get("weeks", [])]


def _format_lesson_block(index: int, lesson: dict[str, Any]) -> List[str]:
    subject = escape(str(lesson.get("subject") or "Без названия"))
    time = escape(str(lesson.get("time") or "—"))
    lines: List[str] = [f"{index}. {subject}"]
    lines.append(f"{_LESSON_INDENT}⏰ {time}")

    group = lesson.get("group")
    if group:
        lines.append(f"{_LESSON_INDENT}👥 {escape(str(group))}")

    room = lesson.get("room")
    if room:
        lines.append(f"{_LESSON_INDENT}📍 {escape(str(room))}")

    teacher = lesson.get("teacher")
    if teacher:
        lines.append(f"{_LESSON_INDENT}👨‍🏫 {escape(str(teacher))}")

    weeks_text = escape(format_weeks(lesson.get("weeks", [])))
    lines.append(f"{_LESSON_INDENT}🗓️ Недели: {weeks_text}")
    return lines


def _format_day_lines(
    day: str,
    week_number: int | None,
    schedule: ScheduleData,
    *,
    show_all_when_week_missing: bool = False,
    header_template: str | None = None,
    empty_message: str = "Пар нет.",
) -> List[str]:
    normalized_day = normalize_day_name(day)
    events = schedule.get(normalized_day, [])
    filtered_events = _filter_events_for_week(
        events, week_number, show_all_when_week_missing=show_all_when_week_missing
    )

    title = escape(pretty_day_name(normalized_day))
    week_text = escape(_week_phrase(week_number))

    if header_template is None:
        header = f"<b>Расписание на {title}</b>\n<i>{week_text}</i>"
    else:
        header = header_template.format(title=title, week_phrase=week_text)

    lines: List[str] = [header]

    if not filtered_events:
        lines.append("")
        if week_number is None and not show_all_when_week_missing:
            lines.append("Нет данных для отображения без номера недели.")
        else:
            lines.append(empty_message)
        return lines

    lines.append("")
    for index, lesson in enumerate(filtered_events, start=1):
        lines.extend(_format_lesson_block(index, lesson))
        lines.append("")

    if lines[-1] == "":
        lines.pop()
    return lines


def format_schedule_day(
    day: str,
    week_number: int | None,
    schedule: ScheduleData,
    *,
    show_all_when_week_missing: bool = False,
) -> str:
    lines = _format_day_lines(
        day,
        week_number,
        schedule,
        show_all_when_week_missing=show_all_when_week_missing,
    )
    return "\n".join(lines).strip()


def format_schedule_week(week_number: int, schedule: ScheduleData) -> str:
    lines: List[str] = [
        f"📅 Расписание на {escape(str(week_number))}-ю учебную неделю",
        "",
    ]
    for index in range(7):
        day = DAY_INDEX_TO_NAME[index]
        day_lines = _format_day_lines(
            day,
            week_number,
            schedule,
            header_template="🗓 {title}",
        )
        lines.extend(day_lines)
        lines.append("")

    if lines[-1] == "":
        lines.pop()
    return "\n".join(lines).strip()


__all__ = [
    "format_schedule_day",
    "format_schedule_week",
    "format_weeks",
    "get_academic_week_number",
    "get_academic_year_start",
    "get_remote_week_number",
    "get_day_name_for_date",
    "normalize_day_name",
    "parse_weeks",
    "pretty_day_name",
]
