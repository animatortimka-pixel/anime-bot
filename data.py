from __future__ import annotations

import random
from urllib.parse import quote_plus

REAL_ANIME: list[dict] = [
    {"name_ru": "Атака титанов", "name_en": "Attack on Titan", "year": 2013, "genres": ["action", "drama", "fantasy"], "rating": 9.1, "episodes": 87, "description": "Человечество сражается за выживание внутри стен против титанов."},
    {"name_ru": "Стальной алхимик: Братство", "name_en": "Fullmetal Alchemist: Brotherhood", "year": 2009, "genres": ["action", "adventure", "fantasy"], "rating": 9.2, "episodes": 64, "description": "Братья Элрики ищут философский камень, чтобы исправить роковую ошибку."},
    {"name_ru": "Тетрадь смерти", "name_en": "Death Note", "year": 2006, "genres": ["thriller", "mystery", "supernatural"], "rating": 8.9, "episodes": 37, "description": "Школьник получает тетрадь, способную убивать, и бросает вызов миру."},
    {"name_ru": "Наруто", "name_en": "Naruto", "year": 2002, "genres": ["action", "adventure", "shounen"], "rating": 8.3, "episodes": 220, "description": "История юного ниндзя, мечтающего стать Хокаге."},
    {"name_ru": "Наруто: Ураганные хроники", "name_en": "Naruto: Shippuden", "year": 2007, "genres": ["action", "adventure", "shounen"], "rating": 8.6, "episodes": 500, "description": "Продолжение пути Наруто и его сражений против Акацуки."},
    {"name_ru": "Ван-Пис", "name_en": "One Piece", "year": 1999, "genres": ["adventure", "comedy", "shounen"], "rating": 9.0, "episodes": 1100, "description": "Команда Луффи отправляется на поиски величайшего сокровища."},
    {"name_ru": "Клинок, рассекающий демонов", "name_en": "Demon Slayer", "year": 2019, "genres": ["action", "fantasy", "historical"], "rating": 8.7, "episodes": 55, "description": "Танджиро вступает в корпус истребителей демонов ради спасения сестры."},
    {"name_ru": "Магическая битва", "name_en": "Jujutsu Kaisen", "year": 2020, "genres": ["action", "supernatural", "school"], "rating": 8.6, "episodes": 47, "description": "Юдзи Итадори сражается с проклятиями в мире магов."},
    {"name_ru": "Код Гиас", "name_en": "Code Geass", "year": 2006, "genres": ["mecha", "thriller", "drama"], "rating": 8.8, "episodes": 50, "description": "Лелуш получает силу повиновения и начинает революцию."},
    {"name_ru": "Евангелион", "name_en": "Neon Genesis Evangelion", "year": 1995, "genres": ["mecha", "psychological", "drama"], "rating": 8.4, "episodes": 26, "description": "Подростки пилотируют Евы, защищая Землю от Ангелов."},
    {"name_ru": "Врата Штейна", "name_en": "Steins;Gate", "year": 2011, "genres": ["sci-fi", "thriller", "drama"], "rating": 9.0, "episodes": 24, "description": "Эксперименты со временем приводят к трагичным последствиям."},
    {"name_ru": "Психопаспорт", "name_en": "Psycho-Pass", "year": 2012, "genres": ["sci-fi", "action", "thriller"], "rating": 8.3, "episodes": 41, "description": "Будущее, где преступления предсказывает система Сивилла."},
    {"name_ru": "Монстр", "name_en": "Monster", "year": 2004, "genres": ["thriller", "psychological", "drama"], "rating": 8.9, "episodes": 74, "description": "Хирург преследует спасенного им ребенка, ставшего убийцей."},
    {"name_ru": "Ковбой Бибоп", "name_en": "Cowboy Bebop", "year": 1998, "genres": ["sci-fi", "action", "drama"], "rating": 8.8, "episodes": 26, "description": "Охотники за головами путешествуют по солнечной системе."},
    {"name_ru": "Самурай Чамплу", "name_en": "Samurai Champloo", "year": 2004, "genres": ["action", "adventure", "historical"], "rating": 8.5, "episodes": 26, "description": "Необычное путешествие самураев в духе хип-хопа."},
    {"name_ru": "Твоё имя", "name_en": "Your Name", "year": 2016, "genres": ["romance", "drama", "supernatural"], "rating": 8.9, "episodes": 1, "description": "Парень и девушка загадочно меняются телами."},
    {"name_ru": "Форма голоса", "name_en": "A Silent Voice", "year": 2016, "genres": ["drama", "romance", "school"], "rating": 8.7, "episodes": 1, "description": "История вины, прощения и второго шанса."},
    {"name_ru": "Унесённые призраками", "name_en": "Spirited Away", "year": 2001, "genres": ["fantasy", "adventure", "family"], "rating": 8.8, "episodes": 1, "description": "Девочка попадает в мир духов и ищет путь домой."},
    {"name_ru": "Ходячий замок", "name_en": "Howl's Moving Castle", "year": 2004, "genres": ["fantasy", "romance", "adventure"], "rating": 8.6, "episodes": 1, "description": "Молодая девушка и загадочный маг в мире войны и магии."},
    {"name_ru": "Вайолет Эвергарден", "name_en": "Violet Evergarden", "year": 2018, "genres": ["drama", "slice of life", "romance"], "rating": 8.7, "episodes": 13, "description": "Бывшая солдатка учится понимать эмоции через письма."},
    {"name_ru": "Re:Zero", "name_en": "Re:Zero - Starting Life in Another World", "year": 2016, "genres": ["fantasy", "isekai", "drama"], "rating": 8.4, "episodes": 50, "description": "Субару возвращается во времени после каждой смерти."},
    {"name_ru": "Реинкарнация безработного", "name_en": "Mushoku Tensei", "year": 2021, "genres": ["fantasy", "isekai", "adventure"], "rating": 8.5, "episodes": 48, "description": "Перерождение в магическом мире и путь к взрослению."},
    {"name_ru": "О моём перерождении в слизь", "name_en": "That Time I Got Reincarnated as a Slime", "year": 2018, "genres": ["fantasy", "isekai", "adventure"], "rating": 8.2, "episodes": 72, "description": "Новый мир, где герой строит государство монстров."},
    {"name_ru": "Семья шпиона", "name_en": "Spy x Family", "year": 2022, "genres": ["comedy", "action", "family"], "rating": 8.5, "episodes": 37, "description": "Шпион, убийца и телепат формируют фальшивую семью."},
    {"name_ru": "Кагуя: в любви как на войне", "name_en": "Kaguya-sama: Love Is War", "year": 2019, "genres": ["comedy", "romance", "school"], "rating": 8.6, "episodes": 37, "description": "Гении школьного совета ведут романтическую психологическую дуэль."},
    {"name_ru": "Монолог фармацевта", "name_en": "The Apothecary Diaries", "year": 2023, "genres": ["mystery", "drama", "historical"], "rating": 8.7, "episodes": 24, "description": "Аптекарша Маомао раскрывает интриги императорского двора."},
    {"name_ru": "Хайкью!!", "name_en": "Haikyuu!!", "year": 2014, "genres": ["sports", "comedy", "school"], "rating": 8.7, "episodes": 85, "description": "Команда Карасуно борется за вершину школьного волейбола."},
    {"name_ru": "Блю Лок", "name_en": "Blue Lock", "year": 2022, "genres": ["sports", "thriller", "drama"], "rating": 8.1, "episodes": 24, "description": "Жёсткая футбольная программа для воспитания лучшего форварда."},
    {"name_ru": "Доктор Стоун", "name_en": "Dr. Stone", "year": 2019, "genres": ["adventure", "sci-fi", "comedy"], "rating": 8.2, "episodes": 57, "description": "Наука возрождает цивилизацию после каменного апокалипсиса."},
    {"name_ru": "No Game No Life", "name_en": "No Game No Life", "year": 2014, "genres": ["fantasy", "isekai", "comedy"], "rating": 8.1, "episodes": 12, "description": "Брат и сестра-геймеры покоряют игровой мир."},
    {"name_ru": "Дорохедоро", "name_en": "Dorohedoro", "year": 2020, "genres": ["action", "dark", "comedy"], "rating": 8.0, "episodes": 12, "description": "Гротескный город и магические эксперименты в поиске правды."},
    {"name_ru": "Сага о Винланде", "name_en": "Vinland Saga", "year": 2019, "genres": ["action", "historical", "drama"], "rating": 8.8, "episodes": 48, "description": "Эпическая история мести, войны и взросления викинга."},
    {"name_ru": "Пламенная бригада пожарных", "name_en": "Fire Force", "year": 2019, "genres": ["action", "supernatural", "shounen"], "rating": 7.8, "episodes": 48, "description": "Спецотряды борются с инферналами в огненном Токио."},
    {"name_ru": "Класс превосходства", "name_en": "Classroom of the Elite", "year": 2017, "genres": ["school", "psychological", "drama"], "rating": 8.0, "episodes": 38, "description": "Элитная школа, где выживает самый расчётливый."},
    {"name_ru": "Охотник x Охотник", "name_en": "Hunter x Hunter", "year": 2011, "genres": ["adventure", "action", "shounen"], "rating": 9.0, "episodes": 148, "description": "Гон отправляется на поиски отца и проходит экзамен охотников."},
    {"name_ru": "Черный клевер", "name_en": "Black Clover", "year": 2017, "genres": ["action", "fantasy", "shounen"], "rating": 8.1, "episodes": 170, "description": "Аста без магии стремится стать королём магов."},
    {"name_ru": "Блич", "name_en": "Bleach", "year": 2004, "genres": ["action", "supernatural", "shounen"], "rating": 8.2, "episodes": 392, "description": "Ичиго становится проводником душ и сражается с пустыми."},
    {"name_ru": "JoJo's Bizarre Adventure", "name_en": "JoJo's Bizarre Adventure", "year": 2012, "genres": ["action", "adventure", "supernatural"], "rating": 8.6, "episodes": 190, "description": "Поколения семьи Джостаров и невероятные битвы стендов."},
    {"name_ru": "Бездомный бог", "name_en": "Noragami", "year": 2014, "genres": ["action", "comedy", "supernatural"], "rating": 8.0, "episodes": 25, "description": "Маленький бог Ято ищет признание и собственный храм."},
    {"name_ru": "Моб Психо 100", "name_en": "Mob Psycho 100", "year": 2016, "genres": ["comedy", "action", "supernatural"], "rating": 8.7, "episodes": 37, "description": "Подросток-экстрасенс пытается жить обычной жизнью."},
    {"name_ru": "Банановая рыба", "name_en": "Banana Fish", "year": 2018, "genres": ["thriller", "drama", "action"], "rating": 8.5, "episodes": 24, "description": "Нью-Йоркский криминальный триллер о заговоре и дружбе."},
    {"name_ru": "Токийский гуль", "name_en": "Tokyo Ghoul", "year": 2014, "genres": ["action", "horror", "psychological"], "rating": 7.9, "episodes": 48, "description": "Студент становится полугулем и ищет место между мирами."},
    {"name_ru": "Паразит: Учение о жизни", "name_en": "Parasyte -the maxim-", "year": 2014, "genres": ["sci-fi", "horror", "drama"], "rating": 8.4, "episodes": 24, "description": "Инопланетный паразит и подросток делят одно тело."},
    {"name_ru": "Обещанный Неверленд", "name_en": "The Promised Neverland", "year": 2019, "genres": ["thriller", "mystery", "fantasy"], "rating": 8.4, "episodes": 23, "description": "Дети из приюта раскрывают страшную правду и планируют побег."},
    {"name_ru": "Моя геройская академия", "name_en": "My Hero Academia", "year": 2016, "genres": ["action", "school", "shounen"], "rating": 8.0, "episodes": 159, "description": "Мир суперсил и путь Изуку Мидории к званию героя."},
    {"name_ru": "Гуррен-Лаганн", "name_en": "Gurren Lagann", "year": 2007, "genres": ["mecha", "action", "adventure"], "rating": 8.6, "episodes": 27, "description": "Эпичный рост от подземелья до космических масштабов."},
    {"name_ru": "Берсерк", "name_en": "Berserk", "year": 1997, "genres": ["action", "dark", "drama"], "rating": 8.7, "episodes": 25, "description": "Мрачная сага о мести, судьбе и цене амбиций."},
]

