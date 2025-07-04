from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

# Разрешаем доступ для Vue (Netlify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # можешь ограничить доменами позже
    allow_methods=["*"],
    allow_headers=["*"],
)

PRODUCTS_FILE = "products.json"

@app.get("/api/products")
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
