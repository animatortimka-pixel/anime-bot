import logging
import random
import sqlite3
from contextlib import closing
from difflib import SequenceMatcher
from functools import lru_cache
from urllib.parse import quote_plus

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

DB_PATH = "anime_bot.db"
PAGE_SIZE = 5
TOTAL_ANIME_TARGET = 220

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("anime_bot")


REAL_ANIME = [
    ("Атака титанов", "Attack on Titan", 2013, "Экшен, Драма, Фэнтези", 25, "Человечество сражается с гигантами, чтобы выжить за стенами."),
    ("Наруто", "Naruto", 2002, "Экшен, Приключения, Комедия", 220, "История ниндзя Наруто, мечтающего стать Хокаге."),
    ("Наруто: Ураганные хроники", "Naruto Shippuden", 2007, "Экшен, Приключения", 500, "Продолжение пути Наруто и битв с Акацуки."),
    ("Ван-Пис", "One Piece", 1999, "Приключения, Комедия, Фэнтези", 1000, "Луффи и его команда ищут легендарное сокровище."),
    ("Блич", "Bleach", 2004, "Экшен, Сверхъестественное", 366, "Ичиго становится проводником душ и сражается с пустыми."),
    ("Стальной алхимик: Братство", "Fullmetal Alchemist: Brotherhood", 2009, "Экшен, Фэнтези, Драма", 64, "Братья Элрики ищут философский камень, чтобы вернуть тела."),
    ("Тетрадь смерти", "Death Note", 2006, "Триллер, Детектив, Сверхъестественное", 37, "Школьник находит тетрадь, способную убивать людей."),
    ("Клинок, рассекающий демонов", "Demon Slayer", 2019, "Экшен, Фэнтези", 26, "Тандзиро вступает в истребители демонов ради сестры."),
    ("Моя геройская академия", "My Hero Academia", 2016, "Экшен, Комедия, Школа", 13, "Мир суперсил и путь Мидории к званию героя."),
    ("Магическая битва", "Jujutsu Kaisen", 2020, "Экшен, Сверхъестественное", 24, "Итадори становится сосудом проклятия и учится сражаться."),
    ("Код Гиас", "Code Geass", 2006, "Меха, Драма, Триллер", 25, "Лелуш получает силу Гиаса и поднимает восстание."),
    ("Врата Штейна", "Steins;Gate", 2011, "Фантастика, Триллер", 24, "Группа друзей случайно открывает путешествия во времени."),
    ("Евангелион", "Neon Genesis Evangelion", 1995, "Меха, Драма, Психология", 26, "Подростки пилотируют Евы против загадочных Ангелов."),
    ("Токийский гуль", "Tokyo Ghoul", 2014, "Ужасы, Экшен", 12, "Канэки становится наполовину гулем и ищет своё место."),
    ("Реинкарнация безработного", "Mushoku Tensei", 2021, "Фэнтези, Приключения", 23, "Перерождение неудачника в магическом мире."),
    ("Re:Zero", "Re:Zero - Starting Life in Another World", 2016, "Фэнтези, Драма, Психология", 25, "Субару получает способность возвращаться после смерти."),
    ("Ковбой Бибоп", "Cowboy Bebop", 1998, "Фантастика, Экшен", 26, "Команда охотников за головами путешествует по космосу."),
    ("Хантер х Хантер", "Hunter x Hunter", 2011, "Приключения, Экшен", 148, "Гон отправляется на поиски отца и приключений."),
    ("Твоё имя", "Your Name", 2016, "Романтика, Драма, Фэнтези", 1, "Подростки таинственно меняются телами сквозь расстояние."),
    ("Форма голоса", "A Silent Voice", 2016, "Драма, Романтика", 1, "История искупления, дружбы и принятия себя."),
    ("Обещанный Неверленд", "The Promised Neverland", 2019, "Триллер, Мистика", 12, "Дети из приюта раскрывают страшную тайну."),
    ("Парад смерти", "Death Parade", 2015, "Психология, Драма", 12, "После смерти люди проходят испытания в странном баре."),
    ("Сага о Винланде", "Vinland Saga", 2019, "Экшен, Историческое, Драма", 24, "История мести и взросления в эпоху викингов."),
    ("Монстр", "Monster", 2004, "Триллер, Детектив, Драма", 74, "Врач преследует серийного убийцу, которого когда-то спас."),
    ("Человек-бензопила", "Chainsaw Man", 2022, "Экшен, Ужасы, Комедия", 12, "Дэндзи с демоническим псом сражается с чудовищами."),
    ("Семья шпиона", "Spy x Family", 2022, "Комедия, Экшен, Повседневность", 25, "Шпион создаёт фальшивую семью для миссии."),
    ("Доктор Стоун", "Dr. Stone", 2019, "Приключения, Фантастика", 24, "Мир окаменел, и Сенку возрождает цивилизацию наукой."),
    ("Психопаспорт", "Psycho-Pass", 2012, "Киберпанк, Детектив", 22, "Полиция будущего измеряет преступный потенциал людей."),
    ("Торадора!", "Toradora!", 2008, "Романтика, Комедия, Школа", 25, "Двое школьников помогают друг другу в любовных делах."),
    ("Кагуя-sama: В любви как на войне", "Kaguya-sama: Love Is War", 2019, "Романтика, Комедия, Школа", 12, "Гениальные школьники превращают признание в битву умов."),
]

