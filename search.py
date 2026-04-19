from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from db import AnimeDB

GENRE_MAP = {
    "экшен": "action",
    "боевик": "action",
    "драма": "drama",
    "романтика": "romance",
    "комедия": "comedy",
    "приключения": "adventure",
    "исекай": "isekai",
    "спорт": "sports",
    "меха": "mecha",
    "фэнтези": "fantasy",
    "психология": "psychological",
    "триллер": "thriller",
    "мистика": "mystery",
    "научная фантастика": "sci-fi",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


@lru_cache(maxsize=256)
def _tokenize(query: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[\w-]+", _norm(query)))


def _extract_filters(query: str) -> tuple[str, int | None, float | None, set[str]]:
    q = _norm(query)
    year_m = re.search(r"\b(19\d{2}|20\d{2})\b", q)
    year = int(year_m.group(1)) if year_m else None
    rating_m = re.search(r"(?:rating|рейтинг|оценка)\s*[:>=]*\s*(\d(?:\.\d)?)", q)
    min_rating = float(rating_m.group(1)) if rating_m else None

    genres = {en for ru, en in GENRE_MAP.items() if ru in q}

    q = re.sub(r"\b(19\d{2}|20\d{2})\b", " ", q)
    q = re.sub(r"(?:rating|рейтинг|оценка)\s*[:>=]*\s*(\d(?:\.\d)?)", " ", q)
    return _norm(q), year, min_rating, genres


def _build_fts(query: str) -> str:
    tokens = [t for t in _tokenize(query) if len(t) > 1]
    return " OR ".join(f"{t}*" for t in tokens) if tokens else "*"


def _score_item(item: dict[str, Any], query: str) -> float:
    q = _norm(query)
    ru = _norm(item["name_ru"])
    en = _norm(item["name_en"])
    desc = _norm(item["description"])

    if q == ru or q == en:
        return 200.0
    if ru.startswith(q) or en.startswith(q):
        return 120.0
    if q in ru or q in en:
        return 90.0
    if q in desc:
        return 60.0

    fuzzy = max(
        SequenceMatcher(None, q, ru).ratio(),
        SequenceMatcher(None, q, en).ratio(),
        SequenceMatcher(None, q, desc[:250]).ratio(),
    )
    return fuzzy * 50


async def smart_search(db: AnimeDB, query: str, limit: int = 12) -> list[dict[str, Any]]:
    clean_query, year, min_rating, genres = _extract_filters(query)
    all_items = await db.get_all_anime()

    fts_rows: list[dict[str, Any]] = []
    try:
        if clean_query:
            fts_rows = await db.search_fts(_build_fts(clean_query), limit=60)
    except Exception:
        fts_rows = []

    score_by_id: dict[int, float] = {}
    anime_by_id = {x["id"]: x for x in all_items}

    for row in fts_rows:
        score_by_id[row["id"]] = score_by_id.get(row["id"], 0) + max(0.0, 35.0 - abs(row.get("bm25", 0)))

    for anime in all_items:
        score_by_id[anime["id"]] = score_by_id.get(anime["id"], 0) + _score_item(anime, clean_query)

    ranked = []
    for anime_id, score in score_by_id.items():
        anime = anime_by_id[anime_id]
        if year and anime["year"] != year:
            continue
        if min_rating and float(anime["rating"]) < min_rating:
            continue
        if genres and not (set(anime["genres"]) & genres):
            continue
        ranked.append((score, anime))

    ranked.sort(key=lambda x: (x[0], x[1]["rating"], x[1]["views"]), reverse=True)
    return [x[1] for x in ranked[:limit]]
