#!/usr/bin/env python3
"""
Скрипт для загрузки данных о чаях из JSON в базу данных
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.models import (
    Country, Region, Tea, TeaType, TeaFlavor,
    Ingredient, IngredientCategory
)


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


async def create_tea_types():
    """Создание типов чая"""
    types = [
        {"name": "Зеленый", "name_en": "Green"},
        {"name": "Черный", "name_en": "Black"},
        {"name": "Белый", "name_en": "White"},
        {"name": "Улун", "name_en": "Oolong"},
        {"name": "Пуэр", "name_en": "Pu-erh"},
        {"name": "Травяной", "name_en": "Herbal"},
    ]
    
    created_types = {}
    for tea_type_data in types:
        tea_type, created = await TeaType.get_or_create(
            name=tea_type_data["name"],
            defaults={"name_en": tea_type_data["name_en"]}
        )
        created_types[tea_type_data["name"]] = tea_type
        if created:
            print(f"✓ Создан тип чая: {tea_type.name}")
    
    return created_types


async def create_tea_flavors():
    """Создание вкусов и ароматов"""
    flavors_data = [
        "свежий", "цветочный", "фруктовый", "сладкий", "медовый",
        "ореховый", "карамельный", "шоколадный", "землистый", "травяной",
        "морской", "умами", "терпкий", "крепкий", "насыщенный",
        "нежный", "мягкий", "яркий", "обжаренный", "минеральный",
        "мускатный", "цитрусовый", "мятный", "молочный", "кремовый",
        "орхидея", "горьковатый", "солодовый", "винный", "сбалансированный",
        "глубокий", "темный", "легкий"
    ]
    
    created_flavors = {}
    for flavor_name in flavors_data:
        flavor, created = await TeaFlavor.get_or_create(
            name=flavor_name,
            defaults={"category": "вкус"}
        )
        created_flavors[flavor_name] = flavor
        if created:
            print(f"✓ Создан вкус: {flavor.name}")
    
    return created_flavors


async def load_countries_and_teas(json_path: str, tea_types: dict, flavors: dict):
    """Загрузка стран, регионов и чаев из JSON"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    countries_data = data.get("countries", [])
    
    for country_data in countries_data:
        # Создаем или получаем страну
        country, created = await Country.get_or_create(
            name=country_data["name"],
            defaults={
                "name_en": country_data.get("name_en"),
                "code": country_data.get("code"),
                "description": country_data.get("description"),
                "tea_traditions": country_data.get("tea_traditions"),
                "latitude": country_data.get("latitude"),
                "longitude": country_data.get("longitude"),
                "flag_emoji": country_data.get("flag_emoji"),
            }
        )
        
        if created:
            print(f"\n✓ Создана страна: {country.name}")
        else:
            print(f"\n→ Страна уже существует: {country.name}")
        
        # Загружаем регионы
        regions_data = country_data.get("regions", [])
        for region_data in regions_data:
            region, created = await Region.get_or_create(
                country=country,
                name=region_data["name"],
                defaults={
                    "name_en": region_data.get("name_en"),
                    "description": region_data.get("description"),
                    "tea_characteristics": region_data.get("tea_characteristics"),
                    "latitude": region_data.get("latitude"),
                    "longitude": region_data.get("longitude"),
                }
            )
            
            if created:
                print(f"  ✓ Создан регион: {region.name}")
            
            # Загружаем чаи
            teas_data = region_data.get("teas", [])
            for tea_data in teas_data:
                # Определяем тип чая
                tea_type_name = tea_data.get("type", "Черный")
                tea_type = tea_types.get(tea_type_name)
                
                if not tea_type:
                    print(f"    ⚠ Тип чая '{tea_type_name}' не найден, пропускаем {tea_data.get('name')}")
                    continue
                
                # Создаем slug из названия
                slug = tea_data["name"].lower().replace(" ", "-").replace(",", "")
                
                # Создаем чай
                tea, created = await Tea.get_or_create(
                    slug=slug,
                    defaults={
                        "name": tea_data["name"],
                        "name_en": tea_data.get("name_en"),
                        "country": country,
                        "region": region,
                        "tea_type": tea_type,
                        "description": tea_data.get("description"),
                        "short_description": tea_data.get("description", "")[:500] if tea_data.get("description") else None,
                        "price_per_100g": 500.00,  # Базовая цена, можно изменить
                        "price_per_20g": 120.00,   # Базовая цена для пробника
                        "stock_quantity": 100,
                        "is_available": True,
                    }
                )
                
                if created:
                    print(f"    ✓ Создан чай: {tea.name}")
                    
                    # Добавляем вкусы
                    tea_flavors = tea_data.get("flavors", [])
                    for flavor_name in tea_flavors:
                        flavor = flavors.get(flavor_name)
                        if flavor:
                            await tea.flavors.add(flavor)
                else:
                    print(f"    → Чай уже существует: {tea.name}")


async def main():
    """Главная функция"""
    print("🚀 Начало загрузки данных...\n")
    
    # Инициализация БД
    await init_db()
    
    try:
        # Создаем типы чая
        print("📋 Создание типов чая...")
        tea_types = await create_tea_types()
        print(f"✓ Создано типов чая: {len(tea_types)}\n")
        
        # Создаем вкусы
        print("📋 Создание вкусов и ароматов...")
        flavors = await create_tea_flavors()
        print(f"✓ Создано вкусов: {len(flavors)}\n")
        
        # Загружаем страны, регионы и чаи
        json_path = os.path.join(os.path.dirname(__file__), "..", "tea_regions_data.json")
        if not os.path.exists(json_path):
            print(f"❌ Файл не найден: {json_path}")
            return
        
        print("📋 Загрузка стран, регионов и чаев...")
        await load_countries_and_teas(json_path, tea_types, flavors)
        
        print("\n✅ Загрузка данных завершена успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

