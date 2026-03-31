"""
Модульные и интеграционные тесты для корзины
"""
import pytest
from decimal import Decimal
from app.models import Tea, TeaType, Country
from app.routers.cart import get_cart_from_session, save_cart_to_session


class TestCartFunctions:
    """Модульные тесты функций корзины"""
    
    def test_get_cart_from_empty_session(self):
        """Тест получения корзины из пустой сессии"""
        class MockRequest:
            def __init__(self):
                self.session = {}
        
        request = MockRequest()
        cart = get_cart_from_session(request)
        
        assert cart == []
        assert isinstance(cart, list)
    
    def test_get_cart_from_session_with_items(self):
        """Тест получения корзины с товарами"""
        class MockRequest:
            def __init__(self):
                self.session = {
                    "cart": [
                        {"product_id": 1, "quantity": 2},
                        {"product_id": 2, "quantity": 1}
                    ]
                }
        
        request = MockRequest()
        cart = get_cart_from_session(request)
        
        assert len(cart) == 2
        assert cart[0]["product_id"] == 1
        assert cart[1]["quantity"] == 1
    
    def test_save_cart_to_session(self):
        """Тест сохранения корзины в сессию"""
        class MockRequest:
            def __init__(self):
                self.session = {}
        
        request = MockRequest()
        cart = [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1}
        ]
        
        save_cart_to_session(request, cart)
        
        assert "cart" in request.session
        assert len(request.session["cart"]) == 2
        assert request.session["cart"][0]["product_id"] == 1


class TestCartAPI:
    """Интеграционные тесты API корзины"""
    
    def test_add_tea_to_cart(self, client, sample_tea):
        """Тест добавления чая в корзину"""
        # Создаем сессию
        response = client.post(
            "/api/cart/add",
            json={
                "product_type": "tea",
                "product_id": sample_tea.id,
                "quantity": 1,
                "size": "100g"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cart_count"] == 1
    
    def test_add_nonexistent_tea_to_cart(self, client):
        """Тест добавления несуществующего чая в корзину"""
        response = client.post(
            "/api/cart/add",
            json={
                "product_type": "tea",
                "product_id": 99999,  # Несуществующий ID
                "quantity": 1,
                "size": "100g"
            }
        )
        
        assert response.status_code == 404
    
    def test_get_empty_cart(self, client):
        """Тест получения пустой корзины"""
        response = client.get("/api/cart")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cart"] == []
        assert data["total"] == 0.0
        assert data["count"] == 0
    
    def test_cart_total_calculation(self, client, sample_tea):
        """Тест расчета итоговой стоимости корзины"""
        # Добавляем несколько товаров
        client.post(
            "/api/cart/add",
            json={
                "product_type": "tea",
                "product_id": sample_tea.id,
                "quantity": 2,
                "size": "100g"
            }
        )
        
        client.post(
            "/api/cart/add",
            json={
                "product_type": "tea",
                "product_id": sample_tea.id,
                "quantity": 1,
                "size": "20g"
            }
        )
        
        # Получаем корзину и проверяем итоговую сумму
        response = client.get("/api/cart")
        assert response.status_code == 200
        
        data = response.json()
        # 2 * 500.00 (100g) + 1 * 120.00 (20g) = 1120.00
        assert data["total"] == pytest.approx(1120.00, rel=1e-2)
        assert len(data["cart"]) >= 1
    
    def test_remove_item_from_cart(self, client, sample_tea):
        """Тест удаления товара из корзины"""
        # Добавляем товар
        client.post(
            "/api/cart/add",
            json={
                "product_type": "tea",
                "product_id": sample_tea.id,
                "quantity": 1,
                "size": "100g"
            }
        )
        
        # Удаляем товар
        response = client.delete("/api/cart/remove?index=0")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Проверяем, что корзина пуста
        cart_response = client.get("/api/cart")
        cart_data = cart_response.json()
        assert len(cart_data["cart"]) == 0
    
    def test_update_cart_item_quantity(self, client, sample_tea):
        """Тест обновления количества товара в корзине"""
        # Добавляем товар
        client.post(
            "/api/cart/add",
            json={
                "product_type": "tea",
                "product_id": sample_tea.id,
                "quantity": 1,
                "size": "100g"
            }
        )
        
        # Обновляем количество
        response = client.put("/api/cart/update?index=0&quantity=3")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Проверяем обновленное количество
        cart_response = client.get("/api/cart")
        cart_data = cart_response.json()
        assert cart_data["cart"][0]["quantity"] == 3
    
    def test_update_cart_item_to_zero_removes_it(self, client, sample_tea):
        """Тест обновления количества товара до нуля (должен удалиться)"""
        # Добавляем товар
        client.post(
            "/api/cart/add",
            json={
                "product_type": "tea",
                "product_id": sample_tea.id,
                "quantity": 1,
                "size": "100g"
            }
        )
        
        # Обновляем количество до нуля
        response = client.put("/api/cart/update?index=0&quantity=0")
        
        assert response.status_code == 200
        
        # Проверяем, что товар удален
        cart_response = client.get("/api/cart")
        cart_data = cart_response.json()
        assert len(cart_data["cart"]) == 0

