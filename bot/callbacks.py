from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class WeekCallback(CallbackData, prefix="week"):
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


__all__ = ["WeekCallback", "DayCallback", "EventCallback", "FieldCallback"]
