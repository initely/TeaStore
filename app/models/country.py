from tortoise.models import Model
from tortoise import fields


class Country(Model):
    """Модель страны - чайного региона"""
    
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True, description="Название страны")
    name_en = fields.CharField(max_length=100, null=True, description="Название на английском")
    code = fields.CharField(max_length=3, unique=True, null=True, description="Код страны (ISO)")
    
    # Описание региона
    description = fields.TextField(null=True, description="Описание чайных традиций страны")
    tea_traditions = fields.TextField(null=True, description="Особенности чайных традиций")
    
    # Географические данные для карты
    latitude = fields.FloatField(null=True, description="Широта для карты")
    longitude = fields.FloatField(null=True, description="Долгота для карты")
    
    # Медиа
    image_url = fields.CharField(max_length=500, null=True, description="URL изображения страны")
    flag_emoji = fields.CharField(max_length=10, null=True, description="Эмодзи флага")
    
    # Метаданные
    is_active = fields.BooleanField(default=True, description="Активна ли страна")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "countries"
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Region(Model):
    """Модель региона/провинции внутри страны"""
    
    id = fields.IntField(pk=True)
    country = fields.ForeignKeyField(
        "models.Country",
        related_name="regions",
        description="Страна"
    )
    name = fields.CharField(max_length=100, description="Название региона")
    name_en = fields.CharField(max_length=100, null=True, description="Название на английском")
    
    # Описание
    description = fields.TextField(null=True, description="Описание региона")
    tea_characteristics = fields.TextField(
        null=True,
        description="Характеристики чая из этого региона"
    )
    
    # Географические данные
    latitude = fields.FloatField(null=True, description="Широта")
    longitude = fields.FloatField(null=True, description="Долгота")
    
    # Медиа
    image_url = fields.CharField(max_length=500, null=True, description="URL изображения")
    
    # Метаданные
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "regions"
        ordering = ["name"]
        unique_together = [("country", "name")]
    
    def __str__(self):
        return f"{self.name}, {self.country.name}"

