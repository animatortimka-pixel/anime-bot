"""Production-ready Telegram Anime Catalog bot (python-telegram-bot v20+)."""

from __future__ import annotations

import asyncio
import html
import logging
import random
import sqlite3
from datetime import datetime
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import BOT_TOKEN, DB_NAME

PAGE_SIZE = 5
TOP_LIMIT = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("anime_catalog_bot")


def db_connect() -> sqlite3.Connection:
    """Create SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create database schema and indexes."""
    with db_connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS anime (
                id INTEGER PRIMARY KEY,
                name_ru TEXT NOT NULL,
                name_en TEXT NOT NULL,
                description TEXT NOT NULL,
                genres TEXT NOT NULL,
                year INTEGER NOT NULL,
                rating REAL NOT NULL,
                type TEXT NOT NULL,
                source TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                reg_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, anime_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ratings (
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 10),
                PRIMARY KEY (user_id, anime_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                view_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_anime_name_ru ON anime(name_ru);
            CREATE INDEX IF NOT EXISTS idx_anime_name_en ON anime(name_en);
            CREATE INDEX IF NOT EXISTS idx_anime_rating ON anime(rating DESC);
            CREATE INDEX IF NOT EXISTS idx_history_user_date ON history(user_id, view_date DESC);
            CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
            CREATE INDEX IF NOT EXISTS idx_ratings_anime ON ratings(anime_id);
            """
        )
        conn.commit()


def init_sample_data() -> None:
    """Fill DB with 120 anime records if table is empty."""
    with db_connect() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
        if existing >= 100:
            return
        genres_pool = [
            "action", "adventure", "drama", "fantasy", "comedy", "romance",
            "mystery", "supernatural", "sci-fi", "slice-of-life", "sports", "thriller",
        ]
        types = ["TV", "Movie"]
        sources = [
            "Crunchyroll / Netflix",
            "Netflix / Prime Video",
            "Crunchyroll / AniLibria",
            "Prime Video / Wakanim",
            "Кинопоиск / Crunchyroll",
        ]
        adjectives = [
            "Лунный", "Стальной", "Алый", "Теневой", "Небесный",
            "Хрустальный", "Пылающий", "Звёздный", "Древний", "Скрытый",
        ]
        nouns = [
            "Клинок", "Путь", "Код", "Хроники", "Пульс",
            "Лабиринт", "Сигнал", "Рубеж", "Манифест", "Парадокс",
        ]
        suffixes = [
            "судьбы", "ветра", "пламени", "мечты", "бездны",
            "времени", "ночи", "рассвета", "памяти", "легенды",
        ]

        records: list[tuple[Any, ...]] = []
        random.seed(42)
        for idx in range(1, 121):
            ru_name = f"{adjectives[idx % len(adjectives)]} {nouns[idx % len(nouns)]} {suffixes[idx % len(suffixes)]}"
            en_name = f"{adjectives[idx % len(adjectives)]} {nouns[idx % len(nouns)]} of {suffixes[idx % len(suffixes)]}".title()
            g_count = 2 + (idx % 3)
            selected_genres = random.sample(genres_pool, g_count)
            description = (
                f"История #{idx}: герои сталкиваются с выбором между долгом и чувствами, "
                f"исследуя тайны мира и собственную силу."
            )
            year = 1998 + (idx % 28)
            rating = round(6.8 + ((idx * 17) % 32) / 10, 1)
            anime_type = types[idx % len(types)]
            source = sources[idx % len(sources)]
            records.append(
                (idx, ru_name, en_name, description, ", ".join(selected_genres), year, rating, anime_type, source)
            )

        conn.executemany(
            """
            INSERT OR REPLACE INTO anime
            (id, name_ru, name_en, description, genres, year, rating, type, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )
        conn.commit()


async def run_db(query: str, params: tuple = (), fetch: str | None = None, many: bool = False) -> Any:
    """Run SQL query in thread pool and optionally fetch results."""

    def worker() -> Any:
        with db_connect() as conn:
            cursor = conn.executemany(query, params) if many else conn.execute(query, params)
            if fetch == "one":
                return cursor.fetchone()
            if fetch == "all":
                return cursor.fetchall()
            conn.commit()
            return cursor.rowcount

    return await asyncio.to_thread(worker)


def build_main_menu() -> InlineKeyboardMarkup:
    """Build main menu keyboard."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Поиск", callback_data="help_search")],
            [InlineKeyboardButton("📋 Список", callback_data="list_0")],
            [InlineKeyboardButton("⭐ Топ", callback_data="top")],
            [InlineKeyboardButton("❤️ Избранное", callback_data="favorites")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")],
        ]
    )


def build_rating_buttons(anime_id: int) -> list[list[InlineKeyboardButton]]:
    """Build compact rating buttons 1..10."""
    row_1 = [InlineKeyboardButton(str(v), callback_data=f"rate_{anime_id}_{v}") for v in range(1, 6)]
    row_2 = [InlineKeyboardButton(str(v), callback_data=f"rate_{anime_id}_{v}") for v in range(6, 11)]
    return [row_1, row_2]


def build_anime_actions(anime_id: int) -> InlineKeyboardMarkup:
    """Build action keyboard for anime card."""
    rows = [[InlineKeyboardButton("❤️ В избранное", callback_data=f"favorite_{anime_id}")]]
    rows += [[InlineKeyboardButton("⭐ Оценить", callback_data=f"rate_prompt_{anime_id}")]]
    rows += [[InlineKeyboardButton("🔎 Похожие", callback_data=f"similar_{anime_id}")]]
    return InlineKeyboardMarkup(rows)


def build_pagination(page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """Build pagination keyboard for list pages."""
    buttons: list[InlineKeyboardButton] = []
    if has_prev:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"list_{page - 1}"))
    if has_next:
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"list_{page + 1}"))
    return InlineKeyboardMarkup([buttons]) if buttons else InlineKeyboardMarkup([])


def rating_stars(value: float) -> str:
    """Convert 10-point rating to 10-star visual string."""
    full = max(0, min(10, round(value)))
    return "★" * full + "☆" * (10 - full)


def format_genres(genre_csv: str) -> str:
    """Convert comma-separated genres into hashtags."""
    return " ".join(f"#{g.strip().replace(' ', '_')}" for g in genre_csv.split(",") if g.strip())


def format_anime_card(anime: sqlite3.Row) -> str:
    """Format beautiful anime card in HTML."""
    return (
        f"🎌 <b>{html.escape(anime['name_ru'])} / {html.escape(anime['name_en'])}</b>\n"
        f"🆔 ID: {anime['id']}\n\n"
        f"⭐ Рейтинг: {rating_stars(float(anime['rating']))} ({float(anime['rating']):.1f}/10)\n"
        f"🎭 Жанры: {format_genres(anime['genres'])}\n"
        f"📅 Год: {anime['year']}\n"
        f"📺 Тип: {html.escape(anime['type'])}\n"
        f"📡 Где смотреть: {html.escape(anime['source'])}\n\n"
        f"📖 <b>Описание:</b>\n{html.escape(anime['description'])}"
    )


async def ensure_user(user_id: int, username: str | None, first_name: str | None, last_name: str | None) -> None:
    """Register user if not exists."""
    await run_db(
        """
        INSERT INTO users (user_id, username, first_name, last_name, reg_date)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name
        """,
        (user_id, username, first_name, last_name, datetime.utcnow().isoformat()),
    )


async def fetch_anime_by_id(anime_id: int) -> sqlite3.Row | None:
    """Fetch single anime by id."""
    return await run_db("SELECT * FROM anime WHERE id = ?", (anime_id,), fetch="one")


async def fetch_search_results(text: str) -> list[sqlite3.Row]:
    """Search anime by partial match in RU/EN names."""
    term = f"%{text.strip()}%"
    return await run_db(
        "SELECT * FROM anime WHERE name_ru LIKE ? OR name_en LIKE ? ORDER BY rating DESC LIMIT 20",
        (term, term),
        fetch="all",
    )


async def fetch_anime_page(page: int) -> list[sqlite3.Row]:
    """Fetch one page of anime records."""
    offset = page * PAGE_SIZE
    return await run_db(
        "SELECT * FROM anime ORDER BY id LIMIT ? OFFSET ?",
        (PAGE_SIZE, offset),
        fetch="all",
    )


async def has_next_page(page: int) -> bool:
    """Check if list has next page."""
    offset = (page + 1) * PAGE_SIZE
    row = await run_db("SELECT id FROM anime ORDER BY id LIMIT 1 OFFSET ?", (offset,), fetch="one")
    return row is not None


async def fetch_top() -> list[sqlite3.Row]:
    """Fetch top anime by rating."""
    return await run_db("SELECT * FROM anime ORDER BY rating DESC, id ASC LIMIT ?", (TOP_LIMIT,), fetch="all")


async def toggle_favorite(user_id: int, anime_id: int) -> bool:
    """Add/remove favorite; return True when added, False when removed."""
    exists = await run_db(
        "SELECT 1 FROM favorites WHERE user_id = ? AND anime_id = ?",
        (user_id, anime_id),
        fetch="one",
    )
    if exists:
        await run_db("DELETE FROM favorites WHERE user_id = ? AND anime_id = ?", (user_id, anime_id))
        return False
    await run_db("INSERT INTO favorites (user_id, anime_id) VALUES (?, ?)", (user_id, anime_id))
    return True


async def fetch_favorites(user_id: int) -> list[sqlite3.Row]:
    """Fetch user favorites list."""
    return await run_db(
        """
        SELECT a.* FROM favorites f
        JOIN anime a ON a.id = f.anime_id
        WHERE f.user_id = ?
        ORDER BY a.rating DESC, a.name_ru ASC
        """,
        (user_id,),
        fetch="all",
    )


async def add_rating(user_id: int, anime_id: int, value: int) -> float:
    """Save user rating and recalculate anime average."""
    await run_db(
        """
        INSERT INTO ratings (user_id, anime_id, rating)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, anime_id) DO UPDATE SET rating=excluded.rating
        """,
        (user_id, anime_id, value),
    )
    avg_row = await run_db("SELECT AVG(rating) AS avg_rating FROM ratings WHERE anime_id = ?", (anime_id,), fetch="one")
    avg = float(avg_row["avg_rating"] or value)
    await run_db("UPDATE anime SET rating = ? WHERE id = ?", (round(avg, 2), anime_id))
    return avg


async def add_history(user_id: int, anime_id: int) -> None:
    """Log anime view in user history."""
    await run_db(
        "INSERT INTO history (user_id, anime_id, view_date) VALUES (?, ?, ?)",
        (user_id, anime_id, datetime.utcnow().isoformat()),
    )


async def fetch_similar(anime_id: int) -> list[sqlite3.Row]:
    """Find up to 3 anime with intersecting genres."""
    anime = await fetch_anime_by_id(anime_id)
    if not anime:
        return []
    genres = [g.strip() for g in anime["genres"].split(",") if g.strip()]
    if not genres:
        return []
    clause = " OR ".join(["genres LIKE ?" for _ in genres])
    params = tuple([f"%{g}%" for g in genres] + [anime_id, 3])
    query = f"SELECT * FROM anime WHERE ({clause}) AND id != ? ORDER BY rating DESC LIMIT ?"
    return await run_db(query, params, fetch="all")


async def send_anime_card(message, anime: sqlite3.Row) -> None:
    """Send formatted anime card with action buttons."""
    await message.reply_text(
        format_anime_card(anime),
        parse_mode=ParseMode.HTML,
        reply_markup=build_anime_actions(int(anime["id"])),
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with rich greeting."""
    try:
        user = update.effective_user
        await ensure_user(user.id, user.username, user.first_name, user.last_name)
        text = (
            "🎌 <b>Добро пожаловать в Anime Bot!</b>\n\n"
            "🔥 Здесь ты можешь:\n"
            "• Найти любое аниме\n"
            "• Смотреть рейтинги\n"
            "• Получать рекомендации\n"
            "• Сохранять в избранное\n\n"
            "Выбери действие ниже 👇"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=build_main_menu())
    except Exception:
        logger.exception("start_handler failed")
        if update.message:
            await update.message.reply_text("⚠️ Не удалось открыть меню. Попробуйте позже.")


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search <text> command."""
    try:
        user = update.effective_user
        await ensure_user(user.id, user.username, user.first_name, user.last_name)
        query = " ".join(context.args).strip()
        if not query:
            await update.message.reply_text("Использование: <code>/search название</code>", parse_mode=ParseMode.HTML)
            return
        rows = await fetch_search_results(query)
        if not rows:
            await update.message.reply_text("😔 Ничего не найдено. Попробуйте другое название.")
            return
        if len(rows) == 1:
            await add_history(user.id, int(rows[0]["id"]))
            await send_anime_card(update.message, rows[0])
            return
        lines = [f"🔍 <b>Найдено результатов:</b> {len(rows)}", ""]
        lines += [f"{r['id']}. {html.escape(r['name_ru'])} ⭐{float(r['rating']):.1f}" for r in rows]
        lines.append("\nОткрой карточку: <code>/id 123</code>")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("search_handler failed")
        if update.message:
            await update.message.reply_text("⚠️ Ошибка поиска. Попробуйте снова чуть позже.")


async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /id <number> command."""
    try:
        user = update.effective_user
        await ensure_user(user.id, user.username, user.first_name, user.last_name)
        if not context.args:
            await update.message.reply_text("Использование: <code>/id число</code>", parse_mode=ParseMode.HTML)
            return
        anime_id = int(context.args[0])
        anime = await fetch_anime_by_id(anime_id)
        if not anime:
            await update.message.reply_text("❌ Аниме с таким ID не найдено.")
            return
        await add_history(user.id, anime_id)
        await send_anime_card(update.message, anime)
    except ValueError:
        await update.message.reply_text("⚠️ ID должен быть целым числом.")
    except Exception:
        logger.exception("id_handler failed")
        if update.message:
            await update.message.reply_text("⚠️ Не удалось открыть карточку аниме.")


async def show_list_page(target_message, page: int) -> None:
    """Send paginated anime list to target message."""
    rows = await fetch_anime_page(page)
    if not rows:
        await target_message.reply_text("Список пуст.")
        return
    lines = [f"📋 <b>Каталог аниме</b> — страница {page + 1}", ""]
    lines += [f"{r['id']}. {html.escape(r['name_ru'])} ⭐{float(r['rating']):.1f}" for r in rows]
    markup = build_pagination(page, has_prev=page > 0, has_next=await has_next_page(page))
    await target_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=markup)


