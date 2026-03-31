from tortoise.models import Model
from tortoise import fields
from decimal import Decimal


class TeaType(Model):
    """Типы чая (черный, зеленый, белый, улун и т.д.)"""
    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True, description="Название типа")
    name_en = fields.CharField(max_length=50, null=True, description="Название на английском")
    description = fields.TextField(null=True, description="Описание типа чая")
    
    class Meta:
        table = "tea_types"
    
    def __str__(self):
        return self.name


class TeaFlavor(Model):
    """Вкусы и ароматы чая (для фильтрации)"""
    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True, description="Название вкуса/аромата")
    name_en = fields.CharField(max_length=50, null=True)
    category = fields.CharField(
        max_length=50,
        null=True,
        description="Категория: вкус, аромат, послевкусие"
    )
    
    class Meta:
        table = "tea_flavors"
    
    def __str__(self):
        return self.name


class Tea(Model):
    """Модель чая - товара в магазине"""
    
    id = fields.IntField(pk=True)
    
    # Основная информация
    name = fields.CharField(max_length=200, description="Название чая")
    name_en = fields.CharField(max_length=200, null=True, description="Название на английском")
    slug = fields.CharField(max_length=250, unique=True, description="URL-слаг")
    
    # Связи с географией
    country = fields.ForeignKeyField(
        "models.Country",
        related_name="teas",
        null=True,
        description="Страна происхождения"
    )
    region = fields.ForeignKeyField(
        "models.Region",
        related_name="teas",
        null=True,
        description="Регион происхождения"
    )
    
    # Тип чая
    tea_type = fields.ForeignKeyField(
        "models.TeaType",
        related_name="teas",
        description="Тип чая"
    )
    
    # Описание
    description = fields.TextField(null=True, description="Описание чая")
    short_description = fields.CharField(
        max_length=500,
        null=True,
        description="Краткое описание"
    )
    
    # Вкусы и ароматы (многие ко многим)
    flavors = fields.ManyToManyField(
        "models.TeaFlavor",
        related_name="teas",
        description="Вкусы и ароматы"
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
        description="Цена за 20г (пробник)"
    )
    stock_quantity = fields.IntField(default=0, description="Количество на складе")
    is_available = fields.BooleanField(default=True, description="Доступен ли для заказа")
    
    # Рейтинг и популярность
    rating = fields.FloatField(default=0.0, description="Средний рейтинг")
    review_count = fields.IntField(default=0, description="Количество отзывов")
    purchase_count = fields.IntField(default=0, description="Количество покупок")
    
    # Медиа
    main_image_url = fields.CharField(
        max_length=500,
        null=True,
        description="URL главного изображения"
    )
    image_urls = fields.JSONField(
        default=list,
        description="Дополнительные изображения"
    )
    
    # Метаданные
    is_featured = fields.BooleanField(default=False, description="Рекомендуемый товар")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "teas"
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.name

