from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ScheduleData = Dict[str, List[Dict[str, Any]]]


def _default_schedule() -> ScheduleData:
    """Return the default schedule template used to populate the storage."""
    return {
        "ПОНЕДЕЛЬНИК": [
            {
                "time": "08:30–10:05",
                "subject": "Метрология, стандартизация и сертификация",
                "weeks": list(range(5, 16)),
                "teacher": "ст.преп. Масягутов Р.Ф.",
                "room": "273/3",
                "group": "1 подгруппа",
            },
            {
                "time": "08:30–10:05",
                "subject": "Электрические машины",
                "weeks": list(range(5, 16)),
                "teacher": "ст.преп. Фефелова С.В.",
                "room": "375/3",
                "group": "2 подгруппа",
            },
            {
                "time": "10:20–11:55",
                "subject": "Электрические машины",
                "weeks": list(range(5, 16)),
                "teacher": "ст.преп. Фефелова С.В.",
                "room": "375/3",
                "group": "1 подгруппа",
            },
            {
                "time": "10:20–11:55",
                "subject": "Метрология, стандартизация и сертификация",
                "weeks": list(range(5, 16)),
                "teacher": "ст.преп. Масягутов Р.Ф.",
                "room": "273/3",
                "group": "2 подгруппа",
            },
            {
                "time": "12:55–14:30",
                "subject": "Системный анализ",
                "weeks": [1, 3, 5],
                "teacher": "доц. Галиева Г.М.",
                "room": "Д/О",
            },
        ],
        "ВТОРНИК": [
            {
                "time": "08:30–10:05",
                "subject": "Метрология, стандартизация и сертификация",
                "weeks": list(range(2, 15, 2)),
                "teacher": "ст.преп. Масягутов Р.Ф.",
                "room": "273/3",
            },
            {
                "time": "10:20–11:55",
                "subject": "НИРС",
                "weeks": list(range(1, 17)),
                "teacher": "",
                "room": "",
            },
            {
                "time": "12:55–14:30",
                "subject": "Элективные дисциплины по физической культуре и спорту",
                "weeks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15],
                "teacher": "доц. Хабибуллин Р.М.",
                "room": "с/зал",
            },
            {
                "time": "14:45–16:20",
                "subject": "Психология и педагогика",
                "weeks": [1, 3, 5, 7, 9, 11],
                "teacher": "доц. Круль А.С.",
                "room": "Д/О",
            },
            {
                "time": "14:45–16:20",
                "subject": "Экономическая теория",
                "weeks": [2, 4, 6, 8, 10, 12],
                "teacher": "доц. Атажанова А.А.",
                "room": "Д/О",
            },
        ],
        "СРЕДА": [
            {
                "time": "08:30–10:05",
                "subject": "Метрология, стандартизация и сертификация",
                "weeks": list(range(1, 10)),
                "teacher": "ст.преп. Масягутов Р.Ф.",
                "room": "Д/О",
            },
            {
                "time": "10:20–11:55",
                "subject": "Электроника",
                "weeks": [2, 4, 6, 8, 10, 12],
                "teacher": "доц. Карпеев И.Р.",
                "room": "372/3",
            },
            {
                "time": "12:55–14:30",
                "subject": "Электроника",
                "weeks": [7, 9, 11, 13],
                "teacher": "доц. Карпеев И.Р.",
                "room": "372/3",
                "group": "1 подгруппа",
            },
            {
                "time": "12:55–14:30",
                "subject": "Электроника",
                "weeks": [8, 10, 12, 14],
                "teacher": "доц. Карпеев И.Р.",
                "room": "372/3",
                "group": "2 подгруппа",
            },
            {
                "time": "14:45–16:20",
                "subject": "Электроника",
                "weeks": [9, 11, 13],
                "teacher": "доц. Карпеев И.Р.",
                "room": "372/3",
                "group": "1 подгруппа",
            },
            {
                "time": "14:45–16:20",
                "subject": "Электроника",
                "weeks": [10, 12, 14],
                "teacher": "доц. Карпеев И.Р.",
                "room": "372/3",
                "group": "2 подгруппа",
            },
        ],
        "ЧЕТВЕРГ": [
            {
                "time": "08:30–10:05",
                "subject": "Электрические машины",
                "weeks": list(range(2, 17, 2)),
                "teacher": "доц. Акчурин С.В.",
                "room": "375/3",
            },
            {
                "time": "10:20–11:55",
                "subject": "Экономическая теория",
                "weeks": list(range(3, 13)),
                "teacher": "доц. Атажанова А.А.",
                "room": "100/1",
            },
            {
                "time": "12:55–14:30",
                "subject": "Электроника",
                "weeks": list(range(1, 10)),
                "teacher": "доц. Карпеев И.Р.",
                "room": "Д/О",
            },
            {
                "time": "14:45–16:20",
                "subject": "Единое время консультаций",
                "weeks": list(range(1, 17)),
                "teacher": "",
                "room": "",
            },
        ],
        "ПЯТНИЦА": [
            {
                "time": "08:30–10:05",
                "subject": "Системный анализ",
                "weeks": list(range(3, 10)),
                "teacher": "доц. Галиева Г.М.",
                "room": "416/1",
            },
            {
                "time": "10:20–11:55",
                "subject": "Психология и педагогика",
                "weeks": list(range(3, 13)),
                "teacher": "доц. Круль А.С.",
                "room": "202а/1",
            },
            {
                "time": "12:55–14:30",
                "subject": "Электрические машины",
                "weeks": list(range(1, 12)),
                "teacher": "доц. Акчурин С.В.",
                "room": "Д/О",
            },
        ],
        "СУББОТА": [
            {
                "time": "12:10–13:45",
                "subject": "Элективные дисциплины по физической культуре и спорту",
                "weeks": [w for w in range(1, 15) if w != 6],
                "teacher": "доц. Хабибуллин Р.М.",
                "room": "спортзал",
            },
        ],
    }