QUOTES = [
    "Когда сдаёшься — игра окончена.",
    "Даже маленький шаг — уже движение к цели.",
    "Сила рождается, когда есть кого защищать.",
    "Ошибки — это опыт, если ты делаешь выводы.",
    "Иногда нужно проиграть, чтобы понять, как победить.",
]

MEMES = [
    "Только одну серию… и уже 4:37 утра.",
    "План: 20 минут аниме. Реальность: целый сезон.",
    "Я не буду смотреть онгоинг. Тоже я: где новая серия?",
    "Когда у героя флешбек — жди power-up.",
    "Смотрю ради сюжета. Сюжет: вечная вайфу-война.",
]


def _make_watch_urls(name: str) -> dict[str, str]:
    q = quote_plus(name)
    return {
        "anilibria": f"https://www.anilibria.tv/search?q={q}",
        "shikimori": f"https://shikimori.one/animes?search={q}",
        "youtube": f"https://www.youtube.com/results?search_query={q}+аниме",
    }


def _make_episodes_data(name: str, episodes: int) -> list[dict[str, str]]:
    safe_name = quote_plus(name)
    return [
        {
            "episode": i,
            "title": f"Серия {i}",
            "url": f"https://example.org/watch/{safe_name}/{i}",
        }
        for i in range(1, episodes + 1)
    ]


