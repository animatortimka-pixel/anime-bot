import random
from typing import Any

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from data import MEMES, QUOTES
from db import AnimeDB
from search import smart_search
from ui import anime_card, anime_navigation_keyboard, genres_keyboard, main_menu_keyboard, rating_keyboard


async def _show_menu(target, text: str = "👋 Выбери действие:") -> None:
    await target.edit_message_text(text=text, reply_markup=main_menu_keyboard())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Аниме-бот готов к работе. Всё управление через inline-кнопки.",
        reply_markup=main_menu_keyboard(),
    )


async def on_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db: AnimeDB = context.bot_data["db"]
    action = query.data.split(":", 1)[1]

    if action == "home":
        await _show_menu(query)
        return

    if action == "search":
        context.user_data["awaiting_search"] = True
        await query.edit_message_text(
            "🔎 Введите запрос сообщением (RU/EN, жанр, год, рейтинг). Например: <code>драма 2016 rating 8.5</code>",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    if action == "list":
        items = await db.get_all_anime()
        await _show_collection(query, context, "list", items, 0)
        return

    if action == "top":
        items = await db.get_top(30)
        await _show_collection(query, context, "top", items, 0)
        return

    if action == "genres":
        genres = await db.get_genres()
        context.user_data["genres"] = genres
        await query.edit_message_text("🎭 Выберите жанр:", reply_markup=genres_keyboard(genres, page=0))
        return

    if action == "favorites":
        user_id = update.effective_user.id
        items = await db.get_favorites(user_id)
        if not items:
            await query.edit_message_text("⭐ Избранное пока пусто.", reply_markup=main_menu_keyboard())
            return
        await _show_collection(query, context, "fav", items, 0)
        return

    if action == "rating":
        await query.edit_message_text("📈 Выберите минимальный рейтинг:", reply_markup=rating_keyboard())
        return

    if action == "meme":
        await query.edit_message_text(f"😂 {random.choice(MEMES)}", reply_markup=main_menu_keyboard())
        return

    if action == "quote":
        await query.edit_message_text(f"💬 {random.choice(QUOTES)}", reply_markup=main_menu_keyboard())
        return

    if action == "random":
        anime = await db.get_random()
        if not anime:
            await query.edit_message_text("База пуста.", reply_markup=main_menu_keyboard())
            return
        await query.edit_message_text(
            anime_card(anime),
            reply_markup=anime_navigation_keyboard("random", 0, 1, anime_id=anime["id"]),
            parse_mode="HTML",
        )


async def on_search_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_search"):
        return

    context.user_data["awaiting_search"] = False
    db: AnimeDB = context.bot_data["db"]
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Введите не пустой запрос.", reply_markup=main_menu_keyboard())
        return

    results = await smart_search(db, text, limit=30)
    context.user_data["search_results"] = results

    if not results:
        await update.message.reply_text("Ничего не найдено.", reply_markup=main_menu_keyboard())
        return

    await update.message.reply_text(
        anime_card(results[0]),
        reply_markup=anime_navigation_keyboard("search", 0, len(results), anime_id=results[0]["id"]),
        parse_mode="HTML",
    )


async def on_nav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db: AnimeDB = context.bot_data["db"]
    parts = query.data.split(":")

    if parts[0] == "noop":
        return

    if parts[0] == "fav" and parts[1] == "add":
        anime_id = int(parts[2])
        added = await db.add_favorite(update.effective_user.id, anime_id)
        text = "⭐ Добавлено в избранное." if added else "⭐ Уже есть в избранном."
        await query.answer(text, show_alert=False)
        return

    if parts[0] == "genre":
        genre = parts[1]
        all_items = await db.get_all_anime()
        filtered = [a for a in all_items if genre in a["genres"].split(",")]
        await _show_collection(query, context, "genre_items", filtered, 0)
        return

    if parts[0] == "genres" and parts[1] == "page":
        page = int(parts[2])
        genres = context.user_data.get("genres", [])
        await query.edit_message_text("🎭 Выберите жанр:", reply_markup=genres_keyboard(genres, page=page))
        return

    if parts[0] == "rating" and parts[1] == "min":
        min_rating = float(parts[2])
        all_items = await db.get_all_anime()
        filtered = [a for a in all_items if float(a["rating"]) >= min_rating]
        await _show_collection(query, context, "rating_items", filtered, 0)
        return

    if len(parts) >= 3 and parts[1] == "page":
        key = parts[0]
        page = int(parts[2])
        items = _resolve_collection(context.user_data, key)
        await _show_collection(query, context, key, items, page)


def _resolve_collection(store: dict[str, Any], key: str) -> list[dict[str, Any]]:
    mapping = {
        "list": "list_results",
        "top": "top_results",
        "fav": "fav_results",
        "search": "search_results",
        "genre_items": "genre_items",
        "rating_items": "rating_items",
    }
    return store.get(mapping.get(key, ""), [])


async def _show_collection(query, context: ContextTypes.DEFAULT_TYPE, key: str, items: list[dict[str, Any]], page: int) -> None:
    if not items:
        await query.edit_message_text("Пусто.", reply_markup=main_menu_keyboard())
        return

    mapping = {
        "list": "list_results",
        "top": "top_results",
        "fav": "fav_results",
        "search": "search_results",
        "genre_items": "genre_items",
        "rating_items": "rating_items",
    }
    store_key = mapping.get(key, key)
    context.user_data[store_key] = items

    page = max(0, min(page, len(items) - 1))
    anime = items[page]

    await query.edit_message_text(
        anime_card(anime),
        reply_markup=anime_navigation_keyboard(key, page, len(items), anime_id=anime["id"]),
        parse_mode="HTML",
    )


def setup_handlers(app: Application, db: AnimeDB) -> None:
    app.bot_data["db"] = db
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(on_nav_callback, pattern=r"^(?!menu:).+"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_search_message))
