from fastapi import FastAPI, Request
import requests
import os
from fastapi.middleware.cors import CORSMiddleware

# === КОНФИГУРАЦИЯ ===
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") or "7653674144:AAFX3gWFCkx0ccRd6FSqLzxdz9EW-7Ryswo"
TELEGRAM_GROUP_ID = os.getenv("GROUP_ID") or "-4838776063"  # Вставь сюда ID группы
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# === ИНИЦИАЛИЗАЦИЯ ===
app = FastAPI()

# === Разрешаем запросы от фронтенда ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно указать только твой домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === МАРШРУТ: Получение заказа ===
@app.post("/api/order")
async def receive_order(request: Request):
    data = await request.json()

    name = data.get("name")
    phone = data.get("phone")
    address = data.get("address")
    cart = data.get("cart", [])

    if not name or not phone or not address or not cart:
        return {"status": "error", "detail": "Недостаточно данных"}

    # Формируем текст заказа
    text = f"🛒 *Новый заказ!*\n\n👤 Имя: {name}\n📞 Телефон: {phone}\n📍 Адрес: {address}\n\n📦 Товары:\n"
    for item in cart:
        quantity = item.get("amount", 1)
        title = item.get("title")
        price = item.get("price")
        text += f"• {title} x{quantity} = {price * quantity} сум\n"

    text += "\n✅ Заказ принят."

    # Отправляем в Telegram
    response = requests.post(API_URL, json={
        "chat_id": TELEGRAM_GROUP_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

    if response.status_code != 200:
        return {"status": "error", "detail": "Ошибка Telegram"}

    return {"status": "ok"}
