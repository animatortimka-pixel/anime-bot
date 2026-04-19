"""Telegram-бот каталога аниме (python-telegram-bot v20+, async)."""

from __future__ import annotations

import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config import settings
from db import AnimeDB

PAGE_SIZE = 5
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("anime_catalog_bot")


def format_anime_card(anime: dict) -> str:
    """Форматирует карточку аниме для HTML-ответа."""
    stars = "★" * max(1, min(10, round(float(anime["rating"]) / 2)))
    return (
        f"<b>{html.escape(anime['name_ru'])}</b> / <i>{html.escape(anime['name_en'])}</i>\n"
        f"🆔 <b>ID:</b> {anime['id']}\n"
        f"⭐ <b>Рейтинг:</b> {anime['rating']} ({stars})\n"
        f"🎭 <b>Жанры:</b> {html.escape(anime['genres'])}\n"
        f"📅 <b>Год:</b> {anime['year']}\n"
        f"📺 <b>Тип:</b> {html.escape(anime['type'])}\n\n"
        f"📝 <b>Описание:</b> {html.escape(anime['description'])}"
    )


def build_main_menu() -> InlineKeyboardMarkup:
    """Строит главное меню."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Поиск", callback_data="help_search")],
            [InlineKeyboardButton("📋 Список", callback_data="list_0")],
            [InlineKeyboardButton("⭐ Топ", callback_data="top")],
            [InlineKeyboardButton("❤️ Избранное", callback_data="favorites")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")],
        ]
    )


def build_anime_actions(anime_id: int) -> InlineKeyboardMarkup:
    """Кнопки действий для карточки аниме."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⭐ Оценить 8", callback_data=f"rate_{anime_id}_8")],
            [InlineKeyboardButton("❤️ В избранное", callback_data=f"favorite_{anime_id}")],
            [InlineKeyboardButton("🔎 Похожие", callback_data=f"similar_{anime_id}")],
        ]
    )


def build_pagination(page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """Клавиатура пагинации."""
    buttons: list[InlineKeyboardButton] = []
    if has_prev:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"list_{page - 1}"))
    if has_next:
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"list_{page + 1}"))
    return InlineKeyboardMarkup([buttons] if buttons else [])


def parse_page(callback_data: str) -> int:
    """Парсинг номера страницы из callback_data."""
    try:
        return max(0, int(callback_data.split("_", maxsplit=1)[1]))
    except (IndexError, ValueError):
        return 0


