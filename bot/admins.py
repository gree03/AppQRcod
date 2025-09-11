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
from aiogram.fsm.storage.base import StorageKey

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
    get_assigned_users,
    assign_user_to_table,
    list_guests,
    get_user,
    uninvite_user,
    unassign_user,
)
from bot.guest import QUESTIONS, Questionnaire


router = Router()

ADMIN_CHAT_ID = 0


class TableEdit(StatesGroup):
    waiting_label = State()
    waiting_capacity = State()


class NotifyTables(StatesGroup):
    waiting_datetime = State()
    waiting_comment = State()
    confirm = State()


def _is_admin(message: Message) -> bool:
    return message.chat.id == ADMIN_CHAT_ID


@router.callback_query(F.data.startswith("whitelist:"))
async def cb_whitelist(
    callback: CallbackQuery,
    conn: sqlite3.Connection,
    state: FSMContext,
) -> None:
    if callback.message.chat.id != ADMIN_CHAT_ID:
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    invite_users(conn, [uid])
    await callback.message.edit_text(f"Добавлен пользователь {uid}")
    await callback.answer("ok")

    user_ctx = FSMContext(
        state.storage, key=StorageKey(bot_id=callback.bot.id, chat_id=uid, user_id=uid)
    )
    if await user_ctx.get_state() == Questionnaire.awaiting_invite.state:
        await callback.bot.send_message(
            uid,
            "Приносим извинения, изначально вас не было в списке. Продолжим анкету.",
        )
        await user_ctx.set_state(Questionnaire.attending)
        await callback.bot.send_message(uid, QUESTIONS[1].text)


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
            [
                InlineKeyboardButton(
                    text=f"{t['table_no']} ({t['capacity']}) {t['label'] or ''}",
                    callback_data=f"table:{t['table_no']}",
                )
            ]
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
            [InlineKeyboardButton(text="Изменить вместимость", callback_data=f"table:{table_no}:capacity")],
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
    occupied = {row["seat"]: row for row in guests}
    kb_rows: List[List[InlineKeyboardButton]] = []
    for seat in range(1, table["capacity"] + 1):
        if seat in occupied:
            name = occupied[seat]["name"]
            kb_rows.append(
                [InlineKeyboardButton(text=f"{seat}. {name}", callback_data=f"rmguest:{table_no}:{seat}")]
            )
        else:
            kb_rows.append(
                [InlineKeyboardButton(text=f"{seat}. Пусто", callback_data=f"addguest:{table_no}:{seat}")]
            )
    kb_rows.append([InlineKeyboardButton(text="Назад", callback_data=f"table:{table_no}")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    await callback.message.edit_text(
        f"Стол {table_no}: {len(guests)}/{table['capacity']} мест",
        reply_markup=kb,
    )
    await callback.answer()


async def show_available_guests(
    callback: CallbackQuery, table_no: int, seat: int, conn: sqlite3.Connection
) -> None:
    guests = get_unassigned_guests(conn)
    kb_rows = [
        [
            InlineKeyboardButton(
                text=str(g["name"]),
                callback_data=f"assign:{table_no}:{seat}:{g['telegram_id']}",
            )
        ]
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
        elif action == "capacity":
            await state.update_data(table_no=table_no)
            await state.set_state(TableEdit.waiting_capacity)
            await callback.message.answer(
                "Новая вместимость стола:", reply_markup=ForceReply()
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
    _, table_no, seat = callback.data.split(":")
    table_no = int(table_no)
    seat = int(seat)
    cur = conn.execute(
        "SELECT 1 FROM users WHERE table_assignment = ? AND seat = ?",
        (table_no, seat),
    )
    if cur.fetchone():
        await callback.answer("Место занято", show_alert=True)
        return
    await show_available_guests(callback, table_no, seat, conn)


@router.callback_query(F.data.startswith("assign:"))
async def cb_assign(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    _, table_no, seat, uid = callback.data.split(":")
    assign_user_to_table(conn, int(uid), int(table_no), int(seat))
    await callback.answer("Гость назначен")
    await show_guest_list(callback, int(table_no), conn)


@router.callback_query(F.data.startswith("rmguest:"))
async def cb_rmguest(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    _, table_no, seat = callback.data.split(":")
    row = conn.execute(
        "SELECT telegram_id, COALESCE(full_name, username, telegram_id) AS name "
        "FROM users WHERE table_assignment = ? AND seat = ?",
        (int(table_no), int(seat)),
    ).fetchone()
    if not row:
        await callback.answer()
        return
    uid = row["telegram_id"]
    name = row["name"]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить", callback_data=f"rmguest_confirm:{table_no}:{seat}"
                )
            ],
            [InlineKeyboardButton(text="Отмена", callback_data=f"table:{table_no}:guests")],
        ]
    )
    await callback.message.edit_text(
        f"Удалить {name} с места {seat}?", reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rmguest_confirm:"))
async def cb_rmguest_confirm(callback: CallbackQuery, conn: sqlite3.Connection) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    _, table_no, seat = callback.data.split(":")
    row = conn.execute(
        "SELECT telegram_id FROM users WHERE table_assignment = ? AND seat = ?",
        (int(table_no), int(seat)),
    ).fetchone()
    if row:
        unassign_user(conn, row["telegram_id"])
        await callback.answer("Гость удалён")
    else:
        await callback.answer()
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


@router.message(TableEdit.waiting_capacity)
async def set_table_capacity(message: Message, state: FSMContext, conn: sqlite3.Connection) -> None:
    if not _is_admin(message):
        return
    data = await state.get_data()
    table_no = data.get("table_no")
    try:
        capacity = int(message.text.strip())
        if capacity <= 0:
            raise ValueError
        update_table_capacity(conn, table_no, capacity)
        await message.answer("Вместимость обновлена")
        await show_table_menu(message, table_no, conn)
        await state.clear()
    except ValueError:
        await message.answer("Введите положительное число")




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
async def cmd_notify_tables(message: Message, state: FSMContext) -> None:
    if not _is_admin(message):
        return
    await state.set_state(NotifyTables.waiting_datetime)
    await message.answer("Дата и время мероприятия:", reply_markup=ForceReply())


@router.message(NotifyTables.waiting_datetime)
async def notify_tables_datetime(message: Message, state: FSMContext) -> None:
    if not _is_admin(message):
        return
    await state.update_data(datetime=message.text.strip())
    await state.set_state(NotifyTables.waiting_comment)
    await message.answer(
        "Комментарий для гостей (или '-' если нет):",
        reply_markup=ForceReply(),
    )


@router.message(NotifyTables.waiting_comment)
async def notify_tables_comment(
    message: Message, state: FSMContext, conn: sqlite3.Connection
) -> None:
    if not _is_admin(message):
        return
    await state.update_data(comment=message.text.strip())
    data = await state.get_data()
    dt = data.get("datetime", "")
    comment = data.get("comment", "")
    rows = get_assigned_users(conn)
    summary = "\n".join(
        f"{r['name']} — стол {r['table_assignment']}" for r in rows
    )
    if summary:
        await message.answer("Гости и столы:\n" + summary)
    else:
        await message.answer("Нет гостей для оповещения")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="notify_confirm:yes")],
            [InlineKeyboardButton(text="Нет", callback_data="notify_confirm:no")],
        ]
    )
    await message.answer(
        f"Отправить уведомление гостям?\nВремя и дата: {dt}\nКомментарий: {comment}",
        reply_markup=kb,
    )
    await state.set_state(NotifyTables.confirm)


