from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from app.models import (
    User,
    Country,
    Region,
    Tea,
    TeaType,
    TeaFlavor,
    Ingredient,
    IngredientCategory,
    CustomBlend,
    BlendComponent,
    Order,
    OrderItem,
    Review,
)


# Список всех моделей для TortoiseORM
MODELS_LIST = [
    "app.models.user",
    "app.models.country",
    "app.models.tea",
    "app.models.ingredient",
    "app.models.blend",
    "app.models.order",
    "app.models.review",
]


async def init_db():
    """Инициализация базы данных"""
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": MODELS_LIST},
    )
    await Tortoise.generate_schemas()


async def close_db():
    """Закрытие соединения с БД"""
    await Tortoise.close_connections()


def register_db(app):
    """Регистрация TortoiseORM в FastAPI приложении"""
    register_tortoise(
        app,
        db_url="sqlite://db.sqlite3",
        modules={"models": MODELS_LIST},
        generate_schemas=True,
        add_exception_handlers=True,
    )

