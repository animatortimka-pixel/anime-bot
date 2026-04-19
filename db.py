from __future__ import annotations

import asyncio
import json
import logging
import random
import sqlite3
from pathlib import Path
from typing import Any

from data import ANIME_DATA, MEMES, QUOTES

logger = logging.getLogger(__name__)


class AnimeDB:
    def __init__(self, db_path: str = "anime.db") -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    async def init(self) -> None:
        await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS anime (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_ru TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    genres TEXT NOT NULL,
                    rating REAL NOT NULL,
                    episodes INTEGER NOT NULL,
                    watch_urls TEXT NOT NULL,
                    views INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
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
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    rated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, anime_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS history (
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS anime_fts USING fts5(
                    name_ru,
                    name_en,
                    description,
                    genres,
                    content='anime',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                );

                CREATE TRIGGER IF NOT EXISTS anime_ai AFTER INSERT ON anime BEGIN
                    INSERT INTO anime_fts(rowid, name_ru, name_en, description, genres)
                    VALUES (new.id, new.name_ru, new.name_en, new.description, new.genres);
                END;

                CREATE TRIGGER IF NOT EXISTS anime_ad AFTER DELETE ON anime BEGIN
                    INSERT INTO anime_fts(anime_fts, rowid, name_ru, name_en, description, genres)
                    VALUES ('delete', old.id, old.name_ru, old.name_en, old.description, old.genres);
                END;

                CREATE TRIGGER IF NOT EXISTS anime_au AFTER UPDATE ON anime BEGIN
                    INSERT INTO anime_fts(anime_fts, rowid, name_ru, name_en, description, genres)
                    VALUES ('delete', old.id, old.name_ru, old.name_en, old.description, old.genres);
                    INSERT INTO anime_fts(rowid, name_ru, name_en, description, genres)
                    VALUES (new.id, new.name_ru, new.name_en, new.description, new.genres);
                END;

                CREATE INDEX IF NOT EXISTS idx_anime_year ON anime(year);
                CREATE INDEX IF NOT EXISTS idx_anime_rating ON anime(rating DESC);
                CREATE INDEX IF NOT EXISTS idx_anime_views ON anime(views DESC);
                CREATE INDEX IF NOT EXISTS idx_fav_user ON favorites(user_id);
                CREATE INDEX IF NOT EXISTS idx_rating_anime ON ratings(anime_id);
                CREATE INDEX IF NOT EXISTS idx_history_user_date ON history(user_id, viewed_at DESC);
                """
            )
            if conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0] == 0:
                conn.executemany(
                    """
                    INSERT INTO anime(name_ru, name_en, year, description, genres, rating, episodes, watch_urls, views)
                    VALUES (:name_ru,:name_en,:year,:description,:genres,:rating,:episodes,:watch_urls,:views)
                    """,
                    [
                        {
                            **item,
                            "genres": ",".join(item["genres"]),
                            "watch_urls": json.dumps(item["watch_urls"], ensure_ascii=False),
                        }
                        for item in ANIME_DATA
                    ],
                )
            if conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0] == 0:
                conn.executemany("INSERT INTO quotes(text) VALUES (?)", [(q,) for q in QUOTES])
            if conn.execute("SELECT COUNT(*) FROM memes").fetchone()[0] == 0:
                conn.executemany("INSERT INTO memes(text) VALUES (?)", [(m,) for m in MEMES])
            conn.commit()
            logger.info("Database initialized")

    def _row_to_anime(self, row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        item["genres"] = [x.strip() for x in item["genres"].split(",") if x.strip()]
        item["watch_urls"] = json.loads(item["watch_urls"] or "[]")
        return item

    async def ensure_user(self, user_id: int, username: str | None) -> None:
        await asyncio.to_thread(self._ensure_user_sync, user_id, username)

    def _ensure_user_sync(self, user_id: int, username: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users(user_id, username) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
                """,
                (user_id, username),
            )
            conn.commit()

    async def get_anime(self, anime_id: int) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_anime_sync, anime_id)

    def _get_anime_sync(self, anime_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM anime WHERE id=?", (anime_id,)).fetchone()
            return self._row_to_anime(row) if row else None

    async def get_all_anime(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_anime_sync)

    def _get_all_anime_sync(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM anime ORDER BY id").fetchall()
            return [self._row_to_anime(r) for r in rows]

    async def search_fts(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._search_fts_sync, query, limit)

    def _search_fts_sync(self, query: str, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, bm25(anime_fts, 12.0, 10.0, 3.0, 7.0) AS bm
                FROM anime_fts
                JOIN anime a ON a.id=anime_fts.rowid
                WHERE anime_fts MATCH ?
                ORDER BY bm
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            result = []
            for row in rows:
                anime = self._row_to_anime(row)
                anime["bm25"] = row["bm"]
                result.append(anime)
            return result

    async def add_view(self, user_id: int, anime_id: int) -> None:
        await asyncio.to_thread(self._add_view_sync, user_id, anime_id)

    def _add_view_sync(self, user_id: int, anime_id: int) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO history(user_id, anime_id) VALUES (?,?)", (user_id, anime_id))
            conn.execute("UPDATE anime SET views = views + 1 WHERE id=?", (anime_id,))
            conn.commit()

    async def toggle_favorite(self, user_id: int, anime_id: int) -> bool:
        return await asyncio.to_thread(self._toggle_favorite_sync, user_id, anime_id)

    def _toggle_favorite_sync(self, user_id: int, anime_id: int) -> bool:
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM favorites WHERE user_id=? AND anime_id=?", (user_id, anime_id)
            ).fetchone()
            if exists:
                conn.execute("DELETE FROM favorites WHERE user_id=? AND anime_id=?", (user_id, anime_id))
                conn.commit()
                return False
            conn.execute("INSERT INTO favorites(user_id, anime_id) VALUES (?,?)", (user_id, anime_id))
            conn.commit()
            return True

    async def set_rating(self, user_id: int, anime_id: int, value: int) -> None:
        await asyncio.to_thread(self._set_rating_sync, user_id, anime_id, value)

    def _set_rating_sync(self, user_id: int, anime_id: int, value: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ratings(user_id, anime_id, rating) VALUES (?, ?, ?)
                ON CONFLICT(user_id, anime_id) DO UPDATE SET rating=excluded.rating, rated_at=CURRENT_TIMESTAMP
                """,
                (user_id, anime_id, value),
            )
            conn.commit()

    async def get_user_favorites(self, user_id: int) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_user_favorites_sync, user_id)

    def _get_user_favorites_sync(self, user_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.* FROM favorites f JOIN anime a ON a.id=f.anime_id
                WHERE f.user_id=? ORDER BY a.rating DESC, a.views DESC
                """,
                (user_id,),
            ).fetchall()
            return [self._row_to_anime(r) for r in rows]

    async def get_user_history(self, user_id: int, limit: int = 100) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_user_history_sync, user_id, limit)

    def _get_user_history_sync(self, user_id: int, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.* FROM history h JOIN anime a ON a.id=h.anime_id
                WHERE h.user_id=? ORDER BY h.viewed_at DESC LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
            return [self._row_to_anime(r) for r in rows]

    async def get_popular(self, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_popular_sync, limit)

    def _get_popular_sync(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, COALESCE(AVG(r.rating), 0) AS user_rating
                FROM anime a
                LEFT JOIN ratings r ON r.anime_id=a.id
                GROUP BY a.id
                ORDER BY a.views DESC, user_rating DESC, a.rating DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            out = []
            for r in rows:
                anime = self._row_to_anime(r)
                anime["user_rating"] = r["user_rating"]
                out.append(anime)
            return out

    async def get_top_rated(self, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_top_rated_sync, limit)

    def _get_top_rated_sync(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM anime ORDER BY rating DESC, views DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_anime(r) for r in rows]

    async def get_genres(self) -> list[str]:
        animes = await self.get_all_anime()
        genres = sorted({g for a in animes for g in a["genres"]})
        return genres

    async def get_average_rating(self, anime_id: int) -> float:
        return await asyncio.to_thread(self._get_average_rating_sync, anime_id)

    def _get_average_rating_sync(self, anime_id: int) -> float:
        with self._connect() as conn:
            row = conn.execute("SELECT AVG(rating) as avg_rating FROM ratings WHERE anime_id=?", (anime_id,)).fetchone()
            return round(float(row["avg_rating"]), 2) if row and row["avg_rating"] else 0.0

    async def get_random_anime(self) -> dict[str, Any] | None:
        all_items = await self.get_all_anime()
        return random.choice(all_items) if all_items else None

    async def get_random_quote(self) -> str:
        return await asyncio.to_thread(self._get_random_text_sync, "quotes")

    async def get_random_meme(self) -> str:
        return await asyncio.to_thread(self._get_random_text_sync, "memes")

    def _get_random_text_sync(self, table: str) -> str:
        with self._connect() as conn:
            row = conn.execute(f"SELECT text FROM {table} ORDER BY RANDOM() LIMIT 1").fetchone()
            return row["text"] if row else "Пока пусто."
