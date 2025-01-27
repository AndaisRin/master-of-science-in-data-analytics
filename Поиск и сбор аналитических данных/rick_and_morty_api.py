import requests


def get_male_female_count():
    """
    Делает GET-запрос к https://rickandmortyapi.com/api/character?page=1
    и возвращает словарь вида {'male': X, 'female': Y}, где X и Y —
    количество персонажей с соответствующим гендером на первой странице.
    """
    url = "https://rickandmortyapi.com/api/character?page=1"
    response = requests.get(url)
    data = response.json()

    male_count = 0
    female_count = 0

    # Перебираем персонажей (только с первой страницы)
    for character in data["results"]:
        if character["gender"] == "Male":
            male_count += 1
        elif character["gender"] == "Female":
            female_count += 1

    return {"male": male_count, "female": female_count}


def get_character_by_status(character_status):
    """
    Принимает статус персонажа (alive, dead, unknown),
    выполняет GET-запрос к https://rickandmortyapi.com/api/character?status=...
    и возвращает список имен ВСЕХ персонажей с таким статусом (по всем страницам).
    """
    url = "https://rickandmortyapi.com/api/character"
    params = {
        "status": character_status,
        "page": 1
    }
    all_names = []

    while True:
        response = requests.get(url, params=params)

        # Если код статуса не 200 (например, 404, если страниц больше нет), выходим
        if response.status_code != 200:
            break

        data = response.json()
        results = data.get("results", [])

        # Собираем имена персонажей с этой страницы
        for character in results:
            all_names.append(character["name"])

        # Проверяем, есть ли следующая страница
        next_page_url = data["info"].get("next")
        if next_page_url is None:
            # Если следующей страницы нет, завершаем цикл
            break
        else:
            # Увеличиваем номер страницы на 1
            params["page"] += 1

    return all_names


if __name__ == "__main__":
    # Пример тестового вызова первой функции
    gender_counts = get_male_female_count()
    print("Male/Female counts (page=1):", gender_counts)

    # Пример тестового вызова второй функции
    alive_characters = get_character_by_status("alive")
    print(f"Список всех 'Alive'-персонажей (количество {len(alive_characters)}):")
    print(alive_characters)
