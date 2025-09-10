"""Guest questionnaire handlers."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.db import (
    get_user,
    set_full_name,
    set_acceptance,
    set_guests_count,
)


@dataclass
class Question:
    id: int
    text: str


QUESTIONS = [
    Question(1, "Имя и фамилия (для идентификации)."),
    Question(2, "Принимаете ли вы приглашение на 26.06.26 (Да / Нет)"),
    Question(3, "Сколько человек будет с вами?"),
]


class Questionnaire(StatesGroup):
    full_name = State()
    attending = State()
    guests = State()


router = Router()


@router.message(Command("start"))
async def start(message: Message, state: FSMContext) -> None:
    conn = message.bot["conn"]
    user = get_user(conn, message.from_user.id)
    if not user or not user.invited:
        await message.answer("Доступ по приглашению")
        return
    if user.onboarding_complete:
        await message.answer("Анкета уже пройдена")
        return
    await message.answer(QUESTIONS[0].text)
    await state.set_state(Questionnaire.full_name)


@router.message(Questionnaire.full_name)
async def answer_full_name(message: Message, state: FSMContext) -> None:
    conn = message.bot["conn"]
    set_full_name(conn, message.from_user.id, message.text.strip())
    await message.answer(QUESTIONS[1].text)
    await state.set_state(Questionnaire.attending)


@router.message(Questionnaire.attending)
async def answer_attending(message: Message, state: FSMContext) -> None:
    text = message.text.strip().lower()
    if text not in {"да", "нет"}:
        await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'")
        return
    conn = message.bot["conn"]
    set_acceptance(conn, message.from_user.id, text == "да")
    await message.answer(QUESTIONS[2].text)
    await state.set_state(Questionnaire.guests)


@router.message(Questionnaire.guests)
async def answer_guests(message: Message, state: FSMContext) -> None:
    try:
        count = int(message.text.strip())
    except ValueError:
        await message.answer("Введите число")
        return
    conn = message.bot["conn"]
    set_guests_count(conn, message.from_user.id, count)
    conn.execute(
        "UPDATE users SET onboarding_complete = 1 WHERE telegram_id = ?",
        (message.from_user.id,),
    )
    conn.commit()
    await message.answer("Спасибо! Анкета завершена.")
    await state.clear()

