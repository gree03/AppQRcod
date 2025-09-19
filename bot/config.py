from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

CONFIG_FILE_NAME = "config.txt"


@dataclass(frozen=True)
class Settings:
    bot_token: str
    schedule_path: Path
    users_path: Path
    timezone: ZoneInfo
    daily_push_hour: int = 7
    daily_push_minute: int = 0


def _load_bot_token(config_path: Path) -> str:
    if not config_path.exists():
        raise RuntimeError(
            f"Файл {CONFIG_FILE_NAME} с токеном бота не найден. Создайте его в корне проекта."
        )

    token: str | None = None
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            if key.strip().lower() in {"bot_token", "token"}:
                token = value.strip().strip("\"'")
                break
        else:
            token = line.strip("\"'")
            break

    if not token:
        raise RuntimeError(
            f"Не найден токен бота в файле {CONFIG_FILE_NAME}. Укажите его в формате BOT_TOKEN=..."
        )

    return token


@lru_cache
def get_settings() -> Settings:
    """Load application settings using ``config.txt`` and optional environment overrides."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    token = _load_bot_token(base_dir / CONFIG_FILE_NAME)

    tz_name = os.environ.get("BOT_TIMEZONE", "Asia/Yekaterinburg")
    try:
        timezone = ZoneInfo(tz_name)
    except Exception as exc:  # pragma: no cover - fallback logging
        logging.getLogger(__name__).warning(
            "Cannot load timezone %s (%s). Falling back to UTC.", tz_name, exc
        )
        timezone = ZoneInfo("UTC")

    return Settings(
        bot_token=token,
        schedule_path=data_dir / "schedule.json",
        users_path=data_dir / "users.json",
        timezone=timezone,
    )


__all__ = ["CONFIG_FILE_NAME", "Settings", "get_settings"]
