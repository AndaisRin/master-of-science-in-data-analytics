from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException
)
import time
import csv
import logging

# --- Логирование ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def init_driver():
    logger.info("Инициализация headless Chrome WebDriver")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    return driver

def load_all_pages(driver, timeout=30, pause=2):
    logger.info("Начинаем подгрузку всех страниц через кнопку 'Показать ещё'")
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.minicard-item.js-results-item")))
    last_count = len(driver.find_elements(By.CSS_SELECTOR, "li.minicard-item.js-results-item"))

    while True:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "span.js-next-page")
            logger.info("Нашли кнопку 'Показать ещё', скроллим")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)

            # Ждём исчезновения прелоадера
            try:
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".js-loading-box")))
                logger.debug("Прелоадер исчез")
            except TimeoutException:
                logger.debug("Прелоадер всё ещё на странице (таймаут)")

            # Пробуем обычный клик
            try:
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.js-next-page")))
                logger.info("Кликаем по кнопке обычным click()")
                btn.click()
            except ElementClickInterceptedException:
                logger.warning("Click() перехвачен — выполняем JS-клик")
                driver.execute_script("arguments[0].click();", btn)

            # Ждём загрузки новых элементов
            time.sleep(pause)
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "li.minicard-item.js-results-item")) > last_count)
            current_count = len(driver.find_elements(By.CSS_SELECTOR, "li.minicard-item.js-results-item"))
            logger.info(f"Новое количество карточек: {current_count}")
            last_count = current_count

        except (NoSuchElementException, TimeoutException):
            logger.info("Кнопка 'Показать ещё' недоступна — пагинация завершена")
            break

def parse_restaurants(driver):
    logger.info("Парсим рестораны")
    elems = driver.find_elements(By.CSS_SELECTOR, "li.minicard-item.js-results-item")
    data = []
    for idx, el in enumerate(elems, start=1):
        logger.info(f"Парсим #{idx}")
        try:
            name = el.find_element(By.CSS_SELECTOR, ".minicard-item__title .title-link").text.strip()
        except:
            name = ""
        try:
            rating = el.find_element(By.CSS_SELECTOR, ".minicard-item__rating .z-text--bold").text.replace(",", ".").strip()
        except:
            rating = ""
        directions = []
        try:
            feat = el.find_element(By.CSS_SELECTOR, ".minicard-item__features")
            for a in feat.find_elements(By.TAG_NAME, "a"):
                directions.append(a.text.strip())
            spans = feat.find_elements(By.CSS_SELECTOR, "span:not(.price-category):not(.bullet)")
            for sp in spans:
                txt = sp.text.strip()
                if txt and txt not in directions:
                    directions.insert(0, txt)
        except:
            pass
        data.append({
            "Название": name,
            "Рейтинг": rating,
            "Направления": ";".join(directions)
        })
    logger.info(f"Всего заведений: {len(data)}")
    return data

def save_to_csv(data, filename="tomsk_restaurants.csv"):
    logger.info(f"Сохраняем CSV: {filename}")
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Название", "Рейтинг", "Направления"])
        writer.writeheader()
        writer.writerows(data)
    logger.info("CSV успешно сохранён")

def main():
    logger.info("Старт скрипта")
    driver = init_driver()
    driver.get("https://zoon.ru/tomsk/restaurants/")
    logger.info("Открыта страница ресторанов Томска")
    load_all_pages(driver, timeout=60, pause=3)
    restaurants = parse_restaurants(driver)
    save_to_csv(restaurants)
    driver.quit()
    logger.info("Драйвер закрыт, работа завершена")

if __name__ == "__main__":
    main()
