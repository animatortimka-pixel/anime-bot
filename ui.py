from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Поиск", callback_data="menu:search"), InlineKeyboardButton("🎲 Случайное", callback_data="menu:random"), InlineKeyboardButton("📚 Каталог", callback_data="menu:catalog")],
            [InlineKeyboardButton("🏆 Топ", callback_data="menu:top"), InlineKeyboardButton("🎯 Рекомендации", callback_data="menu:reco"), InlineKeyboardButton("🎭 Жанры", callback_data="menu:genres")],
            [InlineKeyboardButton("❤️ Избранное", callback_data="menu:fav"), InlineKeyboardButton("💬 Цитата", callback_data="menu:quote"), InlineKeyboardButton("😂 Мем", callback_data="menu:meme")],
        ]
    )


def anime_card_text(anime: dict, avg_user_rating: float = 0.0) -> str:
    user_rating = f"\n👥 Пользовательский рейтинг: {avg_user_rating:.2f}/5" if avg_user_rating else ""
    return (
        f"🎬 <b>{anime['name_ru']}</b>\n"
        f"<i>{anime['name_en']}</i>\n\n"
        f"🗓 Год: <b>{anime['year']}</b>\n"
        f"🎞 Эпизодов: <b>{anime['episodes']}</b>\n"
        f"⭐ Оценка базы: <b>{anime['rating']}/10</b>{user_rating}\n"
        f"🏷 Жанры: {', '.join(anime['genres'])}\n"
        f"👁 Просмотров: {anime['views']}\n\n"
        f"📖 {anime['description']}"
    )


def anime_keyboard(anime_id: int, source: str, idx: int, total: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🎬 Смотреть", callback_data=f"watch:menu:{anime_id}:{source}:{idx}")],
        [InlineKeyboardButton("⭐ Оценить", callback_data=f"rate:menu:{anime_id}:{source}:{idx}"), InlineKeyboardButton("❤️ Избранное", callback_data=f"fav:toggle:{anime_id}")],
        [InlineKeyboardButton("📋 Похожие", callback_data=f"sim:{anime_id}"), InlineKeyboardButton("🎲 Случайное", callback_data="menu:random")],
    ]

    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"page:{source}:{idx-1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{max(total, 1)}", callback_data="noop"))
    if idx < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"page:{source}:{idx+1}"))
    rows.append(nav)

    rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def watch_menu_keyboard(anime_id: int, source: str, idx: int, watch_urls: dict[str, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Anilibria", url=watch_urls.get("anilibria", "https://www.anilibria.tv/"))],
            [InlineKeyboardButton("📖 Shikimori", url=watch_urls.get("shikimori", "https://shikimori.one/"))],
            [InlineKeyboardButton("🎥 YouTube", url=watch_urls.get("youtube", "https://www.youtube.com/"))],
            [InlineKeyboardButton("📺 Серии", callback_data=f"eps:{anime_id}:0:{source}:{idx}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"page:{source}:{idx}")],
        ]
    )


def episodes_keyboard(anime_id: int, episodes_data: list[dict], page: int, source: str, idx: int) -> InlineKeyboardMarkup:
    per_page = 10
    total_pages = max(1, (len(episodes_data) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    items = episodes_data[start : start + per_page]

    rows: list[list[InlineKeyboardButton]] = []
    for ep in items:
        rows.append([InlineKeyboardButton(f"Серия {ep['episode']}", url=ep["url"])])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"eps:{anime_id}:{page-1}:{source}:{idx}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"eps:{anime_id}:{page+1}:{source}:{idx}"))
    rows.append(nav)

    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"watch:menu:{anime_id}:{source}:{idx}")])
    rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def rating_keyboard(anime_id: int, source: str, idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(str(v), callback_data=f"rate:set:{anime_id}:{v}:{source}:{idx}") for v in range(1, 6)],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"page:{source}:{idx}")],
        ]
    )


def genres_keyboard(genres: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(genres), 3):
        rows.append([InlineKeyboardButton(f"#{g}", callback_data=f"genre:{g}") for g in genres[i : i + 3]])
    rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)
