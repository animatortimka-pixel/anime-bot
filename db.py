"""Слой доступа к данным (SQLite) без Telegram-логики."""

from __future__ import annotations

import asyncio
import random
import sqlite3
from pathlib import Path
from typing import Any

from config import settings

BASE_ANIME: list[dict[str, Any]] = [
    {
        "name_ru": "Атака титанов",
        "name_en": "Attack on Titan",
        "description": "Человечество сражается за выживание против гигантских титанов.",
        "genres": "Экшен,Драма,Фэнтези",
        "year": 2013,
        "rating": 9.1,
        "type": "TV",
    },
    {
        "name_ru": "Тетрадь смерти",
        "name_en": "Death Note",
        "description": "Школьник находит тетрадь, убивающую любого, чьё имя в неё вписано.",
        "genres": "Триллер,Мистика,Психология",
        "year": 2006,
        "rating": 8.9,
        "type": "TV",
    },
    {
        "name_ru": "Наруто",
        "name_en": "Naruto",
        "description": "История юного ниндзя, который мечтает стать Хокаге.",
        "genres": "Экшен,Приключения,Сёнэн",
        "year": 2002,
        "rating": 8.3,
        "type": "TV",
    },
    {
        "name_ru": "Ван-Пис",
        "name_en": "One Piece",
        "description": "Пираты Соломенной Шляпы ищут легендарное сокровище One Piece.",
        "genres": "Приключения,Комедия,Сёнэн",
        "year": 1999,
        "rating": 9.0,
        "type": "TV",
    },
    {
        "name_ru": "Клинок, рассекающий демонов",
        "name_en": "Demon Slayer",
        "description": "Юный мечник становится охотником на демонов ради спасения сестры.",
        "genres": "Экшен,Фэнтези,Историческое",
        "year": 2019,
        "rating": 8.7,
        "type": "TV",
    },
]