async def list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command."""
    try:
        await show_list_page(update.message, 0)
    except Exception:
        logger.exception("list_handler failed")
        if update.message:
            await update.message.reply_text("⚠️ Не удалось загрузить список.")


async def top_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /top command."""
    try:
        rows = await fetch_top()
        lines = ["⭐ <b>Топ-5 аниме по рейтингу</b>", ""]
        lines += [f"{i}. {html.escape(r['name_ru'])} — ⭐{float(r['rating']):.1f}" for i, r in enumerate(rows, 1)]
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("top_handler failed")
        if update.message:
            await update.message.reply_text("⚠️ Не удалось получить топ.")


async def favorites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /favorites command."""
    try:
        user = update.effective_user
        await ensure_user(user.id, user.username, user.first_name, user.last_name)
        rows = await fetch_favorites(user.id)
        if not rows:
            await update.message.reply_text("❤️ Избранное пока пустое. Добавь что-нибудь из карточки аниме.")
            return
        lines = ["❤️ <b>Твоё избранное</b>", ""]
        lines += [f"{r['id']}. {html.escape(r['name_ru'])} ⭐{float(r['rating']):.1f}" for r in rows]
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("favorites_handler failed")
        if update.message:
            await update.message.reply_text("⚠️ Не удалось получить избранное.")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    try:
        text = (
            "❓ <b>Помощь по командам</b>\n\n"
            "<code>/start</code> — главное меню\n"
            "<code>/search текст</code> — поиск аниме\n"
            "<code>/id число</code> — карточка по ID\n"
            "<code>/list</code> — список с пагинацией\n"
            "<code>/top</code> — топ-5\n"
            "<code>/favorites</code> — избранное\n"
            "<code>/help</code> — эта справка"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("help_handler failed")
        if update.message:
            await update.message.reply_text("⚠️ Не удалось открыть помощь.")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()
    try:
        user = update.effective_user
        await ensure_user(user.id, user.username, user.first_name, user.last_name)
        data = query.data or ""
        if data.startswith("list_"):
            page = max(0, int(data.split("_")[1]))
            await show_list_page(query.message, page)
            return
        if data == "top":
            rows = await fetch_top()
            text = "⭐ <b>Топ-5 аниме</b>\n\n" + "\n".join(
                f"{i}. {html.escape(r['name_ru'])} — ⭐{float(r['rating']):.1f}" for i, r in enumerate(rows, 1)
            )
            await query.message.reply_text(text, parse_mode=ParseMode.HTML)
            return
        if data == "favorites":
            rows = await fetch_favorites(user.id)
            if not rows:
                await query.message.reply_text("❤️ Избранное пока пустое.")
                return
            text = "❤️ <b>Твоё избранное</b>\n\n" + "\n".join(
                f"{r['id']}. {html.escape(r['name_ru'])} ⭐{float(r['rating']):.1f}" for r in rows
            )
            await query.message.reply_text(text, parse_mode=ParseMode.HTML)
            return
        if data == "help":
            await query.message.reply_text("Введи /help для списка всех команд.")
            return
        if data == "help_search":
            await query.message.reply_text("Напиши: <code>/search Naruto</code>", parse_mode=ParseMode.HTML)
            return
        if data.startswith("favorite_"):
            anime_id = int(data.split("_")[1])
            anime = await fetch_anime_by_id(anime_id)
            if not anime:
                await query.message.reply_text("❌ Аниме не найдено.")
                return
            added = await toggle_favorite(user.id, anime_id)
            text = "❤️ Добавлено в избранное!" if added else "💔 Удалено из избранного."
            await query.message.reply_text(text)
            return
        if data.startswith("similar_"):
            anime_id = int(data.split("_")[1])
            rows = await fetch_similar(anime_id)
            if not rows:
                await query.message.reply_text("🔎 Похожие аниме не найдены.")
                return
            text = "🔎 <b>Похожие аниме:</b>\n\n" + "\n".join(
                f"{r['id']}. {html.escape(r['name_ru'])} ⭐{float(r['rating']):.1f}" for r in rows
            )
            await query.message.reply_text(text, parse_mode=ParseMode.HTML)
            return
        if data.startswith("rate_prompt_"):
            anime_id = int(data.split("_")[2])
            await query.message.reply_text(
                "⭐ Выбери оценку от 1 до 10:",
                reply_markup=InlineKeyboardMarkup(build_rating_buttons(anime_id)),
            )
            return
        if data.startswith("rate_"):
            _, anime_id_str, value_str = data.split("_")
            anime_id = int(anime_id_str)
            value = int(value_str)
            if value < 1 or value > 10:
                await query.message.reply_text("⚠️ Оценка должна быть от 1 до 10.")
                return
            anime = await fetch_anime_by_id(anime_id)
            if not anime:
                await query.message.reply_text("❌ Аниме не найдено.")
                return
            new_avg = await add_rating(user.id, anime_id, value)
            await query.message.reply_text(f"✅ Оценка {value}/10 сохранена. Новый рейтинг: {new_avg:.2f}")
            refreshed = await fetch_anime_by_id(anime_id)
            if refreshed:
                await send_anime_card(query.message, refreshed)
            return
        await query.message.reply_text("Неизвестное действие. Используй /start")
    except Exception:
        logger.exception("callback_handler failed")
        await query.message.reply_text("⚠️ Ошибка обработки кнопки. Попробуйте позже.")


def build_application() -> Application:
    """Configure and return telegram application."""
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("search", search_handler))
    app.add_handler(CommandHandler("id", id_handler))
    app.add_handler(CommandHandler("list", list_handler))
    app.add_handler(CommandHandler("top", top_handler))
    app.add_handler(CommandHandler("favorites", favorites_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    return app


def main() -> None:
    """Initialize DB, seed data, and run bot."""
    if not BOT_TOKEN or BOT_TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН":
        raise ValueError("Укажите реальный BOT_TOKEN в config.py")
    init_db()
    init_sample_data()
    app = build_application()
    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
