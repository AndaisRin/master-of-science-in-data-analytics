import requests
import csv
from datetime import datetime

API_KEY = "SUPERJOB_API_KEY"

BASE_URL = "https://api.superjob.ru/2.0/vacancies/"

headers = {
    "X-Api-App-Id": API_KEY
}

# Параметры поиска:
# - keyword: "Аналитик"
# - period: 7 (неделя)
# - page: начинаем с 0
# - count: количество вакансий на страницу (максимум обычно 100)
params = {
    "keyword": "Аналитик",
    "period": 7,
    "page": 0,
    "count": 100
}

vacancies = []

while True:
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Ошибка запроса: {response.status_code}")
        break

    data = response.json()
    vacancies.extend(data.get("objects", []))
    if not data.get("more", False):
        break
    params["page"] += 1  # переходим к следующей странице

with open("vacancies.csv", mode="w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Ссылка на вакансию",
        "Название вакансии",
        "Название работодателя",
        "Город",
        "Заработная плата",
        "Заработная плата от",
        "Заработная плата до",
        "Должностные обязанности",
        "Дата публикации",
        "Архивная"
    ])

    for vac in vacancies:
        link = vac.get("link", "")
        title = vac.get("profession", "")
        employer = vac.get("firm_name", "")
        town = vac.get("town", {}).get("title", "") if vac.get("town") else ""
        payment_from = vac.get("payment_from", 0)
        payment_to = vac.get("payment_to", 0)
        if payment_from and payment_to:
            salary = f"от {payment_from} до {payment_to}"
        elif payment_from:
            salary = f"от {payment_from}"
        elif payment_to:
            salary = f"до {payment_to}"
        else:
            salary = "По договорённости"
        responsibilities = vac.get("candidat", "")
        timestamp = vac.get("date_published")
        pub_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d") if timestamp else ""
        is_archive = vac.get("is_archive", False)

        writer.writerow([
            link,
            title,
            employer,
            town,
            salary,
            payment_from,
            payment_to,
            responsibilities,
            pub_date,
            is_archive
        ])

print(f"Сохранено {len(vacancies)} вакансий в файл vacancies.csv")
