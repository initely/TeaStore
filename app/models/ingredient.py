from tortoise.models import Model
from tortoise import fields
from decimal import Decimal


class IngredientCategory(Model):
    """Категории ингредиентов для конструктора"""
    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True, description="Название категории")
    name_en = fields.CharField(max_length=100, null=True)
    description = fields.TextField(null=True, description="Описание категории")
    icon = fields.CharField(max_length=50, null=True, description="Иконка категории")
    
    class Meta:
        table = "ingredient_categories"
        verbose_name_plural = "Ingredient Categories"
    
    def __str__(self):
        return self.name


class Ingredient(Model):
    """Ингредиенты для конструктора чайных сборов"""
    
    id = fields.IntField(pk=True)
    
    # Основная информация
    name = fields.CharField(max_length=100, unique=True, description="Название ингредиента")
    name_en = fields.CharField(max_length=100, null=True, description="Название на английском")
    description = fields.TextField(null=True, description="Описание ингредиента")
    
    # Категория
    category = fields.ForeignKeyField(
        "models.IngredientCategory",
        related_name="ingredients",
        description="Категория ингредиента"
    )
    
    # Цена и наличие
    price_per_100g = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        description="Цена за 100г"
    )
    price_per_20g = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        description="Цена за 20г"
    )
    stock_quantity = fields.IntField(default=0, description="Количество на складе")
    is_available = fields.BooleanField(default=True, description="Доступен ли")
    
    # Вкусовые характеристики (для рекомендаций)
    flavor_profile = fields.CharField(
        max_length=200,
        null=True,
        description="Вкусовой профиль (сладкий, терпкий и т.д.)"
    )
    
    # Медиа
    image_url = fields.CharField(max_length=500, null=True, description="URL изображения")
    
    # Метаданные
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "ingredients"
        ordering = ["name"]
    
    def __str__(self):
        return self.name

