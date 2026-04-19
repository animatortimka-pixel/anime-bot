from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Поиск", callback_data="menu_search"), InlineKeyboardButton("❤️ Избранное", callback_data="menu_favorites")],
            [InlineKeyboardButton("🎲 Случайное", callback_data="menu_random"), InlineKeyboardButton("🏆 Топ", callback_data="menu_top")],
            [InlineKeyboardButton("🎭 Жанры", callback_data="menu_genres"), InlineKeyboardButton("ℹ️ Помощь", callback_data="menu_help")],
        ]
    )


def anime_card(anime_data: dict) -> str:
    watch_count = anime_data.get("views", 0)
    return (
        f"🎬 <b>{anime_data['name_ru']}</b>\n"
        f"<i>{anime_data['name_en']}</i>\n\n"
        f"🗓 Год: <b>{anime_data['year']}</b>\n"
        f"⭐ Рейтинг: <b>{anime_data['rating']:.2f}</b>\n"
        f"🎞 Эпизоды: <b>{anime_data['episodes']}</b>\n"
        f"🏷 Жанры: {', '.join(anime_data['genres'])}\n"
        f"👁 Просмотры: {watch_count}\n\n"
        f"📖 {anime_data['description']}"
    )


def anime_actions_keyboard(anime_id: int, source: str = "m", idx: int = 0, total: int = 1) -> InlineKeyboardMarkup:
    nav_row = []
    if idx > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"anime_nav_{source}_{idx-1}"))
    nav_row.append(InlineKeyboardButton(f"{idx + 1}/{total}", callback_data="noop"))
    if idx < total - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"anime_nav_{source}_{idx+1}"))

    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Смотреть", callback_data=f"watch_menu_{anime_id}"), InlineKeyboardButton("📺 Серии", callback_data=f"series_page_{anime_id}_0")],
            [InlineKeyboardButton("❤️ В избранное", callback_data=f"add_fav_{anime_id}"), InlineKeyboardButton("📋 Похожие", callback_data=f"similar_{anime_id}")],
            [InlineKeyboardButton("⭐ Оценить", callback_data=f"rate_menu_{anime_id}"), InlineKeyboardButton("🏠 Меню", callback_data="menu_home")],
            nav_row,
        ]
    )


def watch_keyboard(anime_id: int, watch_urls: dict[str, str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Anilibria", url=watch_urls.get("anilibria", "https://www.anilibria.tv/"))],
            [InlineKeyboardButton("📖 Shikimori", url=watch_urls.get("shikimori", "https://shikimori.one/"))],
            [InlineKeyboardButton("🎥 YouTube", url=watch_urls.get("youtube", "https://www.youtube.com/"))],
            [InlineKeyboardButton("📺 Серии", callback_data=f"series_page_{anime_id}_0")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"anime_view_{anime_id}")],
        ]
    )


def rating_keyboard(anime_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(str(v), callback_data=f"rate_{anime_id}_{v}") for v in range(1, 6)],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"anime_view_{anime_id}")],
        ]
    )


def genres_keyboard(genres: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(genres), 2):
        rows.append([InlineKeyboardButton(genres[i], callback_data=f"genre_{genres[i]}")] + ([InlineKeyboardButton(genres[i + 1], callback_data=f"genre_{genres[i + 1]}")] if i + 1 < len(genres) else []))
    rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu_home")])
    return InlineKeyboardMarkup(rows)


def series_page_keyboard(anime_id: int, episodes_data: dict[str, str], page: int) -> InlineKeyboardMarkup:
    episode_numbers = sorted((int(k) for k in episodes_data.keys()), key=lambda x: x)
    per_page = 10
    total_pages = max(1, (len(episode_numbers) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))

    start = page * per_page
    current = episode_numbers[start : start + per_page]

    rows = [[InlineKeyboardButton(f"Серия {ep}", callback_data=f"episode_{anime_id}_{ep}_{page}")] for ep in current]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"series_page_{anime_id}_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"series_page_{anime_id}_{page+1}"))
    rows.append(nav)

    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"anime_view_{anime_id}")])
    return InlineKeyboardMarkup(rows)
