"""
Тесты для API чаев
"""
import pytest
from decimal import Decimal
from app.models import Tea, TeaType, Country, Region, TeaFlavor


class TestTeasAPI:
    """Тесты API для работы с чаями"""
    
    def test_get_teas_empty_result(self, client, test_db):
        """Тест получения пустого списка чаев"""
        response = await client.get("/api/teas")
        
        assert response.status_code == 200
        data = response.json()
        assert data["teas"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["current_page"] == 1
    
    async def test_get_teas_with_filters(self, client, test_db, sample_tea_type, sample_country):
        """Тест фильтрации чаев по параметрам"""
        from app.models import Region
        
        # Создаем регион
        region = await Region.create(
            name="Чжэцзян",
            name_en="Zhejiang",
            country=sample_country,
            is_active=True
        )
        
        # Создаем несколько чаев
        tea1 = await Tea.create(
            name="Драконов колодец",
            slug="longjing",
            tea_type=sample_tea_type,
            country=sample_country,
            region=region,
            price_per_100g=Decimal("500.00"),
            is_available=True
        )
        
        tea2 = await Tea.create(
            name="Би Ло Чунь",
            slug="bi-luo-chun",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("600.00"),
            is_available=True
        )
        
        # Тест фильтрации по стране
        response = await client.get(f"/api/teas?country_id={sample_country.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["teas"]) == 2
        
        # Тест фильтрации по региону
        response = await client.get(f"/api/teas?region_id={region.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["teas"]) == 1
        assert data["teas"][0]["name"] == "Драконов колодец"
    
    async def test_search_empty_query(self, client, test_db, sample_tea):
        """Тест обработки пустого поискового запроса"""
        # Пустой запрос должен вернуть все чаи
        response = await client.get("/api/teas?search=")
        
        assert response.status_code == 200
        data = response.json()
        # Пустой запрос должен вернуть все доступные чаи
        assert len(data["teas"]) >= 1
    
    async def test_search_with_special_characters(self, client, test_db, sample_tea_type, sample_country):
        """Тест поиска с HTML-значимыми символами"""
        # Создаем чай с названием, содержащим специальные символы
        tea = await Tea.create(
            name="Чай <тест> & проверка",
            slug="test-tea",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("400.00"),
            is_available=True
        )
        
        # Поиск с HTML-символами
        response = await client.get("/api/teas?search=<тест>")
        
        assert response.status_code == 200
        data = response.json()
        # Система должна корректно обработать специальные символы
        assert isinstance(data["teas"], list)
    
    async def test_search_very_long_string(self, client, test_db, sample_tea):
        """Тест поиска с очень длинной строкой"""
        # Создаем очень длинную строку поиска
        long_search = "а" * 1000
        
        response = await client.get(f"/api/teas?search={long_search}")
        
        assert response.status_code == 200
        data = response.json()
        # Система должна корректно обработать длинную строку
        assert isinstance(data["teas"], list)
    
    async def test_sort_by_price_ascending(self, client, test_db, sample_tea_type, sample_country):
        """Тест сортировки по цене (по возрастанию)"""
        # Создаем чаи с разными ценами
        tea1 = await Tea.create(
            name="Дешевый чай",
            slug="cheap-tea",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("200.00"),
            is_available=True
        )
        
        tea2 = await Tea.create(
            name="Дорогой чай",
            slug="expensive-tea",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("800.00"),
            is_available=True
        )
        
        response = await client.get("/api/teas?sort=price_asc")
        
        assert response.status_code == 200
        data = response.json()
        teas = data["teas"]
        
        # Проверяем, что чаи отсортированы по возрастанию цены
        if len(teas) >= 2:
            prices = [t["price_per_100g"] for t in teas]
            assert prices == sorted(prices)
    
    async def test_sort_by_price_descending(self, client, test_db, sample_tea_type, sample_country):
        """Тест сортировки по цене (по убыванию)"""
        # Создаем чаи с разными ценами
        tea1 = await Tea.create(
            name="Дешевый чай",
            slug="cheap-tea-2",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("200.00"),
            is_available=True
        )
        
        tea2 = await Tea.create(
            name="Дорогой чай",
            slug="expensive-tea-2",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("800.00"),
            is_available=True
        )
        
        response = await client.get("/api/teas?sort=price_desc")
        
        assert response.status_code == 200
        data = response.json()
        teas = data["teas"]
        
        # Проверяем, что чаи отсортированы по убыванию цены
        if len(teas) >= 2:
            prices = [t["price_per_100g"] for t in teas]
            assert prices == sorted(prices, reverse=True)
    
    async def test_pagination(self, client, test_db, sample_tea_type, sample_country):
        """Тест пагинации результатов"""
        # Создаем несколько чаев
        for i in range(15):
            await Tea.create(
                name=f"Чай {i}",
                slug=f"tea-{i}",
                tea_type=sample_tea_type,
                country=sample_country,
                price_per_100g=Decimal("300.00"),
                is_available=True
            )
        
        # Запрашиваем первую страницу
        response = await client.get("/api/teas?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["teas"]) <= 10
        assert data["pagination"]["current_page"] == 1
        
        # Запрашиваем вторую страницу
        response = await client.get("/api/teas?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["current_page"] == 2
    
    async def test_filter_by_nonexistent_country(self, client, test_db):
        """Тест фильтрации по несуществующей стране"""
        response = await client.get("/api/teas?country_id=99999")
        
        assert response.status_code == 200
        data = response.json()
        # Несуществующая страна должна вернуть пустой список
        assert data["teas"] == []
        assert data["pagination"]["total"] == 0
    
    async def test_get_popular_teas(self, client, test_db, sample_tea_type, sample_country):
        """Тест получения популярных чаев"""
        # Создаем чаи с разной популярностью
        popular_tea = await Tea.create(
            name="Популярный чай",
            slug="popular-tea",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("500.00"),
            purchase_count=100,
            rating=4.5,
            is_available=True
        )
        
        less_popular_tea = await Tea.create(
            name="Непопулярный чай",
            slug="unpopular-tea",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("400.00"),
            purchase_count=5,
            rating=3.0,
            is_available=True
        )
        
        response = await client.get("/api/teas/popular?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["teas"]) > 0
        
        # Проверяем, что популярный чай идет первым
        if len(data["teas"]) >= 2:
            assert data["teas"][0]["purchase_count"] >= data["teas"][1]["purchase_count"]

