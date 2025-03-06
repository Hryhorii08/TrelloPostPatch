import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔑 API-ключи
TRELLO_API_KEY = "your_trello_api_key"
TRELLO_TOKEN = "your_trello_token"
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# 📌 URL для работы с Trello
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

# ✅ Функция отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 🔹 Функция поиска карточки в Trello по имени
def find_card(name):
    url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/cards"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        for card in response.json():
            if card["name"].lower() == f"Заявка от {name}".lower():
                return card["id"]
    return None

# 📌 Функция добавления заявки в Trello
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    try:
        data = request.json
        name, course, age, city = data["name"], data["course"], data["age"], data["city"]

        # Создаем карточку в Trello
        url = f"https://api.trello.com/1/cards"
        params = {
            "name": f"Заявка от {name}",
            "desc": f"Курс: {course}\nВозраст: {age}\nГород: {city}",
            "idList": TRELLO_LIST_NAME,
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN
        }
        response = requests.post(url, params=params)

        if response.status_code == 200:
            send_telegram_message(f"✅ *Новая заявка*\n📝 Имя: {name}\n📚 Курс: {course}\n🎂 Возраст: {age}\n📍 Город: {city}")
            return "Заявка успешно добавлена в Trello и Telegram"
        else:
            return jsonify({"error": "Ошибка при создании карточки"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📌 Функция обновления данных заявки в Trello
@app.route("/update_trello", methods=["PUT"])
def update_trello():
    try:
        data = request.json
        name, field, new_value = data["name"], data["field"], data["new_value"]

        # Ищем карточку по имени
        card_id = find_card(name)
        if not card_id:
            return jsonify({"error": f"Заявка с именем '{name}' не найдена."}), 404

        # Получаем текущие данные карточки
        url_card = f"https://api.trello.com/1/cards/{card_id}"
        params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
        response = requests.get(url_card, params=params)
        
        if response.status_code != 200:
            return jsonify({"error": "Ошибка при получении данных карточки"}), 500
        
        card_desc = response.json()["desc"]
        updated_desc = []

        # Обновляем только нужное поле
        for line in card_desc.split("\n"):
            if field.lower() in line.lower():
                updated_desc.append(f"{field.capitalize()}: {new_value}")
            else:
                updated_desc.append(line)

        updated_desc_text = "\n".join(updated_desc)

        # Обновляем карточку
        url_update = f"https://api.trello.com/1/cards/{card_id}"
        update_params = {
            "desc": updated_desc_text,
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN
        }
        update_response = requests.put(url_update, params=update_params)

        if update_response.status_code == 200:
            send_telegram_message(f"🔄 *Обновление заявки*\n📝 Имя: {name}\n🖊 Изменено: {field} → {new_value}")
            return f"Заявка '{name}' успешно обновлена!"
        else:
            return jsonify({"error": "Ошибка при обновлении данных"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
