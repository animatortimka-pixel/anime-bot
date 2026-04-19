import re
from difflib import SequenceMatcher
from typing import Any

from db import AnimeDB

GENRE_ALIASES = {
    "экшен": "action",
    "боевик": "action",
    "action": "action",
    "драма": "drama",
    "drama": "drama",
    "комедия": "comedy",
    "comedy": "comedy",
    "приключения": "adventure",
    "adventure": "adventure",
    "фэнтези": "fantasy",
    "fantasy": "fantasy",
    "романтика": "romance",
    "romance": "romance",
    "тайна": "mystery",
    "mystery": "mystery",
    "триллер": "thriller",
    "thriller": "thriller",
    "исекай": "isekai",
    "isekai": "isekai",
    "спорт": "sports",
    "sports": "sports",
    "школа": "school",
    "school": "school",
    "сверхъестественное": "supernatural",
    "supernatural": "supernatural",
    "психология": "psychological",
    "psychological": "psychological",
    "меха": "mecha",
    "mecha": "mecha",
    "научная фантастика": "sci-fi",
    "sci-fi": "sci-fi",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


def _extract_filters(query: str) -> tuple[str, int | None, float | None, set[str]]:
    query_l = _normalize(query)

    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", query_l)
    year = int(year_match.group(1)) if year_match else None

    rating_match = re.search(r"(?:rating|рейтинг|score|оценка)\s*[:>=]*\s*(\d(?:\.\d)?)", query_l)
    rating = float(rating_match.group(1)) if rating_match else None

    genres = {mapped for token, mapped in GENRE_ALIASES.items() if token in query_l}

    query_clean = re.sub(r"\b(19\d{2}|20\d{2})\b", " ", query_l)
    query_clean = re.sub(r"(?:rating|рейтинг|score|оценка)\s*[:>=]*\s*(\d(?:\.\d)?)", " ", query_clean)
    return _normalize(query_clean), year, rating, genres


def _build_fts_query(query: str) -> str:
    tokens = [t for t in re.findall(r"[\w-]+", query) if len(t) > 1]
    if not tokens:
        return "*"
    return " OR ".join([f"{t}*" for t in tokens])


def _composite_text(item: dict[str, Any]) -> str:
    return " ".join(
        [
            item["title_ru"],
            item["title_en"],
            item["description"],
            str(item["genres"]),
            str(item["year"]),
            str(item["rating"]),
        ]
    ).lower()


async def smart_search(db: AnimeDB, query: str, limit: int = 10) -> list[dict[str, Any]]:
    clean_query, year_filter, rating_filter, genre_filters = _extract_filters(query)
    fts_query = _build_fts_query(clean_query)

    try:
        fts_results = await db.search_fts(fts_query, limit=40)
    except Exception:
        fts_results = []

    all_rows = await db.get_all_anime()
    by_id = {r["id"]: r for r in all_rows}

    scored: list[tuple[float, dict[str, Any]]] = []
    for item in fts_results:
        score = 1.0 / (1.0 + abs(item.get("rank", 1.0)))
        scored.append((score, by_id[item["id"]]))

    if len(scored) < limit:
        needle = _normalize(clean_query)
        for item in all_rows:
            hay = _composite_text(item)
            ru_title = _normalize(item["title_ru"])
            en_title = _normalize(item["title_en"])
            genre_blob = _normalize(item["genres"].replace(",", " "))
            ratio = SequenceMatcher(None, needle, hay).ratio() if needle else 0.0
            if needle and (needle in ru_title or needle in en_title or needle in genre_blob):
                ratio = max(ratio, 0.72)
            if ratio >= 0.18:
                scored.append((ratio * 0.65, item))

    dedup: dict[int, tuple[float, dict[str, Any]]] = {}
    for score, item in scored:
        genres = {g.strip() for g in item["genres"].split(",")}

        if year_filter and item["year"] != year_filter:
            score *= 0.65
        if rating_filter and float(item["rating"]) < rating_filter:
            score *= 0.55
        if genre_filters:
            overlap = len(genres & genre_filters)
            if overlap:
                score += 0.25 * overlap
            else:
                score *= 0.6

        previous = dedup.get(item["id"])
        if not previous or score > previous[0]:
            dedup[item["id"]] = (score, item)

    ranked = sorted(dedup.values(), key=lambda x: (x[0], x[1]["rating"], x[1]["year"]), reverse=True)

    filtered = []
    for _, item in ranked:
        if year_filter and item["year"] != year_filter:
            continue
        if rating_filter and float(item["rating"]) < rating_filter:
            continue
        if genre_filters:
            genres = {g.strip() for g in item["genres"].split(",")}
            if not (genres & genre_filters):
                continue
        filtered.append(item)

    if filtered:
        return filtered[:limit]

    if year_filter or rating_filter or genre_filters:
        fallback = []
        for item in all_rows:
            if year_filter and item["year"] != year_filter:
                continue
            if rating_filter and float(item["rating"]) < rating_filter:
                continue
            if genre_filters:
                genres = {g.strip() for g in item["genres"].split(",")}
                if not (genres & genre_filters):
                    continue
            fallback.append(item)
        fallback.sort(key=lambda x: (x["rating"], x["year"]), reverse=True)
        if fallback:
            return fallback[:limit]

    return [i[1] for i in ranked][:limit]
