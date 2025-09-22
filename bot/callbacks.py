from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class WeekCallback(CallbackData, prefix="week"):
    week: int


class WeekViewCallback(CallbackData, prefix="view_week"):
    week: int


class DayCallback(CallbackData, prefix="day"):
    week: int
    day: str


class EventCallback(CallbackData, prefix="event"):
    week: int
    day: str
    index: int


class FieldCallback(CallbackData, prefix="field"):
    day: str
    index: int
    field: str


class ReminderToggleCallback(CallbackData, prefix="remind"):
    kind: str


__all__ = [
    "WeekCallback",
    "WeekViewCallback",
    "DayCallback",
    "EventCallback",
    "FieldCallback",
    "ReminderToggleCallback",
]
