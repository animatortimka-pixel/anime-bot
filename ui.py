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
        f"🎬 <b>{anime['name_ru']}</b> / <i>{anime['name_en']}</i>\n"
        f"🗓 Год: {anime['year']} | 🎞 Эпизодов: {anime['episodes']}\n"
        f"⭐ База: {anime['rating']}/10{user_rating}\n"
        f"🏷 Жанры: {', '.join(anime['genres'])}\n"
        f"👁 Просмотры: {anime['views']}\n\n"
        f"📖 {anime['description']}"
    )


def anime_keyboard(anime_id: int, source: str, idx: int, total: int, watch_urls: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"▶️ Смотреть {i+1}", url=u) for i, u in enumerate(watch_urls[:2])],
        [InlineKeyboardButton("⭐ Оценить", callback_data=f"rate:menu:{anime_id}:{source}:{idx}"), InlineKeyboardButton("❤️ В избранное", callback_data=f"fav:toggle:{anime_id}")],
        [InlineKeyboardButton("📋 Похожие", callback_data=f"sim:{anime_id}"), InlineKeyboardButton("🎲 Случайное", callback_data="menu:random")],
    ]
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"page:{source}:{idx-1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{max(total,1)}", callback_data="noop"))
    if idx < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"page:{source}:{idx+1}"))
    rows.append(nav)
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
