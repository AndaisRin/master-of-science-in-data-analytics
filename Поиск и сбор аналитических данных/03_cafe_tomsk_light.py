from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

# Инициализация браузера в режиме без окна (headless)
def init_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    return driver


# Парсим названия, рейтинги и направления у всех карточек ресторанов
def parse_restaurants(driver):
    items = driver.find_elements(By.CSS_SELECTOR, "li.minicard-item.js-results-item")
    data = []
    for item in items:
        # Название ресторана
        name = item.find_element(By.CSS_SELECTOR, ".minicard-item__title .title-link").text
        # Рейтинг (заменяем запятую на точку)
        rating = item.find_element(By.CSS_SELECTOR, ".minicard-item__rating .z-text--bold").text.replace(",", ".")
        # Категории/направления
        features = item.find_elements(By.CSS_SELECTOR, ".minicard-item__features a")
        spans = item.find_elements(By.CSS_SELECTOR, ".minicard-item__features span:not(.price-category):not(.bullet)")
        directions = [f.text for f in features + spans if f.text]
        # Добавляем запись в список
        data.append({
            "Название": name,
            "Рейтинг": rating,
            "Направления": ";".join(directions)
        })
    return data

# Сохраняем данные в CSV-файл
def save_to_csv(data, filename="tomsk_restaurants.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Название", "Рейтинг", "Направления"])
        writer.writeheader()
        writer.writerows(data)

# Главная функция: запускаем браузер, загружаем страницу, парсим и сохраняем данные
def main():
    driver = init_driver()
    driver.get("https://zoon.ru/tomsk/restaurants/")
    data = parse_restaurants(driver)
    save_to_csv(data)
    driver.quit()

if __name__ == "__main__":
    main()
