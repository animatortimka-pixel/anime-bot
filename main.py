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
TOTAL_ANIME_TARGET = 230

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("anime_bot")

REAL_ANIME = [
    ("Атака титанов", "Attack on Titan", 2013, "Экшен, Драма, Фэнтези", 25, "Человечество ведёт отчаянную войну с титанами за стенами последнего города.", 9.0),
    ("Наруто", "Naruto", 2002, "Экшен, Приключения, Комедия", 220, "Юный ниндзя Наруто мечтает стать Хокаге и заслужить признание деревни.", 8.2),
    ("Наруто: Ураганные хроники", "Naruto Shippuden", 2007, "Экшен, Приключения, Драма", 500, "Наруто возвращается сильнее и сталкивается с Акацуки и судьбой мира шиноби.", 8.7),
    ("Ван-Пис", "One Piece", 1999, "Приключения, Комедия, Фэнтези", 1100, "Луффи собирает пиратскую команду и отправляется за сокровищем One Piece.", 9.1),
    ("Блич", "Bleach", 2004, "Экшен, Сверхъестественное, Приключения", 366, "Ичиго Куросаки получает силу синигами и вступает в битву с пустыми.", 8.0),
    ("Стальной алхимик: Братство", "Fullmetal Alchemist: Brotherhood", 2009, "Экшен, Фэнтези, Драма", 64, "Братья Элрики ищут философский камень после страшного алхимического ритуала.", 9.2),
    ("Тетрадь смерти", "Death Note", 2006, "Триллер, Детектив, Сверхъестественное", 37, "Лайт Ягами находит тетрадь смерти и вступает в интеллектуальную дуэль с L.", 8.9),
    ("Клинок, рассекающий демонов", "Demon Slayer", 2019, "Экшен, Фэнтези, Приключения", 55, "Танджиро становится охотником на демонов, чтобы спасти сестру Незуко.", 8.6),
    ("Моя геройская академия", "My Hero Academia", 2016, "Экшен, Комедия, Школа", 138, "В мире причуд Изуку Мидория идёт к мечте стать героем номер один.", 8.1),
    ("Магическая битва", "Jujutsu Kaisen", 2020, "Экшен, Сверхъестественное, Школа", 47, "Итадори вступает в токийский техникум магии, сражаясь с проклятиями.", 8.5),
    ("Код Гиас", "Code Geass", 2006, "Меха, Драма, Триллер", 50, "Лелуш получает Гиас и под маской Зеро поднимает революцию против империи.", 8.8),
    ("Врата Штейна", "Steins;Gate", 2011, "Фантастика, Триллер, Драма", 24, "Самопровозглашённый безумный учёный случайно запускает цепь временных парадоксов.", 9.0),
    ("Евангелион", "Neon Genesis Evangelion", 1995, "Меха, Драма, Психология", 26, "Подростки пилотируют Евангелионы и пытаются понять себя на фоне апокалипсиса.", 8.4),
    ("Токийский гуль", "Tokyo Ghoul", 2014, "Ужасы, Экшен, Психология", 48, "Канэки становится полугулем и вынужден жить между двумя враждующими мирами.", 7.8),
    ("Re:Zero", "Re:Zero - Starting Life in Another World", 2016, "Фэнтези, Драма, Психология", 50, "Субару получает способность возвращаться после смерти и меняет судьбу друзей.", 8.4),
    ("Ковбой Бибоп", "Cowboy Bebop", 1998, "Фантастика, Экшен, Драма", 26, "Команда охотников за головами путешествует по галактике под джазовый ритм.", 8.9),
    ("Хантер х Хантер", "Hunter x Hunter", 2011, "Приключения, Экшен, Фэнтези", 148, "Гон проходит экзамен на хантера и узнаёт цену силы и дружбы.", 9.0),
    ("Твоё имя", "Your Name", 2016, "Романтика, Драма, Фэнтези", 1, "Таки и Мицуха внезапно начинают меняться телами, связывая города и судьбы.", 8.7),
    ("Форма голоса", "A Silent Voice", 2016, "Драма, Романтика, Школа", 1, "История искупления бывшего хулигана и глухой девочки, которую он обидел.", 8.6),
    ("Обещанный Неверленд", "The Promised Neverland", 2019, "Триллер, Мистика, Драма", 23, "Дети из приюта раскрывают страшную тайну и планируют побег.", 8.3),
    ("Сага о Винланде", "Vinland Saga", 2019, "Экшен, Историческое, Драма", 48, "Торфинн идёт по пути мести в эпоху викингов и поисков истинной свободы.", 8.8),
    ("Монстр", "Monster", 2004, "Триллер, Детектив, Драма", 74, "Хирург Тэмма охотится на чудовище, которого когда-то спас собственными руками.", 8.9),
    ("Человек-бензопила", "Chainsaw Man", 2022, "Экшен, Ужасы, Комедия", 12, "Дэндзи сливается с демоном-бензопилой и попадает в опасный мир охотников.", 8.2),
    ("Семья шпиона", "Spy x Family", 2022, "Комедия, Экшен, Повседневность", 37, "Шпион, убийца и телепат создают семью ради миссии и неожиданной теплоты.", 8.5),
    ("Доктор Стоун", "Dr. Stone", 2019, "Приключения, Фантастика, Комедия", 57, "После окаменения человечества Сенку возвращает цивилизацию с помощью науки.", 8.3),
    ("Психопаспорт", "Psycho-Pass", 2012, "Киберпанк, Детектив, Триллер", 41, "В антиутопии индекс преступности решает судьбу каждого человека.", 8.2),
    ("Торадора!", "Toradora!", 2008, "Романтика, Комедия, Школа", 25, "Рюдзи и Тайга помогают друг другу в любви, но находят нечто большее.", 8.1),
    ("Кагуя-sama: В любви как на войне", "Kaguya-sama: Love Is War", 2019, "Романтика, Комедия, Школа", 37, "Два гения превращают признание в любви в психологическую войну.", 8.7),
    ("Реинкарнация безработного", "Mushoku Tensei", 2021, "Фэнтези, Приключения, Драма", 47, "Безработный затворник перерождается в другом мире и проживает жизнь заново.", 8.4),
    ("Самурай Чамплу", "Samurai Champloo", 2004, "Экшен, Приключения, Комедия", 26, "Троица странников путешествует по Японии Эдо под хип-хоп ритм.", 8.5),
]

