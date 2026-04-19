from __future__ import annotations

import logging
import os

from bot import create_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable")

    app = create_bot(token, db_path="anime.db")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
