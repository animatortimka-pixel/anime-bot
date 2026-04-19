from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

from data import MEMES, QUOTES, fill_data


class AnimeDB:
    def __init__(self, db_path: str = "anime.db") -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
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
                    episodes_data TEXT NOT NULL,
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
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, anime_id),
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ratings (
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                    rated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, anime_id),
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_anime_year ON anime(year);
                CREATE INDEX IF NOT EXISTS idx_anime_rating ON anime(rating DESC);
                CREATE INDEX IF NOT EXISTS idx_anime_views ON anime(views DESC);
                CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
                CREATE INDEX IF NOT EXISTS idx_ratings_anime ON ratings(anime_id);
                CREATE INDEX IF NOT EXISTS idx_history_user_date ON history(user_id, viewed_at DESC);

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

                CREATE TRIGGER IF NOT EXISTS anime_au AFTER UPDATE ON anime BEGIN
                    INSERT INTO anime_fts(anime_fts, rowid, name_ru, name_en, description, genres)
                    VALUES ('delete', old.id, old.name_ru, old.name_en, old.description, old.genres);
                    INSERT INTO anime_fts(rowid, name_ru, name_en, description, genres)
                    VALUES (new.id, new.name_ru, new.name_en, new.description, new.genres);
                END;

                CREATE TRIGGER IF NOT EXISTS anime_ad AFTER DELETE ON anime BEGIN
                    INSERT INTO anime_fts(anime_fts, rowid, name_ru, name_en, description, genres)
                    VALUES ('delete', old.id, old.name_ru, old.name_en, old.description, old.genres);
                END;
                """
            )

            if conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0] == 0:
                payload = []
                for item in fill_data():
                    payload.append(
                        {
                            **item,
                            "genres": ",".join(item["genres"]),
                            "watch_urls": json.dumps(item["watch_urls"], ensure_ascii=False),
                            "episodes_data": json.dumps(item["episodes_data"], ensure_ascii=False),
                            "views": 0,
                        }
                    )
                conn.executemany(
                    """
                    INSERT INTO anime(name_ru, name_en, year, description, genres, rating, episodes, watch_urls, episodes_data, views)
                    VALUES (:name_ru, :name_en, :year, :description, :genres, :rating, :episodes, :watch_urls, :episodes_data, :views)
                    """,
                    payload,
                )

            if conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0] == 0:
                conn.executemany("INSERT INTO quotes(text) VALUES (?)", [(q,) for q in QUOTES])

            if conn.execute("SELECT COUNT(*) FROM memes").fetchone()[0] == 0:
                conn.executemany("INSERT INTO memes(text) VALUES (?)", [(m,) for m in MEMES])

            conn.commit()

    def _row_to_anime(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        data = dict(row)
        data["genres"] = [x.strip() for x in data["genres"].split(",") if x.strip()]
        data["watch_urls"] = json.loads(data["watch_urls"])
        data["episodes_data"] = json.loads(data.get("episodes_data") or "[]")
        return data

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
            return self._row_to_anime(conn.execute("SELECT * FROM anime WHERE id=?", (anime_id,)).fetchone())

    async def get_all_anime(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_anime_sync)

    def _get_all_anime_sync(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM anime ORDER BY id").fetchall()
            return [self._row_to_anime(row) for row in rows if row]

    async def search_fts(self, query: str, limit: int = 80) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._search_fts_sync, query, limit)

    def _search_fts_sync(self, query: str, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, bm25(anime_fts, 12.0, 10.0, 4.0, 6.0) AS score
                FROM anime_fts
                JOIN anime a ON a.id = anime_fts.rowid
                WHERE anime_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            result = []
            for row in rows:
                anime = self._row_to_anime(row)
                if anime:
                    anime["bm25"] = row["score"]
                    result.append(anime)
            return result

    async def add_view(self, user_id: int, anime_id: int) -> None:
        await asyncio.to_thread(self._add_view_sync, user_id, anime_id)

    def _add_view_sync(self, user_id: int, anime_id: int) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO history(user_id, anime_id) VALUES (?, ?)", (user_id, anime_id))
            conn.execute("UPDATE anime SET views = views + 1 WHERE id=?", (anime_id,))
            conn.commit()

    async def toggle_favorite(self, user_id: int, anime_id: int) -> bool:
        return await asyncio.to_thread(self._toggle_favorite_sync, user_id, anime_id)

    def _toggle_favorite_sync(self, user_id: int, anime_id: int) -> bool:
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM favorites WHERE user_id=? AND anime_id=?",
                (user_id, anime_id),
            ).fetchone()
            if exists:
                conn.execute("DELETE FROM favorites WHERE user_id=? AND anime_id=?", (user_id, anime_id))
                conn.commit()
                return False
            conn.execute("INSERT INTO favorites(user_id, anime_id) VALUES (?, ?)", (user_id, anime_id))
            conn.commit()
            return True

    async def set_rating(self, user_id: int, anime_id: int, value: int) -> None:
        await asyncio.to_thread(self._set_rating_sync, user_id, anime_id, value)

    def _set_rating_sync(self, user_id: int, anime_id: int, value: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ratings(user_id, anime_id, rating) VALUES (?, ?, ?)
                ON CONFLICT(user_id, anime_id)
                DO UPDATE SET rating=excluded.rating, rated_at=CURRENT_TIMESTAMP
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
                SELECT a.*
                FROM favorites f
                JOIN anime a ON a.id = f.anime_id
                WHERE f.user_id=?
                ORDER BY f.created_at DESC
                """,
                (user_id,),
            ).fetchall()
            return [self._row_to_anime(row) for row in rows if row]

    async def get_user_history(self, user_id: int, limit: int = 100) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_user_history_sync, user_id, limit)

    def _get_user_history_sync(self, user_id: int, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*
                FROM history h
                JOIN anime a ON a.id = h.anime_id
                WHERE h.user_id=?
                ORDER BY h.viewed_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
            return [self._row_to_anime(row) for row in rows if row]

    async def get_popular(self, limit: int = 30) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_popular_sync, limit)

    def _get_popular_sync(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM anime ORDER BY views DESC, rating DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_anime(row) for row in rows if row]

    async def get_average_rating(self, anime_id: int) -> float:
        return await asyncio.to_thread(self._get_average_rating_sync, anime_id)

    def _get_average_rating_sync(self, anime_id: int) -> float:
        with self._connect() as conn:
            row = conn.execute("SELECT AVG(rating) AS avg_rating FROM ratings WHERE anime_id=?", (anime_id,)).fetchone()
            return round(float(row["avg_rating"]), 2) if row and row["avg_rating"] else 0.0

    async def get_genres(self) -> list[str]:
        rows = await self.get_all_anime()
        return sorted({genre for anime in rows for genre in anime["genres"]})

    async def get_random_anime(self) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_random_anime_sync)

    def _get_random_anime_sync(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            return self._row_to_anime(conn.execute("SELECT * FROM anime ORDER BY RANDOM() LIMIT 1").fetchone())

    async def get_random_quote(self) -> str:
        return await asyncio.to_thread(self._get_random_text_sync, "quotes")

    async def get_random_meme(self) -> str:
        return await asyncio.to_thread(self._get_random_text_sync, "memes")

    def _get_random_text_sync(self, table: str) -> str:
        with self._connect() as conn:
            row = conn.execute(f"SELECT text FROM {table} ORDER BY RANDOM() LIMIT 1").fetchone()
            return row["text"] if row else "Пока пусто"
