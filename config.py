"""Конфигурация приложения, загружаемая из .env."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Загружаем переменные окружения из .env (если файл существует).
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Типизированный контейнер настроек."""

    bot_token: str = os.getenv("BOT_TOKEN", "")
    db_name: str = os.getenv("DB_NAME", "anime.db")
    cache_size: int = int(os.getenv("CACHE_SIZE", "128"))


settings = Settings()
