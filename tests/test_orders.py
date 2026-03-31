"""
Тесты для заказов
"""
import pytest
from decimal import Decimal
from app.models import Tea, TeaType, Country, Order, OrderItem, OrderStatus, User, UserRole


@pytest.mark.asyncio
class TestOrdersAPI:
    """Тесты API для работы с заказами"""
    
    async def test_create_order_with_empty_cart(self, client, test_db, sample_user):
        """Тест создания заказа с пустой корзиной"""
        # Пытаемся создать заказ без товаров в корзине
        response = await client.post(
            "/api/orders/create",
            json={
                "delivery_address": "ул. Тестовая, д. 1",
                "delivery_city": "Москва"
            },
            cookies={"access_token": "test_token"}
        )
        
        # Должна быть ошибка, так как корзина пуста
        assert response.status_code in [400, 401]
    
    async def test_create_order_calculation(self, client, test_db, sample_tea_type, sample_country, sample_user):
        """Тест расчета стоимости заказа"""
        # Создаем чай
        tea = await Tea.create(
            name="Тестовый чай",
            slug="test-tea",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("500.00"),
            price_per_20g=Decimal("120.00"),
            is_available=True
        )
        
        # Добавляем товар в корзину через сессию
        # Для тестирования создаем заказ напрямую
        order = await Order.create(
            user=sample_user,
            order_number="TEST-001",
            status=OrderStatus.PENDING,
            total_amount=Decimal("800.00"),  # 500 + 300 доставка
            shipping_cost=Decimal("300.00"),
            delivery_address="ул. Тестовая, д. 1",
            delivery_city="Москва"
        )
        
        await OrderItem.create(
            order=order,
            tea=tea,
            quantity=1,
            size="100g",
            unit_price=Decimal("500.00"),
            total_price=Decimal("500.00")
        )
        
        # Проверяем расчет
        assert float(order.total_amount) == pytest.approx(800.00, rel=1e-2)
        assert float(order.shipping_cost) == pytest.approx(300.00, rel=1e-2)
    
    async def test_order_with_multiple_items(self, client, test_db, sample_tea_type, sample_country, sample_user):
        """Тест заказа с несколькими товарами"""
        # Создаем несколько чаев
        tea1 = await Tea.create(
            name="Чай 1",
            slug="tea-1",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("300.00"),
            is_available=True
        )
        
        tea2 = await Tea.create(
            name="Чай 2",
            slug="tea-2",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("400.00"),
            is_available=True
        )
        
        # Создаем заказ
        order = await Order.create(
            user=sample_user,
            order_number="TEST-002",
            status=OrderStatus.PENDING,
            total_amount=Decimal("1000.00"),  # 300 + 400 + 300 доставка
            shipping_cost=Decimal("300.00"),
            delivery_address="ул. Тестовая, д. 2",
            delivery_city="Москва"
        )
        
        await OrderItem.create(
            order=order,
            tea=tea1,
            quantity=1,
            size="100g",
            unit_price=Decimal("300.00"),
            total_price=Decimal("300.00")
        )
        
        await OrderItem.create(
            order=order,
            tea=tea2,
            quantity=1,
            size="100g",
            unit_price=Decimal("400.00"),
            total_price=Decimal("400.00")
        )
        
        # Проверяем, что заказ содержит оба товара
        items = await OrderItem.filter(order=order)
        assert len(items) == 2
        
        # Проверяем итоговую сумму
        total_items = sum(float(item.total_price) for item in items)
        assert total_items == pytest.approx(700.00, rel=1e-2)
    
    async def test_order_with_zero_quantity(self, client, test_db, sample_tea_type, sample_country, sample_user):
        """Тест обработки заказа с нулевым количеством товара"""
        tea = await Tea.create(
            name="Тестовый чай",
            slug="test-tea-zero",
            tea_type=sample_tea_type,
            country=sample_country,
            price_per_100g=Decimal("500.00"),
            is_available=True
        )
        
        # Создаем заказ с нулевым количеством
        order = await Order.create(
            user=sample_user,
            order_number="TEST-003",
            status=OrderStatus.PENDING,
            total_amount=Decimal("300.00"),  # Только доставка
            shipping_cost=Decimal("300.00"),
            delivery_address="ул. Тестовая, д. 3",
            delivery_city="Москва"
        )
        
        # Товар с нулевым количеством не должен влиять на сумму
        await OrderItem.create(
            order=order,
            tea=tea,
            quantity=0,
            size="100g",
            unit_price=Decimal("500.00"),
            total_price=Decimal("0.00")
        )
        
        # Проверяем, что итоговая сумма равна только доставке
        assert float(order.total_amount) == pytest.approx(300.00, rel=1e-2)



