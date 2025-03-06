from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# 🔑 Токены и настройки
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# ДАННЫЕ ДЛЯ ДОСТУПА К TRELLO
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_BOARD_ID = "67c19cc6cd0d960e2398be79"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

# 📌 URL для Trello API
TRELLO_URL = "https://api.trello.com/1"
HEADERS = {"Accept": "application/json"}

# 📌 Функция отправки сообщения в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# 📌 Создание новой заявки в Trello
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    data = request.json
    name = data.get("name")
    course = data.get("course")
    age = data.get("age")
    city = data.get("city")

    if not all([name, course, age, city]):
        response = {"error": "Не все данные заполнены"}
        return json.dumps(response), 400, {'Content-Type': 'application/json'}

    # Создание карточки в Trello
    query = {
        "name": f"Заявка от {name}",
        "desc": f"📚 Курс: {course}\n🎂 Возраст: {age}\n📍 Город: {city}",
        "idList": TRELLO_LIST_ID,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.post(f"{TRELLO_URL}/cards", params=query, headers=HEADERS)

    if response.status_code == 200:
        send_telegram_message(f"✅ *Новая заявка*\n📌 Имя: {name}\n📚 Курс: {course}\n🎂 Возраст: {age}\n📍 Город: {city}")
        response_data = {"status": "success", "message": "Заявка успешно добавлена"}
        return json.dumps(response_data, ensure_ascii=False), 200, {'Content-Type': 'application/json'}
    else:
        response_data = {"error": "Ошибка создания заявки в Trello"}
        return json.dumps(response_data, ensure_ascii=False), 500, {'Content-Type': 'application/json'}

# 📌 Обновление заявки в Trello
@app.route("/update_trello", methods=["PATCH"])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field")
    new_value = data.get("new_value")

    if not all([name, field, new_value]):
        response = {"error": "Не все данные заполнены"}
        return json.dumps(response), 400, {'Content-Type': 'application/json'}

    # Поиск карточки по имени
    cards_response = requests.get(f"{TRELLO_URL}/boards/{TRELLO_BOARD_ID}/cards",
                                  params={"key": TRELLO_API_KEY, "token": TRELLO_TOKEN},
                                  headers=HEADERS)

    if cards_response.status_code != 200:
        response = {"error": "Ошибка при получении списка карточек"}
        return json.dumps(response), 500, {'Content-Type': 'application/json'}

    cards = cards_response.json()
    card = next((c for c in cards if c["name"] == f"Заявка от {name}"), None)

    if not card:
        response = {"error": "Заявка не найдена"}
        return json.dumps(response), 404, {'Content-Type': 'application/json'}

    card_id = card["id"]
    new_desc = card["desc"].split("\n")

    # Обновляем только указанное поле
    field_mapping = {"course": "📚 Курс", "age": "🎂 Возраст", "city": "📍 Город"}

    for i, line in enumerate(new_desc):
        if line.startswith(field_mapping[field]):
            new_desc[i] = f"{field_mapping[field]}: {new_value}"

    updated_desc = "\n".join(new_desc)
    update_response = requests.put(f"{TRELLO_URL}/cards/{card_id}",
                                   params={"desc": updated_desc, "key": TRELLO_API_KEY, "token": TRELLO_TOKEN},
                                   headers=HEADERS)

    if update_response.status_code == 200:
        send_telegram_message(f"🛠 *Обновление заявки*\n📌 Имя: {name}\n✏ Изменено: {field_mapping[field]} → {new_value}")
        response_data = {"status": "success", "message": f"{field_mapping[field]} успешно обновлено"}
        return json.dumps(response_data, ensure_ascii=False), 200, {'Content-Type': 'application/json'}
    else:
        response_data = {"error": "Ошибка обновления заявки"}
        return json.dumps(response_data, ensure_ascii=False), 500, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
