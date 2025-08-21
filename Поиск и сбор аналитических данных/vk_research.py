import requests
import csv
import re
import time
import sys

# Введите токен
TOKEN = ""
API_VERSION = "5.199"


def get_city_id(city_name):
    """
    Описание функции:
        Получает id города по его названию, используя метод database.getCities VK API.
    Входные данные:
        city_name (str) – название города.
    Выходные данные:
        int или None – id города, если город найден, иначе None.
    """
    url = "https://api.vk.com/method/database.getCities"
    params = {
        "q": city_name,
        "country_id": 1,  # Россия
        "count": 1000,
        "access_token": TOKEN,
        "v": API_VERSION
    }
    response = requests.get(url, params=params).json()
    for city in response.get("response", {}).get("items", []):
        if city.get("title", "").lower() == city_name.lower():
            return city.get("id")
    return None


def search_groups(keyword, city_id):
    """
    Описание функции:
        Выполняет поиск сообществ по ключевому слову в заданном городе с использованием метода groups.search VK API.
    Входные данные:
        keyword (str) – ключевое слово для поиска сообществ;
        city_id (int) – id города, в котором производится поиск.
    Выходные данные:
        list – список найденных сообществ (словарей) с дополнительными полями (описание, статус, число подписчиков, контакты).
    """
    url = "https://api.vk.com/method/groups.search"
    params = {
        "q": keyword,
        "city_id": city_id,
        "count": 1000,
        "extended": 1,
        "fields": "description,is_closed,members_count,contacts",
        "access_token": TOKEN,
        "v": API_VERSION
    }
    response = requests.get(url, params=params).json()
    return response.get("response", {}).get("items", [])


def extract_contact_phone(contacts):
    """
    Описание функции:
        Извлекает номер телефона из списка контактов. Если в контакте присутствует непустое значение по ключу "phone",
        оно используется. Если же значение отсутствует, производится поиск номера телефона в строке из поля "desc" с помощью регулярного выражения.
        Найденные номера объединяются в одну строку, разделённую "; ".
    Входные данные:
        contacts (list) – список контактов, где каждый контакт представлен словарём с ключами 'user_id', 'desc' и 'phone'.
    Выходные данные:
        str – строка с найденными номерами телефонов, разделёнными "; ". Если номера не найдены, возвращается пустая строка.
    """
    if not contacts:
        return ""
    phones = []
    phone_regex = re.compile(r'(\+7|8)[\s(]?\d{3}[)\s]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')
    for contact in contacts:
        phone = contact.get("phone", "").strip()
        if phone:
            phones.append(phone)
        else:
            desc = contact.get("desc", "")
            match = phone_regex.search(desc)
            if match:
                phones.append(match.group(0))
    return "; ".join(phones)


def main():
    """
    Описание функции:
        Основная функция, выполняющая поиск сообществ по ключевым словам в заданном городе (Омск),
        сортировку найденных сообществ по числу подписчиков и запись результатов в CSV-файл.
        После завершения работы выводится общее количество полученных групп и время выполнения.
    Входные данные:
        Нет (использует внутренние параметры: название города и ключевые слова).
    Выходные данные:
        CSV-файл "vk_groups.csv", содержащий информацию о найденных сообществах:
        id, название, описание, статус (is_closed), число подписчиков и контакты.
    """
    start_time = time.time()

    city_name = "Омск"
    city_id = get_city_id(city_name)
    if city_id is None:
        raise Exception(f"Город '{city_name}' не найден")

    # Ключевые слова для поиска сообществ
    keywords = ["цветы", "флористика", "магазин цветов"]
    groups_dict = {}

    # Поиск по каждому ключевому слову
    for keyword in keywords:
        groups = search_groups(keyword, city_id)
        for group in groups:
            groups_dict[group["id"]] = group

    # Сортировка сообществ по количеству подписчиков (members_count) по убыванию
    sorted_groups = sorted(groups_dict.values(), key=lambda x: x.get("members_count", 0), reverse=True)

    # Запись результатов в CSV-файл
    with open("vk_groups.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id", "name", "description", "is_closed", "members_count", "contacts"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for group in sorted_groups:
            # Извлекаем номера телефонов из списка контактов, если имеются
            contacts = extract_contact_phone(group.get("contacts", []))
            writer.writerow({
                "id": group.get("id"),
                "name": group.get("name"),
                "description": group.get("description", ""),
                "is_closed": group.get("is_closed"),
                "members_count": group.get("members_count", 0),
                "contacts": contacts
            })

    total_groups = len(sorted_groups)
    elapsed_time = time.time() - start_time
    print(f"Общее количество полученных групп: {total_groups}")
    print(f"Время выполнения: {elapsed_time:.2f} секунд")
    print("Работа завершена.")
    sys.exit(0)


if __name__ == "__main__":
    main()