class AnimeDB:
    """Асинхронная обёртка над SQLite через asyncio.to_thread."""

    def __init__(self, db_name: str | None = None) -> None:
        self.db_path = Path(db_name or settings.db_name)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    async def init_db(self) -> None:
        await asyncio.to_thread(self._init_db_sync)

    def _init_db_sync(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS anime (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_ru TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    description TEXT NOT NULL,
                    genres TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    rating REAL NOT NULL,
                    type TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    reg_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, anime_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ratings (
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 10),
                    PRIMARY KEY (user_id, anime_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS history (
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    view_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_anime_name_ru ON anime(name_ru);
                CREATE INDEX IF NOT EXISTS idx_anime_name_en ON anime(name_en);
                CREATE INDEX IF NOT EXISTS idx_anime_year ON anime(year);
                CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
                CREATE INDEX IF NOT EXISTS idx_ratings_anime ON ratings(anime_id);
                CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id);
                """
            )

    async def init_sample_data(self) -> None:
        await asyncio.to_thread(self._init_sample_data_sync)

    def _init_sample_data_sync(self) -> None:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
            if total >= 150:
                return
            payload = list(BASE_ANIME)
            random.seed(42)
            genres_pool = [
                "Экшен,Приключения,Фэнтези",
                "Комедия,Школа,Романтика",
                "Триллер,Драма,Мистика",
                "Фантастика,Экшен,Киберпанк",
                "Повседневность,Драма,Комедия",
            ]
            types = ["TV", "Movie", "OVA", "ONA"]
            for i in range(145):
                payload.append(
                    {
                        "name_ru": f"Аниме-история #{i + 1}",
                        "name_en": f"Anime Story #{i + 1}",
                        "description": "История о героях, дружбе и преодолении сложностей в необычном мире.",
                        "genres": random.choice(genres_pool),
                        "year": random.randint(1995, 2026),
                        "rating": round(random.uniform(6.5, 9.5), 1),
                        "type": random.choice(types),
                    }
                )
            conn.executemany(
                """
                INSERT INTO anime (name_ru, name_en, description, genres, year, rating, type)
                VALUES (:name_ru, :name_en, :description, :genres, :year, :rating, :type)
                """,
                payload,
            )
            conn.commit()

    async def ensure_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> None:
        await asyncio.to_thread(
            self._ensure_user_sync,
            user_id,
            username,
            first_name,
            last_name,
        )

    def _ensure_user_sync(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name
                """,
                (user_id, username, first_name, last_name),
            )
            conn.commit()

    async def get_anime_by_id(self, anime_id: int) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_anime_by_id_sync, anime_id)

    def _get_anime_by_id_sync(self, anime_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM anime WHERE id = ?", (anime_id,)).fetchone()
            return dict(row) if row else None

    async def search_anime(self, query: str) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._search_anime_sync, query)

    def _search_anime_sync(self, query: str) -> list[dict[str, Any]]:
        like = f"%{query.strip()}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM anime
                WHERE name_ru LIKE ? OR name_en LIKE ? OR genres LIKE ?
                ORDER BY rating DESC, year DESC
                LIMIT 30
                """,
                (like, like, like),
            ).fetchall()
            return [dict(row) for row in rows]

    async def get_all_anime(self, limit: int, offset: int) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_anime_sync, limit, offset)

    def _get_all_anime_sync(self, limit: int, offset: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM anime ORDER BY id LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]

    async def get_similar_anime(self, anime_id: int) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_similar_anime_sync, anime_id)

    def _get_similar_anime_sync(self, anime_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            source = conn.execute("SELECT genres FROM anime WHERE id = ?", (anime_id,)).fetchone()
            if not source:
                return []
            main_genre = source["genres"].split(",")[0].strip()
            rows = conn.execute(
                """
                SELECT * FROM anime
                WHERE id != ? AND genres LIKE ?
                ORDER BY rating DESC
                LIMIT 3
                """,
                (anime_id, f"%{main_genre}%"),
            ).fetchall()
            return [dict(row) for row in rows]

    async def add_favorite(self, user_id: int, anime_id: int) -> bool:
        return await asyncio.to_thread(self._add_favorite_sync, user_id, anime_id)

    def _add_favorite_sync(self, user_id: int, anime_id: int) -> bool:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO favorites (user_id, anime_id) VALUES (?, ?)",
                (user_id, anime_id),
            )
            conn.commit()
            return conn.total_changes > 0

    async def remove_favorite(self, user_id: int, anime_id: int) -> bool:
        return await asyncio.to_thread(self._remove_favorite_sync, user_id, anime_id)

    def _remove_favorite_sync(self, user_id: int, anime_id: int) -> bool:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM favorites WHERE user_id = ? AND anime_id = ?",
                (user_id, anime_id),
            )
            conn.commit()
            return conn.total_changes > 0

    async def get_favorites(self, user_id: int) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_favorites_sync, user_id)

    def _get_favorites_sync(self, user_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.* FROM anime a
                JOIN favorites f ON f.anime_id = a.id
                WHERE f.user_id = ?
                ORDER BY a.rating DESC
                """,
                (user_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    async def add_rating(self, user_id: int, anime_id: int, rating: int) -> None:
        await asyncio.to_thread(self._add_rating_sync, user_id, anime_id, rating)

    def _add_rating_sync(self, user_id: int, anime_id: int, rating: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ratings (user_id, anime_id, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, anime_id) DO UPDATE SET rating = excluded.rating
                """,
                (user_id, anime_id, rating),
            )
            conn.commit()

    async def get_top_anime(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_top_anime_sync)

    def _get_top_anime_sync(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, COALESCE(AVG(r.rating), a.rating) AS avg_rating
                FROM anime a
                LEFT JOIN ratings r ON r.anime_id = a.id
                GROUP BY a.id
                ORDER BY avg_rating DESC
                LIMIT 10
                """
            ).fetchall()
            return [dict(row) for row in rows]

    async def add_to_history(self, user_id: int, anime_id: int) -> None:
        await asyncio.to_thread(self._add_to_history_sync, user_id, anime_id)

    def _add_to_history_sync(self, user_id: int, anime_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO history (user_id, anime_id) VALUES (?, ?)",
                (user_id, anime_id),
            )
            conn.commit()
