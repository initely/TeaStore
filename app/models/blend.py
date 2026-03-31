from tortoise.models import Model
from tortoise import fields
from decimal import Decimal


class CustomBlend(Model):
    """Авторский чайный сбор, созданный пользователем"""
    
    id = fields.IntField(pk=True)
    
    # Создатель
    creator = fields.ForeignKeyField(
        "models.User",
        related_name="custom_blends",
        description="Создатель сбора"
    )
    
    # Основная информация
    name = fields.CharField(max_length=200, description="Название сбора")
    description = fields.TextField(null=True, description="Описание сбора")
    
    # Основа сбора
    base_tea = fields.ForeignKeyField(
        "models.Tea",
        related_name="used_as_base",
        null=True,
        description="Основа (чай)"
    )
    base_tea_type = fields.ForeignKeyField(
        "models.TeaType",
        related_name="blends",
        null=True,
        description="Тип основы (если не выбран конкретный чай)"
    )
    
    # Статус модерации
    is_approved = fields.BooleanField(
        default=False,
        description="Одобрен ли администратором для публикации"
    )
    is_public = fields.BooleanField(
        default=False,
        description="Публичный ли сбор (виден другим пользователям)"
    )
    is_featured = fields.BooleanField(
        default=False,
        description="Рекомендуемый сбор"
    )
    
    # Рейтинг и популярность
    rating = fields.FloatField(default=0.0, description="Средний рейтинг")
    review_count = fields.IntField(default=0, description="Количество отзывов")
    purchase_count = fields.IntField(default=0, description="Количество заказов")
    view_count = fields.IntField(default=0, description="Количество просмотров")
    
    # Цена (рассчитывается из компонентов)
    price_per_100g = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        description="Цена за 100г"
    )
    price_per_20g = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        description="Цена за 20г"
    )
    
    # Метаданные
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "custom_blends"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} (by {self.creator.username})"


class BlendComponent(Model):
    """Компонент авторского сбора (ингредиент с пропорцией)"""
    
    id = fields.IntField(pk=True)
    
    # Сбор
    blend = fields.ForeignKeyField(
        "models.CustomBlend",
        related_name="components",
        description="Сбор"
    )
    
    # Ингредиент
    ingredient = fields.ForeignKeyField(
        "models.Ingredient",
        related_name="used_in_blends",
        null=True,
        description="Ингредиент"
    )
    
    # Или чай как компонент
    tea = fields.ForeignKeyField(
        "models.Tea",
        related_name="used_in_blends",
        null=True,
        description="Чай как компонент"
    )
    
    # Пропорция (в процентах, от 0 до 100)
    percentage = fields.DecimalField(
        max_digits=5,
        decimal_places=2,
        description="Процент в смеси"
    )
    
    # Количество в граммах (для расчета цены)
    grams_per_100g = fields.DecimalField(
        max_digits=5,
        decimal_places=2,
        description="Грамм на 100г смеси"
    )
    
    # Порядок добавления (для отображения)
    order = fields.IntField(default=0, description="Порядок в списке")
    
    class Meta:
        table = "blend_components"
        ordering = ["order"]
        unique_together = [("blend", "ingredient", "tea")]
    
    def __str__(self):
        component_name = self.ingredient.name if self.ingredient else self.tea.name
        return f"{component_name} ({self.percentage}%)"

