from fastapi import FastAPI, Request, HTTPException, Body
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

# === ИНИЦИАЛИЗАЦИЯ ===
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",       # для локальной разработки
        "https://store-ma.netlify.app",         # для размещения на netlify
        ],
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
    phone: str = Field(min_length=5)
    address: str = Field(min_length=5)
    cart: List[CartItem]

class Product(BaseModel):
    id: int
    title: str
    price: int
    image: str
    discountPercentage: int

# === API ===
@app.post("/api/order")
@limiter.limit("25/minute")  # ⚠️ ограничение: 5 заказов в минуту с одного IP
async def receive_order(order: Order, request: Request):
    if not order.cart:
        raise HTTPException(status_code=400, detail="Корзина пуста")

    text = f"🛒 *Новый заказ!*\n\n👤 Имя: {order.name}\n📞 Телефон: {order.phone}\n📍 Адрес: {order.address}\n\n📦 Товары:\n"
    for item in order.cart:
        total = item.price * item.amount
        text += f"• {item.title} x{item.amount} = {total} сум\n"
    text += "\n✅ Заказ принят."

    response = requests.post(API_URL, json={
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка при отправке Telegram")

    return {"status": "ok"}

@app.get("/api/products")
def get_products():
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось загрузить товары")

@app.post("/api/products")
def update_products(products: List[Product]):
    try:
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump([p.dict() for p in products], f, ensure_ascii=False, indent=2)
        return {"message": "Товары обновлены"}
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось сохранить товары")
