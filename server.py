import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ДАННЫЕ ДЛЯ ДОСТУПА К TRELLO
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_BOARD_ID = "67c19cc6cd0d960e2398be79"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

# ДАННЫЕ ДЛЯ ТЕЛЕГРАМ-КАНАЛА
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# Функция отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, params=params)

# Функция создания карточки в Trello
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
        send_telegram_message(f"✅ Новая заявка от {name} добавлена в Trello!")
    return response.status_code, response.json()

# Функция поиска ID карточки по имени
def get_card_id_by_name(name):
    url = f"https://api.trello.com/1/lists/{TRELLO_LIST_ID}/cards"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        for card in response.json():
            if card["name"] == f"Заявка от {name}":
                return card["id"], card["desc"]
    return None, None

# Функция обновления данных в карточке Trello
def update_trello_card(name, field, new_value):
    card_id, current_desc = get_card_id_by_name(name)
    if not card_id:
        return 404, {"error": "Карточка не найдена"}
    
    # Разбираем текущее описание
    desc_lines = current_desc.split("\n")
    desc_dict = {line.split(": ")[0]: line.split(": ")[1] for line in desc_lines if ": " in line}
    
    # Обновляем только нужное поле
    if field in desc_dict:
        desc_dict[field] = new_value
    else:
        return 400, {"error": "Поле не найдено"}
    
    # Формируем обновленное описание
    updated_desc = "\n".join([f"{key}: {value}" for key, value in desc_dict.items()])
    
    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {"desc": updated_desc, "key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    response = requests.put(url, params=params)
    
    if response.status_code == 200:
        send_telegram_message(f"✅ Данные обновлены! В Trello изменено: {field} → {new_value}")
    return response.status_code, response.json()

# API-эндпоинт для добавления новой заявки
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    data = request.json
    name, course, age, city = data.get("name"), data.get("course"), data.get("age"), data.get("city")
    if not all([name, course, age, city]):
        return jsonify({"error": "Не все данные заполнены"}), 400
    status, response = create_trello_card(name, course, age, city)
    return jsonify(response), status

# API-эндпоинт для обновления данных в карточке Trello
@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name, field, new_value = data.get("name"), data.get("field"), data.get("new_value")
    if not all([name, field, new_value]):
        return jsonify({"error": "Не все данные заполнены"}), 400
    status, response = update_trello_card(name, field, new_value)
    return jsonify(response), status

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
