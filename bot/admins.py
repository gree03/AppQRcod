"""Admin chat command handlers."""

from __future__ import annotations

from typing import List
import sqlite3

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    ForceReply,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db import (
    invite_users,
    add_invite_tokens,
    get_invited_user_ids,
    list_tables,
    add_table,
    update_table_label,
    update_table_capacity,
    delete_table,
    get_table,
    get_table_guests,
    get_unassigned_guests,
    assign_user_to_table,
    list_guests,
    get_user,
    uninvite_user,
    unassign_user,
)
from bot.guest import QUESTIONS


router = Router()

ADMIN_CHAT_ID = 0


class TableEdit(StatesGroup):
    waiting_label = State()


def _is_admin(message: Message) -> bool:
    return message.chat.id == ADMIN_CHAT_ID


async def show_guests(msg_or_cb, conn: sqlite3.Connection) -> None:
    guests = list_guests(conn)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(g["name"]), callback_data=f"guest:{g['telegram_id']}")]
            for g in guests
        ]
    )
    text = "Гости:" if guests else "Список гостей пуст"
    if isinstance(msg_or_cb, CallbackQuery):
        await msg_or_cb.message.edit_text(text, reply_markup=kb)
        await msg_or_cb.answer()
    else:
        await msg_or_cb.answer(text, reply_markup=kb)


async def show_tables(msg_or_cb, conn: sqlite3.Connection) -> None:
    tables = list_tables(conn)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{t['table_no']} {t['label'] or ''}", callback_data=f"table:{t['table_no']}")]  # type: ignore[index]
            for t in tables
        ]
    )
    kb.inline_keyboard.append([InlineKeyboardButton(text="+", callback_data="table:add")])
    text = "Столы:" if tables else "Список столов пуст"
    if isinstance(msg_or_cb, CallbackQuery):
        await msg_or_cb.message.edit_text(text, reply_markup=kb)
        await msg_or_cb.answer()
    else:
        await msg_or_cb.answer(text, reply_markup=kb)


async def show_table_menu(msg_or_cb, table_no: int, conn: sqlite3.Connection) -> None:
    table = get_table(conn, table_no)
    if not table:
        return
    text = f"Стол {table['table_no']} {table['label'] or ''} (мест: {table['capacity']})"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить название", callback_data=f"table:{table_no}:label")],
            [InlineKeyboardButton(text="Гости", callback_data=f"table:{table_no}:guests")],
            [InlineKeyboardButton(text="Удалить стол", callback_data=f"table:{table_no}:del")],
            [InlineKeyboardButton(text="Назад", callback_data="tables")],
        ]
    )
    if isinstance(msg_or_cb, CallbackQuery):
        await msg_or_cb.message.edit_text(text, reply_markup=kb)
        await msg_or_cb.answer()
    else:
        await msg_or_cb.answer(text, reply_markup=kb)


