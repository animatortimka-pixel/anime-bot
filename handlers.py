from __future__ import annotations

from collections import Counter

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from db import AnimeDB
from search import smart_search
from ui import (
    anime_card_text,
    anime_keyboard,
    episodes_keyboard,
    genres_keyboard,
    main_menu_keyboard,
    rating_keyboard,
    watch_menu_keyboard,
)

SOURCE_MAP = {
    "catalog": "catalog_items",
    "top": "top_items",
    "fav": "fav_items",
    "reco": "reco_items",
    "genre": "genre_items",
    "search": "search_items",
    "similar": "similar_items",
}


async def _safe_edit(query, text: str, reply_markup, parse_mode: str | None = "HTML") -> None:
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as exc:
        if "Message is not modified" not in str(exc):
            raise


async def _show_menu(query) -> None:
    await _safe_edit(query, "👋 Добро пожаловать в Anime Hub. Выберите действие:", main_menu_keyboard())


async def build_recommendations(db: AnimeDB, user_id: int, limit: int = 24) -> list[dict]:
    favorites = await db.get_user_favorites(user_id)
    history = await db.get_user_history(user_id, limit=150)
    all_items = await db.get_all_anime()

    watched_ids = {item["id"] for item in favorites + history}
    genre_weights = Counter(genre for item in favorites + history for genre in item["genres"])

    scored: list[tuple[float, dict]] = []
    for anime in all_items:
        if anime["id"] in watched_ids:
            continue
        genre_score = sum(genre_weights[g] for g in anime["genres"]) * 2
        score = genre_score + anime["rating"] + (anime["views"] / 200)
        scored.append((score, anime))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [anime for _, anime in scored[:limit]] or await db.get_popular(limit=limit)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db: AnimeDB = context.bot_data["db"]
    user = update.effective_user
    await db.ensure_user(user.id, user.username)
    context.user_data.clear()
    await update.message.reply_text("👋 Нажми кнопку ниже, чтобы открыть меню.", reply_markup=main_menu_keyboard())


async def render_card(query, context: ContextTypes.DEFAULT_TYPE, anime: dict, source: str, idx: int, total: int) -> None:
    db: AnimeDB = context.bot_data["db"]
    await db.add_view(query.from_user.id, anime["id"])
    avg_rating = await db.get_average_rating(anime["id"])
    await _safe_edit(query, anime_card_text(anime, avg_rating), anime_keyboard(anime["id"], source, idx, total))


async def render_source(update: Update, context: ContextTypes.DEFAULT_TYPE, source: str, idx: int) -> None:
    data = context.user_data.get(SOURCE_MAP[source], [])
    if not data:
        await _safe_edit(update.callback_query, "⚠️ Пусто. Попробуйте другой раздел.", main_menu_keyboard())
        return
    idx = max(0, min(idx, len(data) - 1))
    await render_card(update.callback_query, context, data[idx], source, idx, len(data))


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    db: AnimeDB = context.bot_data["db"]
    user = update.effective_user
    await db.ensure_user(user.id, user.username)

    if action == "home":
        await _show_menu(query)
        return

    if action == "search":
        context.user_data["await_search"] = True
        context.user_data["search_anchor"] = (query.message.chat_id, query.message.message_id)
        await _safe_edit(query, "🔍 Введите запрос: название, жанр, год или описание.", main_menu_keyboard())
        return

    if action == "catalog":
        context.user_data[SOURCE_MAP["catalog"]] = await db.get_all_anime()
        await render_source(update, context, "catalog", 0)
        return

    if action == "top":
        context.user_data[SOURCE_MAP["top"]] = await db.get_popular(60)
        await render_source(update, context, "top", 0)
        return

    if action == "fav":
        context.user_data[SOURCE_MAP["fav"]] = await db.get_user_favorites(user.id)
        await render_source(update, context, "fav", 0)
        return

    if action == "reco":
        context.user_data[SOURCE_MAP["reco"]] = await build_recommendations(db, user.id, 60)
        await render_source(update, context, "reco", 0)
        return

    if action == "genres":
        await _safe_edit(query, "🎭 Выберите жанр:", genres_keyboard(await db.get_genres()))
        return

    if action == "quote":
        await _safe_edit(query, f"💬 {await db.get_random_quote()}", main_menu_keyboard())
        return

    if action == "meme":
        await _safe_edit(query, f"😂 {await db.get_random_meme()}", main_menu_keyboard())
        return

    if action == "random":
        random_item = await db.get_random_anime()
        if random_item:
            context.user_data[SOURCE_MAP["catalog"]] = [random_item]
            await render_card(query, context, random_item, "catalog", 0, 1)