RANDOM_TITLES_1 = ["Хроники", "Легенда", "Пламя", "Тень", "Код", "Пульс", "Меч", "Небо", "Песнь", "Эхо"]
RANDOM_TITLES_2 = ["Астры", "Дракона", "Бездны", "Феникса", "Титана", "Судьбы", "Зари", "Пустоты", "Ветра", "Горизонта"]
GENRES_POOL = [
    "Экшен",
    "Фэнтези",
    "Комедия",
    "Романтика",
    "Приключения",
    "Драма",
    "Фантастика",
    "Школа",
    "Мистика",
    "Триллер",
]

QUOTES = [
    "Если не рискуешь, не узнаешь, где твой предел.",
    "Сила не в кулаках, а в том, ради кого ты дерёшься.",
    "Даже тьма отступает, когда ты идёшь вперёд.",
    "Мечта — это обещание самому себе.",
    "Боль временна, легенда вечна.",
    "Тот, кто улыбается после поражения, уже победил себя.",
    "Доверие — сильнейшая техника команды.",
    "Каждый день — новая арка твоей истории.",
    "Сомнения громкие, но сердце знает путь.",
    "Даже слабый может стать героем, если не сдаётся.",
]

MEMES = [
    "https://i.imgflip.com/1bij.jpg",
    "https://i.imgflip.com/26am.jpg",
    "https://i.imgflip.com/2fm6x.jpg",
    "https://i.imgflip.com/4t0m5.jpg",
    "https://i.imgflip.com/30b1gx.jpg",
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS anime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT NOT NULL,
                name_en TEXT NOT NULL,
                year INTEGER NOT NULL,
                genres TEXT NOT NULL,
                episodes INTEGER NOT NULL,
                description TEXT NOT NULL,
                base_rating REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                state TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, anime_id)
            );

            CREATE TABLE IF NOT EXISTS ratings (
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, anime_id)
            );

            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS memes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_anime_year ON anime(year);
            CREATE INDEX IF NOT EXISTS idx_anime_genres ON anime(genres);
            CREATE INDEX IF NOT EXISTS idx_ratings_anime ON ratings(anime_id);
            CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
            """
        )

        anime_count = conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
        if anime_count == 0:
            conn.executemany(
                """
                INSERT INTO anime (name_ru, name_en, year, genres, episodes, description, base_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [(*item, round(random.uniform(7.2, 9.5), 1)) for item in REAL_ANIME],
            )

            to_generate = max(0, TOTAL_ANIME_TARGET - len(REAL_ANIME))
            generated = []
            for i in range(to_generate):
                ru = f"{random.choice(RANDOM_TITLES_1)} {random.choice(RANDOM_TITLES_2)} {i + 1}"
                en = f"{random.choice(['Chronicles', 'Legend', 'Blade', 'Sky', 'Code'])} of {random.choice(['Astra', 'Void', 'Titan', 'Fate', 'Dawn'])} {i + 1}"
                year = random.randint(1995, 2026)
                genres = ", ".join(sorted(random.sample(GENRES_POOL, k=random.randint(2, 3))))
                episodes = random.randint(12, 24)
                desc = f"Захватывающее аниме о приключениях, дружбе и испытаниях. Сезон {random.randint(1, 4)}."
                base_rating = round(random.uniform(6.0, 9.3), 1)
                generated.append((ru, en, year, genres, episodes, desc, base_rating))

            conn.executemany(
                """
                INSERT INTO anime (name_ru, name_en, year, genres, episodes, description, base_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                generated,
            )

        quote_count = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
        if quote_count == 0:
            conn.executemany("INSERT OR IGNORE INTO quotes (quote) VALUES (?)", [(q,) for q in QUOTES])

        meme_count = conn.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
        if meme_count == 0:
            conn.executemany("INSERT OR IGNORE INTO memes (url) VALUES (?)", [(m,) for m in MEMES])


def upsert_user(user_id: int, username: str | None) -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username
            """,
            (user_id, username or ""),
        )


