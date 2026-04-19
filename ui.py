import json
from math import ceil
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🔎 Search", callback_data="menu:search"), InlineKeyboardButton("📚 List", callback_data="menu:list"), InlineKeyboardButton("🏆 Top", callback_data="menu:top")],
        [InlineKeyboardButton("🎭 Genres", callback_data="menu:genres"), InlineKeyboardButton("⭐ Favorites", callback_data="menu:favorites"), InlineKeyboardButton("📈 Rating", callback_data="menu:rating")],
        [InlineKeyboardButton("😂 Meme", callback_data="menu:meme"), InlineKeyboardButton("💬 Quote", callback_data="menu:quote"), InlineKeyboardButton("🎲 Random", callback_data="menu:random")],
    ]
    return InlineKeyboardMarkup(buttons)


def genres_keyboard(genres: list[str], page: int = 0, per_page: int = 6) -> InlineKeyboardMarkup:
    total_pages = max(1, ceil(len(genres) / per_page))
    start = page * per_page
    chunk = genres[start : start + per_page]

    rows = []
    row = []
    for genre in chunk:
        row.append(InlineKeyboardButton(f"#{genre}", callback_data=f"genre:{genre}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.extend(_pager_row("genres", page, total_pages))
    rows.append([InlineKeyboardButton("🏠 Menu", callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def anime_card(anime: dict[str, Any]) -> str:
    return (
        f"🎬 <b>{anime['title_ru']}</b> / <i>{anime['title_en']}</i>\n"
        f"🗓 {anime['year']} | ⭐ {anime['rating']}\n"
        f"🏷 {anime['genres']}\n\n"
        f"📖 {anime['description']}"
    )


def anime_navigation_keyboard(
    prefix: str,
    index: int,
    total: int,
    anime_id: int | None = None,
    watch_urls_raw: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    links = _extract_watch_links(watch_urls_raw)
    if links:
        rows.append(links)

    action_row = []
    if anime_id is not None:
        action_row.append(InlineKeyboardButton("⭐ В избранное", callback_data=f"fav:add:{anime_id}"))
    if action_row:
        rows.append(action_row)

    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}:page:{index - 1}"))
    nav.append(InlineKeyboardButton(f"{index + 1}/{max(total, 1)}", callback_data="noop"))
    if index < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}:page:{index + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Menu", callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def rating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("8.0+", callback_data="rating:min:8.0"), InlineKeyboardButton("8.5+", callback_data="rating:min:8.5"), InlineKeyboardButton("9.0+", callback_data="rating:min:9.0")],
            [InlineKeyboardButton("🏠 Menu", callback_data="menu:home")],
        ]
    )


def _pager_row(prefix: str, page: int, total_pages: int) -> list[list[InlineKeyboardButton]]:
    row = []
    if page > 0:
        row.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}:page:{page - 1}"))
    row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        row.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}:page:{page + 1}"))
    return [row]


def _extract_watch_links(watch_urls_raw: str | None) -> list[InlineKeyboardButton]:
    if watch_urls_raw is None:
        return []
    try:
        watch_urls = json.loads(watch_urls_raw) if isinstance(watch_urls_raw, str) else watch_urls_raw
    except json.JSONDecodeError:
        watch_urls = {}
    buttons = []
    if watch_urls.get("anilibria"):
        buttons.append(InlineKeyboardButton("▶️ Anilibria", url=watch_urls["anilibria"]))
    if watch_urls.get("animego"):
        buttons.append(InlineKeyboardButton("▶️ AnimeGo", url=watch_urls["animego"]))
    if watch_urls.get("jut_su"):
        buttons.append(InlineKeyboardButton("▶️ Jut.su", url=watch_urls["jut_su"]))
    return buttons