RANDOM_WORDS_RU_1 = [
    "Хроники",
    "Легенда",
    "Пламя",
    "Тень",
    "Код",
    "Меч",
    "Небо",
    "Песнь",
    "Импульс",
    "Осколки",
]
RANDOM_WORDS_RU_2 = [
    "Астры",
    "Бездны",
    "Дракона",
    "Титана",
    "Судьбы",
    "Зари",
    "Пустоты",
    "Ветра",
    "Горизонта",
    "Луны",
]
RANDOM_WORDS_EN_1 = ["Chronicles", "Legend", "Flame", "Shadow", "Code", "Blade", "Sky", "Pulse", "Echo", "Fragments"]
RANDOM_WORDS_EN_2 = ["Astra", "Abyss", "Dragon", "Titan", "Fate", "Dawn", "Void", "Wind", "Horizon", "Moon"]
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
    "https://i.imgur.com/uXQ3Q8M.jpeg",
    "https://i.imgur.com/XV8O0m7.jpeg",
    "https://i.imgur.com/jxQ6vQx.jpeg",
    "https://i.imgur.com/f7sQpYB.jpeg",
    "https://i.imgur.com/5xQ4Q2f.jpeg",
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
                description TEXT NOT NULL,
                genres TEXT NOT NULL,
                rating REAL NOT NULL,
                episodes INTEGER NOT NULL
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

            CREATE INDEX IF NOT EXISTS idx_anime_name_ru ON anime(name_ru);
            CREATE INDEX IF NOT EXISTS idx_anime_name_en ON anime(name_en);
            CREATE INDEX IF NOT EXISTS idx_anime_year ON anime(year);
            CREATE INDEX IF NOT EXISTS idx_ratings_anime ON ratings(anime_id);
            CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
            """
        )

        anime_count = conn.execute("SELECT COUNT(*) FROM anime").fetchone()[0]
        if anime_count == 0:
            conn.executemany(
                """
                INSERT INTO anime (name_ru, name_en, year, description, genres, rating, episodes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                REAL_ANIME,
            )

            generated = []
            to_generate = max(0, TOTAL_ANIME_TARGET - len(REAL_ANIME))
            for i in range(to_generate):
                title_ru = f"{random.choice(RANDOM_WORDS_RU_1)} {random.choice(RANDOM_WORDS_RU_2)} {i + 1}"
                title_en = f"{random.choice(RANDOM_WORDS_EN_1)} of {random.choice(RANDOM_WORDS_EN_2)} {i + 1}"
                year = random.randint(1995, 2026)
                genres = ", ".join(sorted(random.sample(GENRES_POOL, random.randint(2, 3))))
                episodes = random.choice([12, 13, 24, 25])
                desc = (
                    "Динамичная история о дружбе, выборе и столкновении идеалов в мире, "
                    "где героев проверяют на прочность в каждой арке."
                )
                rating = round(random.uniform(6.2, 9.1), 1)
                generated.append((title_ru, title_en, year, desc, genres, rating, episodes))

            conn.executemany(
                """
                INSERT INTO anime (name_ru, name_en, year, description, genres, rating, episodes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                generated,
            )

        if conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0] == 0:
            conn.executemany("INSERT OR IGNORE INTO quotes (quote) VALUES (?)", [(q,) for q in QUOTES])

        if conn.execute("SELECT COUNT(*) FROM memes").fetchone()[0] == 0:
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


def set_state(user_id: int, state: str) -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute("UPDATE users SET state=? WHERE user_id=?", (state, user_id))


def get_state(user_id: int) -> str:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT state FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else ""


@lru_cache(maxsize=2048)
def get_anime(anime_id: int) -> sqlite3.Row | None:
    with closing(get_conn()) as conn:
        return conn.execute("SELECT * FROM anime WHERE id=?", (anime_id,)).fetchone()


def avg_rating(anime_id: int) -> float:
    with closing(get_conn()) as conn:
        row = conn.execute(
            """
            SELECT COALESCE(AVG(r.rating), (SELECT rating FROM anime WHERE id=?)) AS avg_r
            FROM ratings r
            WHERE r.anime_id=?
            """,
            (anime_id, anime_id),
        ).fetchone()
    return round(float(row[0] or 0.0), 2)


def short_desc(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def anime_card_text(row: sqlite3.Row) -> str:
    return (
        f"🎬 {row['name_ru']}\n"
        f"🇺🇸 {row['name_en']}\n"
        f"📅 {row['year']}\n"
        f"⭐ {avg_rating(int(row['id']))}\n"
        f"🎭 {row['genres']}\n"
        f"📺 Серии: {row['episodes']}\n\n"
        f"📝 {short_desc(row['description'], 200)}"
    )


def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔍 Поиск", callback_data="menu:search"),
                InlineKeyboardButton("🎲 Случайное", callback_data="menu:random"),
                InlineKeyboardButton("📚 Список", callback_data="menu:list:0"),
            ],
            [
                InlineKeyboardButton("🏆 Топ", callback_data="menu:top"),
                InlineKeyboardButton("🎯 Рекомендации", callback_data="menu:recommend"),
                InlineKeyboardButton("🎭 Жанры", callback_data="menu:genres"),
            ],
            [
                InlineKeyboardButton("❤️ Избранное", callback_data="menu:fav:0"),
                InlineKeyboardButton("💬 Цитата", callback_data="menu:quote"),
                InlineKeyboardButton("😂 Мем", callback_data="menu:meme"),
            ],
        ]
    )


def anime_card_kb(anime_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("▶️ Смотреть", callback_data=f"watch:{anime_id}"),
                InlineKeyboardButton("⭐ Оценить", callback_data=f"rate_menu:{anime_id}"),
            ],
            [
                InlineKeyboardButton("❤️ Избранное", callback_data=f"fav_toggle:{anime_id}"),
                InlineKeyboardButton("📋 Похожие", callback_data=f"similar:{anime_id}"),
            ],
            [
                InlineKeyboardButton("🎲 Случайное", callback_data="menu:random"),
                InlineKeyboardButton("🏠 Меню", callback_data="menu:home"),
            ],
        ]
    )


def pager(prefix: str, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    row = []
    if has_prev:
        row.append(InlineKeyboardButton("◀ Назад", callback_data=f"{prefix}:{page - 1}"))
    if has_next:
        row.append(InlineKeyboardButton("▶ Вперёд", callback_data=f"{prefix}:{page + 1}"))
    row.append(InlineKeyboardButton("🏠 Меню", callback_data="menu:home"))
    return InlineKeyboardMarkup([row])


def search_anime(query: str, limit: int = 15) -> list[sqlite3.Row]:
    q = " ".join((query or "").lower().strip().split())
    if not q:
        return []

    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT * FROM anime").fetchall()

    q_tokens = q.split()

    def sim(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    scored: list[tuple[float, sqlite3.Row]] = []
    for row in rows:
        ru = row["name_ru"].lower()
        en = row["name_en"].lower()
        genres = row["genres"].lower()
        desc = row["description"].lower()
        year = str(row["year"])

        score = 0.0
        blob = f"{ru} {en} {genres} {desc} {year}"

        if q in ru:
            score += 90
        if q in en:
            score += 80
        if q in genres:
            score += 65
        if q in desc:
            score += 45
        if q in year:
            score += 50

        score += sim(q, ru) * 55
        score += sim(q, en) * 50
        score += sim(q, genres) * 35
        score += sim(q, desc[:140]) * 25

        token_bonus = 0.0
        for token in q_tokens:
            if token in blob:
                token_bonus += 14
            token_bonus += sim(token, ru) * 10
            token_bonus += sim(token, en) * 9
            token_bonus += sim(token, genres) * 7
            token_bonus += sim(token, year) * 8
        score += token_bonus

        if score > 34:
            scored.append((score, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:limit]]


async def safe_edit(query, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except BadRequest:
        await query.message.reply_text(text, reply_markup=markup)


async def safe_edit_photo(query, photo_url: str, caption: str, markup: InlineKeyboardMarkup) -> None:
    try:
        await query.edit_message_media(InputMediaPhoto(media=photo_url, caption=caption), reply_markup=markup)
    except BadRequest:
        await query.message.reply_photo(photo=photo_url, caption=caption, reply_markup=markup)


async def show_home(target, edit: bool = True) -> None:
    text = (
        "🎬 ANIME BOT\n"
        "━━━━━━━━━━━━━━\n"
        "🔥 Найду любое аниме\n"
        "⭐ Подберу под тебя\n"
        "🎯 Дам рекомендации"
    )
    if edit:
        await target.edit_message_text(text, reply_markup=menu_kb())
    else:
        await target.reply_text(text, reply_markup=menu_kb())


async def show_anime_card(query, anime_id: int) -> None:
    row = get_anime(anime_id)
    if not row:
        await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    await safe_edit(query, anime_card_text(row), anime_card_kb(anime_id))


async def show_watch(query, anime_id: int) -> None:
    row = get_anime(anime_id)
    if not row:
        await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    name = row["name_ru"]
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Anilibria", url=f"https://anilibria.top/search?q={quote_plus(name)}")],
            [InlineKeyboardButton("📖 Shikimori", url=f"https://shikimori.one/animes?search={quote_plus(name)}")],
            [InlineKeyboardButton("🎥 YouTube", url=f"https://youtube.com/results?search_query={quote_plus(name + ' аниме')}")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
        ]
    )
    await safe_edit(query, f"🎥 Где смотреть: {name}", kb)


async def show_list(query, page: int) -> None:
    p = max(0, page)
    offset = p * PAGE_SIZE
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT id, name_ru, year FROM anime ORDER BY id LIMIT ? OFFSET ?",
            (PAGE_SIZE + 1, offset),
        ).fetchall()

    if not rows:
        await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return

    current = rows[:PAGE_SIZE]
    has_next = len(rows) > PAGE_SIZE
    text_lines = ["📚 Список аниме:"]
    kb_rows = []
    for row in current:
        text_lines.append(f"• {row['name_ru']} ({row['year']})")
        kb_rows.append([InlineKeyboardButton(f"🎬 {row['name_ru'][:28]}", callback_data=f"anime:{row['id']}")])
    kb_rows.extend(pager("menu:list", p, p > 0, has_next).inline_keyboard)
    await safe_edit(query, "\n".join(text_lines), InlineKeyboardMarkup(kb_rows))


async def show_top(query) -> None:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.name_ru, ROUND(COALESCE(AVG(r.rating), a.rating), 2) AS avg_rating
            FROM anime a
            LEFT JOIN ratings r ON r.anime_id = a.id
            GROUP BY a.id
            ORDER BY avg_rating DESC, a.year DESC
            LIMIT 10
            """
        ).fetchall()
    if not rows:
        await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return

    lines = ["🏆 Топ аниме:"]
    kb_rows = []
    for i, row in enumerate(rows, start=1):
        lines.append(f"{i}. {row['name_ru']} — ⭐ {row['avg_rating']}")
        kb_rows.append([InlineKeyboardButton(f"#{i} {row['name_ru'][:24]}", callback_data=f"anime:{row['id']}")])
    kb_rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu:home")])
    await safe_edit(query, "\n".join(lines), InlineKeyboardMarkup(kb_rows))


