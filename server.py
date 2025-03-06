import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔹 ДАННЫЕ TRELLO (замени на свои)
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

# 🔹 ДАННЫЕ ДЛЯ ОТПРАВКИ В TELEGRAM
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# 🔹 Функция поиска карточки по имени
def find_card_by_name(name):
    url = f"https://api.trello.com/1/lists/{TRELLO_LIST_ID}/cards"
    query = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.get(url, params=query)
    
    if response.status_code == 200:
        cards = response.json()
        for card in cards:
            if card["name"].strip().lower() == f"Заявка от {name}".strip().lower():
                return card  # Возвращаем всю карточку
    return None  # Если не нашли

# 🔹 Функция создания заявки
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

# 🔹 Функция обновления данных заявки
def update_trello_card(name, field, new_value):
    card = find_card_by_name(name)
    
    if not card:
        return False, f"Заявка с именем '{name}' не найдена."
    
    card_id = card["id"]
    description = card.get("desc", "")

    # Парсим существующее описание
    data_lines = description.split("\n")
    updated_description = []
    field_map = {"course": "Курс", "age": "Возраст", "city": "Город"}

    field_updated = False
    for line in data_lines:
        if line.startswith(field_map[field]):
            updated_description.append(f"{field_map[field]}: {new_value}")
            field_updated = True
        else:
            updated_description.append(line)

    # Если нужное поле не было найдено, добавляем его в конец
    if not field_updated:
        updated_description.append(f"{field_map[field]}: {new_value}")

    # Собираем новое описание
    new_desc = "\n".join(updated_description)

    url = f"https://api.trello.com/1/cards/{card_id}"
    query = {
        "desc": new_desc,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.put(url, params=query)

    if response.status_code == 200:
        return True, f"Данные обновлены! Информация в Trello изменена на {new_value}"
    else:
        return False, "Ошибка при обновлении заявки."

# 🔹 Функция отправки уведомления в Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

# 🔹 API-эндпоинт для отправки заявки в Trello
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
        return jsonify({"message": "Заявка успешно отправлена в Trello"})
    else:
        return jsonify({"error": "Ошибка при создании карточки", "details": response}), 500

# 🔹 API-эндпоинт для обновления данных в Trello
@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field")  # Что изменяем (course, age, city)
    new_value = data.get("new_value")  # Новое значение

    if not all([name, field, new_value]):
        return jsonify({"error": "Недостаточно данных для обновления"}), 400

    success, message = update_trello_card(name, field, new_value)

    if success:
        send_telegram_message(f"✅ Данные обновлены! В заявке {name} изменено: {field} → {new_value}")
        return jsonify({"message": message})
    else:
        send_telegram_message(f"❌ {message}")
        return jsonify({"error": message}), 400

# 🔹 Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
