from __future__ import annotations

import asyncio
import logging
import os
import signal

from bot import create_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _configure_uvloop() -> None:
    try:
        import uvloop  # type: ignore

        uvloop.install()
    except Exception:
        logger.info("uvloop недоступен, используется стандартный asyncio loop")


def _resolve_token() -> str:
    return os.getenv("BOT_TOKEN", "").strip() or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


async def _run() -> None:
    token = _resolve_token()
    if not token:
        raise RuntimeError("Set BOT_TOKEN environment variable")

    app = create_bot(token, db_path="anime.db")
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    await app.initialize()
    await app.start()
    if app.updater:
        await app.updater.start_polling(drop_pending_updates=True)

    await stop_event.wait()

    if app.updater:
        await app.updater.stop()
    await app.stop()
    await app.shutdown()


def main() -> None:
    _configure_uvloop()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
