from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class Config:
    """Basic application configuration.

    Values are read from environment variables with sane defaults for development.
    """

    bot_token: str
    admin_chat_id: int
    database_url: str = "sqlite+aiosqlite:///./bot.db"

    @classmethod
    def load(cls) -> "Config":
        token = os.getenv("BOT_TOKEN")
        admin = int(os.getenv("ADMIN_CHAT_ID", "0"))
        db = os.getenv("DATABASE_URL", cls.database_url)
        if not token:
            raise RuntimeError("BOT_TOKEN environment variable not set")
        if not admin:
            raise RuntimeError("ADMIN_CHAT_ID environment variable not set")
        return cls(bot_token=token, admin_chat_id=admin, database_url=db)