async def show_genres_menu(query) -> None:
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Экшен", callback_data="genre:Экшен"), InlineKeyboardButton("Фэнтези", callback_data="genre:Фэнтези")],
            [InlineKeyboardButton("Комедия", callback_data="genre:Комедия"), InlineKeyboardButton("Романтика", callback_data="genre:Романтика")],
            [InlineKeyboardButton("Приключения", callback_data="genre:Приключения")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
        ]
    )
    await safe_edit(query, "🎭 Выбери жанр:", kb)


async def show_recommendations(query, user_id: int) -> None:
    with closing(get_conn()) as conn:
        favs = conn.execute(
            """
            SELECT a.genres
            FROM favorites f
            JOIN anime a ON a.id = f.anime_id
            WHERE f.user_id=?
            """,
            (user_id,),
        ).fetchall()

    if not favs:
        with closing(get_conn()) as conn:
            row = conn.execute("SELECT id FROM anime ORDER BY RANDOM() LIMIT 1").fetchone()
        if not row:
            await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
            return
        await show_anime_card(query, int(row["id"]))
        return

    genre_counter: dict[str, int] = {}
    for row in favs:
        for genre in [g.strip() for g in row["genres"].split(",") if g.strip()]:
            genre_counter[genre] = genre_counter.get(genre, 0) + 1
    best_genres = sorted(genre_counter.items(), key=lambda x: x[1], reverse=True)

    with closing(get_conn()) as conn:
        for genre, _ in best_genres[:3]:
            pick = conn.execute(
                """
                SELECT a.id
                FROM anime a
                WHERE a.genres LIKE ?
                ORDER BY RANDOM() LIMIT 1
                """,
                (f"%{genre}%",),
            ).fetchone()
            if pick:
                await show_anime_card(query, int(pick["id"]))
                return

    await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))


