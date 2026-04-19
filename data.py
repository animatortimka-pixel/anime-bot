from __future__ import annotations

import random
from urllib.parse import quote_plus

REAL_ANIME: list[dict] = [
    {"name_ru": "Провожающая в последний путь Фрирен", "name_en": "Sousou no Frieren", "year": 2023, "genres": ["adventure", "drama", "fantasy"], "rating": 9.1, "episodes": 28},
    {"name_ru": "Стальной алхимик: Братство", "name_en": "Fullmetal Alchemist: Brotherhood", "year": 2009, "genres": ["action", "adventure", "fantasy"], "rating": 9.2, "episodes": 64},
    {"name_ru": "Врата Штейна", "name_en": "Steins;Gate", "year": 2011, "genres": ["sci-fi", "thriller", "drama"], "rating": 9.0, "episodes": 24},
    {"name_ru": "Атака титанов", "name_en": "Shingeki no Kyojin", "year": 2013, "genres": ["action", "drama", "fantasy"], "rating": 9.0, "episodes": 87},
    {"name_ru": "Тетрадь смерти", "name_en": "Death Note", "year": 2006, "genres": ["thriller", "mystery", "supernatural"], "rating": 8.8, "episodes": 37},
    {"name_ru": "Код Гиас", "name_en": "Code Geass", "year": 2006, "genres": ["mecha", "thriller", "drama"], "rating": 8.8, "episodes": 50},
    {"name_ru": "Охотник x Охотник", "name_en": "Hunter x Hunter", "year": 2011, "genres": ["adventure", "action", "shounen"], "rating": 9.0, "episodes": 148},
    {"name_ru": "Ван-Пис", "name_en": "One Piece", "year": 1999, "genres": ["adventure", "comedy", "shounen"], "rating": 9.0, "episodes": 1100},
    {"name_ru": "Наруто", "name_en": "Naruto", "year": 2002, "genres": ["action", "adventure", "shounen"], "rating": 8.3, "episodes": 220},
    {"name_ru": "Наруто: Ураганные хроники", "name_en": "Naruto: Shippuden", "year": 2007, "genres": ["action", "adventure", "shounen"], "rating": 8.6, "episodes": 500},
    {"name_ru": "Клинок, рассекающий демонов", "name_en": "Demon Slayer", "year": 2019, "genres": ["action", "fantasy", "historical"], "rating": 8.6, "episodes": 55},
    {"name_ru": "Магическая битва", "name_en": "Jujutsu Kaisen", "year": 2020, "genres": ["action", "supernatural", "school"], "rating": 8.5, "episodes": 47},
    {"name_ru": "Монолог фармацевта", "name_en": "The Apothecary Diaries", "year": 2023, "genres": ["mystery", "drama", "historical"], "rating": 8.7, "episodes": 24},
    {"name_ru": "Реинкарнация безработного", "name_en": "Mushoku Tensei", "year": 2021, "genres": ["fantasy", "isekai", "adventure"], "rating": 8.5, "episodes": 48},
    {"name_ru": "Re:Zero", "name_en": "Re:Zero - Starting Life in Another World", "year": 2016, "genres": ["fantasy", "isekai", "drama"], "rating": 8.4, "episodes": 50},
    {"name_ru": "Семья шпиона", "name_en": "Spy x Family", "year": 2022, "genres": ["comedy", "action", "family"], "rating": 8.5, "episodes": 37},
    {"name_ru": "Твоё имя", "name_en": "Your Name", "year": 2016, "genres": ["romance", "drama", "supernatural"], "rating": 8.9, "episodes": 1},
    {"name_ru": "Форма голоса", "name_en": "A Silent Voice", "year": 2016, "genres": ["drama", "romance", "school"], "rating": 8.7, "episodes": 1},
    {"name_ru": "Унесённые призраками", "name_en": "Spirited Away", "year": 2001, "genres": ["fantasy", "adventure", "family"], "rating": 8.8, "episodes": 1},
    {"name_ru": "Ходячий замок", "name_en": "Howl's Moving Castle", "year": 2004, "genres": ["fantasy", "romance", "adventure"], "rating": 8.6, "episodes": 1},
    {"name_ru": "Ковбой Бибоп", "name_en": "Cowboy Bebop", "year": 1998, "genres": ["sci-fi", "action", "drama"], "rating": 8.8, "episodes": 26},
    {"name_ru": "Самурай Чамплу", "name_en": "Samurai Champloo", "year": 2004, "genres": ["action", "adventure", "historical"], "rating": 8.5, "episodes": 26},
    {"name_ru": "Психопаспорт", "name_en": "Psycho-Pass", "year": 2012, "genres": ["sci-fi", "action", "thriller"], "rating": 8.3, "episodes": 41},
    {"name_ru": "Монстр", "name_en": "Monster", "year": 2004, "genres": ["thriller", "psychological", "drama"], "rating": 8.8, "episodes": 74},
    {"name_ru": "Евангелион", "name_en": "Neon Genesis Evangelion", "year": 1995, "genres": ["mecha", "psychological", "drama"], "rating": 8.4, "episodes": 26},
    {"name_ru": "Хайкью!!", "name_en": "Haikyuu!!", "year": 2014, "genres": ["sports", "comedy", "school"], "rating": 8.7, "episodes": 85},
    {"name_ru": "Блю Лок", "name_en": "Blue Lock", "year": 2022, "genres": ["sports", "thriller", "drama"], "rating": 8.1, "episodes": 24},
    {"name_ru": "Доктор Стоун", "name_en": "Dr. Stone", "year": 2019, "genres": ["adventure", "sci-fi", "comedy"], "rating": 8.2, "episodes": 57},
    {"name_ru": "No Game No Life", "name_en": "No Game No Life", "year": 2014, "genres": ["fantasy", "isekai", "comedy"], "rating": 8.1, "episodes": 12},
    {"name_ru": "Дорохедоро", "name_en": "Dorohedoro", "year": 2020, "genres": ["action", "dark", "comedy"], "rating": 8.0, "episodes": 12},
    {"name_ru": "Сага о Винланде", "name_en": "Vinland Saga", "year": 2019, "genres": ["action", "historical", "drama"], "rating": 8.8, "episodes": 48},
    {"name_ru": "Блич", "name_en": "Bleach", "year": 2004, "genres": ["action", "supernatural", "shounen"], "rating": 8.2, "episodes": 392},
    {"name_ru": "Черный клевер", "name_en": "Black Clover", "year": 2017, "genres": ["action", "fantasy", "shounen"], "rating": 8.1, "episodes": 170},
    {"name_ru": "Бездомный бог", "name_en": "Noragami", "year": 2014, "genres": ["action", "comedy", "supernatural"], "rating": 8.0, "episodes": 25},
    {"name_ru": "Моб Психо 100", "name_en": "Mob Psycho 100", "year": 2016, "genres": ["comedy", "action", "supernatural"], "rating": 8.7, "episodes": 37},
    {"name_ru": "Токийский гуль", "name_en": "Tokyo Ghoul", "year": 2014, "genres": ["action", "horror", "psychological"], "rating": 7.9, "episodes": 48},
    {"name_ru": "Паразит: Учение о жизни", "name_en": "Parasyte -the maxim-", "year": 2014, "genres": ["sci-fi", "horror", "drama"], "rating": 8.4, "episodes": 24},
    {"name_ru": "Обещанный Неверленд", "name_en": "The Promised Neverland", "year": 2019, "genres": ["thriller", "mystery", "fantasy"], "rating": 8.4, "episodes": 23},
    {"name_ru": "Моя геройская академия", "name_en": "My Hero Academia", "year": 2016, "genres": ["action", "school", "shounen"], "rating": 8.0, "episodes": 159},
    {"name_ru": "Гуррен-Лаганн", "name_en": "Gurren Lagann", "year": 2007, "genres": ["mecha", "action", "adventure"], "rating": 8.6, "episodes": 27},
    {"name_ru": "Берсерк", "name_en": "Berserk", "year": 1997, "genres": ["action", "dark", "drama"], "rating": 8.7, "episodes": 25},
    {"name_ru": "Кайдзю №8", "name_en": "Kaiju No. 8", "year": 2024, "genres": ["action", "sci-fi", "shounen"], "rating": 8.2, "episodes": 12},
    {"name_ru": "Оши но Ко", "name_en": "Oshi no Ko", "year": 2023, "genres": ["drama", "mystery", "supernatural"], "rating": 8.5, "episodes": 24},
    {"name_ru": "Человек-бензопила", "name_en": "Chainsaw Man", "year": 2022, "genres": ["action", "horror", "dark"], "rating": 8.4, "episodes": 12},
    {"name_ru": "Хеллсинг Ultimate", "name_en": "Hellsing Ultimate", "year": 2006, "genres": ["action", "horror", "supernatural"], "rating": 8.3, "episodes": 10},
    {"name_ru": "Кэйон!", "name_en": "K-On!", "year": 2009, "genres": ["comedy", "music", "slice of life"], "rating": 7.9, "episodes": 39},
    {"name_ru": "Банановая рыба", "name_en": "Banana Fish", "year": 2018, "genres": ["thriller", "drama", "action"], "rating": 8.5, "episodes": 24},
    {"name_ru": "Вайолет Эвергарден", "name_en": "Violet Evergarden", "year": 2018, "genres": ["drama", "slice of life", "romance"], "rating": 8.7, "episodes": 13},
    {"name_ru": "Пламенная бригада пожарных", "name_en": "Fire Force", "year": 2019, "genres": ["action", "supernatural", "shounen"], "rating": 7.8, "episodes": 48},
    {"name_ru": "JoJo's Bizarre Adventure", "name_en": "JoJo's Bizarre Adventure", "year": 2012, "genres": ["action", "adventure", "supernatural"], "rating": 8.6, "episodes": 190},
    {"name_ru": "Класс превосходства", "name_en": "Classroom of the Elite", "year": 2017, "genres": ["school", "psychological", "drama"], "rating": 8.0, "episodes": 38},
]