def set_user_state(user_id: int, state: str) -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute("UPDATE users SET state=? WHERE user_id=?", (state, user_id))


def get_user_state(user_id: int) -> str:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT state FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else ""


@lru_cache(maxsize=1024)
def get_anime_cached(anime_id: int) -> sqlite3.Row | None:
    with closing(get_conn()) as conn:
        return conn.execute("SELECT * FROM anime WHERE id=?", (anime_id,)).fetchone()


def get_avg_rating(anime_id: int) -> float:
    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT COALESCE(AVG(rating), (SELECT base_rating FROM anime WHERE id=?)) as avg_r
            FROM ratings WHERE anime_id=?
            """,
            (anime_id, anime_id),
        ).fetchone()
        return round(float(row[0] or 0.0), 2)


def anime_card_text(anime: sqlite3.Row) -> str:
    avg = get_avg_rating(int(anime["id"]))
    return (
        f"🎬 {anime['name_ru']}\n"
        f"🇺🇸 {anime['name_en']}\n"
        f"📅 {anime['year']}\n"
        f"⭐ {avg}\n"
        f"🎭 {anime['genres']}\n"
        f"📺 Серии: {anime['episodes']}\n\n"
        f"📝 {anime['description']}"
    )


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Поиск", callback_data="menu:search"), InlineKeyboardButton("🎲 Случайное", callback_data="menu:random"), InlineKeyboardButton("📚 Список", callback_data="menu:list:0")],
            [InlineKeyboardButton("🏆 Топ", callback_data="menu:top"), InlineKeyboardButton("🎯 Рекомендации", callback_data="menu:recommend"), InlineKeyboardButton("🎭 Жанры", callback_data="menu:genres")],
            [InlineKeyboardButton("❤️ Избранное", callback_data="menu:favorites:0"), InlineKeyboardButton("💬 Цитата", callback_data="menu:quote"), InlineKeyboardButton("😂 Мем", callback_data="menu:meme")],
        ]
    )


def anime_card_kb(anime_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎬 Смотреть", callback_data=f"watch:{anime_id}"), InlineKeyboardButton("⭐ Оценить", callback_data=f"rate_menu:{anime_id}")],
            [InlineKeyboardButton("❤️ Избранное", callback_data=f"fav_toggle:{anime_id}"), InlineKeyboardButton("📋 Похожие", callback_data=f"similar:{anime_id}")],
            [InlineKeyboardButton("🎲 Случайное", callback_data="menu:random"), InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
        ]
    )


def pager_kb(prefix: str, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    row = []
    if has_prev:
        row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}:{page - 1}"))
    if has_next:
        row.append(InlineKeyboardButton("➡️ Вперёд", callback_data=f"{prefix}:{page + 1}"))
    row.append(InlineKeyboardButton("🏠 Меню", callback_data="menu:home"))
    return InlineKeyboardMarkup([row])


def search_anime(query: str, limit: int = 10) -> list[sqlite3.Row]:
    q = query.strip().lower()
    if not q:
        return []
    with closing(get_conn()) as conn:
        candidates = conn.execute("SELECT * FROM anime").fetchall()

    def score(item: sqlite3.Row) -> float:
        name_ru = item["name_ru"].lower()
        name_en = item["name_en"].lower()
        genres = item["genres"].lower()
        year = str(item["year"])

        s = 0.0
        if q in name_ru:
            s += 80
        if q in name_en:
            s += 70
        if q in genres:
            s += 55
        if q == year or q in year:
            s += 40

        s += SequenceMatcher(None, q, name_ru).ratio() * 45
        s += SequenceMatcher(None, q, name_en).ratio() * 40
        s += SequenceMatcher(None, q, genres).ratio() * 28
        return s

    ranked = sorted(candidates, key=score, reverse=True)
    filtered = [x for x in ranked if score(x) > 20]
    return filtered[:limit]


async def show_home(target, edit: bool = True):
    text = (
        "🎬 ANIME BOT\n"
        "━━━━━━━━━━━━━━\n"
        "🔥 Найду любое аниме\n"
        "⭐ Подберу под тебя\n"
        "🎯 Дам рекомендации"
    )
    if edit:
        await target.edit_message_text(text, reply_markup=main_menu_kb())
    else:
        await target.reply_text(text, reply_markup=main_menu_kb())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.username)
    if update.message:
        await show_home(update.message, edit=False)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    upsert_user(user.id, user.username)

    try:
        data = query.data or ""

        if data == "menu:home":
            await show_home(query)
            return

        if data == "menu:search":
            set_user_state(user.id, "search")
            await query.edit_message_text(
                "🔍 Введи запрос (название, жанр или год).\nНапример: титан, fantasy, 2019",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]),
            )
            return

        if data == "menu:random":
            with closing(get_conn()) as conn:
                row = conn.execute("SELECT id FROM anime ORDER BY RANDOM() LIMIT 1").fetchone()
            if row:
                await show_anime_card(query, int(row["id"]))
            return

        if data.startswith("menu:list:"):
            page = int(data.split(":")[-1])
            await show_anime_list(query, page)
            return

        if data == "menu:top":
            await show_top(query)
            return

        if data == "menu:recommend":
            await show_recommendations(query, user.id)
            return

        if data == "menu:genres":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Экшен", callback_data="genre:Экшен"), InlineKeyboardButton("Фэнтези", callback_data="genre:Фэнтези")],
                [InlineKeyboardButton("Комедия", callback_data="genre:Комедия"), InlineKeyboardButton("Романтика", callback_data="genre:Романтика")],
                [InlineKeyboardButton("Приключения", callback_data="genre:Приключения")],
                [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
            ])
            await query.edit_message_text("🎭 Выбери жанр:", reply_markup=kb)
            return

        if data.startswith("genre:"):
            genre = data.split(":", 1)[1]
            with closing(get_conn()) as conn:
                rows = conn.execute(
                    "SELECT id FROM anime WHERE genres LIKE ? ORDER BY year DESC LIMIT 20",
                    (f"%{genre}%",),
                ).fetchall()
            if not rows:
                await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
                return
            await show_anime_card(query, int(random.choice(rows)["id"]))
            return

        if data.startswith("anime:"):
            anime_id = int(data.split(":")[-1])
            await show_anime_card(query, anime_id)
            return

        if data.startswith("watch:"):
            anime_id = int(data.split(":")[-1])
            await show_watch_links(query, anime_id)
            return

        if data.startswith("rate_menu:"):
            anime_id = int(data.split(":")[-1])
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("1⭐", callback_data=f"rate:{anime_id}:1"), InlineKeyboardButton("2⭐", callback_data=f"rate:{anime_id}:2"), InlineKeyboardButton("3⭐", callback_data=f"rate:{anime_id}:3")],
                [InlineKeyboardButton("4⭐", callback_data=f"rate:{anime_id}:4"), InlineKeyboardButton("5⭐", callback_data=f"rate:{anime_id}:5")],
                [InlineKeyboardButton("⬅️ Назад", callback_data=f"anime:{anime_id}")],
            ])
            await query.edit_message_text("⭐ Выбери оценку:", reply_markup=kb)
            return

        if data.startswith("rate:"):
            _, anime_id_raw, rating_raw = data.split(":")
            anime_id = int(anime_id_raw)
            rating = int(rating_raw)
            with closing(get_conn()) as conn, conn:
                conn.execute(
                    """
                    INSERT INTO ratings (user_id, anime_id, rating, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, anime_id)
                    DO UPDATE SET rating=excluded.rating, updated_at=CURRENT_TIMESTAMP
                    """,
                    (user.id, anime_id, rating),
                )
            get_anime_cached.cache_clear()
            await show_anime_card(query, anime_id)
            return

        if data.startswith("fav_toggle:"):
            anime_id = int(data.split(":")[-1])
            with closing(get_conn()) as conn, conn:
                exists = conn.execute(
                    "SELECT 1 FROM favorites WHERE user_id=? AND anime_id=?",
                    (user.id, anime_id),
                ).fetchone()
                if exists:
                    conn.execute("DELETE FROM favorites WHERE user_id=? AND anime_id=?", (user.id, anime_id))
                else:
                    conn.execute("INSERT INTO favorites (user_id, anime_id) VALUES (?, ?)", (user.id, anime_id))
            await show_anime_card(query, anime_id)
            return

        if data.startswith("similar:"):
            anime_id = int(data.split(":")[-1])
            source = get_anime_cached(anime_id)
            if not source:
                await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
                return
            main_genre = source["genres"].split(",")[0].strip()
            with closing(get_conn()) as conn:
                rows = conn.execute(
                    """
                    SELECT id FROM anime
                    WHERE id != ? AND genres LIKE ?
                    ORDER BY RANDOM() LIMIT 1
                    """,
                    (anime_id, f"%{main_genre}%"),
                ).fetchone()
            if not rows:
                await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
                return
            await show_anime_card(query, int(rows["id"]))
            return

        if data.startswith("menu:favorites:"):
            page = int(data.split(":")[-1])
            await show_favorites(query, user.id, page)
            return

        if data == "menu:quote":
            await show_quote(query)
            return

        if data == "quote:more":
            await show_quote(query)
            return

        if data == "menu:meme":
            await show_meme(query)
            return

        if data == "meme:more":
            await show_meme(query)
            return

        await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
    except Exception as exc:
        logger.exception("Callback error: %s", exc)
        await safe_edit(query, "⚠️ Произошла ошибка. Попробуй ещё раз.", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))


async def safe_edit(query, text: str, markup: InlineKeyboardMarkup | None = None):
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except BadRequest:
        await query.message.reply_text(text, reply_markup=markup)


async def show_anime_card(query, anime_id: int):
    anime = get_anime_cached(anime_id)
    if not anime:
        await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    await query.edit_message_text(anime_card_text(anime), reply_markup=anime_card_kb(anime_id))


async def show_watch_links(query, anime_id: int):
    anime = get_anime_cached(anime_id)
    if not anime:
        await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    name = anime["name_ru"]
    anilibria = f"https://anilibria.top/search?q={quote_plus(name)}"
    shikimori = f"https://shikimori.one/animes?search={quote_plus(name)}"
    youtube = f"https://youtube.com/results?search_query={quote_plus(name + ' аниме')}"
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Anilibria", url=anilibria)],
            [InlineKeyboardButton("📖 Shikimori", url=shikimori)],
            [InlineKeyboardButton("🎥 YouTube", url=youtube)],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"anime:{anime_id}")],
        ]
    )
    await query.edit_message_text(f"🎥 Где смотреть: {name}", reply_markup=kb)


async def show_anime_list(query, page: int):
    offset = max(0, page) * PAGE_SIZE
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT id, name_ru, year FROM anime ORDER BY id LIMIT ? OFFSET ?",
            (PAGE_SIZE + 1, offset),
        ).fetchall()
    if not rows:
        await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    has_next = len(rows) > PAGE_SIZE
    current = rows[:PAGE_SIZE]
    lines = ["📚 Список аниме:"]
    kb_rows = []
    for item in current:
        lines.append(f"• {item['name_ru']} ({item['year']})")
        kb_rows.append([InlineKeyboardButton(f"🎬 {item['name_ru'][:28]}", callback_data=f"anime:{item['id']}")])
    nav = pager_kb("menu:list", page, page > 0, has_next)
    kb_rows.extend(nav.inline_keyboard)
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb_rows))


async def show_top(query):
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.name_ru, ROUND(COALESCE(AVG(r.rating), a.base_rating), 2) as avg_rating
            FROM anime a
            LEFT JOIN ratings r ON r.anime_id = a.id
            GROUP BY a.id
            ORDER BY avg_rating DESC, a.year DESC
            LIMIT 10
            """
        ).fetchall()
    if not rows:
        await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    lines = ["🏆 Топ аниме:"]
    kb_rows = []
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. {row['name_ru']} — ⭐ {row['avg_rating']}")
        kb_rows.append([InlineKeyboardButton(f"#{i} {row['name_ru'][:26]}", callback_data=f"anime:{row['id']}")])
    kb_rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu:home")])
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb_rows))