async def send_anime_card(target, anime: dict) -> None:
    """Универсальная отправка карточки аниме."""
    await target.reply_text(
        format_anime_card(anime),
        parse_mode="HTML",
        reply_markup=build_anime_actions(anime["id"]),
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /start."""
    try:
        db: AnimeDB = context.bot_data["db"]
        user = update.effective_user
        await db.ensure_user(user.id, user.username, user.first_name, user.last_name)
        text = (
            "👋 <b>Добро пожаловать в Anime Catalog Bot</b>\n\n"
            "Доступные команды:\n"
            "/search <текст> — поиск аниме\n"
            "/id <id> — открыть карточку по ID\n"
            "/list — список аниме"
        )
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=build_main_menu())
    except Exception:
        logger.exception("Ошибка в /start")
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /search."""
    try:
        db: AnimeDB = context.bot_data["db"]
        query = " ".join(context.args).strip()
        if not query:
            await update.message.reply_text("Использование: /search <текст>")
            return
        results = await db.search_anime(query)
        if not results:
            await update.message.reply_text("😔 Ничего не найдено.")
            return
        if len(results) == 1:
            anime = results[0]
            await db.add_to_history(update.effective_user.id, anime["id"])
            await send_anime_card(update.message, anime)
            return
        lines = [f"🔎 Найдено: <b>{len(results)}</b>"]
        lines.extend(f"• <b>{a['id']}</b> — {html.escape(a['name_ru'])}" for a in results[:10])
        lines.append("\nОткройте карточку: /id <ID>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    except Exception:
        logger.exception("Ошибка в /search")
        await update.message.reply_text("⚠️ Ошибка поиска. Попробуйте позже.")


async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /id."""
    try:
        if not context.args:
            await update.message.reply_text("Использование: /id <число>")
            return
        anime_id = int(context.args[0])
        db: AnimeDB = context.bot_data["db"]
        anime = await db.get_anime_by_id(anime_id)
        if not anime:
            await update.message.reply_text("❌ Аниме с таким ID не найдено.")
            return
        await db.add_to_history(update.effective_user.id, anime_id)
        await send_anime_card(update.message, anime)
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
    except Exception:
        logger.exception("Ошибка в /id")
        await update.message.reply_text("⚠️ Не удалось открыть карточку.")


async def list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /list."""
    try:
        await send_list_page(update.message, context, page=0)
    except Exception:
        logger.exception("Ошибка в /list")
        await update.message.reply_text("⚠️ Не удалось получить список.")


async def send_list_page(target, context: ContextTypes.DEFAULT_TYPE, page: int) -> None:
    """Отправка страницы списка аниме."""
    db: AnimeDB = context.bot_data["db"]
    offset = page * PAGE_SIZE
    items = await db.get_all_anime(limit=PAGE_SIZE, offset=offset)
    next_items = await db.get_all_anime(limit=1, offset=offset + PAGE_SIZE)
    if not items:
        await target.reply_text("Список пуст.")
        return
    text = [f"📋 <b>Список аниме</b> (страница {page + 1})"]
    text.extend(f"• <b>{a['id']}</b> — {html.escape(a['name_ru'])} ({a['year']})" for a in items)
    text.append("\nОткройте карточку: /id <ID>")
    await target.reply_text(
        "\n".join(text),
        parse_mode="HTML",
        reply_markup=build_pagination(page, has_prev=page > 0, has_next=bool(next_items)),
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Единый обработчик callback-кнопок."""
    query = update.callback_query
    await query.answer()
    try:
        db: AnimeDB = context.bot_data["db"]
        user_id = update.effective_user.id
        data = query.data
        if data.startswith("list_"):
            await send_list_page(query.message, context, parse_page(data))
            return
        if data.startswith("similar_"):
            anime_id = int(data.split("_", maxsplit=1)[1])
            similar = await db.get_similar_anime(anime_id)
            if not similar:
                await query.message.reply_text("Похожие аниме не найдены.")
                return
            lines = ["🔎 <b>Похожие аниме:</b>"]
            lines.extend(f"• <b>{a['id']}</b> — {html.escape(a['name_ru'])}" for a in similar)
            await query.message.reply_text("\n".join(lines), parse_mode="HTML")
            return
        if data.startswith("favorite_"):
            anime_id = int(data.split("_", maxsplit=1)[1])
            added = await db.add_favorite(user_id, anime_id)
            if not added:
                removed = await db.remove_favorite(user_id, anime_id)
                text = "💔 Удалено из избранного." if removed else "ℹ️ Уже удалено из избранного."
                await query.message.reply_text(text)
                return
            await query.message.reply_text("❤️ Добавлено в избранное.")
            return
        if data.startswith("rate_"):
            _, anime_id, value = data.split("_")
            await db.add_rating(user_id, int(anime_id), int(value))
            await query.message.reply_text(f"⭐ Оценка {value} сохранена.")
            return
        if data == "top":
            top = await db.get_top_anime()
            lines = ["⭐ <b>Топ аниме:</b>"]
            lines.extend(f"{i+1}. <b>{a['id']}</b> — {html.escape(a['name_ru'])}" for i, a in enumerate(top))
            await query.message.reply_text("\n".join(lines), parse_mode="HTML")
            return
        if data == "favorites":
            favorites = await db.get_favorites(user_id)
            if not favorites:
                await query.message.reply_text("У вас пока нет избранного.")
                return
            lines = ["❤️ <b>Ваше избранное:</b>"]
            lines.extend(f"• <b>{a['id']}</b> — {html.escape(a['name_ru'])}" for a in favorites[:20])
            await query.message.reply_text("\n".join(lines), parse_mode="HTML")
            return
        help_text = "❓ Команды: /start, /search <текст>, /id <id>, /list"
        await query.message.reply_text(help_text)
    except Exception:
        logger.exception("Ошибка в callback")
        await query.message.reply_text("⚠️ Ошибка действия. Попробуйте позже.")


async def post_init(app: Application) -> None:
    """Инициализация БД после старта приложения."""
    db: AnimeDB = app.bot_data["db"]
    await db.init_db()
    await db.init_sample_data()


def build_app() -> Application:
    """Создаёт и настраивает Telegram-приложение."""
    db = AnimeDB(settings.db_name)
    app = Application.builder().token(settings.bot_token).post_init(post_init).build()
    app.bot_data["db"] = db
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("search", search_handler))
    app.add_handler(CommandHandler("id", id_handler))
    app.add_handler(CommandHandler("list", list_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    return app


def main() -> None:
    """Точка входа."""
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN пустой. Укажите токен в .env")
    app = build_app()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
