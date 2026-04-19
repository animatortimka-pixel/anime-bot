from __future__ import annotations

import random

BASE_ANIME = [
    ("Атака титанов", "Attack on Titan", "Темное фэнтези о борьбе человечества против титанов.", ["action", "drama", "fantasy"]),
    ("Стальной алхимик: Братство", "Fullmetal Alchemist: Brotherhood", "Братья-алхимики ищут путь вернуть свои тела.", ["action", "adventure", "fantasy"]),
    ("Тетрадь смерти", "Death Note", "Психологическая игра между Кирой и детективом L.", ["thriller", "mystery", "supernatural"]),
    ("Наруто", "Naruto", "Путь ниндзя, мечтающего стать Хокаге.", ["action", "adventure", "shounen"]),
    ("Ван-Пис", "One Piece", "Пираты Соломенной шляпы и великое путешествие.", ["adventure", "comedy", "shounen"]),
    ("Клинок, рассекающий демонов", "Demon Slayer", "Охота на демонов и сила семьи.", ["action", "fantasy", "historical"]),
    ("Магическая битва", "Jujutsu Kaisen", "Битвы магов против проклятий.", ["action", "supernatural", "school"]),
    ("Код Гиас", "Code Geass", "Революция, тактика и сила Гиаса.", ["mecha", "thriller", "drama"]),
    ("Евангелион", "Neon Genesis Evangelion", "Психологическая история пилотов ЕВА.", ["mecha", "psychological", "drama"]),
    ("Врата Штейна", "Steins;Gate", "Эксперименты со временем и их последствия.", ["sci-fi", "thriller", "drama"]),
    ("Психопаспорт", "Psycho-Pass", "Киберпанк-антиутопия о контроле общества.", ["sci-fi", "action", "thriller"]),
    ("Монстр", "Monster", "Охота на чудовище в человеческом обличье.", ["thriller", "psychological", "drama"]),
    ("Ковбой Бибоп", "Cowboy Bebop", "Космические охотники за головами.", ["sci-fi", "action", "drama"]),
    ("Самурай Чамплу", "Samurai Champloo", "Роуд-муви в эпоху Эдо с хип-хопом.", ["action", "adventure", "historical"]),
    ("Твоё имя", "Your Name", "Романтическая история о смене тел.", ["romance", "drama", "supernatural"]),
    ("Форма голоса", "A Silent Voice", "Искупление, травля и шанс на прощение.", ["drama", "romance", "school"]),
    ("Унесённые призраками", "Spirited Away", "Путешествие девочки в мире духов.", ["fantasy", "adventure", "family"]),
    ("Ходячий замок", "Howl's Moving Castle", "Магия, война и сила любви.", ["fantasy", "romance", "adventure"]),
    ("Вайолет Эвергарден", "Violet Evergarden", "Бывшая солдатка учится понимать чувства.", ["drama", "slice of life", "romance"]),
    ("Re:Zero", "Re:Zero - Starting Life in Another World", "Смерть как точка сохранения в новом мире.", ["fantasy", "isekai", "drama"]),
    ("Реинкарнация безработного", "Mushoku Tensei", "Второй шанс прожить жизнь правильно.", ["fantasy", "isekai", "adventure"]),
    ("О моём перерождении в слизь", "That Time I Got Reincarnated as a Slime", "Создание королевства в мире монстров.", ["fantasy", "isekai", "adventure"]),
    ("Семья шпиона", "Spy x Family", "Шпионская семья, где у каждого свой секрет.", ["comedy", "action", "family"]),
    ("Госпожа Кагуя: в любви как на войне", "Kaguya-sama: Love Is War", "Романтическая война гордости.", ["comedy", "romance", "school"]),
    ("Монолог фармацевта", "The Apothecary Diaries", "Дворцовые интриги и медицинские загадки.", ["mystery", "drama", "historical"]),
    ("Хайкью!!", "Haikyuu!!", "Школьный волейбол и командный дух.", ["sports", "comedy", "school"]),
    ("Блю Лок", "Blue Lock", "Экстремальная программа подготовки нападающих.", ["sports", "thriller", "drama"]),
    ("Доктор Стоун", "Dr. Stone", "Наука перезапускает цивилизацию.", ["adventure", "sci-fi", "comedy"]),
    ("No Game No Life", "No Game No Life", "Гении-сиблинги покоряют мир игр.", ["fantasy", "isekai", "comedy"]),
    ("Дорохедоро", "Dorohedoro", "Сюрреалистичный мир магов и хаоса.", ["action", "dark", "comedy"]),
    ("Сага о Винланде", "Vinland Saga", "История мести и взросления викинга.", ["action", "historical", "drama"]),
    ("Пламенная бригада пожарных", "Fire Force", "Спецотряды против инферналов.", ["action", "supernatural", "shounen"]),
    ("Класс превосходства", "Classroom of the Elite", "Школьная стратегия и манипуляции.", ["school", "psychological", "drama"]),
    ("Охотник х Охотник", "Hunter x Hunter", "Путешествие Гона в мире охотников.", ["adventure", "action", "shounen"]),
    ("Черный клевер", "Black Clover", "Маги-соперники и путь к трону.", ["action", "fantasy", "shounen"]),
    ("Блич", "Bleach", "Синигами, пустые и битвы духов.", ["action", "supernatural", "shounen"]),
    ("JoJo", "JoJo's Bizarre Adventure", "Поколения семьи Джостаров и стенды.", ["action", "adventure", "supernatural"]),
    ("Бездомный бог", "Noragami", "Маленький бог ищет признание.", ["action", "comedy", "supernatural"]),
    ("Моб Психо 100", "Mob Psycho 100", "Экстрасенс-школьник и взросление.", ["comedy", "action", "supernatural"]),
    ("Банановая рыба", "Banana Fish", "Криминальный триллер о тайном веществе.", ["thriller", "drama", "action"]),
]

