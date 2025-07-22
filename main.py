from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import requests
import json
import os

# === Загрузка .env ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

if not BOT_TOKEN or not GROUP_ID:
    raise RuntimeError("BOT_TOKEN и GROUP_ID обязательны в .env")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
PRODUCTS_FILE = "products.json"

# === ИНИЦИАЛИЗАЦИЯ FastAPI ===
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# === CORS (для фронтенда) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === МОДЕЛИ ===
class CartItem(BaseModel):
    title: str
    price: int
    amount: int = Field(gt=0)

class Order(BaseModel):
    name: str = Field(min_length=2)
    phone: int = Field(min_length=5)
    address: str = Field(min_length=5)
    cart: List[CartItem]

class Product(BaseModel):
    id: int
    title: str
    price: int
    image: str
    discountPercentage: int

# === API: получение заказа ===
@app.post("/api/order")
async def receive_order(order: Order, requests: Request):
    if not order.cart:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    text = (
        f"🛒 Новый заказ!\n\n"
        f"👤 Имя: {order.name}\n"
        f"📞 Телефон: {order.phone}\n"
        f"📍 Адрес: {order.address}\n\n"
        f"📦 Товары:\n"
    )
    for item in order.cart:
        total = item.price * item.amount
        text += f"• {item.title} x{item.amount} = {total} сум\n"
    text += "\n✅ Заказ принят."

    # Отправка в Telegram
    response = requests.post(API_URL, json={
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

    if response.status_code != 200:
        print("Ошибка Telegram:", response.text)
        raise HTTPException(status_code=500, detail="Ошибка при отправке Telegram")

    return {"status": "ok"}

# === API: получение товаров ===
@app.get("/api/products")
def get_products():
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось загрузить товары")

# === API: обновление товаров ===
@app.post("/api/products")
def update_products(products: List[Product]):
    try:
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump([p.dict() for p in products], f, ensure_ascii=False, indent=2)
        return {"message": "Товары обновлены"}
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось сохранить товары")
