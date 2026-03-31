"""
Скрипт для назначения пользователя администратором
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.models import User, UserRole


async def make_admin(username_or_email: str):
    """Назначает пользователя администратором"""
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": ["app.models"]}
    )
    
    # Ищем пользователя по username или email
    user = await User.get_or_none(username=username_or_email)
    if not user:
        user = await User.get_or_none(email=username_or_email)
    
    if not user:
        print(f"❌ Пользователь '{username_or_email}' не найден")
        await Tortoise.close_connections()
        return
    
    # Устанавливаем роль администратора
    user.role = UserRole.ADMIN
    await user.save()
    
    print(f"✅ Пользователь '{user.username}' ({user.email}) теперь администратор")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/make_admin.py <username или email>")
        print("Пример: python scripts/make_admin.py tel")
        sys.exit(1)
    
    username_or_email = sys.argv[1]
    asyncio.run(make_admin(username_or_email))




