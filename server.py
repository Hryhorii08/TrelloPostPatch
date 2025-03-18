from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 🔑 Токены и настройки
TELEGRAM_BOT_TOKEN = "7788946008:AAF8mtYczEkg_O_1iVwmieQPhZoHBUpLz2Q"
CHAT_ID = "-1002307069728"
TRELLO_API_KEY = "5880197335c3d727693408202c68375d"
TRELLO_TOKEN = "ATTA1ea4c6edf0b2892fec32580ab1417a42f521cd70c11af1453ddd0a4956e72896C175BE4E"
TRELLO_BOARD_ID = "67c19cc6cd0d960e2398be79"
TRELLO_LIST_ID = "67c19cd6641117e44ae95227"

TRELLO_URL = "https://api.trello.com/1"
HEADERS = {"Accept": "application/json"}

# 📌 Функция отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# 📌 Создание новой заявки в Trello
@app.route("/send_to_trello", methods=["POST"])
def send_to_trello():
    data = request.json
    name, course, age, city = data.get("name"), data.get("course"), data.get("age"), data.get("city")

    if not all([name, course, age, city]):
        return "error: Не все данные заполнены", 400  # Возвращаем текст

    query = {
        "name": f"Заявка от {name}",
        "desc": f"Курс: {course}\nВозраст: {age}\nГород: {city}",
        "idList": TRELLO_LIST_ID,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    response = requests.post(f"{TRELLO_URL}/cards", params=query, headers=HEADERS)

    if response.status_code == 200:
        send_telegram_message(f"✅ *Новая заявка*\n📌 Имя: {name}\n📚 Курс: {course}\n🎂 Возраст: {age}\n📍 Город: {city}")
        return "success: Заявка успешно добавлена", 200  # Текстовый ответ
    else:
        return "error: Ошибка создания заявки в Trello", 500  # Текстовый ответ

# 📌 Обновление заявки в Trello
@app.route("/update_trello", methods=["PATCH"])
def update_trello():
    data = request.json
    name, field, new_value = data.get("name"), data.get("field"), data.get("new_value")

    if not all([name, field, new_value]):
        return "error: Не все данные заполнены", 400  # Текстовый ответ

    # Запрашиваем все карточки в Trello
    cards_response = requests.get(f"{TRELLO_URL}/boards/{TRELLO_BOARD_ID}/cards",
                                  params={"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}, headers=HEADERS)

    if cards_response.status_code != 200:
        return "error: Ошибка при получении списка карточек", 500  # Текстовый ответ

    cards = cards_response.json()
    card = next((c for c in cards if c["name"] == f"Заявка от {name}"), None)

    if not card:
        return "error: Заявка не найдена", 404  # Текстовый ответ

    card_id = card["id"]
    new_desc = card["desc"].split("\n")

    field_mapping = {"course": "Курс", "age": "Возраст", "city": "Город"}

    if field in field_mapping:
        for i, line in enumerate(new_desc):
            if line.startswith(field_mapping[field]):
                new_desc[i] = f"{field_mapping[field]}: {new_value}"

        updated_desc = "\n".join(new_desc)
        update_response = requests.put(f"{TRELLO_URL}/cards/{card_id}",
                                       params={"desc": updated_desc, "key": TRELLO_API_KEY, "token": TRELLO_TOKEN},
                                       headers=HEADERS)

        if update_response.status_code == 200:
            send_telegram_message(f"🛠 *Обновление заявки*\n📌 Имя: {name}\n✏ Изменено: {field} → {new_value}")
            return f"success: {field} успешно обновлено", 200  # Текстовый ответ
        else:
            return "error: Ошибка обновления заявки", 500  # Текстовый ответ
    else:
        return "error: Некорректное поле для обновления", 400  # Текстовый ответ

# 📌 Обработчик ошибок (гарантированно возвращает текст)
@app.errorhandler(500)
@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(e):
    return f"error: {str(e)}", e.code  # Всегда возвращает текст

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
