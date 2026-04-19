from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from db import AnimeDB
from search import smart_search
from ui import (
    anime_actions_keyboard,
    anime_card,
    genres_keyboard,
    main_menu_keyboard,
    rating_keyboard,
    series_page_keyboard,
    watch_keyboard,
)

logger = logging.getLogger(__name__)

LIST_PREFIXES = {"m", "s", "f", "t", "g", "r"}


async def _safe_edit(query, text: str, markup, parse_mode: str = "HTML") -> None:
    try:
        await query.edit_message_text(text=text, reply_markup=markup, parse_mode=parse_mode)
    except BadRequest as exc:
        if "Message is not modified" not in str(exc):
            raise


def _set_list(context: ContextTypes.DEFAULT_TYPE, key: str, ids: list[int]) -> None:
    context.user_data.setdefault("lists", {})[key] = ids


def _get_list(context: ContextTypes.DEFAULT_TYPE, key: str) -> list[int]:
    return context.user_data.get("lists", {}).get(key, [])


async def _render_from_list(query, context: ContextTypes.DEFAULT_TYPE, key: str, idx: int) -> None:
    ids = _get_list(context, key)
    if not ids:
        await _safe_edit(query, "Список пуст.", main_menu_keyboard())
        return
    idx = max(0, min(idx, len(ids) - 1))
    db: AnimeDB = context.bot_data["db"]
    anime = await db.get_anime(ids[idx])
    if anime is None:
        await _safe_edit(query, "Аниме не найдено.", main_menu_keyboard())
        return
    await db.add_view(query.from_user.id, anime["id"])
    await _safe_edit(query, anime_card(anime), anime_actions_keyboard(anime["id"], key, idx, len(ids)))


async def _show_anime(query, context: ContextTypes.DEFAULT_TYPE, anime_id: int) -> None:
    db: AnimeDB = context.bot_data["db"]
    anime = await db.get_anime(anime_id)
    if anime is None:
        await _safe_edit(query, "Аниме не найдено.", main_menu_keyboard())
        return
    await db.add_view(query.from_user.id, anime_id)
    _set_list(context, "m", [anime_id])
    await _safe_edit(query, anime_card(anime), anime_actions_keyboard(anime_id, "m", 0, 1))


