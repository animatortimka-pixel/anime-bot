from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

from data import fill_data


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
                    rating REAL NOT NULL DEFAULT 0,
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_anime_year ON anime(year);
                CREATE INDEX IF NOT EXISTS idx_anime_rating ON anime(rating DESC);
                CREATE INDEX IF NOT EXISTS idx_anime_views ON anime(views DESC);
                CREATE INDEX IF NOT EXISTS idx_favorites_user_created ON favorites(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_ratings_anime_user ON ratings(anime_id, user_id);

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
                seed = []
                for row in fill_data():
                    seed.append(
                        {
                            **row,
                            "genres": ",".join(row["genres"]),
                            "watch_urls": json.dumps(row["watch_urls"], ensure_ascii=False),
                            "episodes_data": json.dumps(row["episodes_data"], ensure_ascii=False),
                        }
                    )
                conn.executemany(
                    """
                    INSERT INTO anime(name_ru, name_en, year, description, genres, rating, episodes, watch_urls, episodes_data, views)
                    VALUES (:name_ru,:name_en,:year,:description,:genres,:rating,:episodes,:watch_urls,:episodes_data,:views)
                    """,
                    seed,
                )
                conn.commit()

    def _row_to_anime(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["genres"] = [x.strip() for x in item["genres"].split(",") if x.strip()]
        item["watch_urls"] = json.loads(item["watch_urls"])
        item["episodes_data"] = json.loads(item["episodes_data"])
        return item

    async def ensure_user(self, user_id: int, username: str | None) -> None:
        await asyncio.to_thread(self._ensure_user_sync, user_id, username)

    def _ensure_user_sync(self, user_id: int, username: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users(user_id, username) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username",
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
            rows = conn.execute("SELECT * FROM anime ORDER BY rating DESC, views DESC, id ASC").fetchall()
            return [self._row_to_anime(row) for row in rows if row is not None]

    async def get_popular(self, limit: int = 30) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_popular_sync, limit)

    def _get_popular_sync(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM anime ORDER BY views DESC, rating DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_anime(row) for row in rows if row is not None]

    async def get_random_anime(self) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_random_anime_sync)

    def _get_random_anime_sync(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            return self._row_to_anime(conn.execute("SELECT * FROM anime ORDER BY RANDOM() LIMIT 1").fetchone())

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
            return [self._row_to_anime(row) for row in rows if row is not None]

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

    async def set_rating(self, user_id: int, anime_id: int, rating_value: int) -> float:
        return await asyncio.to_thread(self._set_rating_sync, user_id, anime_id, rating_value)

    def _set_rating_sync(self, user_id: int, anime_id: int, rating_value: int) -> float:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ratings(user_id, anime_id, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, anime_id)
                DO UPDATE SET rating=excluded.rating, rated_at=CURRENT_TIMESTAMP
                """,
                (user_id, anime_id, rating_value),
            )
            row = conn.execute("SELECT AVG(rating) AS avg_rating FROM ratings WHERE anime_id=?", (anime_id,)).fetchone()
            avg_rating = float(row["avg_rating"]) if row and row["avg_rating"] is not None else 0.0
            conn.execute("UPDATE anime SET rating=? WHERE id=?", (round(avg_rating, 2), anime_id))
            conn.commit()
            return round(avg_rating, 2)

    async def add_view(self, user_id: int, anime_id: int) -> None:
        await asyncio.to_thread(self._add_view_sync, user_id, anime_id)

    def _add_view_sync(self, user_id: int, anime_id: int) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO history(user_id, anime_id) VALUES (?, ?)", (user_id, anime_id))
            conn.execute("UPDATE anime SET views = views + 1 WHERE id=?", (anime_id,))
            conn.commit()

    async def get_genres(self) -> list[str]:
        all_items = await self.get_all_anime()
        return sorted({genre for item in all_items for genre in item["genres"]})

    async def search_fts(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._search_fts_sync, query, limit)

    def _search_fts_sync(self, query: str, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, -bm25(anime_fts, 12.0, 10.0, 4.0, 6.0) AS rank_score
                FROM anime_fts
                JOIN anime a ON a.id = anime_fts.rowid
                WHERE anime_fts MATCH ?
                ORDER BY rank_score DESC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            out: list[dict[str, Any]] = []
            for row in rows:
                anime = self._row_to_anime(row)
                if anime is not None:
                    anime["rank"] = float(row["rank_score"])
                    out.append(anime)
            return out