class ScheduleRepository:
    """Storage layer for working with schedule data."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self.save(_default_schedule())

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> ScheduleData:
        with self._path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def save(self, schedule: ScheduleData) -> None:
        with self._path.open("w", encoding="utf-8") as fp:
            json.dump(schedule, fp, ensure_ascii=False, indent=2)

    def list_days(self) -> Iterable[str]:
        return self.load().keys()

REMINDER_KEYS = ("morning", "evening")
SCOPE_CHAT = "chat"
SCOPE_USER = "user"
REMINDER_SCOPES = {SCOPE_CHAT, SCOPE_USER}


def _default_reminders(scope: str) -> Dict[str, bool]:
    """Return default reminder configuration for the given scope."""

    if scope == SCOPE_CHAT:
        # Chats (групповые беседы) получают рассылку по умолчанию.
        return {"morning": True, "evening": True}
    if scope == SCOPE_USER:
        # Для личных напоминаний значения отключены до явного включения.
        return {"morning": False, "evening": False}
    raise ValueError(f"Неизвестный тип напоминаний: {scope}")


class UserRepository:
    """JSON-based storage for chat and user reminder preferences."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._save_entries([])

    def _empty_entry(
        self,
        *,
        chat_id: int,
        scope: str,
        user_id: int | None = None,
    ) -> Dict[str, Any]:
        if scope not in REMINDER_SCOPES:
            raise ValueError(f"Неизвестный тип напоминаний: {scope}")

        entry: Dict[str, Any] = {
            "chat_id": int(chat_id),
            "scope": scope,
            "reminders": dict(_default_reminders(scope)),
        }

        if scope == SCOPE_USER:
            entry["user_id"] = int(user_id if user_id is not None else chat_id)

        return entry

    def _load_entries(self) -> List[Dict[str, Any]]:
        with self._path.open("r", encoding="utf-8") as fp:
            try:
                raw = json.load(fp)
            except json.JSONDecodeError:
                return []

        if not isinstance(raw, list):
            return []

        entries: List[Dict[str, Any]] = []
        for item in raw:
            if isinstance(item, int):
                scope = SCOPE_CHAT if item < 0 else SCOPE_USER
                entries.append(
                    self._empty_entry(chat_id=item, scope=scope, user_id=item if scope == SCOPE_USER else None)
                )
                continue

            if not isinstance(item, dict):
                continue

            chat_id = item.get("chat_id")
            try:
                chat_id_int = int(chat_id)
            except (TypeError, ValueError):
                continue

            raw_scope = item.get("scope") or item.get("type")
            if raw_scope in REMINDER_SCOPES:
                scope = raw_scope
            else:
                scope = SCOPE_CHAT if chat_id_int < 0 else SCOPE_USER

            user_id: int | None = None
            if scope == SCOPE_USER:
                stored_user_id = item.get("user_id")
                try:
                    user_id = int(stored_user_id) if stored_user_id is not None else chat_id_int
                except (TypeError, ValueError):
                    user_id = chat_id_int

            entry = self._empty_entry(chat_id=chat_id_int, scope=scope, user_id=user_id)

            reminders = item.get("reminders")
            if isinstance(reminders, dict):
                for key in entry["reminders"].keys():
                    if key in reminders:
                        entry["reminders"][key] = bool(reminders[key])

            entries.append(entry)

        unique: Dict[tuple[int, str, int | None], Dict[str, Any]] = {}
        for entry in entries:
            key = (
                entry["chat_id"],
                entry.get("scope", SCOPE_CHAT),
                entry.get("user_id") if entry.get("scope") == SCOPE_USER else None,
            )
            unique[key] = entry

        return list(unique.values())

    def _save_entries(self, entries: Iterable[Dict[str, Any]]) -> None:
        with self._path.open("w", encoding="utf-8") as fp:
            json.dump(list(entries), fp, ensure_ascii=False, indent=2)

    def _ensure_entry(
        self,
        *,
        chat_id: int,
        scope: str,
        user_id: int | None = None,
        entries: List[Dict[str, Any]] | None = None,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        chat_id = int(chat_id)
        if entries is None:
            entries = self._load_entries()

        target_user_id = int(user_id) if scope == SCOPE_USER and user_id is not None else (
            int(chat_id) if scope == SCOPE_USER else None
        )

        for entry in entries:
            if entry["chat_id"] != chat_id:
                continue
            if entry.get("scope", SCOPE_CHAT) != scope:
                continue
            if scope == SCOPE_USER and entry.get("user_id") != target_user_id:
                continue
            return entries, entry

        entry = self._empty_entry(chat_id=chat_id, scope=scope, user_id=target_user_id)
        entries.append(entry)
        return entries, entry

    def register_chat(self, chat_id: int) -> None:
        entries, _ = self._ensure_entry(chat_id=chat_id, scope=SCOPE_CHAT)
        self._save_entries(entries)

    def register_user(self, user_id: int) -> None:
        entries, _ = self._ensure_entry(chat_id=user_id, scope=SCOPE_USER, user_id=user_id)
        self._save_entries(entries)

    def add_user(self, chat_id: int) -> None:
        # Backwards compatibility: treat as registration of chat context.
        self.register_chat(chat_id)

    def list_users(self) -> List[int]:
        return [
            entry.get("user_id", entry["chat_id"])
            for entry in self._load_entries()
            if entry.get("scope", SCOPE_CHAT) == SCOPE_USER
        ]

    def get_reminders(
        self,
        chat_id: int,
        *,
        scope: str = SCOPE_CHAT,
        user_id: int | None = None,
    ) -> Dict[str, bool]:
        entries, entry = self._ensure_entry(chat_id=chat_id, scope=scope, user_id=user_id)
        self._save_entries(entries)
        return dict(entry["reminders"])

    def set_reminder(
        self,
        chat_id: int,
        kind: str,
        enabled: bool,
        *,
        scope: str = SCOPE_CHAT,
        user_id: int | None = None,
    ) -> Dict[str, bool]:
        if kind not in REMINDER_KEYS:
            raise KeyError(f"Неизвестный тип напоминания: {kind}")
        entries = self._load_entries()
        entries, entry = self._ensure_entry(
            chat_id=chat_id,
            scope=scope,
            user_id=user_id,
            entries=entries,
        )
        entry["reminders"][kind] = bool(enabled)
        self._save_entries(entries)
        return dict(entry["reminders"])

    def toggle_reminder(
        self,
        chat_id: int,
        kind: str,
        *,
        scope: str = SCOPE_CHAT,
        user_id: int | None = None,
    ) -> Dict[str, bool]:
        if kind not in REMINDER_KEYS:
            raise KeyError(f"Неизвестный тип напоминания: {kind}")
        entries = self._load_entries()
        entries, entry = self._ensure_entry(
            chat_id=chat_id,
            scope=scope,
            user_id=user_id,
            entries=entries,
        )
        entry["reminders"][kind] = not entry["reminders"].get(kind, False)
        self._save_entries(entries)
        return dict(entry["reminders"])

    def clear_reminders(
        self,
        chat_id: int,
        *,
        scope: str = SCOPE_CHAT,
        user_id: int | None = None,
    ) -> Dict[str, bool]:
        entries = self._load_entries()
        entries, entry = self._ensure_entry(
            chat_id=chat_id,
            scope=scope,
            user_id=user_id,
            entries=entries,
        )
        for key in entry["reminders"].keys():
            entry["reminders"][key] = False
        self._save_entries(entries)
        return dict(entry["reminders"])

    def list_reminder_chats(
        self,
        kind: str,
        *,
        scopes: Iterable[str] | None = None,
    ) -> List[int]:
        if kind not in REMINDER_KEYS:
            raise KeyError(f"Неизвестный тип напоминания: {kind}")

        allowed_scopes = set(scopes or REMINDER_SCOPES)
        entries = self._load_entries()
        result: List[int] = []
        for entry in entries:
            scope = entry.get("scope", SCOPE_CHAT)
            if scope not in allowed_scopes:
                continue
            if entry["reminders"].get(kind):
                result.append(entry["chat_id"])
        return result


__all__ = ["ScheduleRepository", "UserRepository", "ScheduleData"]
