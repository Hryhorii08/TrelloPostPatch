import requests
from flask import Flask, request

app = Flask(__name__)

# 🔹 ДАННЫЕ TRELLO (замени на свои)
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"
TELEGRAM_BOT_TOKEN = "7788946008:AAGULYh-GIkpr-GA3ZA70ERdCAT6BcGNW-g"
TELEGRAM_CHAT_ID = "-1002307069728"

# Локальное хранилище заявок (для поиска заявок по имени)
applications = {}

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
    
    if response.status_code == 200:
        applications[name] = {"course": course, "age": age, "city": city, "card_id": response.json().get("id")}
    
    return response.status_code

# 🔹 Функция обновления заявки в Trello
def update_trello_card(name, field, new_value):
    if name not in applications:
        return "Ошибка: заявка с таким именем не найдена"
    
    card_id = applications[name]["card_id"]
    applications[name][field] = new_value

    # Формируем новое описание
    new_desc = f"Курс: {applications[name]['course']}\nВозраст: {applications[name]['age']}\nГород: {applications[name]['city']}"
    
    url = f"https://api.trello.com/1/cards/{card_id}"
    query = {
        "desc": new_desc,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.put(url, params=query)

    return response.status_code

# 🔹 Функция отправки сообщения в Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, params=params)

# 🔹 API-эндпоинт для обработки заявки
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    data = request.json
    name = data.get("name")
    course = data.get("course")
    age = data.get("age")
    city = data.get("city")

    if not all([name, course, age, city]):
        return "Ошибка: не все данные заполнены"

    status = create_trello_card(name, course, age, city)

    message_text = f"✅ Новая заявка\n👤 Имя: {name}\n📚 Курс: {course}\n🎂 Возраст: {age}\n🌍 Город: {city}"
    send_telegram_message(message_text)

    if status == 200:
        return "Заявка успешно отправлена в Trello и Telegram"
    else:
        return "Ошибка при создании заявки в Trello"

# 🔹 API-эндпоинт для обновления заявки
@app.route("/update_trello", methods=["POST"])
def update_trello():
    data = request.json
    name = data.get("name")
    field = data.get("field")  # что меняем (course, age, city)
    new_value = data.get("new_value")  # на что меняем

    if not all([name, field, new_value]):
        return "Ошибка: недостаточно данных"

    status = update_trello_card(name, field, new_value)

    if status == 200:
        message_text = f"🔄 Изменение данных заявки\n👤 Имя: {name}\n✏️ {field.capitalize()} изменен на: {new_value}"
        send_telegram_message(message_text)
        return "Данные успешно обновлены в Trello и Telegram"
    else:
        return "Ошибка при обновлении заявки в Trello"

# 🔹 Запуск сервера
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