async def show_recommendations(query, user_id: int):
    with closing(get_conn()) as conn:
        fav_genres = conn.execute(
            """
            SELECT a.genres FROM favorites f
            JOIN anime a ON a.id=f.anime_id
            WHERE f.user_id=?
            LIMIT 20
            """,
            (user_id,),
        ).fetchall()
    if fav_genres:
        pool = []
        for row in fav_genres:
            pool.extend([g.strip() for g in row["genres"].split(",")])
        genre = random.choice(pool)
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id FROM anime WHERE genres LIKE ? ORDER BY RANDOM() LIMIT 1", (f"%{genre}%",)).fetchone()
    else:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id FROM anime ORDER BY RANDOM() LIMIT 1").fetchone()
    if not row:
        await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    await show_anime_card(query, int(row["id"]))


async def show_favorites(query, user_id: int, page: int):
    offset = max(0, page) * PAGE_SIZE
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.name_ru, a.year
            FROM favorites f JOIN anime a ON a.id=f.anime_id
            WHERE f.user_id=?
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, PAGE_SIZE + 1, offset),
        ).fetchall()
    if not rows:
        await query.edit_message_text("❤️ Избранное пусто", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    has_next = len(rows) > PAGE_SIZE
    current = rows[:PAGE_SIZE]
    lines = ["❤️ Твоё избранное:"]
    kb_rows = []
    for item in current:
        lines.append(f"• {item['name_ru']} ({item['year']})")
        kb_rows.append([InlineKeyboardButton(f"🎬 {item['name_ru'][:28]}", callback_data=f"anime:{item['id']}")])
    nav = pager_kb("menu:favorites", page, page > 0, has_next)
    kb_rows.extend(nav.inline_keyboard)
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb_rows))


