from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .callbacks import (
    DayCallback,
    EventCallback,
    FieldCallback,
    ReminderToggleCallback,
    WeekCallback,
    WeekViewCallback,
)
from .config import Settings
from .keyboards import (
    build_day_keyboard,
    build_event_keyboard,
    build_field_keyboard,
    build_reminders_keyboard,
    build_week_keyboard,
    build_week_view_keyboard,
    main_menu_keyboard,
)
from .repositories import ScheduleRepository, UserRepository
from .states import EditScheduleStates
from .utils import (
    format_schedule_day,
    format_schedule_week,
    format_weeks,
    get_academic_week_number,
    get_day_name_for_date,
    parse_weeks,
    pretty_day_name,
)

router = Router()


def _format_reminders_message(reminders: dict[str, bool]) -> str:
    morning = "✅ включено" if reminders.get("morning") else "❌ выключено"
    evening = "✅ включено" if reminders.get("evening") else "❌ выключено"
    lines = [
        "<b>Напоминания о расписании</b>",
        "",
        f"⏰ <b>07:00</b> — на сегодня: {morning}",
        f"🌙 <b>20:00</b> — на завтра: {evening}",
        "",
        (
            "Напоминания работают и в беседах: бот отправит расписание "
            "автоматически."
        ),
        "Используйте кнопки ниже, чтобы включить или отключить нужные напоминания.",
    ]
    return "\n".join(lines)


async def _show_schedule_for_date(
    message: Message,
    schedule_repo: ScheduleRepository,
    target_date: date,
) -> None:
    schedule = schedule_repo.load()
    week_number = get_academic_week_number(target_date)

    day_name = get_day_name_for_date(target_date)
    text = format_schedule_day(
        day_name,
        week_number,
        schedule,
    )

    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(CommandStart())
async def handle_start(
    message: Message,
    user_repo: UserRepository,
) -> None:
    user_repo.add_user(message.chat.id)
    greeting = (
        "Привет! Я бот расписания БГАУ для 3 курса направления 35.03.06.\n\n"
        "Доступные команды:\n"
        "• /сегодня — расписание на сегодня\n"
        "• /завтра — расписание на завтра\n"
        "• /неделя — расписание на всю неделю\n"
        "• /notify — управление напоминаниями\n"
        "• /edit — изменить расписание (доступно через кнопки)\n"
        "• /cancel — отменить редактирование"
    )
    await message.answer(greeting, reply_markup=main_menu_keyboard())


@router.message(Command("today"))
@router.message(Command("сегодня"))
@router.message(F.text == "/сегодня")
async def handle_today(
    message: Message,
    schedule_repo: ScheduleRepository,
    settings: Settings,
) -> None:
    del settings
    await _show_schedule_for_date(message, schedule_repo, date.today())


@router.message(Command("tomorrow"))
@router.message(Command("завтра"))
@router.message(F.text == "/завтра")
async def handle_tomorrow(
    message: Message,
    schedule_repo: ScheduleRepository,
    settings: Settings,
) -> None:
    del settings
    await _show_schedule_for_date(
        message,
        schedule_repo,
        date.today() + timedelta(days=1),
    )


@router.message(Command("week"))
@router.message(Command("неделя"))
@router.message(F.text.casefold() == "расписание на неделю")
async def handle_week_schedule(
    message: Message,
    schedule_repo: ScheduleRepository,
) -> None:
    schedule = schedule_repo.load()
    week_number = get_academic_week_number(date.today())
    text = (
        format_schedule_week(week_number, schedule)
        + "\n\n<em>Выберите нужную учебную неделю с помощью кнопок ниже.</em>"
    )
    await message.answer(
        text,
        reply_markup=build_week_view_keyboard(week_number),
    )


