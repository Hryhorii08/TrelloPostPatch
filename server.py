import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔹 ДАННЫЕ TRELLO
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

# 🔹 ДАННЫЕ TELEGRAM
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# 🔹 Функция отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, params=params)
    return response.status_code, response.json()

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
    trello_response = response.json()

    # Отправляем уведомление в Telegram
    if response.status_code == 200:
        send_telegram_message(f"✅ Новая заявка от {name}!\n📖 Курс: {course}\n🎂 Возраст: {age}\n📍 Город: {city}")

    return response.status_code, trello_response

# 🔹 Функция поиска карточки в Trello
def find_card_by_name(name):
    url = f"https://api.trello.com/1/lists/{TRELLO_LIST_ID}/cards"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        cards = response.json()
        for card in cards:
            if card["name"] == f"Заявка от {name}":
                return card["id"]
    return None

# 🔹 Функция обновления заявки в Trello
def update_trello_card(name, field, new_value):
    card_id = find_card_by_name(name)

    if not card_id:
        return 404, {"error": "Карточка не найдена"}

    # Получаем текущие данные карточки
    url_get = f"https://api.trello.com/1/cards/{card_id}"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response_get = requests.get(url_get, params=params)

    if response_get.status_code != 200:
        return 500, {"error": "Ошибка при получении карточки"}

    card_data = response_get.json()
    description = card_data.get("desc", "")

    # Обновляем нужное поле
    updated_description = ""
    for line in description.split("\n"):
        if line.startswith(field + ":"):
            updated_description += f"{field}: {new_value}\n"
        else:
            updated_description += line + "\n"

    url_update = f"https://api.trello.com/1/cards/{card_id}"
    update_params = {
        "desc": updated_description.strip(),
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response_update = requests.put(url_update, params=update_params)

    # Отправляем уведомление в Telegram
    if response_update.status_code == 200:
        send_telegram_message(f"🔄 Изменение заявки {name}:\n✏️ {field} теперь: {new_value}")

    return response_update.status_code, response_update.json()

# 🔹 API-эндпоинт для добавления заявки
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
        return jsonify({"message": "Заявка успешно отправлена в Trello"})
    else:
        return jsonify({"error": "Ошибка при создании карточки", "details": response}), 500

# 🔹 API-эндпоинт для обновления заявки
@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field")  # "course", "age", "city"
    new_value = data.get("new_value")

    if not all([name, field, new_value]):
        return jsonify({"error": "Не все данные для обновления переданы"}), 400

    status, response = update_trello_card(name, field, new_value)

    if status == 200:
        return jsonify({"message": f"Данные успешно обновлены: {field} → {new_value}"})
    else:
        return jsonify({"error": "Ошибка при обновлении", "details": response}), 500

# 🔹 Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
