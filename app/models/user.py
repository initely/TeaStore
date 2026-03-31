from tortoise.models import Model
from tortoise import fields
from enum import IntEnum


class UserRole(IntEnum):
    """Роли пользователей"""
    CUSTOMER = 1  # Покупатель
    ADMIN = 2     # Администратор
    MODERATOR = 3 # Модератор


class User(Model):
    """Модель пользователя"""
    
    id = fields.IntField(pk=True)
    
    # Основная информация
    email = fields.CharField(max_length=255, unique=True, description="Email пользователя")
    username = fields.CharField(max_length=100, unique=True, description="Имя пользователя")
    hashed_password = fields.CharField(max_length=255, description="Хешированный пароль")
    
    # Персональные данные
    first_name = fields.CharField(max_length=100, null=True, description="Имя")
    last_name = fields.CharField(max_length=100, null=True, description="Фамилия")
    phone = fields.CharField(max_length=20, null=True, description="Телефон")
    
    # Роль и статус
    role = fields.IntEnumField(UserRole, default=UserRole.CUSTOMER, description="Роль пользователя")
    is_active = fields.BooleanField(default=True, description="Активен ли пользователь")
    
    # Адрес доставки (можно вынести в отдельную модель при необходимости)
    address = fields.TextField(null=True, description="Адрес доставки")
    city = fields.CharField(max_length=100, null=True, description="Город")
    postal_code = fields.CharField(max_length=20, null=True, description="Почтовый индекс")
    
    # Метаданные
    created_at = fields.DatetimeField(auto_now_add=True, description="Дата регистрации")
    updated_at = fields.DatetimeField(auto_now=True, description="Дата последнего обновления")
    last_login = fields.DatetimeField(null=True, description="Последний вход")
    
    class Meta:
        table = "users"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.username} ({self.email})"

