import requests
from flask import Flask, request

app = Flask(__name__)

# Telegram Bot данные
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
CHAT_ID = "-1002307069728"

# Trello API данные
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

# Функция отправки сообщения в Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text}
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
    return response.status_code == 200

# Функция обновления заявки в Trello
def update_trello_card(name, field, new_value):
    search_url = f"https://api.trello.com/1/search"
    search_params = {
        "query": name,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.get(search_url, params=search_params)
    data = response.json()
    
    if "cards" in data and data["cards"]:
        card_id = data["cards"][0]["id"]
        update_url = f"https://api.trello.com/1/cards/{card_id}"
        update_params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN,
            "desc": f"{field}: {new_value}"  # Обновляем только описание
        }
        update_response = requests.put(update_url, params=update_params)
        return update_response.status_code == 200
    return False

# Эндпоинт для создания новой заявки
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    data = request.json
    name, course, age, city = data.get("name"), data.get("course"), data.get("age"), data.get("city")
    
    if not all([name, course, age, city]):
        return "Ошибка: не все данные заполнены"
    
    if create_trello_card(name, course, age, city):
        message = f"✅ Новая заявка:\nИмя: {name}\nКурс: {course}\nВозраст: {age}\nГород: {city}"
        send_telegram_message(message)
        return "Заявка успешно отправлена"
    else:
        return "Ошибка при создании заявки в Trello"

# Эндпоинт для обновления заявки
@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name, field, new_value = data.get("name"), data.get("field"), data.get("new_value")
    
    if not all([name, field, new_value]):
        return "Ошибка: недостаточно данных для обновления"
    
    if update_trello_card(name, field, new_value):
        message = f"🔄 Обновление заявки:\nИмя: {name}\nИзменено: {field} → {new_value}"
        send_telegram_message(message)
        return "Данные успешно обновлены"
    else:
        return "Ошибка при обновлении заявки в Trello"

# Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