async def show_favorites(query, user_id: int, page: int) -> None:
    p = max(0, page)
    offset = p * PAGE_SIZE
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.name_ru, a.year
            FROM favorites f
            JOIN anime a ON a.id=f.anime_id
            WHERE f.user_id=?
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, PAGE_SIZE + 1, offset),
        ).fetchall()

    if not rows:
        await safe_edit(query, "❤️ Пусто", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return

    current = rows[:PAGE_SIZE]
    has_next = len(rows) > PAGE_SIZE
    text_lines = ["❤️ Избранное:"]
    kb_rows = []
    for row in current:
        text_lines.append(f"• {row['name_ru']} ({row['year']})")
        kb_rows.append([InlineKeyboardButton(f"🎬 {row['name_ru'][:28]}", callback_data=f"anime:{row['id']}")])
    kb_rows.extend(pager("menu:fav", p, p > 0, has_next).inline_keyboard)
    await safe_edit(query, "\n".join(text_lines), InlineKeyboardMarkup(kb_rows))


async def show_quote(query) -> None:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT quote FROM quotes ORDER BY RANDOM() LIMIT 1").fetchone()
    text = f"💬 {row['quote']}" if row else "❌ Не найдено"
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💬 Ещё", callback_data="quote:more")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
        ]
    )
    await safe_edit(query, text, kb)


