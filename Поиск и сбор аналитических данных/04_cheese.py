from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv

# Настройки браузера
options = Options()
options.add_argument('--headless')  # Для запуска без интерфейса
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Запуск драйвера
print("[INFO] Запуск браузера...")
driver = webdriver.Chrome(options=options)
driver.get('https://pro-syr.ru/zakvaski-dlya-syra/mezofilnye/')
print("[INFO] Открыта страница с мезофильными заквасками.")

# Нажатие кнопки "Показать еще", пока она присутствует
while True:
    try:
        print("[INFO] Поиск кнопки 'Показать еще'...")
        show_more_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.next_button_div a'))
        )
        print("[INFO] Кнопка найдена. Нажатие...")
        driver.execute_script("arguments[0].click();", show_more_button)
        time.sleep(2)  # Дать время подгрузке
    except:
        print("[INFO] Кнопка 'Показать еще' не найдена или товары загружены полностью.")
        break

# Получение HTML после полной загрузки
print("[INFO] Сбор HTML-кода страницы...")
soup = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()

# Поиск карточек товаров
products = soup.find_all('div', class_='product-layout')
print(f"[INFO] Найдено товаров: {len(products)}")

# Запись в CSV
csv_file = 'zakvaski_prosyr_full.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Название продукта', 'Цена', 'Наличие'])

    for index, product in enumerate(products, start=1):
        name_tag = product.find('div', class_='nameproduct')
        name = name_tag.get_text(strip=True) if name_tag else 'Нет данных'

        price_tag = product.find('p', class_='price')
        price = price_tag.get_text(strip=True) if price_tag else 'Нет данных'

        button = product.find('button', string=lambda s: s and 'В корзину' in s)
        availability = 'В наличии' if button else 'Нет в наличии'

        print(f"[{index}] {name} | {price} | {availability}")
        writer.writerow([name, price, availability])

print(f"[INFO] Данные успешно сохранены в файл {csv_file}")
