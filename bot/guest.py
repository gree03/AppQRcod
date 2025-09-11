"""Guest questionnaire handlers."""

from __future__ import annotations

from dataclasses import dataclass

import sqlite3

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.db import (
    add_user,
    get_user,
    set_full_name,
    set_acceptance,
    set_cuisine,
    set_allergies,
    set_companions,
    set_atmosphere,
    set_alcohol,
    use_invite_token,
)


@dataclass
class Question:
    id: int
    text: str


QUESTIONS = [
    Question(1, "Имя и фамилия (для идентификации)."),
    Question(2, "Принимаете ли вы приглашение на 26.06.26 (Да / Нет)"),
    Question(3, "Предпочтения по кухне (Европейская/Азиатская/Кавказская/Без разницы)"),
    Question(4, "Аллергии или ограничения (Арахис/Лактоза/Глютен/Рыба/морепродукты/Нет)"),
    Question(5, "Хотели бы сидеть рядом с друзьями/коллегами? Укажите @username через запятую или 'Нет'"),
    Question(6, "Предпочтения по атмосфере (Тихий столик/Более общительный столик/Без разницы)"),
    Question(7, "Будете ли вы спиртное? (Да / Нет)"),
]


class Questionnaire(StatesGroup):
    full_name = State()
    attending = State()
    cuisine = State()
    allergies = State()
    companions = State()
    atmosphere = State()
    alcohol = State()


router = Router()

ADMIN_CHAT_ID = 0


def _user_label(message: Message) -> str:
    user = message.from_user
    return user.full_name or (user.username and f"@{user.username}") or str(user.id)


@router.message(Command("start"))
async def start(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    # Notify admins about any /start call with add option
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Добавить человека",
                    callback_data=f"whitelist:{message.from_user.id}",
                )
            ]
        ]
    )
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"/start от {message.from_user.id} @{message.from_user.username or ''}",
        reply_markup=kb,
    )

    user = get_user(conn, message.from_user.id)
    if not user or not user.invited:
        parts = message.text.split(maxsplit=1)
        token = parts[1] if len(parts) > 1 else None
        if token and use_invite_token(conn, token):
            if not user:
                add_user(conn, message.from_user.id, message.from_user.username, True)
            else:
                conn.execute(
                    "UPDATE users SET invited = 1 WHERE telegram_id = ?",
                    (message.from_user.id,),
                )
                conn.commit()
            user = get_user(conn, message.from_user.id)
        else:
            await message.answer("Доступ по приглашению")
            return
    if user.onboarding_complete:
        await message.answer("Анкета уже пройдена")
        return
    await message.bot.send_message(
        ADMIN_CHAT_ID, f"{_user_label(message)} начал анкету"
    )
    await message.answer(QUESTIONS[0].text)
    await state.set_state(Questionnaire.full_name)


@router.message(Questionnaire.full_name)
async def answer_full_name(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    set_full_name(conn, message.from_user.id, message.text.strip())
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"{_user_label(message)}: {QUESTIONS[0].text} -> {message.text.strip()}",
    )
    await message.answer(QUESTIONS[1].text)
    await state.set_state(Questionnaire.attending)


@router.message(Questionnaire.attending)
async def answer_attending(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    text = message.text.strip().lower()
    if text not in {"да", "нет"}:
        await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'")
        return
    set_acceptance(conn, message.from_user.id, text == "да")
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"{_user_label(message)}: {QUESTIONS[1].text} -> {message.text.strip()}",
    )
    await message.answer(QUESTIONS[2].text)
    await state.set_state(Questionnaire.cuisine)


CUISINE_OPTIONS = {"европейская", "азиатская", "кавказская", "без разницы"}


@router.message(Questionnaire.cuisine)
async def answer_cuisine(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    text = message.text.strip().lower()
    if text not in CUISINE_OPTIONS:
        await message.answer("Выберите один из вариантов: Европейская, Азиатская, Кавказская, Без разницы")
        return
    set_cuisine(conn, message.from_user.id, message.text.strip())
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"{_user_label(message)}: {QUESTIONS[2].text} -> {message.text.strip()}",
    )
    await message.answer(QUESTIONS[3].text)
    await state.set_state(Questionnaire.allergies)


ALLERGY_OPTIONS = {"арахис", "лактоза", "глютен", "рыба", "рыба/морепродукты", "морепродукты", "нет"}


@router.message(Questionnaire.allergies)
async def answer_allergies(
    message: Message, state: FSMContext, conn: sqlite3.Connection
) -> None:
    parts = [p.strip().lower() for p in message.text.split(',')]
    if not all(p in ALLERGY_OPTIONS for p in parts):
        await message.answer(
            "Пожалуйста, укажите варианты через запятую из списка: "
            "Арахис, Лактоза, Глютен, Рыба/морепродукты, Нет"
        )
        return
    set_allergies(
        conn, message.from_user.id, ",".join(p.strip() for p in message.text.split(','))
    )
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"{_user_label(message)}: {QUESTIONS[3].text} -> {message.text.strip()}",
    )
    await message.answer(QUESTIONS[4].text)
    await state.set_state(Questionnaire.companions)


@router.message(Questionnaire.companions)
async def answer_companions(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    set_companions(conn, message.from_user.id, message.text.strip())
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"{_user_label(message)}: {QUESTIONS[4].text} -> {message.text.strip()}",
    )
    await message.answer(QUESTIONS[5].text)
    await state.set_state(Questionnaire.atmosphere)


ATMOSPHERE_OPTIONS = {"тихий столик", "более общительный столик", "без разницы"}


@router.message(Questionnaire.atmosphere)
async def answer_atmosphere(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    text = message.text.strip().lower()
    if text not in ATMOSPHERE_OPTIONS:
        await message.answer("Выберите: Тихий столик, Более общительный столик, Без разницы")
        return
    set_atmosphere(conn, message.from_user.id, message.text.strip())
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"{_user_label(message)}: {QUESTIONS[5].text} -> {message.text.strip()}",
    )
    await message.answer(QUESTIONS[6].text)
    await state.set_state(Questionnaire.alcohol)


@router.message(Questionnaire.alcohol)
async def answer_alcohol(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    text = message.text.strip().lower()
    if text not in {"да", "нет"}:
        await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'")
        return
    set_alcohol(conn, message.from_user.id, text == "да")
    conn.execute(
        "UPDATE users SET onboarding_complete = 1 WHERE telegram_id = ?",
        (message.from_user.id,),
    )
    conn.commit()
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"{_user_label(message)}: {QUESTIONS[6].text} -> {message.text.strip()}",
    )
    await message.bot.send_message(
        ADMIN_CHAT_ID, f"{_user_label(message)} завершил анкету"
    )
    await message.answer("Спасибо! Анкета завершена.")
    await state.clear()
