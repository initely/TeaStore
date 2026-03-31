import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from app.database import register_db
from app.routers import teas, blends, auth, tea_map, cart, admin, reviews, payment
from app.templates import render_template

app = FastAPI(
    title="Wanderleaf Teas",
    description="Интернет-магазин чая с конструктором авторских сборов",
    version="1.0.0",
)

# Подключение middleware для сессий (для корзины)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Регистрация базы данных
register_db(app)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(teas.router)
app.include_router(blends.router)
app.include_router(tea_map.router)
app.include_router(cart.router)
app.include_router(admin.router)
app.include_router(reviews.router)
app.include_router(payment.router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница"""
    from app.templates import render_template
    return render_template("index.html")


@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "ok"}

