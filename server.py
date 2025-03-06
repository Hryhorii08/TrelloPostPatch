import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔹 ДАННЫЕ TRELLO
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# 🔹 Функция отправки заявки в Trello
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
    return response.status_code, response.json()

# 🔹 Функция поиска заявки
def find_trello_card(name):
    url = f"https://api.trello.com/1/lists/{TRELLO_LIST_ID}/cards"
    query = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(url, params=query)

    if response.status_code == 200:
        cards = response.json()
        for card in cards:
            if card["name"].lower() == f"заявка от {name}".lower():
                return card
    return None

# 🔹 Функция обновления заявки
def update_trello_card(name, field, new_value):
    card = find_trello_card(name)
    if not card:
        return False, "Заявка не найдена."

    # Изменяем только нужное поле, сохраняя остальные данные
    desc_lines = card["desc"].split("\n")
    new_desc = []
    updated = False

    for line in desc_lines:
        if field in line.lower():
            new_desc.append(f"{field.capitalize()}: {new_value}")
            updated = True
        else:
            new_desc.append(line)

    if not updated:
        return False, f"Поле {field} не найдено в заявке."

    url = f"https://api.trello.com/1/cards/{card['id']}"
    query = {"desc": "\n".join(new_desc), "key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.put(url, params=query)

    if response.status_code == 200:
        send_telegram_message(f"✅ Данные обновлены! В заявке '{name}' изменено поле '{field}' на '{new_value}'.")
        return True, f"Данные обновлены: {field} → {new_value}"
    else:
        return False, "Ошибка при обновлении заявки."

# 🔹 Функция отправки сообщений в Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, params=params)

# 🔹 API-эндпоинт для отправки заявки
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
        send_telegram_message(f"✅ Новая заявка от {name} успешно добавлена в Trello!")
        return "Заявка успешно отправлена в Trello"
    else:
        return "Ошибка при создании заявки в Trello"

# 🔹 API-эндпоинт для обновления заявки
@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field").lower()
    new_value = data.get("new_value")

    if not all([name, field, new_value]):
        return jsonify({"error": "Не все данные переданы"}), 400

    success, message = update_trello_card(name, field, new_value)
    return message if success else message

# 🔹 Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