async def show_meme(query) -> None:
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT url FROM memes ORDER BY RANDOM() LIMIT 1").fetchone()
    if not row:
        await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
        return
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("😂 Ещё", callback_data="meme:more")],
            [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
        ]
    )
    await safe_edit_photo(query, row["url"], "😂 Аниме-мем", kb)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user:
        return
    upsert_user(update.effective_user.id, update.effective_user.username)
    if update.message:
        await show_home(update.message, edit=False)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()
    user = query.from_user
    upsert_user(user.id, user.username)

    try:
        data = query.data or ""

        if data == "menu:home":
            await show_home(query, edit=True)
            return

        if data == "menu:search":
            set_state(user.id, "search")
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]])
            await safe_edit(query, "🔍 Введи запрос (название, жанр, год, описание):", kb)
            return

        if data == "menu:random":
            with closing(get_conn()) as conn:
                row = conn.execute("SELECT id FROM anime ORDER BY RANDOM() LIMIT 1").fetchone()
            if row:
                await show_anime_card(query, int(row["id"]))
            else:
                await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
            return

        if data.startswith("menu:list:"):
            await show_list(query, int(data.split(":")[-1]))
            return

        if data == "menu:top":
            await show_top(query)
            return

        if data == "menu:recommend":
            await show_recommendations(query, user.id)
            return

        if data == "menu:genres":
            await show_genres_menu(query)
            return

        if data.startswith("menu:fav:"):
            await show_favorites(query, user.id, int(data.split(":")[-1]))
            return

        if data.startswith("genre:"):
            genre = data.split(":", 1)[1]
            with closing(get_conn()) as conn:
                row = conn.execute(
                    "SELECT id FROM anime WHERE genres LIKE ? ORDER BY RANDOM() LIMIT 1",
                    (f"%{genre}%",),
                ).fetchone()
            if row:
                await show_anime_card(query, int(row["id"]))
            else:
                await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
            return

        if data.startswith("anime:"):
            await show_anime_card(query, int(data.split(":")[-1]))
            return

        if data.startswith("watch:"):
            await show_watch(query, int(data.split(":")[-1]))
            return

        if data.startswith("rate_menu:"):
            anime_id = int(data.split(":")[-1])
            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1⭐", callback_data=f"rate:{anime_id}:1"),
                        InlineKeyboardButton("2⭐", callback_data=f"rate:{anime_id}:2"),
                        InlineKeyboardButton("3⭐", callback_data=f"rate:{anime_id}:3"),
                    ],
                    [
                        InlineKeyboardButton("4⭐", callback_data=f"rate:{anime_id}:4"),
                        InlineKeyboardButton("5⭐", callback_data=f"rate:{anime_id}:5"),
                    ],
                    [InlineKeyboardButton("🏠 Меню", callback_data="menu:home")],
                ]
            )
            await safe_edit(query, "⭐ Оцени аниме:", kb)
            return

        if data.startswith("rate:"):
            _, anime_id_raw, value_raw = data.split(":")
            anime_id, value = int(anime_id_raw), int(value_raw)
            if value < 1 or value > 5:
                await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
                return
            with closing(get_conn()) as conn, conn:
                conn.execute(
                    """
                    INSERT INTO ratings (user_id, anime_id, rating, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, anime_id)
                    DO UPDATE SET rating=excluded.rating, updated_at=CURRENT_TIMESTAMP
                    """,
                    (user.id, anime_id, value),
                )
            get_anime.cache_clear()
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
                    conn.execute("INSERT OR IGNORE INTO favorites (user_id, anime_id) VALUES (?, ?)", (user.id, anime_id))
            await show_anime_card(query, anime_id)
            return

        if data.startswith("similar:"):
            anime_id = int(data.split(":")[-1])
            source = get_anime(anime_id)
            if not source:
                await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
                return
            genre = source["genres"].split(",")[0].strip()
            with closing(get_conn()) as conn:
                row = conn.execute(
                    "SELECT id FROM anime WHERE id != ? AND genres LIKE ? ORDER BY RANDOM() LIMIT 1",
                    (anime_id, f"%{genre}%"),
                ).fetchone()
            if row:
                await show_anime_card(query, int(row["id"]))
            else:
                await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
            return

        if data == "menu:quote" or data == "quote:more":
            await show_quote(query)
            return

        if data == "menu:meme" or data == "meme:more":
            await show_meme(query)
            return

        await safe_edit(query, "❌ Не найдено", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))
    except Exception as exc:
        logger.exception("Callback error: %s", exc)
        await safe_edit(query, "⚠️ Произошла ошибка. Попробуй ещё раз.", InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]))


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    user = update.effective_user
    upsert_user(user.id, user.username)

    try:
        state = get_state(user.id)
        if state != "search":
            return

        user_text = (update.message.text or "").strip()
        set_state(user.id, "")
        results = search_anime(user_text, limit=10)

        if not results:
            await update.message.reply_text(
                "❌ Не найдено",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu:home")]]),
            )
            return

        lines = [f"🔍 Результаты для: {user_text}"]
        kb_rows = []
        for row in results:
            lines.append(f"• {row['name_ru']} ({row['year']})")
            kb_rows.append([InlineKeyboardButton(f"🎬 {row['name_ru'][:28]}", callback_data=f"anime:{row['id']}")])
        kb_rows.append([InlineKeyboardButton("🏠 Меню", callback_data="menu:home")])
        await update.message.reply_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb_rows))
    except Exception as exc:
        logger.exception("Text handler error: %s", exc)
        await update.message.reply_text("⚠️ Произошла ошибка. Нажми /start")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)


def main() -> None:
    init_db()

    token = "PASTE_YOUR_TOKEN_HERE"

    if token == "PASTE_YOUR_TOKEN_HERE" or not token.strip():
        raise RuntimeError("Вставь токен в переменную token внутри main.py")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_error_handler(on_error)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
