from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from db import AnimeDB

GENRE_KEYWORDS = {
    "экшн": "action",
    "боевик": "action",
    "комедия": "comedy",
    "драма": "drama",
    "романтика": "romance",
    "фэнтези": "fantasy",
    "фантастика": "sci-fi",
    "триллер": "thriller",
    "мистика": "mystery",
    "история": "historical",
    "спорт": "sports",
    "исекай": "isekai",
}


@lru_cache(maxsize=128)
def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


@lru_cache(maxsize=128)
def _extract_filters(query: str) -> tuple[str, int | None, tuple[str, ...]]:
    q = _normalize(query)
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", q)
    year = int(year_match.group(1)) if year_match else None
    genres = tuple(sorted({v for k, v in GENRE_KEYWORDS.items() if k in q}))
    if year is not None:
        q = q.replace(str(year), " ")
    for alias in GENRE_KEYWORDS:
        q = q.replace(alias, " ")
    return _normalize(q), year, genres


@lru_cache(maxsize=128)
def _fts_query(clean: str) -> str:
    parts = re.findall(r"[\w-]+", clean)
    return " OR ".join(f"{part}*" for part in parts if len(part) > 1) or "*"


def _fuzzy_score(clean: str, anime: dict[str, Any]) -> float:
    if not clean:
        return 0.0
    name_ru = _normalize(anime["name_ru"])
    name_en = _normalize(anime["name_en"])
    description = _normalize(anime["description"])

    if clean == name_ru or clean == name_en:
        return 250.0
    if clean in name_ru or clean in name_en:
        return 120.0
    if clean in description:
        return 60.0

    return max(
        SequenceMatcher(None, clean, name_ru).ratio(),
        SequenceMatcher(None, clean, name_en).ratio(),
        SequenceMatcher(None, clean, description[:250]).ratio(),
    ) * 80.0


async def smart_search(db: AnimeDB, query: str, limit: int = 12) -> list[dict[str, Any]]:
    clean, year, genre_filters = _extract_filters(query)
    all_items = await db.get_all_anime()
    anime_by_id = {a["id"]: a for a in all_items}
    score_map = {a["id"]: 0.0 for a in all_items}

    if clean:
        try:
            fts_rows = await db.search_fts(_fts_query(clean), limit=80)
            for row in fts_rows:
                # bm25 rank уже рассчитан в db.search_fts как rank_score
                score_map[row["id"]] += 180.0 + float(row.get("rank", 0.0))
        except Exception:
            pass

    for anime in all_items:
        score_map[anime["id"]] += _fuzzy_score(clean, anime)

    ranked: list[tuple[float, dict[str, Any]]] = []
    for anime_id, score in score_map.items():
        anime = anime_by_id[anime_id]
        if year and anime["year"] != year:
            continue
        if genre_filters and not set(anime["genres"]).intersection(genre_filters):
            continue
        ranked.append((score + float(anime["rating"]) + anime["views"] / 10000.0, anime))

    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [anime for _, anime in ranked[:limit]]
