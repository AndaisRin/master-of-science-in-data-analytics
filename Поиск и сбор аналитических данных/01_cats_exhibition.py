import requests
from bs4 import BeautifulSoup
import csv
import logging
import re
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_soup(url):
    """Получает объект BeautifulSoup по URL."""
    try:
        logging.info("Запрос: %s", url)
        response = requests.get(url)
        response.raise_for_status()
        # Приводим кодировку к UTF-8, если нужно
        response.encoding = 'windows-1251'
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        logging.error("Ошибка при запросе %s: %s", url, e)
        return None


def extract_max_page(soup):
    """
    Определяет максимальное количество страниц на основании блока пагинации.
    Ищем в <div id='paginator'> все ссылки с параметром page.
    """
    max_page = 1
    paginator = soup.find('div', id='paginator')
    if paginator:
        links = paginator.find_all('a', href=True)
        for link in links:
            href = link['href']
            match = re.search(r'page=(\d+)', href)
            if match:
                page_num = int(match.group(1))
                if page_num > max_page:
                    max_page = page_num
    return max_page


def parse_exhibition(div):
    """
    Извлекает из блока (div.listitem) информацию:
    - Дата проведения (из <h2>)
    - Название выставки (из <span class="cl-green"> внутри <h2>)
    - Клуб-Организатор (из текста блока <div class="msgtext">)
    """
    # Ищем ссылку с <h2>
    a_tag = div.find('a')
    if not a_tag:
        return None

    h2_tag = a_tag.find('h2')
    if not h2_tag:
        return None

    # Получаем полный текст заголовка
    full_text = h2_tag.get_text(separator=' ', strip=True)
    # Предполагаем, что название выставки находится в кавычках «...»
    if '«' in full_text:
        date_text = full_text.split('«')[0].strip().rstrip('.,')
    else:
        date_text = full_text

    # Извлекаем название выставки
    span_title = h2_tag.find('span', class_='cl-green')
    title_text = span_title.get_text(strip=True) if span_title else ''

    # Извлекаем Клуб-Организатор из блока msgtext
    organizer = ""
    msg_div = div.find('div', class_='msgtext')
    if msg_div:
        msg_text = msg_div.get_text(separator=' ', strip=True)
        # Ищем подстроку вида "Клуб - Организатор: <значение>;"
        match = re.search(r'Клуб - Организатор:\s*([^;]+)', msg_text)
        if match:
            organizer = match.group(1).strip()

    return (date_text, title_text, organizer)


def parse_exhibitions(soup):
    """
    Извлекает список выставок со страницы (каждая выставка – из блока с классом 'listitem').
    """
    exhibitions = []
    items = soup.find_all('div', class_='listitem')
    for item in items:
        data = parse_exhibition(item)
        if data:
            exhibitions.append(data)
    return exhibitions


def main():
    base_url = "http://ru-pets.ru/index.php?m=6&c=2&to=1"

    # Получаем первую страницу и определяем максимальное число страниц
    soup = get_soup(base_url)
    if not soup:
        logging.error("Не удалось загрузить первую страницу.")
        return
    max_page = extract_max_page(soup)
    logging.info("Найдено страниц: %s", max_page)

    all_exhibitions = []
    # Обрабатываем все страницы
    for page in range(1, max_page + 1):
        if page == 1:
            url = base_url
        else:
            url = f"http://ru-pets.ru/index.php?m=6&to=1&c=2&page={page}"
        logging.info("Обработка страницы %s: %s", page, url)
        soup = get_soup(url)
        if soup:
            exhibitions = parse_exhibitions(soup)
            logging.info("Найдено выставок на странице %s: %s", page, len(exhibitions))
            all_exhibitions.extend(exhibitions)
        else:
            logging.error("Пропуск страницы %s из-за ошибки запроса.", page)
        time.sleep(1)  # задержка между запросами

    # Записываем данные в CSV
    csv_filename = "exhibitions.csv"
    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Дата проведения", "Название выставки", "Клуб-Организатор"])
            writer.writerows(all_exhibitions)
        logging.info("Данные успешно сохранены в файл %s", csv_filename)
    except Exception as e:
        logging.error("Ошибка записи в CSV: %s", e)


if __name__ == '__main__':
    main()
    logging.info("Сбор данных завершён.")
