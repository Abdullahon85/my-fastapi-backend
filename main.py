from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests, os, json

app = FastAPI()

PRODUCTS_FILE = "products.json"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") or "твоя_резервная_копия_токена"
TELEGRAM_GROUP_ID = os.getenv("GROUP_ID") or "-1001234567890"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.post("/api/order")
async def send_order(request: Request):
    data = await request.json()
    name = data.get("name")
    phone = data.get("phone")
    address = data.get("address")
    cart = data.get("cart")

    text = f"📦 Новый заказ\n\n👤 Имя: {name}\n📞 Телефон: {phone}\n📍 Адрес: {address}\n🛒 Товары:\n"
    for item in cart:
        text += f"• {item.get('title')} x {item.get('amount')}\n"

    payload = {"chat_id": TELEGRAM_GROUP_ID, "text": text}
    try:
        requests.post(API_URL, json=payload)
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}

def get_products():
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось загрузить товары")

@app.post("/api/products")
def update_products(products: list):
    try:
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as file:
            json.dump(products, file, ensure_ascii=False, indent=2)
        return {"message": "Товары обновлены"}
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось сохранить товары")
