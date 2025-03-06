import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔑 API-ключи и параметры
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# 📌 URL Trello
TRELLO_BASE_URL = "https://api.trello.com/1"

# 🔹 Функция для поиска карточки по имени
def find_card_by_name(name):
    url = f"{TRELLO_BASE_URL}/boards/{TRELLO_BOARD_ID}/cards"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        cards = response.json()
        for card in cards:
            if card["name"].lower() == f"Заявка от {name}".lower():
                return card["id"], card["desc"]
    return None, None  # Если карточка не найдена

# 🔹 Функция для отправки уведомлений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

# 📌 Обработка создания заявки
@app.route('/send_to_trello', methods=['POST'])
def send_to_trello():
    data = request.json
    name = data.get("name")
    course = data.get("course")
    age = data.get("age")
    city = data.get("city")

    if not all([name, course, age, city]):
        return "Ошибка: не все данные заполнены", 400

    # 📌 Создаём карточку
    url = f"{TRELLO_BASE_URL}/cards"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "idList": "your_list_id",
        "name": f"Заявка от {name}",
        "desc": f"Курс: {course}\nВозраст: {age}\nГород: {city}"
    }
    response = requests.post(url, params=params)

    if response.status_code == 200:
        send_telegram_message(f"✅ *Новая заявка*\n👤 Имя: {name}\n📚 Курс: {course}\n🎂 Возраст: {age}\n🌍 Город: {city}")
        return f"Заявка успешно добавлена в Trello!", 200
    else:
        return "Ошибка при добавлении заявки в Trello", 500

# 📌 Обновление заявки (PATCH)
@app.route('/update_trello', methods=['PATCH'])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field")
    new_value = data.get("new_value")

    if not all([name, field, new_value]):
        return "Ошибка: не все данные заполнены", 400

    # 🔍 Ищем карточку по имени
    card_id, card_desc = find_card_by_name(name)
    if not card_id:
        return f"Заявка с именем '{name}' не найдена.", 404

    # 🔄 Обновляем только нужное поле в описании
    desc_lines = card_desc.split("\n")
    updated_desc = []
    field_mapping = {"course": "Курс", "age": "Возраст", "city": "Город"}

    field_found = False
    for line in desc_lines:
        if line.startswith(field_mapping.get(field, "")):
            updated_desc.append(f"{field_mapping[field]}: {new_value}")
            field_found = True
        else:
            updated_desc.append(line)

    if not field_found:
        updated_desc.append(f"{field_mapping[field]}: {new_value}")

    new_desc = "\n".join(updated_desc)

    # 🔄 Запрос на обновление карточки
    url = f"{TRELLO_BASE_URL}/cards/{card_id}"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "desc": new_desc
    }
    response = requests.put(url, params=params)

    if response.status_code == 200:
        send_telegram_message(f"🔄 *Обновление данных заявки*\n👤 Имя: {name}\n✏️ {field_mapping[field]} изменено на: {new_value}")
        return f"Данные обновлены! Информация в Trello изменена на {new_value}", 200
    else:
        return "Ошибка при обновлении заявки в Trello", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
