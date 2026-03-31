#!/usr/bin/env python3
"""
Скрипт для загрузки ингредиентов из JSON в базу данных
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.models import Ingredient, IngredientCategory


async def init_db():
    """Инициализация базы данных"""
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={
            "models": [
                "app.models.user",
                "app.models.country",
                "app.models.tea",
                "app.models.ingredient",
                "app.models.blend",
                "app.models.order",
                "app.models.review",
            ]
        },
    )
    await Tortoise.generate_schemas()


async def close_db():
    """Закрытие соединения с БД"""
    await Tortoise.close_connections()


async def load_ingredients(json_path: str):
    """Загрузка категорий и ингредиентов из JSON"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Создаем категории
    categories_data = data.get("categories", [])
    categories_map = {}
    
    for category_data in categories_data:
        category, created = await IngredientCategory.get_or_create(
            name=category_data["name"],
            defaults={
                "name_en": category_data.get("name_en"),
                "description": category_data.get("description"),
                "icon": category_data.get("icon"),
            }
        )
        categories_map[category_data["name"]] = category
        if created:
            print(f"✓ Создана категория: {category.name}")
        else:
            print(f"→ Категория уже существует: {category.name}")
    
    # Загружаем ингредиенты
    ingredients_data = data.get("ingredients", [])
    
    for ingredient_data in ingredients_data:
        category_name = ingredient_data.get("category")
        category = categories_map.get(category_name)
        
        if not category:
            print(f"⚠ Категория '{category_name}' не найдена для ингредиента {ingredient_data.get('name')}")
            continue
        
        # Создаем slug из названия
        slug = ingredient_data["name"].lower().replace(" ", "-").replace(",", "")
        
        ingredient, created = await Ingredient.get_or_create(
            name=ingredient_data["name"],
            defaults={
                "category": category,
                "name_en": ingredient_data.get("name_en"),
                "description": ingredient_data.get("description"),
                "price_per_100g": ingredient_data.get("price_per_100g", 300),
                "price_per_20g": ingredient_data.get("price_per_20g"),
                "flavor_profile": ingredient_data.get("flavor_profile"),
                "stock_quantity": 100,
                "is_available": True,
            }
        )
        
        if created:
            print(f"  ✓ Создан ингредиент: {ingredient.name} ({category.name})")
        else:
            print(f"  → Ингредиент уже существует: {ingredient.name}")


async def main():
    """Главная функция"""
    print("🚀 Начало загрузки ингредиентов...\n")
    
    # Инициализация БД
    await init_db()
    
    try:
        # Загружаем ингредиенты
        json_path = os.path.join(os.path.dirname(__file__), "..", "ingredients_data.json")
        if not os.path.exists(json_path):
            print(f"❌ Файл не найден: {json_path}")
            return
        
        print("📋 Загрузка категорий и ингредиентов...")
        await load_ingredients(json_path)
        
        print("\n✅ Загрузка ингредиентов завершена успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())




