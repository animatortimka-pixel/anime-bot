from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from db import AnimeDB

GENRE_ALIASES = {
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
    "фантастика": "sci-fi",
    "ужасы": "horror",
}


@lru_cache(maxsize=512)
def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


@lru_cache(maxsize=512)
def tokenize(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[\w-]+", normalize(text)))


@lru_cache(maxsize=512)
def parse_query(query: str) -> tuple[str, int | None, set[str]]:
    q = normalize(query)
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", q)
    year = int(year_match.group(1)) if year_match else None
    genres = {en for ru, en in GENRE_ALIASES.items() if ru in q}
    if year:
        q = q.replace(str(year), " ")
    for ru in GENRE_ALIASES:
        q = q.replace(ru, " ")
    return normalize(q), year, genres


@lru_cache(maxsize=512)
def build_fts_query(query: str) -> str:
    terms = [token for token in tokenize(query) if len(token) > 1]
    return " OR ".join(f"{term}*" for term in terms) if terms else "*"


def _similarity(query: str, anime: dict[str, Any]) -> float:
    q = normalize(query)
    if not q:
        return 0.0

    ru = normalize(anime["name_ru"])
    en = normalize(anime["name_en"])
    desc = normalize(anime["description"])
    genres = " ".join(anime["genres"])

    if q == ru or q == en:
        return 200.0
    if q in ru or q in en:
        return 120.0
    if q in genres:
        return 70.0
    if q in desc:
        return 50.0

    fuzzy = max(
        SequenceMatcher(None, q, ru).ratio(),
        SequenceMatcher(None, q, en).ratio(),
        SequenceMatcher(None, q, desc[:200]).ratio(),
    )
    return fuzzy * 65


async def smart_search(db: AnimeDB, query: str, limit: int = 12) -> list[dict[str, Any]]:
    text_query, year_filter, genre_filters = parse_query(query)
    items = await db.get_all_anime()

    scored: dict[int, float] = {item["id"]: 0.0 for item in items}
    by_id = {item["id"]: item for item in items}

    if text_query:
        try:
            fts_rows = await db.search_fts(build_fts_query(text_query), limit=80)
            for row in fts_rows:
                scored[row["id"]] += max(0.0, 30.0 - abs(float(row.get("bm25", 0.0))))
        except Exception:
            pass

    for item in items:
        scored[item["id"]] += _similarity(text_query, item)

    result: list[tuple[float, dict[str, Any]]] = []
    for anime_id, score in scored.items():
        anime = by_id[anime_id]
        if year_filter and anime["year"] != year_filter:
            continue
        if genre_filters and not set(anime["genres"]).intersection(genre_filters):
            continue
        result.append((score + anime["rating"], anime))

    result.sort(key=lambda x: (x[0], x[1]["views"]), reverse=True)
    return [anime for _, anime in result[:limit]]
