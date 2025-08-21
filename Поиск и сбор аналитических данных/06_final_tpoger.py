# Инструменты парсинга:
# Selenium используется для автоматизации браузера и загрузки динамического контента (прокрутка страницы, подгрузка статей).
# BeautifulSoup применяется для парсинга HTML-кода и извлечения нужных данных из DOM после полной загрузки страницы.
# Такой подход позволяет обрабатывать сайты с динамической подгрузкой контента через JavaScript, как у tproger.ru.


import time
import logging
import csv
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Создание объекта временной зоны UTC+3
utc_plus_3 = timezone(timedelta(hours=3))

def get_date_range():
    """Получение диапазона дат за последние 2 месяца"""
    end_date = datetime.now(utc_plus_3).replace(hour=23, minute=59, second=59)
    start_date = (end_date - timedelta(days=60)).replace(hour=0, minute=0, second=0)
    logger.debug(f"Диапазон дат: {start_date} - {end_date}")
    return start_date, end_date

def scroll_to_load_all_articles(driver, start_date):
    """Прокрутка страницы вниз до загрузки всех статей в заданном диапазоне дат"""
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    logger.info("Начало прокрутки страницы для загрузки всех статей.")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            logger.debug("Достигнут конец страницы.")
            break
        last_height = new_height
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = soup.select('.tp-ui-post-card')
        if articles:
            last_article = articles[-1]
            date_element = last_article.select_one('time')
            if date_element and date_element.has_attr('datetime'):
                article_date = datetime.fromisoformat(date_element['datetime'])
                if article_date < start_date:
                    logger.debug(f"Дата последней статьи {article_date} раньше начальной даты {start_date}.")
                    break
    logger.info("Прокрутка страницы завершена.")

def parse_articles(driver, start_date, end_date):
    """Парсинг статей в заданном диапазоне дат"""
    logger.info("Начало парсинга статей.")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.select('.tp-ui-post-card')
    data = []
    for article in articles:
        try:
            date_element = article.select_one('time')
            if date_element and date_element.has_attr('datetime'):
                article_date = datetime.fromisoformat(date_element['datetime'])
                if not (start_date <= article_date <= end_date):
                    continue
            else:
                continue
            title_element = article.select_one('.tp-ui-post-card__title a')
            title = title_element.get_text(strip=True) if title_element else ''
            url = 'https://tproger.ru' + title_element['href'] if title_element and title_element.has_attr('href') else ''
            description_element = article.select_one('.tp-ui-post-card__description')
            description = description_element.get_text(strip=True) if description_element else ''
            likes_element = article.select_one('.tp-ui-post-card__action-entity--like .tp-ui-post-card__action-entity-text')
            likes = int(likes_element.get_text(strip=True)) if likes_element else 0
            comments_element = article.select_one('.tp-ui-post-card__action-entity--comments .tp-ui-post-card__action-entity-text')
            comments = int(comments_element.get_text(strip=True)) if comments_element else 0
            data.append({
                'url': url,
                'date': article_date.strftime('%Y-%m-%d %H:%M:%S'),
                'title': title,
                'description': description,
                'likes': likes,
                'comments': comments
            })
            logger.debug(f"Добавлена статья: {title}")
        except Exception as e:
            logger.exception(f"Ошибка при обработке статьи: {e}")
    logger.info(f"Парсинг завершен. Найдено статей: {len(data)}")
    return data

def save_to_csv(data):
    """Сохранение данных в CSV файл"""
    filename = f"tproger_articles_{datetime.now().strftime('%Y%m%d')}.csv"
    try:
        with open(filename, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['url', 'date', 'title', 'description', 'likes', 'comments'])
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logger.info(f"Данные сохранены в файл {filename}")
    except Exception as e:
        logger.exception(f"Ошибка при сохранении данных в CSV: {e}")

def main():
    start_date, end_date = get_date_range()
    logger.info("Запуск парсера Tproger")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://tproger.ru/")
        logger.info("Открытие главной страницы Tproger")
        scroll_to_load_all_articles(driver, start_date)
        articles_data = parse_articles(driver, start_date, end_date)
        if articles_data:
            save_to_csv(articles_data)
        else:
            logger.warning("Нет данных для сохранения.")
    except Exception as e:
        logger.exception(f"Ошибка в процессе выполнения: {e}")
    finally:
        driver.quit()
        logger.info("Завершение работы парсера.")

if __name__ == "__main__":
    main()
