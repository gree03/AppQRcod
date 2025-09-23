from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import (
    DayCallback,
    EventCallback,
    FieldCallback,
    ReminderToggleCallback,
    WeekCallback,
    WeekViewCallback,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="/сегодня"), KeyboardButton(text="/завтра")],
        [KeyboardButton(text="Расписание на неделю")],
        [KeyboardButton(text="Изменить расписание"), KeyboardButton(text="Напоминания")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def build_week_keyboard(max_week: int = 16) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for week in range(1, max_week + 1):
        builder.button(text=str(week), callback_data=WeekCallback(week=week).pack())
    builder.adjust(4)
    return builder.as_markup()


def build_day_keyboard(week: int, days: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day in days:
        builder.button(
            text=day.capitalize(),
            callback_data=DayCallback(week=week, day=day).pack(),
        )
    builder.adjust(2)
    return builder.as_markup()


def build_event_keyboard(week: int, day: str, events: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, caption in events:
        builder.button(
            text=caption,
            callback_data=EventCallback(week=week, day=day, index=index).pack(),
        )
    builder.adjust(1)
    return builder.as_markup()


def build_field_keyboard(day: str, index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fields = {
        "subject": "Предмет",
        "time": "Время",
        "teacher": "Преподаватель",
        "room": "Аудитория",
        "group": "Подгруппа",
        "weeks": "Недели",
    }
    for field, title in fields.items():
        builder.button(
            text=title,
            callback_data=FieldCallback(day=day, index=index, field=field).pack(),
        )
    builder.adjust(2)
    return builder.as_markup()


def build_week_view_keyboard(
    current_week: int,
    max_week: int = 16,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for week in range(1, max_week + 1):
        label = f"• {week}" if week == current_week else str(week)
        builder.button(
            text=label,
            callback_data=WeekViewCallback(week=week).pack(),
        )
    builder.adjust(4)
    return builder.as_markup()


def build_reminders_keyboard(reminders: dict[str, bool]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [
        ("morning", "07:00 — на сегодня"),
        ("evening", "20:00 — на завтра"),
    ]
    for kind, caption in options:
        enabled = reminders.get(kind, False)
        marker = "✅" if enabled else "❌"
        builder.button(
            text=f"{marker} {caption}",
            callback_data=ReminderToggleCallback(kind=kind).pack(),
        )
    builder.adjust(1)
    builder.button(
        text="Отключить все",
        callback_data=ReminderToggleCallback(kind="all").pack(),
    )
    return builder.as_markup()


__all__ = [
    "build_day_keyboard",
    "build_event_keyboard",
    "build_field_keyboard",
    "build_week_keyboard",
    "build_week_view_keyboard",
    "build_reminders_keyboard",
    "main_menu_keyboard",
]