@router.callback_query(F.data.startswith("notify_confirm:"))
async def cb_notify_confirm(
    callback: CallbackQuery, state: FSMContext, conn: sqlite3.Connection
) -> None:
    if not _is_admin(callback.message):
        await callback.answer()
        return
    action = callback.data.split(":")[1]
    data = await state.get_data()
    if action == "yes":
        dt = data.get("datetime", "")
        comment = data.get("comment", "")
        rows = get_assigned_users(conn)
        lines = []
        for row in rows:
            uid = row["telegram_id"]
            table_no = row["table_assignment"]
            text = f"Ваш стол: {table_no}\nВремя и дата: {dt}"
            if comment and comment != "-":
                text += f"\n{comment}"
            try:
                await callback.bot.send_message(uid, text)
            except Exception:
                continue
            lines.append(f"{row['name']} — стол {table_no}")
        summary = "\n".join(lines) if lines else "Нет гостей для оповещения"
        await callback.message.edit_text(
            f"Уведомления отправлены\n{summary}"
        )
        await state.clear()
        await callback.answer()
    else:
        await state.clear()
        await state.set_state(NotifyTables.waiting_datetime)
        await callback.message.answer(
            "Дата и время мероприятия:", reply_markup=ForceReply()
        )
        await callback.answer()


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

