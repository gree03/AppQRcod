from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class EditScheduleStates(StatesGroup):
    choosing_week = State()
    choosing_day = State()
    choosing_event = State()
    choosing_field = State()
    entering_value = State()


__all__ = ["EditScheduleStates"]
