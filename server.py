import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔹 Данные Trello и Telegram
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# 🔹 Базовый URL API Trello
TRELLO_BASE_URL = "https://api.trello.com/1"

# 🔹 Функция для поиска карточки по имени
def find_card(name):
    url = f"{TRELLO_BASE_URL}/lists/{TRELLO_LIST_ID}/cards"
    query = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(url, params=query)
    
    if response.status_code == 200:
        cards = response.json()
        for card in cards:
            if card["name"].lower() == f"заявка от {name.lower()}":
                return card["id"], card.get("desc", "")
    return None, None

# 🔹 Функция для отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 🔹 Функция для создания заявки
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    data = request.json
    name = data.get("name")
    course = data.get("course")
    age = data.get("age")
    city = data.get("city")

    if not all([name, course, age, city]):
        return "Ошибка: не все данные заполнены", 400

    card_id, _ = find_card(name)
    if card_id:
        return "Ошибка: заявка с таким именем уже существует", 400

    url = f"{TRELLO_BASE_URL}/cards"
    query = {
        "name": f"Заявка от {name}",
        "desc": f"Курс: {course}\nВозраст: {age}\nГород: {city}",
        "idList": TRELLO_LIST_ID,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.post(url, params=query)

    if response.status_code == 200:
        send_telegram_message(f"✅ *Новая заявка* от {name} успешно добавлена в Trello!")
        return f"Заявка от {name} успешно добавлена", 200
    else:
        return "Ошибка при создании заявки", 500

# 🔹 Функция для обновления заявки
@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field")
    new_value = data.get("new_value")

    if not all([name, field, new_value]):
        return "Ошибка: не все данные переданы", 400

    card_id, old_desc = find_card(name)
    if not card_id:
        return f"Заявка с именем '{name}' не найдена", 400

    # Обновление конкретного поля в описании заявки
    updated_desc = []
    field_updated = False
    for line in old_desc.split("\n"):
        if line.startswith(f"{field.capitalize()}:"):
            updated_desc.append(f"{field.capitalize()}: {new_value}")
            field_updated = True
        else:
            updated_desc.append(line)

    if not field_updated:
        updated_desc.append(f"{field.capitalize()}: {new_value}")

    new_desc = "\n".join(updated_desc)

    url = f"{TRELLO_BASE_URL}/cards/{card_id}"
    query = {"desc": new_desc, "key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.put(url, params=query)

    if response.status_code == 200:
        send_telegram_message(f"🟢 *Обновление заявки*\nИмя: {name}\n✏ Изменено: {field} → {new_value}")
        return f"Заявка '{name}' успешно обновлена. {field.capitalize()} изменен на {new_value}", 200
    else:
        return "Ошибка при обновлении заявки", 500

# 🔹 Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
