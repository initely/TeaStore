from tortoise.models import Model
from tortoise import fields
from decimal import Decimal
from enum import IntEnum


class OrderStatus(IntEnum):
    """Статусы заказа"""
    PENDING = 1        # Ожидает оплаты
    PAID = 2           # Оплачен
    PROCESSING = 3     # В обработке
    SHIPPED = 4        # Отправлен
    DELIVERED = 5      # Доставлен
    CANCELLED = 6      # Отменен
    REFUNDED = 7       # Возврат


class Order(Model):
    """Модель заказа"""
    
    id = fields.IntField(pk=True)
    
    # Пользователь
    user = fields.ForeignKeyField(
        "models.User",
        related_name="orders",
        description="Покупатель"
    )
    
    # Номер заказа
    order_number = fields.CharField(
        max_length=50,
        unique=True,
        description="Номер заказа"
    )
    
    # Статус
    status = fields.IntEnumField(
        OrderStatus,
        default=OrderStatus.PENDING,
        description="Статус заказа"
    )
    
    # Сумма
    total_amount = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        description="Общая сумма заказа"
    )
    shipping_cost = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        description="Стоимость доставки"
    )
    
    # Адрес доставки
    delivery_address = fields.TextField(description="Адрес доставки")
    delivery_city = fields.CharField(max_length=100, description="Город")
    delivery_postal_code = fields.CharField(
        max_length=20,
        null=True,
        description="Почтовый индекс"
    )
    delivery_phone = fields.CharField(max_length=20, null=True, description="Телефон")
    
    # Комментарий к заказу
    notes = fields.TextField(null=True, description="Комментарий покупателя")
    
    # Даты
    created_at = fields.DatetimeField(auto_now_add=True, description="Дата создания")
    updated_at = fields.DatetimeField(auto_now=True, description="Дата обновления")
    paid_at = fields.DatetimeField(null=True, description="Дата оплаты")
    shipped_at = fields.DatetimeField(null=True, description="Дата отправки")
    delivered_at = fields.DatetimeField(null=True, description="Дата доставки")
    
    class Meta:
        table = "orders"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"


class OrderItem(Model):
    """Элемент заказа"""
    
    id = fields.IntField(pk=True)
    
    # Заказ
    order = fields.ForeignKeyField(
        "models.Order",
        related_name="items",
        description="Заказ"
    )
    
    # Товар (может быть чай или авторский сбор)
    tea = fields.ForeignKeyField(
        "models.Tea",
        related_name="order_items",
        null=True,
        description="Чай"
    )
    custom_blend = fields.ForeignKeyField(
        "models.CustomBlend",
        related_name="order_items",
        null=True,
        description="Авторский сбор"
    )
    
    # Количество и цена
    quantity = fields.IntField(description="Количество (в граммах)")
    unit_price = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        description="Цена за единицу"
    )
    total_price = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        description="Общая цена позиции"
    )
    
    # Размер (20г или 100г)
    size = fields.CharField(
        max_length=10,
        default="100g",
        description="Размер: 20g или 100g"
    )
    
    class Meta:
        table = "order_items"
    
    def __str__(self):
        product_name = self.tea.name if self.tea else self.custom_blend.name
        return f"{product_name} x{self.quantity}g"

