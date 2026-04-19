from __future__ import annotations

from telegram.ext import Application

from db import AnimeDB
from handlers import setup_handlers


async def post_init(app: Application) -> None:
    db: AnimeDB = app.bot_data["db"]
    await db.init()


def create_bot(token: str, db_path: str = "anime.db") -> Application:
    db = AnimeDB(db_path)
    app = Application.builder().token(token).post_init(post_init).build()
    setup_handlers(app, db)
    return app