@router.callback_query(WeekViewCallback.filter())
async def handle_week_schedule_choice(
    callback: CallbackQuery,
    callback_data: WeekViewCallback,
    schedule_repo: ScheduleRepository,
) -> None:
    await callback.answer(f"Неделя {callback_data.week}")
    schedule = schedule_repo.load()
    text = (
        format_schedule_week(callback_data.week, schedule)
        + "\n\n<em>Выберите нужную учебную неделю с помощью кнопок ниже.</em>"
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=build_week_view_keyboard(callback_data.week),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise


@router.message(Command("notify"))
@router.message(Command("reminders"))
@router.message(F.text.casefold() == "напоминания")
async def handle_reminders_command(
    message: Message,
    user_repo: UserRepository,
) -> None:
    reminders = user_repo.get_reminders(message.chat.id)
    text = _format_reminders_message(reminders)
    await message.answer(text, reply_markup=build_reminders_keyboard(reminders))


@router.callback_query(ReminderToggleCallback.filter())
async def handle_reminder_toggle(
    callback: CallbackQuery,
    callback_data: ReminderToggleCallback,
    user_repo: UserRepository,
) -> None:
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id

    if callback_data.kind == "all":
        reminders = user_repo.clear_reminders(chat_id)
        await callback.answer("Все напоминания отключены.")
    else:
        reminders = user_repo.toggle_reminder(chat_id, callback_data.kind)
        label = "Утреннее" if callback_data.kind == "morning" else "Вечернее"
        status = "включено" if reminders.get(callback_data.kind) else "выключено"
        await callback.answer(f"{label} напоминание {status}.")

    text = _format_reminders_message(reminders)
    try:
        await callback.message.edit_text(
            text,
            reply_markup=build_reminders_keyboard(reminders),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise


@router.message(Command("edit"))
@router.message(F.text == "Изменить расписание")
async def handle_edit_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(EditScheduleStates.choosing_week)
    await message.answer(
        "Выберите учебную неделю для изменения расписания:",
        reply_markup=build_week_keyboard(),
    )


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def handle_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Нет активного редактирования.", reply_markup=main_menu_keyboard())
        return
    await state.clear()
    await message.answer("Редактирование отменено.", reply_markup=main_menu_keyboard())


@router.callback_query(EditScheduleStates.choosing_week, WeekCallback.filter())
async def handle_choose_week(
    callback: CallbackQuery,
    callback_data: WeekCallback,
    schedule_repo: ScheduleRepository,
    state: FSMContext,
) -> None:
    await callback.answer()
    schedule = schedule_repo.load()
    days = [day for day in schedule.keys() if day != "ВОСКРЕСЕНЬЕ"]
    await state.update_data(week=callback_data.week)
    await state.set_state(EditScheduleStates.choosing_day)
    await callback.message.edit_text(
        f"Неделя {callback_data.week}. Выберите день недели:",
        reply_markup=build_day_keyboard(callback_data.week, days),
    )


@router.callback_query(EditScheduleStates.choosing_day, DayCallback.filter())
async def handle_choose_day(
    callback: CallbackQuery,
    callback_data: DayCallback,
    schedule_repo: ScheduleRepository,
    state: FSMContext,
) -> None:
    await callback.answer()
    schedule = schedule_repo.load()
    days = [day for day in schedule.keys() if day != "ВОСКРЕСЕНЬЕ"]
    lessons = schedule.get(callback_data.day, [])
    matching = []
    for index, lesson in enumerate(lessons):
        weeks = lesson.get("weeks", [])
        if callback_data.week in weeks:
            caption = f"{len(matching) + 1}. {lesson['time']} — {lesson['subject']}"
            group = lesson.get("group")
            if group:
                caption += f" ({group})"
            matching.append((index, caption))

    if not matching:
        await callback.message.edit_text(
            (
                f"На {pretty_day_name(callback_data.day)} {callback_data.week}-й недели "
                "нет занятий. Выберите другой день."
            ),
            reply_markup=build_day_keyboard(callback_data.week, days),
        )
        return

    await state.update_data(day=callback_data.day, week=callback_data.week)
    await state.set_state(EditScheduleStates.choosing_event)

    lines = [
        (
            f"Неделя {callback_data.week}, {pretty_day_name(callback_data.day)}. "
            "Выберите занятие для изменения:"
        )
    ]
    lines.extend(caption for _, caption in matching)
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=build_event_keyboard(
            callback_data.week, callback_data.day, matching
        ),
    )


@router.callback_query(EditScheduleStates.choosing_event, EventCallback.filter())
async def handle_choose_event(
    callback: CallbackQuery,
    callback_data: EventCallback,
    schedule_repo: ScheduleRepository,
    state: FSMContext,
) -> None:
    await callback.answer()
    schedule = schedule_repo.load()
    lessons = schedule.get(callback_data.day, [])
    if callback_data.index >= len(lessons):
        await callback.message.answer("Занятие не найдено. Попробуйте снова.")
        return

    lesson = lessons[callback_data.index]
    await state.update_data(
        day=callback_data.day,
        event_index=callback_data.index,
        week=callback_data.week,
    )
    await state.set_state(EditScheduleStates.choosing_field)

    description_lines = [
        f"Неделя {callback_data.week}, {pretty_day_name(callback_data.day)}",
        f"{lesson['time']} — {lesson['subject']}",
    ]
    group = lesson.get("group")
    if group:
        description_lines[-1] += f" ({group})"
    teacher = lesson.get("teacher")
    room = lesson.get("room")
    if room or teacher:
        details = []
        if room:
            details.append(f"ауд. {room}")
        if teacher:
            details.append(teacher)
        description_lines.append(", ".join(details))
    description_lines.append(f"Недели: {format_weeks(lesson.get('weeks', []))}")
    description_lines.append("Выберите поле для изменения:")

    await callback.message.edit_text(
        "\n".join(description_lines),
        reply_markup=build_field_keyboard(callback_data.day, callback_data.index),
    )


@router.callback_query(EditScheduleStates.choosing_field, FieldCallback.filter())
async def handle_choose_field(
    callback: CallbackQuery,
    callback_data: FieldCallback,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.update_data(field=callback_data.field)
    await state.set_state(EditScheduleStates.entering_value)

    if callback_data.field == "weeks":
        prompt = (
            "Введите недели через запятую или диапазоны (например, 1-5,7,9). "
            "Отправьте '-' чтобы очистить список недель."
        )
    else:
        prompt = (
            "Введите новое значение. Отправьте '-' чтобы очистить поле."  # noqa: B950
        )

    await callback.message.edit_reply_markup()
    await callback.message.answer(prompt)


@router.message(EditScheduleStates.entering_value)
async def handle_new_value(
    message: Message,
    schedule_repo: ScheduleRepository,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    day = data.get("day")
    index = data.get("event_index")
    field = data.get("field")
    week = data.get("week")

    if day is None or index is None or field is None:
        await state.clear()
        await message.answer("Не удалось определить контекст редактирования.")
        return

    raw_value = message.text or ""
    raw_value = raw_value.strip()

    if field == "weeks":
        if raw_value == "-":
            new_value: Any = []
        else:
            try:
                new_value = parse_weeks(raw_value, min_week=1, max_week=30)
            except ValueError as exc:
                await message.answer(f"Ошибка: {exc}. Попробуйте снова.")
                return
    else:
        new_value = "" if raw_value == "-" else raw_value

    schedule = schedule_repo.load()
    lessons = schedule.get(day, [])
    if index >= len(lessons):
        await message.answer("Занятие не найдено. Попробуйте начать редактирование заново.")
        await state.clear()
        return

    lessons[index][field] = new_value
    schedule_repo.save(schedule)

    await state.set_state(EditScheduleStates.choosing_field)
    await message.answer("Изменения сохранены.")

    lesson = lessons[index]
    summary_lines = [
        f"Неделя {week}, {pretty_day_name(day)}",
        f"{lesson['time']} — {lesson['subject']}",
        f"Недели: {format_weeks(lesson.get('weeks', []))}",
        "Выберите поле для дальнейших изменений или отправьте /cancel.",
    ]
    group = lesson.get("group")
    if group:
        summary_lines[1] += f" ({group})"
    details = []
    room = lesson.get("room")
    if room:
        details.append(f"ауд. {room}")
    teacher = lesson.get("teacher")
    if teacher:
        details.append(teacher)
    if details:
        summary_lines.insert(2, ", ".join(details))

    await message.answer(
        "\n".join(summary_lines),
        reply_markup=build_field_keyboard(day, index),
    )


__all__ = ["router"]
