import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher

from bot import admins, guest, export
from bot.admins import router as admin_router
from bot.db import init_db
from bot.guest import router as guest_router
from bot.export import router as export_router


def load_config(path: str = "config.txt") -> dict:
    data: dict[str, str] = {}
    p = Path(path)
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


async def main() -> None:
    config = load_config()
    token = config.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not found in config.txt")

    db_path = config.get("DATABASE_PATH", "./bot.db")
    admin_chat = int(config.get("ADMIN_CHAT_ID", "0"))

    conn = init_db(db_path)

    bot = Bot(token)
    dp = Dispatcher()
    dp["conn"] = conn
    admins.ADMIN_CHAT_ID = admin_chat
    guest.ADMIN_CHAT_ID = admin_chat
    export.ADMIN_CHAT_ID = admin_chat
    dp.include_router(admin_router)
    dp.include_router(export_router)
    dp.include_router(guest_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
