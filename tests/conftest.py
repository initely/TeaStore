"""
Конфигурация для тестов
"""
import pytest
from httpx import AsyncClient
from tortoise import Tortoise
from app.main import app
from app.database import MODELS_LIST
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient


@pytest.fixture(scope="function")
async def test_db():
    """Создание тестовой базы данных"""
    # Используем отдельную тестовую БД в памяти
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": MODELS_LIST},
    )
    await Tortoise.generate_schemas()
    
    yield
    
    await Tortoise.close_connections()


@pytest.fixture(scope="function")
def client(test_db):
    """Создание тестового клиента с поддержкой сессий"""
    # Создаем клиент с поддержкой сессий
    test_client = TestClient(app)
    yield test_client


@pytest.fixture(scope="function")
async def async_client(test_db):
    """Создание асинхронного тестового клиента"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def sample_tea_type(test_db):
    """Создание тестового типа чая"""
    from app.models import TeaType
    
    tea_type = await TeaType.create(
        name="Зеленый чай",
        name_en="Green Tea",
        description="Описание зеленого чая"
    )
    return tea_type


@pytest.fixture(scope="function")
async def sample_country(test_db):
    """Создание тестовой страны"""
    from app.models import Country
    
    country = await Country.create(
        name="Китай",
        name_en="China",
        code="CN",
        is_active=True
    )
    return country


@pytest.fixture(scope="function")
async def sample_tea(test_db, sample_tea_type, sample_country):
    """Создание тестового чая"""
    from app.models import Tea
    from decimal import Decimal
    
    tea = await Tea.create(
        name="Драконов колодец",
        name_en="Longjing",
        slug="longjing",
        tea_type=sample_tea_type,
        country=sample_country,
        price_per_100g=Decimal("500.00"),
        price_per_20g=Decimal("120.00"),
        is_available=True,
        stock_quantity=100
    )
    return tea


@pytest.fixture(scope="function")
async def sample_user(test_db):
    """Создание тестового пользователя"""
    from app.models import User, UserRole
    from app.auth import get_password_hash
    
    user = await User.create(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    return user


@pytest.fixture(scope="function")
async def auth_token(test_db, sample_user):
    """Создание токена авторизации для тестового пользователя"""
    from app.auth import create_access_token
    from datetime import timedelta
    
    access_token = create_access_token(
        data={"sub": str(sample_user.id)},
        expires_delta=timedelta(minutes=60)
    )
    return access_token