QUOTES = [
    "Когда ты сдаёшься — игра окончена. — Леви",
    "Люди сильнее всего тогда, когда защищают важное.",
    "Шаг за шагом даже слабый становится легендой.",
    "Ошибки — это тоже опыт, если сделать выводы.",
    "Сначала действие, потом вдохновение.",
]

MEMES = [
    "Когда сказал 'ещё одну серию', а уже 4:37 утра.",
    "План на вечер: посмотреть 1 эпизод. Реальность: целый сезон.",
    "Я: не буду начинать онгоинг. Тоже я: где 2 серия?",
    "Когда у героя флешбек и ты понимаешь — сейчас будет power-up.",
    "Смотрю аниме ради сюжета. Сюжет: waifu война.",
]


def _build_dataset() -> list[dict]:
    random.seed(42)
    dataset: list[dict] = []
    for idx in range(160):
        base = BASE_ANIME[idx % len(BASE_ANIME)]
        season = idx // len(BASE_ANIME) + 1
        title_ru = base[0] if season == 1 else f"{base[0]}: Арка {season}"
        title_en = base[1] if season == 1 else f"{base[1]} Arc {season}"
        year = 1995 + (idx % 31)
        rating = round(7.1 + ((idx * 7) % 28) / 10, 1)
        episodes = 12 + (idx % 4) * 12
        views = 500 + idx * 37
        watch_urls = [
            f"https://example.com/anime/{idx+1}/sub",
            f"https://example.org/anime/{idx+1}/dub",
        ]
        dataset.append(
            {
                "name_ru": title_ru,
                "name_en": title_en,
                "year": year,
                "description": f"{base[2]} Сезон {season}.",
                "genres": base[3],
                "rating": rating,
                "episodes": episodes,
                "watch_urls": watch_urls,
                "views": views,
            }
        )
    return dataset


ANIME_DATA = _build_dataset()