def generate_episodes(count: int) -> dict[str, str]:
    return {str(i): f"https://kodik.example/stream/ep-{i}" for i in range(1, count + 1)}


def generate_description(title: str) -> str:
    templates = [
        "{title} рассказывает о героях, которые проходят через тяжелые испытания и взросление.",
        "В {title} переплетаются дружба, потери и борьба за будущее мира.",
        "{title} — история о выборе, ответственности и цене силы.",
        "Сюжет {title} строится вокруг конфликта идеалов, верности и личной свободы.",
    ]
    return random.choice(templates).format(title=title)


def _watch_urls(name_en: str) -> dict[str, str]:
    q = quote_plus(name_en)
    return {
        "anilibria": f"https://www.anilibria.tv/search?q={q}",
        "shikimori": f"https://shikimori.one/animes?search={q}",
        "youtube": f"https://www.youtube.com/results?search_query={q}+anime",
    }


def fill_data() -> list[dict]:
    random.seed(42)
    data: list[dict] = []

    for item in REAL_ANIME:
        episodes = max(1, int(item["episodes"]))
        data.append(
            {
                "name_ru": item["name_ru"],
                "name_en": item["name_en"],
                "year": item["year"],
                "description": generate_description(item["name_ru"]),
                "genres": item["genres"],
                "rating": item["rating"],
                "episodes": episodes,
                "watch_urls": _watch_urls(item["name_en"]),
                "episodes_data": generate_episodes(min(episodes, 24)),
                "views": random.randint(500, 20000),
            }
        )

    prefixes_ru = ["Хроники", "Легенда", "Тайна", "Код", "Империя", "Песнь", "Грань", "Проект"]
    cores_ru = ["пепла", "луны", "судьбы", "бури", "тумана", "клинка", "памяти", "пустоты"]
    endings_ru = ["рассвета", "хаоса", "звёзд", "перерождения", "вечности", "безмолвия"]
    prefixes_en = ["Chronicles", "Code", "Legacy", "Echo", "Saga", "Project", "Frontier", "Shards"]
    cores_en = ["Ash", "Moon", "Fate", "Storm", "Mist", "Blade", "Memory", "Void"]
    endings_en = ["Dawn", "Chaos", "Stars", "Rebirth", "Eternity", "Silence"]
    genre_pool = [
        "action", "adventure", "fantasy", "drama", "comedy", "romance", "thriller", "mystery",
        "sci-fi", "supernatural", "historical", "sports", "school", "mecha", "isekai", "slice of life",
    ]

    for i in range(150):
        ru = f"{random.choice(prefixes_ru)} {random.choice(cores_ru)} {random.choice(endings_ru)}"
        en = f"{random.choice(prefixes_en)} of {random.choice(cores_en)} {random.choice(endings_en)}"
        year = random.randint(1995, 2026)
        genres = random.sample(genre_pool, 3)
        episodes = random.randint(12, 24)
        data.append(
            {
                "name_ru": f"{ru} #{i + 1}",
                "name_en": f"{en} {i + 1}",
                "year": year,
                "description": generate_description(ru),
                "genres": genres,
                "rating": round(random.uniform(6.9, 8.9), 1),
                "episodes": episodes,
                "watch_urls": _watch_urls(en),
                "episodes_data": generate_episodes(episodes),
                "views": random.randint(100, 7000),
            }
        )

    return data
