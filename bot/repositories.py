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


class UserRepository:
    """Simple JSON-based storage for chat identifiers."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self.save([])

    def _load(self) -> List[int]:
        with self._path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        return list(data)

    def save(self, users: Iterable[int]) -> None:
        with self._path.open("w", encoding="utf-8") as fp:
            json.dump(list(dict.fromkeys(users)), fp, ensure_ascii=False, indent=2)

    def add_user(self, chat_id: int) -> None:
        users = self._load()
        if chat_id not in users:
            users.append(chat_id)
            self.save(users)

    def list_users(self) -> List[int]:
        return self._load()


__all__ = ["ScheduleRepository", "UserRepository", "ScheduleData"]
