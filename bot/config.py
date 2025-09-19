from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

WEEK_SOURCE_URL = (
    "https://www.bsau.ru/obrazovanie/raspisanie/?FAKULTET=1257&NAPR=48&KURS=3&LEVEL_EDUCATION=165&FORM_EDUCATION=169"
)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    week_source_url: str
    schedule_path: Path
    users_path: Path
    timezone: ZoneInfo
    daily_push_hour: int = 7
    daily_push_minute: int = 0


@lru_cache
def get_settings() -> Settings:
    """Load application settings from environment variables."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("Environment variable BOT_TOKEN is required to start the bot.")

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
        week_source_url=WEEK_SOURCE_URL,
        schedule_path=data_dir / "schedule.json",
        users_path=data_dir / "users.json",
        timezone=timezone,
    )


__all__ = ["Settings", "get_settings", "WEEK_SOURCE_URL"]
