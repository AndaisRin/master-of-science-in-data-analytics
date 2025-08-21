import requests
import json
import time

# Укажите свой API-токен, полученный на https://api.kinopoisk.dev/
API_KEY = "API-токен"
BASE_URL = "https://api.kinopoisk.dev/v1.4/movie"

# Начальные параметры запроса:
# - year: 2000
# - genres.name: +комедия (оператор включения; requests сам выполнит URL-кодирование)
# - sortField: сортировка по рейтингу Кинопоиска (rating.kp)
# - sortType: -1 означает сортировку по убыванию (если API поддерживает такой синтаксис)
# - limit: количество записей на страницу (здесь предполагается 100; уточните максимальное значение в документации)
params = {
    "year": 2000,
    "genres.name": "+комедия",
    "sortField": "rating.kp",
    "sortType": "-1",
    "limit": 100,
}

headers = {
    "X-API-KEY": API_KEY
}

all_films = []
page = 1

while len(all_films) < 1000:
    params["page"] = page
    print(f"Запрос страницы {page}...")
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Ошибка {response.status_code} на странице {page}. Завершаем сбор.")
        break

    # Предполагается, что данные возвращаются в формате JSON и содержат список фильмов в ключе "docs"
    data = response.json()
    films = data.get("docs", [])
    if not films:
        print("Фильмы закончились.")
        break

    for film in films:
        name = film.get("name", "Нет названия")
        duration = film.get("movieLength", "Не указана")
        countries = film.get("countries", [])
        countries_names = ", ".join([country.get("name", "") for country in countries])

        all_films.append({
            "название": name,
            "длительность": duration,
            "страна производитель": countries_names
        })

        if len(all_films) >= 1000:
            break

    page += 1
    time.sleep(0.5)

# Если найдено больше 1000 фильмов, оставляем только первые 1000
all_films = all_films[:1000]

# Сохраняем данные в JSON-файл
with open("kinopoisk_comedy_2000.json", "w", encoding="utf-8") as f:
    json.dump(all_films, f, ensure_ascii=False, indent=4)

print(f"Собрано {len(all_films)} фильмов.")
