import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔹 Данные Trello
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"
TRELLO_BOARD_ID = "Ваш_BOARD_ID"  # Добавьте ID доски Trello

# 🔹 Данные Telegram
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# 🔹 Функция отправки уведомления в Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=payload)

# 🔹 Функция поиска карточки по имени ученика
def find_trello_card(name):
    url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/cards"
    query = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(url, params=query)

    if response.status_code == 200:
        cards = response.json()
        for card in cards:
            if card["name"].lower().strip() == f"Заявка от {name}".lower().strip():
                return card["id"], card.get("desc", "")
    return None, None

# 🔹 Функция создания заявки в Trello
def create_trello_card(name, course, age, city):
    url = "https://api.trello.com/1/cards"
    query = {
        "name": f"Заявка от {name}",
        "desc": f"Курс: {course}\nВозраст: {age}\nГород: {city}",
        "idList": TRELLO_LIST_ID,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.post(url, params=query)
    if response.status_code == 200:
        send_telegram_message(f"✅ Новая заявка от {name} добавлена в Trello.\n\n"
                              f"📌 Курс: {course}\n👶 Возраст: {age}\n📍 Город: {city}")
    return response.status_code, response.json()

# 🔹 Функция обновления данных заявки
def update_trello_card(name, field, new_value):
    card_id, current_desc = find_trello_card(name)
    if not card_id:
        return False, f"Заявка с именем '{name}' не найдена."

    # Разбираем текущее описание
    desc_lines = current_desc.split("\n")
    updated_desc = []
    found = False

    for line in desc_lines:
        if field in line.lower():
            updated_desc.append(f"{field.capitalize()}: {new_value}")
            found = True
        else:
            updated_desc.append(line)

    if not found:
        updated_desc.append(f"{field.capitalize()}: {new_value}")

    # Собираем новое описание
    new_desc = "\n".join(updated_desc)
    url = f"https://api.trello.com/1/cards/{card_id}"
    query = {"desc": new_desc, "key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.put(url, params=query)

    if response.status_code == 200:
        send_telegram_message(f"🟢 Данные обновлены!\n"
                              f"📌 В заявке <b>{name}</b> изменено <b>{field}</b> → {new_value}.")
        return True, "Изменения успешно внесены в Trello."

    return False, "Ошибка при обновлении данных Trello."

# 🔹 API-эндпоинты
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    data = request.json
    name = data.get("name")
    course = data.get("course")
    age = data.get("age")
    city = data.get("city")

    if not all([name, course, age, city]):
        return jsonify({"error": "Не все данные заполнены"}), 400

    status, response = create_trello_card(name, course, age, city)
    if status == 200:
        return jsonify({"message": "Заявка успешно отправлена в Trello."})
    else:
        return jsonify({"error": "Ошибка при создании карточки", "details": response}), 500

@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field")
    new_value = data.get("new_value")

    if not all([name, field, new_value]):
        return jsonify({"error": "Не все данные заполнены"}), 400

    success, message = update_trello_card(name, field, new_value)
    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 400

# 🔹 Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
