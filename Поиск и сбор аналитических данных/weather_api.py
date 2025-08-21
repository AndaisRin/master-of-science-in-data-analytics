import requests

# Укажите свой API-токен, полученный на https://www.weatherapi.com
API_KEY = "API-токен"
CITY = "Смоленск"
url = "http://api.weatherapi.com/v1/current.json"

# Параметры запроса: ключ API, название города и отключение данных об качестве воздуха (не обязательный параметр)
params = {
    "key": API_KEY,
    "q": CITY,
    "aqi": "no"
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()

    # Извлекаем название города, температуру и "ощущается как"
    city_name = data["location"]["name"]
    temp_c = data["current"]["temp_c"]
    feelslike_c = data["current"]["feelslike_c"]

    print("Город:", city_name)
    print("Температура:", temp_c, "°C")
    print("Ощущается как:", feelslike_c, "°C")
else:
    print("Ошибка запроса:", response.status_code)
