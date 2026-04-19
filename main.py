import logging
import os

from telegram.ext import Application

from db import AnimeDB
from handlers import setup_handlers


logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)


async def post_init(app: Application) -> None:
    db: AnimeDB = app.bot_data["db"]
    await db.init()


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN env variable")

    db = AnimeDB("anime.db")

    app = Application.builder().token(token).post_init(post_init).build()
    setup_handlers(app, db)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
