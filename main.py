from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import requests
import json
import os

# === КОНФИГУРАЦИЯ ===
PRODUCTS_FILE = "products.json"
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") or "твой_токен"
TELEGRAM_GROUP_ID = os.getenv("GROUP_ID") or "-1001234567890"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# === ИНИЦИАЛИЗАЦИЯ ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно заменить на свой домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === МОДЕЛИ ===
class CartItem(BaseModel):
    title: str
    price: int
    amount: int

class Order(BaseModel):
    name: str
    phone: str
    address: str
    cart: List[CartItem]

class Product(BaseModel):
    id: int
    title: str
    price: int
    image: str
    discountPercentage: int

# === ЗАКАЗ: /api/order ===
@app.post("/api/order")
async def receive_order(order: Order):
    if not order.cart:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    text = f"🛒 *Новый заказ!*\n\n👤 Имя: {order.name}\n📞 Телефон: {order.phone}\n📍 Адрес: {order.address}\n\n📦 Товары:\n"
    for item in order.cart:
        total = item.price * item.amount
        text += f"• {item.title} x{item.amount} = {total} сум\n"
    text += "\n✅ Заказ принят."

    response = requests.post(API_URL, json={
        "chat_id": TELEGRAM_GROUP_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка Telegram")

    return {"status": "ok"}

# === ТОВАРЫ: GET /api/products ===
@app.get("/api/products")
def get_products():
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Не удалось загрузить товары")

# === ТОВАРЫ: POST /api/products ===
@app.post("/api/products")
def update_products(products: List[Product]):
    try:
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump([p.dict() for p in products], f, ensure_ascii=False, indent=2)
        return {"message": "Товары обновлены"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Не удалось сохранить товары")