async def text_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("await_search"):
        return

    context.user_data["await_search"] = False
    query_text = (update.message.text or "").strip()
    db: AnimeDB = context.bot_data["db"]

    results = await smart_search(db, query_text, limit=50)
    context.user_data[SOURCE_MAP["search"]] = results

    chat_id, msg_id = context.user_data.get("search_anchor", (None, None))
    if not chat_id or not msg_id:
        await update.message.reply_text("Нажмите /start для открытия меню.")
        return

    if not results:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text="Ничего не найдено. Попробуйте изменить запрос.",
            reply_markup=main_menu_keyboard(),
        )
        return

    first = results[0]
    avg = await db.get_average_rating(first["id"])
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=msg_id,
        text=anime_card_text(first, avg),
        parse_mode="HTML",
        reply_markup=anime_keyboard(first["id"], "search", 0, len(results)),
    )


async def nav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    db: AnimeDB = context.bot_data["db"]
    user_id = update.effective_user.id

    if parts[0] == "noop":
        return

    if parts[0] == "page":
        await render_source(update, context, parts[1], int(parts[2]))
        return

    if parts[0] == "fav" and parts[1] == "toggle":
        added = await db.toggle_favorite(user_id, int(parts[2]))
        await query.answer("Добавлено в избранное" if added else "Удалено из избранного")
        return

    if parts[0] == "rate" and parts[1] == "menu":
        await _safe_edit(query, "⭐ Выберите оценку:", rating_keyboard(int(parts[2]), parts[3], int(parts[4])))
        return

    if parts[0] == "rate" and parts[1] == "set":
        anime_id, value, source, idx = int(parts[2]), int(parts[3]), parts[4], int(parts[5])
        await db.set_rating(user_id, anime_id, value)
        await query.answer(f"Оценка {value} сохранена")
        await render_source(update, context, source, idx)
        return

    if parts[0] == "genre":
        genre = parts[1]
        items = await db.get_all_anime()
        context.user_data[SOURCE_MAP["genre"]] = [item for item in items if genre in item["genres"]]
        await render_source(update, context, "genre", 0)
        return

    if parts[0] == "sim":
        source_anime = await db.get_anime(int(parts[1]))
        if not source_anime:
            await query.answer("Не найдено", show_alert=True)
            return
        items = await db.get_all_anime()
        context.user_data[SOURCE_MAP["similar"]] = [
            item for item in items if item["id"] != source_anime["id"] and set(item["genres"]).intersection(source_anime["genres"])
        ]
        await render_source(update, context, "similar", 0)
        return

    if parts[0] == "watch" and parts[1] == "menu":
        anime_id, source, idx = int(parts[2]), parts[3], int(parts[4])
        anime = await db.get_anime(anime_id)
        if anime:
            await _safe_edit(
                query,
                f"🎬 Где смотреть <b>{anime['name_ru']}</b>?",
                watch_menu_keyboard(anime_id, source, idx, anime["watch_urls"]),
            )
        return

    if parts[0] == "eps":
        anime_id, page, source, idx = int(parts[1]), int(parts[2]), parts[3], int(parts[4])
        anime = await db.get_anime(anime_id)
        if anime:
            await _safe_edit(
                query,
                f"📺 Серии: <b>{anime['name_ru']}</b>",
                episodes_keyboard(anime_id, anime["episodes_data"], page, source, idx),
            )


def setup_handlers(app: Application, db: AnimeDB) -> None:
    app.bot_data["db"] = db
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(nav_callback, pattern=r"^(?!menu:).+"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_search))
