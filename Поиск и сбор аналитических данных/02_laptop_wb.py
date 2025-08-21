import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_laptop_specs(url):
    # Настройка драйвера
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)

    # Перечень характеристик, которые нужно найти
    required_specs = {
        "Операционная система",
        "Диагональ экрана (дюйм)",
        "Тип матрицы",
        "Разрешение экрана",
        "Линейка процессоров",
        "Процессор",
        "Количество ядер процессора",
        "Тактовая частота процессора",
        "Тип оперативной памяти",
        "Объем оперативной памяти (Гб)",
        "Тип накопителя",
        "Объем накопителя",
        "Комплектация",
        "Страна производства",
        "Разъем HDMI",
        "Разъем для наушн./микрофона",
        "Разъем карт памяти",
        "Материал корпуса",
        "Габариты ноутбука",
        "Вес без упаковки (кг)",
        "Количество динамиков",
        "Емкость аккумулятора"
    }

    collected_data = {}

    try:
        driver.get(url)

        # Подождать загрузки таблицы характеристик
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'product-params__table'))
        )

        # Найти все строки характеристик
        rows = driver.find_elements(By.CSS_SELECTOR, '.product-params__table .product-params__row')

        for row in rows:
            try:
                # Название характеристики
                key_element = row.find_element(By.CSS_SELECTOR, 'th span span')
                key = key_element.text.strip()

                # Значение характеристики
                value_element = row.find_element(By.CSS_SELECTOR, 'td span')
                value = value_element.text.strip()

                # Если характеристика в списке нужных, сохранить
                if key in required_specs:
                    collected_data[key] = value
            except Exception as e:
                continue

        # Вывод результата в формате JSON
        print(json.dumps(collected_data, ensure_ascii=False, indent=4))

    finally:
        driver.quit()

# Запуск функции
scrape_laptop_specs('https://www.wildberries.ru/catalog/216378094/detail.aspx')
