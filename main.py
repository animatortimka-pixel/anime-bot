from __future__ import annotations

import logging
import os

from telegram.ext import Application

from db import AnimeDB
from handlers import setup_handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


async def post_init(app: Application) -> None:
    db: AnimeDB = app.bot_data["db"]
    await db.init()


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable")

    db = AnimeDB("anime.db")
    app = Application.builder().token(token).post_init(post_init).build()
    setup_handlers(app, db)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
