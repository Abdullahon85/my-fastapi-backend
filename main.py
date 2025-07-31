from datetime import datetime, date
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()

# Разрешаем CORS для всех (или настрой под конкретный домен)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Файлы
ORDERS_FILE = "orders.json"
PRODUCTS_FILE = "products.json"

# Telegram конфиг
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
TELEGRAM_GROUP_ID = os.getenv("GROUP_ID") or "YOUR_GROUP_ID"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Хелпер: сохранить в файл
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Хелпер: загрузить из файла
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

# === Заказы ===
@app.post("/api/order")
async def make_order(request: Request):
    data = await request.json()
    name = data.get("name")
    table = data.get("table")
    comment = data.get("comment", "")
    cart = data.get("cart", [])

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order = {
        "name": name,
        "table": table,
        "comment": comment,
        "cart": cart,
        "time": time_str,
    }

    # Сохраняем заказ
    orders = load_json(ORDERS_FILE)
    orders.append(order)
    save_json(ORDERS_FILE, orders)

    # Отправляем в Telegram
    text = f"🍽 Новый заказ\n👤 Имя: {name}\n🪑 Стол: {table}\n📝 Комментарий: {comment}\n\n🛒 Товары:\n"
    for item in cart:
        text += f"• {item.get('title')} x {item.get('amount')}\n"
    text += f"\n⏰ Время: {time_str}"

    try:
        requests.post(API_URL, json={"chat_id": TELEGRAM_GROUP_ID, "text": text})
    except Exception:
        pass

    return {"status": "ok"}

@app.get("/api/orders/today")
def get_orders_today():
    today_str = date.today().isoformat()
    orders = load_json(ORDERS_FILE)
    filtered = [o for o in orders if o["time"].startswith(today_str)]
    return filtered

@app.get("/api/orders/history")
def get_orders_history():
    return load_json(ORDERS_FILE)

# === Продукты ===
@app.get("/api/products")
def get_products():
    return load_json(PRODUCTS_FILE)

@app.post("/api/products")
async def update_products(request: Request):
    products = await request.json()
    save_json(PRODUCTS_FILE, products)
    return {"message": "Товары обновлены"}
