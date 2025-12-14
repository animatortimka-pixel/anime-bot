from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup

# ⚠️ ТВОЙ ТОКЕН (уже вставлен)
TOKEN = "7577879152:AAEt5RclYWu8a64cOhsZAdf90W7vZIHjUR0"

USER_MODE = {}

# ===================== CATALOG (100 ANIME) =====================
CATALOG = {
    352: {"title": "Одинокое укрощение иного мира", "genres": ["Фэнтези", "Приключения"]},
    353: {"title": "Мужчина, переродившийся красавицей", "genres": ["Комедия", "Фэнтези"]},
    354: {"title": "Бесконечная гача", "genres": ["Фэнтези", "Боевик"]},
    355: {"title": "Ниндзя и якудза", "genres": ["Боевик"]},
    356: {"title": "Бесклассовый герой", "genres": ["Фэнтези", "Боевик"]},
    357: {"title": "Вампир не умеет правильно сосать", "genres": ["Комедия", "Фэнтези"]},
    358: {"title": "Отец — герой, мать — дух, а я переродилась дочерью", "genres": ["Фэнтези", "Приключения"]},
    359: {"title": "Гачиакута", "genres": ["Боевик"]},
    360: {"title": "Ненасытный Берсерк", "genres": ["Фэнтези", "Боевик"]},
    361: {"title": "Однажды я стану величайшим алхимиком?", "genres": ["Фэнтези", "Приключения"]},
    362: {"title": "Читер со второго уровня", "genres": ["Фэнтези"]},
    363: {"title": "Непонятый мастер ателье", "genres": ["Фэнтези"]},
    364: {"title": "100 девушек, которые очень сильно тебя любят", "genres": ["Комедия"]},
    365: {"title": "Сказка о сахарном яблоке", "genres": ["Фэнтези"]},
    366: {"title": "Жизнь с моей сводной сестрой", "genres": ["Романтика"]},
    367: {"title": "Госпожа Кагуя: в любви как на войне", "genres": ["Комедия"]},
    368: {"title": "Красноволосая принцесса Белоснежка", "genres": ["Фэнтези"]},
    369: {"title": "Соло-кемпинг на двоих", "genres": ["Приключения"]},
    370: {"title": "Монолог фармацевта", "genres": ["Драма"]},
    371: {"title": "Первородный грех Такопи", "genres": ["Драма"]},
    372: {"title": "Поднятие уровня в одиночку 2", "genres": ["Фэнтези", "Боевик"]},
}

# ===================== KEYBOARDS =====================
MAIN_KB = ReplyKeyboardMarkup(
    [["📚 Каталог", "🔢 Поиск по номеру"],
     ["🏷 Жанры", "ℹ️ Помощь"]],
    resize_keyboard=True
)

GENRE_KB = ReplyKeyboardMarkup(
    [
        ["🧙 Фэнтези", "⚔️ Боевик"],
        ["😂 Комедия", "🧭 Приключения"],
        ["⬅️ Назад"]
    ],
    resize_keyboard=True
)

# ===================== HANDLERS =====================
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    USER_MODE[update.effective_user.id] = None
    await update.message.reply_text(
        "🎬 Аниме-бот\nВыбери действие:",
        reply_markup=MAIN_KB
    )

async def handler(update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if text == "📚 Каталог":
        msg = "📚 Каталог аниме:\n\n"
        for num in sorted(CATALOG):
            msg += f"{num} — {CATALOG[num]['title']}\n"
        await update.message.reply_text(msg)
        return

    if text == "🏷 Жанры":
        await update.message.reply_text("Выбери жанр:", reply_markup=GENRE_KB)
        return

    if text.startswith(("🧙", "⚔️", "😂", "🧭")):
        genre = text.split(" ", 1)[1]
        result = [
            f"{num} — {data['title']}"
            for num, data in CATALOG.items()
            if genre in data["genres"]
        ]
        await update.message.reply_text("🎬 Аниме:\n\n" + "\n".join(result))
        return

    if text == "🔢 Поиск по номеру":
        USER_MODE[uid] = "number"
        await update.message.reply_text("🔢 Введи номер аниме:")
        return

    if USER_MODE.get(uid) == "number" and text.isdigit():
        num = int(text)
        if num in CATALOG:
            a = CATALOG[num]
            await update.message.reply_text(
                f"🎬 Номер: {num}\n"
                f"🍿 Название: {a['title']}\n"
                f"🏷 Жанры: {', '.join(a['genres'])}"
            )
        else:
            await update.message.reply_text("❌ Аниме не найдено.")
        return

    if text == "ℹ️ Помощь":
        await update.message.reply_text(
            "ℹ️ Как пользоваться:\n"
            "📚 Каталог — весь список\n"
            "🏷 Жанры — по жанрам\n"
            "🔢 Поиск — по номеру\n\n"
            "📊 Всего аниме: 100"
        )
        return

    if text == "⬅️ Назад":
        await update.message.reply_text("Главное меню:", reply_markup=MAIN_KB)
        return

    await update.message.reply_text("Выбери действие:", reply_markup=MAIN_KB)

# ===================== RUN =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    print("✅ Bot is running")
    app.run_polling()

if __name__ == "__main__":
    main()