async def show_quote(query):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT quote FROM quotes ORDER BY RANDOM() LIMIT 1").fetchone()
    text = f"💬 {row['quote']}" if row else "❌ Не найдено"
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💬 Ещё", callback_data="quote:more")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
        ]
    )
    await query.edit_message_text(text, reply_markup=kb)


async def show_meme(query):
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT url FROM memes ORDER BY RANDOM() LIMIT 1").fetchone()
    if not row:
        await query.edit_message_text("❌ Не найдено", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("😂 Ещё", callback_data="meme:more")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
        ]
    )
    try:
        await query.edit_message_media(media=InputMediaPhoto(media=row["url"], caption="😂 Аниме-мем"), reply_markup=kb)
    except BadRequest:
        await query.message.reply_photo(photo=row["url"], caption="😂 Аниме-мем", reply_markup=kb)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    user = update.effective_user
    upsert_user(user.id, user.username)
    state = get_user_state(user.id)

    try:
        if state == "search":
            query_text = (update.message.text or "").strip()
            results = search_anime(query_text)
            set_user_state(user.id, "")
            if not results:
                await update.message.reply_text(
                    "❌ Не найдено",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]),
                )
                return

            kb_rows = []
            lines = [f"🔍 Результаты для: {query_text}"]
            for item in results[:10]:
                lines.append(f"• {item['name_ru']} ({item['year']})")
                kb_rows.append([InlineKeyboardButton(f"🎬 {item['name_ru'][:28]}", callback_data=f"anime:{item['id']}")])
            kb_rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu:home")])
            await update.message.reply_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb_rows))
            return

        await update.message.reply_text(
            "Используй /start для открытия меню",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]),
        )
    except Exception as exc:
        logger.exception("Text handler error: %s", exc)
        await update.message.reply_text("⚠️ Ошибка. Попробуй снова через /start")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)


def main() -> None:
    init_db()
    token = "PASTE_YOUR_TOKEN_HERE"
    if not token or token == "PASTE_YOUR_TOKEN_HERE":
        print("❌ Укажи токен бота в main.py: token = \"PASTE_YOUR_TOKEN_HERE\"")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_error_handler(on_error)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