async def show_guest_list(callback: CallbackQuery, table_no: int, conn: sqlite3.Connection) -> None:
    table = get_table(conn, table_no)
    if not table:
        await callback.answer()
        return
    guests = get_table_guests(conn, table_no)
    kb_rows: List[List[InlineKeyboardButton]] = []
    for row in guests:
        kb_rows.append(
            [InlineKeyboardButton(text=str(row["name"]), callback_data=f"rmguest:{table_no}:{row['telegram_id']}")]
        )
    for _ in range(table["capacity"] - len(guests)):
        kb_rows.append([InlineKeyboardButton(text="Пусто", callback_data=f"delseat:{table_no}")])
    kb_rows.append([InlineKeyboardButton(text="Добавить гостя", callback_data=f"addguest:{table_no}")])
    kb_rows.append([InlineKeyboardButton(text="+", callback_data=f"addseat:{table_no}")])
    kb_rows.append([InlineKeyboardButton(text="Назад", callback_data=f"table:{table_no}")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    await callback.message.edit_text("Гости стола", reply_markup=kb)
    await callback.answer()


async def show_available_guests(callback: CallbackQuery, table_no: int, conn: sqlite3.Connection) -> None:
    guests = get_unassigned_guests(conn)
    kb_rows = [
        [InlineKeyboardButton(text=str(g["name"]), callback_data=f"assign:{table_no}:{g['telegram_id']}")]
        for g in guests
    ]
    kb_rows.append([InlineKeyboardButton(text="Назад", callback_data=f"table:{table_no}:guests")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    text = "Выберите гостя" if guests else "Нет доступных гостей"
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not _is_admin(message):
        return
    await message.answer(
        "/help — список команд.\n"
        "/status — сводка.\n"
        "/invite_add <id...> — пополнение белого списка.\n"
        "/guest — список гостей.\n"
        "/questions — показать текущую анкету.\n"
        "/set_tables — настроить количество столов.\n"
        "/broadcast <текст> — рассылка гостям.\n"
        "/set_rules — правила группировки.\n"
        "/assign — выполнить распределение.\n"
        "/assign_dry — сухой прогон.\n"
        "/notify_tables — оповестить гостей о столах.\n"
        "/export — выгрузка реестра.\n"
        "/reset_assignments — сброс назначений.\n"
        "/ban <id> — отозвать доступ.\n"
        "/unban <id> — вернуть доступ."
    )


@router.message(Command("status"))
async def cmd_status(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    completed = conn.execute(
        "SELECT COUNT(*) FROM users WHERE onboarding_complete = 1"
    ).fetchone()[0]
    assigned = conn.execute(
        "SELECT COUNT(*) FROM users WHERE table_assignment IS NOT NULL"
    ).fetchone()[0]
    percent = (completed / total * 100) if total else 0
    tables_loaded = (
        conn.execute("SELECT COUNT(*) FROM tables").fetchone()[0] > 0
    )
    unassigned = total - assigned
    await message.answer(
        "Всего гостей: {}\nОнбординг завершили: {}\nАнкет завершили: {} ({:.0f}%)\n"
        "Назначены за столы: {} / {}\nСтолов настроено: {}".format(
            total,
            completed,
            completed,
            percent,
            assigned,
            unassigned,
            "да" if tables_loaded else "нет",
        )
    )


@router.message(Command("invite_add"))
async def cmd_invite_add(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    parts = message.text.split()[1:]
    ids: List[int] = []
    count = 0
    for part in parts:
        if part.startswith("count="):
            try:
                count = int(part.split("=", 1)[1])
            except ValueError:
                pass
        else:
            try:
                ids.append(int(part))
            except ValueError:
                continue
    lines: List[str] = []
    if ids:
        invite_users(conn, ids)
        lines.append(f"IDs добавлены: {len(ids)}")
    if count:
        tokens = add_invite_tokens(conn, count)
        lines.append("Токены: " + " ".join(tokens))
    if not lines:
        await message.answer("Использование: /invite_add <id...> [count=N]")
    else:
        await message.answer("\n".join(lines))


@router.message(Command("guest"))
async def cmd_guest(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    await show_guests(message, conn)


@router.callback_query(F.data == "guestlist")
async def cb_guestlist(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    await show_guests(callback, conn)


@router.callback_query(F.data.startswith("guest:"))
async def cb_guest(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    uid = int(callback.data.split(":")[1])
    user = get_user(conn, uid)
    if not user:
        await callback.answer()
        return
    name = user.full_name or user.username or str(uid)
    table = user.table if user.table is not None else "не назначен"
    lines = [name, f"Стол: {table}"]
    if user.onboarding_complete:
        lines.extend(
            [
                f"Приглашение: {'Да' if user.accepted else 'Нет'}",
                f"Кухня: {user.cuisine or '-'}",
                f"Аллергии: {user.allergies or '-'}",
                f"Компаньоны: {user.companions or '-'}",
                f"Атмосфера: {user.atmosphere or '-'}",
                f"Спиртное: {'Да' if user.alcohol else 'Нет'}",
            ]
        )
    else:
        lines.append("Анкета: не пройдена")
    text = "\n".join(lines)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Удалить из приглашённых", callback_data=f"guestdel:{uid}")],
            [InlineKeyboardButton(text="Назад", callback_data="guestlist")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("guestdel:"))
async def cb_guestdel(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    uid = int(callback.data.split(":")[1])
    user = get_user(conn, uid)
    name = user.full_name or user.username or str(uid)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f"guestdelconf:{uid}")],
            [InlineKeyboardButton(text="Нет", callback_data=f"guest:{uid}")],
        ]
    )
    await callback.message.edit_text(f"Удалить {name} из приглашённых?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("guestdelconf:"))
async def cb_guestdelconf(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    uid = int(callback.data.split(":")[1])
    uninvite_user(conn, uid)
    await callback.answer("Гость удалён")
    await show_guests(callback, conn)


@router.message(Command("questions"))
async def cmd_questions(message: Message) -> None:
    if not _is_admin(message):
        return
    text = "\n".join(f"{q.id}. {q.text}" for q in QUESTIONS)
    await message.answer(text)


@router.message(Command("set_tables"))
async def cmd_set_tables(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    await show_tables(message, conn)


@router.callback_query(F.data == "tables")
async def cb_tables(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    await show_tables(callback, conn)


@router.callback_query(F.data.startswith("table:"))
async def cb_table(callback: CallbackQuery, state: FSMContext, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    parts = callback.data.split(":")
    if parts[1] == "add":
        table_no = add_table(conn)
        await show_table_menu(callback, table_no, conn)
        return
    table_no = int(parts[1])
    if len(parts) == 2:
        await show_table_menu(callback, table_no, conn)
    elif len(parts) == 3:
        action = parts[2]
        if action == "label":
            await state.update_data(table_no=table_no)
            await state.set_state(TableEdit.waiting_label)
            await callback.message.answer(
                "Новое название стола:", reply_markup=ForceReply()
            )
            await callback.answer()
        elif action == "guests":
            await show_guest_list(callback, table_no, conn)
        elif action == "del":
            try:
                delete_table(conn, table_no)
                await callback.answer("Стол удалён")
                await show_tables(callback, conn)
            except ValueError:
                await callback.answer("Нельзя удалить: есть гости", show_alert=True)


@router.callback_query(F.data.startswith("addguest:"))
async def cb_addguest(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    table_no = int(callback.data.split(":")[1])
    table = get_table(conn, table_no)
    guests = get_table_guests(conn, table_no)
    if len(guests) >= table["capacity"]:
        await callback.answer("Нет свободных мест", show_alert=True)
        return
    await show_available_guests(callback, table_no, conn)


@router.callback_query(F.data.startswith("addseat:"))
async def cb_addseat(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    table_no = int(callback.data.split(":")[1])
    table = get_table(conn, table_no)
    update_table_capacity(conn, table_no, table["capacity"] + 1)
    await callback.answer("Место добавлено")
    await show_guest_list(callback, table_no, conn)


@router.callback_query(F.data.startswith("delseat:"))
async def cb_delseat(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    table_no = int(callback.data.split(":")[1])
    table = get_table(conn, table_no)
    try:
        update_table_capacity(conn, table_no, table["capacity"] - 1)
        await callback.answer("Место удалено")
    except ValueError:
        await callback.answer("Нельзя удалить: есть гости", show_alert=True)
    await show_guest_list(callback, table_no, conn)


@router.callback_query(F.data.startswith("assign:"))
async def cb_assign(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    _, table_no, uid = callback.data.split(":")
    assign_user_to_table(conn, int(uid), int(table_no))
    await callback.answer("Гость назначен")
    await show_guest_list(callback, int(table_no), conn)


@router.callback_query(F.data.startswith("rmguest:"))
async def cb_rmguest(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    _, table_no, uid = callback.data.split(":")
    user = get_user(conn, int(uid))
    name = user.full_name or user.username or str(uid)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить", callback_data=f"rmguest_confirm:{table_no}:{uid}"
                )
            ],
            [InlineKeyboardButton(text="Отмена", callback_data=f"table:{table_no}:guests")],
        ]
    )
    await callback.message.edit_text(f"Удалить {name} со стола?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("rmguest_confirm:"))
async def cb_rmguest_confirm(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    _, table_no, uid = callback.data.split(":")
    unassign_user(conn, int(uid))
    await callback.answer("Гость удалён")
    await show_guest_list(callback, int(table_no), conn)


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(TableEdit.waiting_label)
async def set_table_label(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    data = await state.get_data()
    table_no = data.get("table_no")
    update_table_label(conn, table_no, message.text.strip())
    await message.answer("Название обновлено")
    await show_table_menu(message, table_no, conn)
    await state.clear()




@router.message(Command("set_rules"))
async def cmd_set_rules(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("assign"))
async def cmd_assign(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("assign_dry"))
async def cmd_assign_dry(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("notify_tables"))
async def cmd_notify_tables(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("reset_assignments"))
async def cmd_reset_assignments(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("ban"))
async def cmd_ban(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("unban"))
async def cmd_unban(message: Message) -> None:
    if _is_admin(message):
        await message.answer("Команда пока не реализована")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Нужно указать текст")
        return
    text = parts[1]
    for uid in get_invited_user_ids(conn):
        try:
            await message.bot.send_message(uid, text)
        except Exception:
            continue
    await message.answer("Рассылка отправлена")