def fill_data() -> list[dict]:
    random.seed(42)
    dataset: list[dict] = []

    for anime in REAL_ANIME:
        item = dict(anime)
        item["watch_urls"] = _make_watch_urls(item["name_en"])
        item["episodes_data"] = _make_episodes_data(item["name_en"], min(item["episodes"], 24))
        dataset.append(item)

    prefixes_ru = ["Хроники", "Легенда", "Тайна", "Песнь", "Код", "Дневник", "Империя", "Наследие"]
    nouns_ru = ["луны", "дракона", "пепла", "бури", "клинка", "мечты", "тумана", "пустоты"]
    suffixes_ru = ["рассвета", "судьбы", "вечности", "хаоса", "звёзд", "безмолвия"]

    prefixes_en = ["Chronicles", "Legacy", "Code", "Echo", "Saga", "Tales", "Orbit", "Shards"]
    nouns_en = ["Moon", "Dragon", "Ash", "Storm", "Blade", "Dream", "Mist", "Void"]
    suffixes_en = ["Dawn", "Fate", "Eternity", "Chaos", "Stars", "Silence"]

    genre_pool = [
        "action", "drama", "fantasy", "thriller", "mystery", "adventure", "comedy", "romance",
        "sci-fi", "supernatural", "school", "historical", "sports", "mecha", "slice of life", "isekai",
    ]

    for i in range(160):
        name_ru = f"{random.choice(prefixes_ru)} {random.choice(nouns_ru)} {random.choice(suffixes_ru)}"
        name_en = f"{random.choice(prefixes_en)} of {random.choice(nouns_en)} {random.choice(suffixes_en)}"
        year = random.randint(1995, 2026)
        episodes = random.randint(12, 24)
        genres = random.sample(genre_pool, k=3)
        rating = round(random.uniform(6.8, 9.1), 1)
        description = (
            f"{name_ru} — приключенческая история о героях, которые пытаются изменить свою судьбу "
            f"в мире, где сталкиваются {genres[0]}, {genres[1]} и {genres[2]}."
        )
        dataset.append(
            {
                "name_ru": f"{name_ru} #{i + 1}",
                "name_en": f"{name_en} {i + 1}",
                "year": year,
                "description": description,
                "genres": genres,
                "rating": rating,
                "episodes": episodes,
                "watch_urls": _make_watch_urls(name_en),
                "episodes_data": _make_episodes_data(name_en, episodes),
            }
        )

    return dataset
