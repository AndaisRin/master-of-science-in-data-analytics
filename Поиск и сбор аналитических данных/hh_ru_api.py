import requests
import csv
import time

def get_employers(area_id, max_employers=1000, per_page=100):
    """
    Получает список работодателей из заданного региона, у которых есть открытые вакансии.
    Параметры:
      - area_id: идентификатор региона
      - max_employers: максимальное число работодателей для выборки
      - per_page: число работодателей на одной странице запроса (максимум обычно 100)
    """
    employers = []
    page = 0
    while len(employers) < max_employers:
        params = {
            "area": area_id,
            "only_with_vacancies": "true",
            "page": page,
            "per_page": per_page
        }
        response = requests.get("https://api.hh.ru/employers", params=params)
        if response.status_code != 200:
            print(f"Ошибка при получении данных работодателей (код {response.status_code}).")
            break
        data = response.json()
        items = data.get("items", [])
        if not items:
            break
        employers.extend(items)
        if page >= data.get("pages", 0) - 1:
            break
        page += 1
        time.sleep(0.1)  # небольшая задержка для снижения нагрузки на API
    return employers[:max_employers]

def get_vacancy_links(employer_id, per_page=100):
    """
    Получает список ссылок на вакансии для конкретного работодателя.
    Для каждого работодателя выполняется запрос к API вакансий с параметром employer_id.
    """
    vacancy_links = []
    page = 0
    while True:
        params = {
            "employer_id": employer_id,
            "page": page,
            "per_page": per_page
        }
        response = requests.get("https://api.hh.ru/vacancies", params=params)
        if response.status_code != 200:
            print(f"Ошибка при получении вакансий для работодателя {employer_id} (код {response.status_code}).")
            break
        data = response.json()
        items = data.get("items", [])
        for vacancy in items:
            vacancy_links.append(vacancy.get("alternate_url"))
        if page >= data.get("pages", 0) - 1:
            break
        page += 1
        time.sleep(0.1)
    return vacancy_links

def main():
    area_id = 1217  # Идентификатор Алтайского края
    max_employers = 1000

    print("Получение списка работодателей...")
    employers = get_employers(area_id, max_employers)
    print(f"Найдено {len(employers)} работодателей с открытыми вакансиями.")

    employers_data = []
    for idx, employer in enumerate(employers, start=1):
        employer_id = employer.get("id")
        employer_name = employer.get("name")
        open_vacancies = employer.get("open_vacancies", 0)
        print(f"[{idx}/{len(employers)}] Обработка работодателя {employer_id} - {employer_name} "
              f"({open_vacancies} вакансий)...")
        vacancy_links = get_vacancy_links(employer_id)
        vacancy_links_str = "; ".join(vacancy_links)
        employers_data.append({
            "id": employer_id,
            "name": employer_name,
            "vacancy_links": vacancy_links_str,
            "open_vacancies": open_vacancies
        })

    employers_data.sort(key=lambda x: x["open_vacancies"], reverse=True)

    csv_filename = "employers_altai_krai.csv"
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id", "name", "vacancy_links", "open_vacancies"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for employer in employers_data:
            writer.writerow(employer)

    print(f"Данные успешно сохранены в файле: {csv_filename}")

if __name__ == "__main__":
    main()