async def _build_recommendations(db: AnimeDB, user_id: int, limit: int = 30) -> list[dict[str, Any]]:
    favorites = await db.get_user_favorites(user_id)
    catalog = await db.get_all_anime()
    seen = {x["id"] for x in favorites}
    taste = Counter(g for anime in favorites for g in anime["genres"])
    scored: list[tuple[float, dict[str, Any]]] = []
    for anime in catalog:
        if anime["id"] in seen:
            continue
        genre_bonus = sum(taste[g] for g in anime["genres"])
        score = anime["rating"] * 2 + genre_bonus + anime["views"] / 5000
        scored.append((score, anime))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:limit]]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db: AnimeDB = context.bot_data["db"]
    user = update.effective_user
    await db.ensure_user(user.id, user.username)
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Добро пожаловать в Anime SaaS Bot. Используйте меню ниже.",
        reply_markup=main_menu_keyboard(),
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data.get("awaiting_search"):
        return
    context.user_data["awaiting_search"] = False

    db: AnimeDB = context.bot_data["db"]
    results = await smart_search(db, (update.message.text or "").strip(), limit=50)
    result_ids = [item["id"] for item in results]
    _set_list(context, "s", result_ids)

    anchor = context.user_data.get("search_anchor")
    if not anchor:
        await update.message.reply_text("Нажмите /start для запуска меню.")
        return

    chat_id, message_id = anchor
    if not result_ids:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="По вашему запросу ничего не найдено.",
            reply_markup=main_menu_keyboard(),
        )
        return

    first = await db.get_anime(result_ids[0])
    if first is None:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Ошибка: найденный элемент недоступен.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=anime_card(first),
        parse_mode="HTML",
        reply_markup=anime_actions_keyboard(first["id"], "s", 0, len(result_ids)),
    )


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    db: AnimeDB = context.bot_data["db"]
    user = update.effective_user
    await db.ensure_user(user.id, user.username)

    if data == "noop":
        return

    if data == "menu_home":
        await _safe_edit(query, "Главное меню:", main_menu_keyboard())
        return

    if data == "menu_search":
        context.user_data["awaiting_search"] = True
        context.user_data["search_anchor"] = (query.message.chat_id, query.message.message_id)
        await _safe_edit(query, "Введите поисковый запрос: название, год, жанр.", main_menu_keyboard())
        return

    if data == "menu_favorites":
        favorites = await db.get_user_favorites(user.id)
        ids = [x["id"] for x in favorites]
        _set_list(context, "f", ids)
        await _render_from_list(query, context, "f", 0)
        return

    if data == "menu_random":
        anime = await db.get_random_anime()
        if anime is None:
            await _safe_edit(query, "Каталог пуст.", main_menu_keyboard())
            return
        _set_list(context, "r", [anime["id"]])
        await _safe_edit(query, anime_card(anime), anime_actions_keyboard(anime["id"], "r", 0, 1))
        return

    if data == "menu_top":
        top = await db.get_popular(50)
        ids = [x["id"] for x in top]
        _set_list(context, "t", ids)
        await _render_from_list(query, context, "t", 0)
        return

    if data == "menu_genres":
        await _safe_edit(query, "Выберите жанр:", genres_keyboard(await db.get_genres()))
        return

    if data == "menu_help":
        await _safe_edit(
            query,
            "ℹ️ Доступно: поиск, топ, избранное, рекомендации через похожие и рейтинг."
            "\nВсе обновления идут через edit_message_text без спама.",
            main_menu_keyboard(),
        )
        return

    if data.startswith("anime_view_"):
        anime_id = int(data.split("_")[-1])
        await _show_anime(query, context, anime_id)
        return

    if data.startswith("anime_nav_"):
        _, _, source, idx = data.split("_")
        if source not in LIST_PREFIXES:
            source = "m"
        await _render_from_list(query, context, source, int(idx))
        return

    if data.startswith("genre_"):
        genre = data.split("_", 1)[1]
        all_anime = await db.get_all_anime()
        ids = [a["id"] for a in all_anime if genre in a["genres"]]
        _set_list(context, "g", ids)
        await _render_from_list(query, context, "g", 0)
        return

    if data.startswith("add_fav_"):
        anime_id = int(data.split("_")[-1])
        added = await db.toggle_favorite(user.id, anime_id)
        await query.answer("Добавлено в избранное" if added else "Удалено из избранного")
        await _show_anime(query, context, anime_id)
        return

    if data.startswith("rate_menu_"):
        anime_id = int(data.split("_")[-1])
        anime = await db.get_anime(anime_id)
        if anime:
            await _safe_edit(query, f"Оцените <b>{anime['name_ru']}</b> от 1 до 5:", rating_keyboard(anime_id))
        return

    if data.startswith("rate_") and data.count("_") == 2:
        _, anime_id, value = data.split("_")
        avg = await db.set_rating(user.id, int(anime_id), int(value))
        await query.answer(f"Спасибо! Средний рейтинг: {avg:.2f}")
        await _show_anime(query, context, int(anime_id))
        return

    if data.startswith("similar_"):
        anime_id = int(data.split("_")[-1])
        base = await db.get_anime(anime_id)
        if not base:
            await _safe_edit(query, "Исходное аниме не найдено.", main_menu_keyboard())
            return
        recommendations = await _build_recommendations(db, user.id, limit=80)
        similar_ids = [a["id"] for a in recommendations if set(a["genres"]).intersection(base["genres"])][:50]
        if not similar_ids:
            all_items = await db.get_all_anime()
            similar_ids = [a["id"] for a in all_items if a["id"] != anime_id and set(a["genres"]).intersection(base["genres"])][:50]
        _set_list(context, "r", similar_ids)
        await _render_from_list(query, context, "r", 0)
        return

    if data.startswith("watch_menu_"):
        anime_id = int(data.split("_")[-1])
        anime = await db.get_anime(anime_id)
        if anime:
            await _safe_edit(query, f"Выберите источник просмотра для <b>{anime['name_ru']}</b>:", watch_keyboard(anime_id, anime["watch_urls"]))
        return

    if data.startswith("series_page_"):
        _, _, anime_id, page = data.split("_")
        anime = await db.get_anime(int(anime_id))
        if anime:
            await _safe_edit(
                query,
                f"📺 Серии: <b>{anime['name_ru']}</b>\nВыберите эпизод:",
                series_page_keyboard(anime["id"], anime["episodes_data"], int(page)),
            )
        return

    if data.startswith("episode_"):
        _, anime_id, episode_no, page = data.split("_")
        anime = await db.get_anime(int(anime_id))
        if anime:
            url = anime["episodes_data"].get(str(int(episode_no)), "https://www.anilibria.tv/")
            await _safe_edit(
                query,
                f"🎞 <b>{anime['name_ru']}</b>\nСерия {episode_no}\n"
                f"🔗 Прямая ссылка: {url}\n\n"
                "Если плеер не открывается в Telegram — откройте ссылку в браузере.",
                series_page_keyboard(anime["id"], anime["episodes_data"], int(page)),
            )
        return

    logger.warning("Unknown callback data: %s", data)


def setup_handlers(app: Application, db: AnimeDB) -> None:
    app.bot_data["db"] = db
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
