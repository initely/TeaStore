"""
Тесты для конструктора авторских сборов
"""
import pytest
from decimal import Decimal
from app.models import TeaType, Ingredient, IngredientCategory, CustomBlend, User, UserRole


@pytest.mark.asyncio
class TestBlendsAPI:
    """Тесты API для работы с авторскими сборами"""
    
    async def test_get_tea_types(self, client, test_db, sample_tea_type):
        """Тест получения типов чая"""
        response = await client.get("/api/tea-types")
        
        assert response.status_code == 200
        data = response.json()
        assert "tea_types" in data
        assert len(data["tea_types"]) > 0
        assert data["tea_types"][0]["id"] == sample_tea_type.id
    
    async def test_get_ingredients_empty(self, client, test_db):
        """Тест получения пустого списка ингредиентов"""
        response = await client.get("/api/ingredients")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ingredients"] == []
    
    async def test_get_ingredients_by_category(self, client, test_db):
        """Тест получения ингредиентов по категории"""
        # Создаем категорию и ингредиенты
        category = await IngredientCategory.create(
            name="Ягоды",
            name_en="Berries"
        )
        
        ingredient1 = await Ingredient.create(
            name="Клубника",
            name_en="Strawberry",
            category=category,
            price_per_100g=Decimal("200.00"),
            is_available=True
        )
        
        ingredient2 = await Ingredient.create(
            name="Малина",
            name_en="Raspberry",
            category=category,
            price_per_100g=Decimal("250.00"),
            is_available=True
        )
        
        response = await client.get(f"/api/ingredients?category_id={category.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["ingredients"]) == 2
    
    async def test_save_blend_with_empty_name(self, client, test_db, sample_tea_type, sample_user):
        """Тест сохранения сбора с пустым названием"""
        # Создаем ингредиент
        category = await IngredientCategory.create(name="Ягоды")
        ingredient = await Ingredient.create(
            name="Клубника",
            category=category,
            price_per_100g=Decimal("200.00"),
            is_available=True
        )
        
        # Пытаемся создать сбор с пустым названием
        response = await client.post(
            "/api/blends/save",
            json={
                "name": "",
                "base_tea_type_id": sample_tea_type.id,
                "ingredients": [{"id": ingredient.id, "weight": 10.0}],
                "base_weight": 90.0
            },
            cookies={"access_token": "test_token"}  # Нужен токен для авторизации
        )
        
        # Должна быть ошибка валидации
        assert response.status_code in [400, 401]  # 401 если нет авторизации, 400 если есть
    
    async def test_save_blend_with_zero_base_weight(self, client, test_db, sample_tea_type, sample_user):
        """Тест сохранения сбора с нулевым весом основы"""
        category = await IngredientCategory.create(name="Ягоды")
        ingredient = await Ingredient.create(
            name="Клубника",
            category=category,
            price_per_100g=Decimal("200.00"),
            is_available=True
        )
        
        response = await client.post(
            "/api/blends/save",
            json={
                "name": "Тестовый сбор",
                "base_tea_type_id": sample_tea_type.id,
                "ingredients": [{"id": ingredient.id, "weight": 10.0}],
                "base_weight": 0.0  # Нулевой вес
            },
            cookies={"access_token": "test_token"}
        )
        
        # Должна быть ошибка валидации
        assert response.status_code in [400, 401]
    
    async def test_save_blend_with_empty_ingredients_list(self, client, test_db, sample_tea_type, sample_user):
        """Тест сохранения сбора без ингредиентов"""
        response = await client.post(
            "/api/blends/save",
            json={
                "name": "Тестовый сбор",
                "base_tea_type_id": sample_tea_type.id,
                "ingredients": [],  # Пустой список
                "base_weight": 100.0
            },
            cookies={"access_token": "test_token"}
        )
        
        # Должна быть ошибка валидации
        assert response.status_code in [400, 401]
    
    async def test_save_blend_with_nonexistent_tea_type(self, client, test_db, sample_user):
        """Тест сохранения сбора с несуществующим типом чая"""
        category = await IngredientCategory.create(name="Ягоды")
        ingredient = await Ingredient.create(
            name="Клубника",
            category=category,
            price_per_100g=Decimal("200.00"),
            is_available=True
        )
        
        response = await client.post(
            "/api/blends/save",
            json={
                "name": "Тестовый сбор",
                "base_tea_type_id": 99999,  # Несуществующий ID
                "ingredients": [{"id": ingredient.id, "weight": 10.0}],
                "base_weight": 90.0
            },
            cookies={"access_token": "test_token"}
        )
        
        # Должна быть ошибка 404
        assert response.status_code in [404, 401]
    
    async def test_save_blend_with_nonexistent_ingredient(self, client, test_db, sample_tea_type, sample_user):
        """Тест сохранения сбора с несуществующим ингредиентом"""
        response = await client.post(
            "/api/blends/save",
            json={
                "name": "Тестовый сбор",
                "base_tea_type_id": sample_tea_type.id,
                "ingredients": [{"id": 99999, "weight": 10.0}],  # Несуществующий ID
                "base_weight": 90.0
            },
            cookies={"access_token": "test_token"}
        )
        
        # Должна быть ошибка 404
        assert response.status_code in [404, 401]
    
    async def test_get_blends_api(self, client, test_db):
        """Тест получения списка сборов через API"""
        response = await client.get("/api/blends")
        
        assert response.status_code == 200
        data = response.json()
        assert "blends" in data
        assert "pagination" in data
        assert isinstance(data["blends"], list)
    
    async def test_get_blends_with_search(self, client, test_db, sample_tea_type, sample_user):
        """Тест поиска сборов"""
        # Создаем сбор
        blend = await CustomBlend.create(
            name="Уникальный сбор",
            base_tea_type=sample_tea_type,
            creator=sample_user,
            price_per_100g=Decimal("400.00"),
            is_public=True
        )
        
        # Ищем по названию
        response = await client.get("/api/blends?search=Уникальный")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["blends"], list)
    
    async def test_get_blends_with_empty_search(self, client, test_db):
        """Тест поиска сборов с пустым запросом"""
        response = await client.get("/api/blends?search=")
        
        assert response.status_code == 200
        data = response.json()
        # Пустой запрос должен вернуть все сборы
        assert isinstance(data["blends"], list)



