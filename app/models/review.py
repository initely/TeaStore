from tortoise.models import Model
from tortoise import fields


class Review(Model):
    """Отзыв на чай или авторский сбор"""
    
    id = fields.IntField(pk=True)
    
    # Автор отзыва
    user = fields.ForeignKeyField(
        "models.User",
        related_name="reviews",
        description="Автор отзыва"
    )
    
    # Объект отзыва
    tea = fields.ForeignKeyField(
        "models.Tea",
        related_name="reviews",
        null=True,
        description="Чай"
    )
    custom_blend = fields.ForeignKeyField(
        "models.CustomBlend",
        related_name="reviews",
        null=True,
        description="Авторский сбор"
    )
    
    # Рейтинг (от 1 до 5)
    rating = fields.IntField(description="Рейтинг (1-5)")
    
    # Текст отзыва
    title = fields.CharField(max_length=200, null=True, description="Заголовок отзыва")
    text = fields.TextField(null=True, description="Текст отзыва")
    
    # Модерация
    is_approved = fields.BooleanField(
        default=True,
        description="Одобрен ли отзыв"
    )
    
    # Метаданные
    created_at = fields.DatetimeField(auto_now_add=True, description="Дата создания")
    updated_at = fields.DatetimeField(auto_now=True, description="Дата обновления")
    
    class Meta:
        table = "reviews"
        ordering = ["-created_at"]
        unique_together = [
            ("user", "tea"),
            ("user", "custom_blend"),
        ]
    
    def __str__(self):
        product = self.tea.name if self.tea else self.custom_blend.name
        return f"Review by {self.user.username} for {product}"

