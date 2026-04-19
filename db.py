import asyncio
import json
import random
import sqlite3
from pathlib import Path
from typing import Any

from data import ANIME_DATA


class AnimeDB:
    def __init__(self, db_path: str = "anime.db") -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    async def init(self) -> None:
        await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS anime (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title_ru TEXT NOT NULL,
                    title_en TEXT NOT NULL,
                    description TEXT NOT NULL,
                    genres TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    rating REAL NOT NULL,
                    watch_urls TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER NOT NULL,
                    anime_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, anime_id),
                    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS anime_fts USING fts5(
                    title_ru,
                    title_en,
                    description,
                    genres,
                    content='anime',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                );

                CREATE TRIGGER IF NOT EXISTS anime_ai AFTER INSERT ON anime BEGIN
                    INSERT INTO anime_fts(rowid, title_ru, title_en, description, genres)
                    VALUES (new.id, new.title_ru, new.title_en, new.description, new.genres);
                END;

                CREATE TRIGGER IF NOT EXISTS anime_ad AFTER DELETE ON anime BEGIN
                    INSERT INTO anime_fts(anime_fts, rowid, title_ru, title_en, description, genres)
                    VALUES ('delete', old.id, old.title_ru, old.title_en, old.description, old.genres);
                END;

                CREATE TRIGGER IF NOT EXISTS anime_au AFTER UPDATE ON anime BEGIN
                    INSERT INTO anime_fts(anime_fts, rowid, title_ru, title_en, description, genres)
                    VALUES ('delete', old.id, old.title_ru, old.title_en, old.description, old.genres);
                    INSERT INTO anime_fts(rowid, title_ru, title_en, description, genres)
                    VALUES (new.id, new.title_ru, new.title_en, new.description, new.genres);
                END;
                """
            )

            columns = {row["name"] for row in conn.execute("PRAGMA table_info(anime)").fetchall()}
            if "watch_urls" not in columns:
                conn.execute("ALTER TABLE anime ADD COLUMN watch_urls TEXT NOT NULL DEFAULT ''")

            count = conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
            if count == 0:
                for item in ANIME_DATA:
                    self._add_anime_sync(
                        conn=conn,
                        name_ru=item["name_ru"],
                        name_en=item["name_en"],
                        year=item["year"],
                        description=item["description"],
                        genres=item["genres"],
                        watch_urls=item.get("watch_urls", ""),
                        rating=item.get("rating", 8.0),
                    )
            conn.commit()

    async def add_anime(
        self,
        name_ru: str,
        name_en: str,
        year: int,
        description: str,
        genres: str,
        watch_urls: str | dict[str, str] | None = None,
        rating: float = 8.0,
    ) -> bool:
        return await asyncio.to_thread(
            self._add_anime_detached_sync,
            name_ru,
            name_en,
            year,
            description,
            genres,
            watch_urls,
            rating,
        )

    def _add_anime_detached_sync(
        self,
        name_ru: str,
        name_en: str,
        year: int,
        description: str,
        genres: str,
        watch_urls: str | dict[str, str] | None,
        rating: float,
    ) -> bool:
        with self._connect() as conn:
            created = self._add_anime_sync(
                conn=conn,
                name_ru=name_ru,
                name_en=name_en,
                year=year,
                description=description,
                genres=genres,
                watch_urls=watch_urls,
                rating=rating,
            )
            conn.commit()
            return created

    def _add_anime_sync(
        self,
        conn: sqlite3.Connection,
        name_ru: str,
        name_en: str,
        year: int,
        description: str,
        genres: str,
        watch_urls: str | dict[str, str] | None,
        rating: float,
    ) -> bool:
        duplicate = conn.execute(
            "SELECT 1 FROM anime WHERE lower(title_en)=lower(?) OR lower(title_ru)=lower(?) LIMIT 1",
            (name_en.strip(), name_ru.strip()),
        ).fetchone()
        if duplicate:
            return False

        if isinstance(watch_urls, dict):
            watch_urls_payload = json.dumps(watch_urls, ensure_ascii=False)
        else:
            watch_urls_payload = watch_urls or ""

        conn.execute(
            """
            INSERT INTO anime(title_ru, title_en, description, genres, year, rating, watch_urls)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name_ru, name_en, description, genres, year, float(rating), watch_urls_payload),
        )
        return True

    async def get_anime(self, anime_id: int) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_anime_sync, anime_id)

    def _get_anime_sync(self, anime_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM anime WHERE id = ?", (anime_id,)).fetchone()
            return dict(row) if row else None

    async def get_all_anime(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_anime_sync)

    def _get_all_anime_sync(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM anime ORDER BY id").fetchall()
            return [dict(r) for r in rows]

    async def add_favorite(self, user_id: int, anime_id: int) -> bool:
        return await asyncio.to_thread(self._add_favorite_sync, user_id, anime_id)

    def _add_favorite_sync(self, user_id: int, anime_id: int) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO favorites(user_id, anime_id) VALUES (?, ?)",
                    (user_id, anime_id),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    async def get_favorites(self, user_id: int) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_favorites_sync, user_id)

    def _get_favorites_sync(self, user_id: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*
                FROM favorites f
                JOIN anime a ON a.id = f.anime_id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
                """,
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    async def get_top(self, limit: int = 10) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_top_sync, limit)

    def _get_top_sync(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM anime ORDER BY rating DESC, year DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    async def get_random(self) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._get_random_sync)

    def _get_random_sync(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            ids = [r[0] for r in conn.execute("SELECT id FROM anime").fetchall()]
            if not ids:
                return None
            anime_id = random.choice(ids)
            row = conn.execute("SELECT * FROM anime WHERE id = ?", (anime_id,)).fetchone()
            return dict(row) if row else None

    async def search_fts(self, fts_query: str, limit: int = 20) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._search_fts_sync, fts_query, limit)

    def _search_fts_sync(self, fts_query: str, limit: int) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.*, bm25(anime_fts, 10.0, 8.0, 4.0, 3.0) AS rank
                FROM anime_fts
                JOIN anime a ON a.id = anime_fts.rowid
                WHERE anime_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    async def get_genres(self) -> list[str]:
        return await asyncio.to_thread(self._get_genres_sync)

    def _get_genres_sync(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT genres FROM anime").fetchall()
            genres = set()
            for row in rows:
                genres.update([g.strip() for g in row[0].split(",") if g.strip()])
            return sorted(genres)
