#!/usr/bin/env python3
"""
Генерация демо-контента для промо:
- пользователи с паролем qwerty
- авторские сборы от разных пользователей
- рандомные отзывы для чаев и сборов
"""
import asyncio
import random
import sys
from decimal import Decimal
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise

from app.auth import get_password_hash
from app.models import User, Tea, Ingredient, CustomBlend, BlendComponent, Review


USERS_TO_CREATE = 24
PASSWORD = "qwerty"
BLENDS_MIN = 12
BLENDS_MAX = 24
TEA_REVIEWS_MIN = 50
TEA_REVIEWS_MAX = 70
BLEND_REVIEWS_MIN = 50
BLEND_REVIEWS_MAX = 70

DEMO_PROFILES = [
    ("anna.kozlova", "Анна", "Козлова", "Москва"),
    ("mikhail.sokolov", "Михаил", "Соколов", "Санкт-Петербург"),
    ("elena.romanova", "Елена", "Романова", "Казань"),
    ("ivan.belov", "Иван", "Белов", "Екатеринбург"),
    ("daria.morozova", "Дарья", "Морозова", "Нижний Новгород"),
    ("nikita.orlov", "Никита", "Орлов", "Новосибирск"),
    ("alina.grigorieva", "Алина", "Григорьева", "Самара"),
    ("pavel.vinogradov", "Павел", "Виноградов", "Ростов-на-Дону"),
    ("irina.fedorova", "Ирина", "Федорова", "Краснодар"),
    ("sergey.litvinov", "Сергей", "Литвинов", "Воронеж"),
    ("oksana.yakovleva", "Оксана", "Яковлева", "Пермь"),
    ("andrey.egorov", "Андрей", "Егоров", "Уфа"),
    ("yulia.nikolaeva", "Юлия", "Николаева", "Челябинск"),
    ("kirill.denisov", "Кирилл", "Денисов", "Волгоград"),
    ("tatiana.vlasova", "Татьяна", "Власова", "Омск"),
    ("viktor.pankratov", "Виктор", "Панкратов", "Тюмень"),
    ("svetlana.baranova", "Светлана", "Баранова", "Калининград"),
    ("maksim.kudryavtsev", "Максим", "Кудрявцев", "Ярославль"),
    ("nadezhda.mironova", "Надежда", "Миронова", "Тула"),
    ("stepan.filin", "Степан", "Филин", "Сочи"),
    ("polina.kiseleva", "Полина", "Киселева", "Хабаровск"),
    ("egor.larin", "Егор", "Ларин", "Иркутск"),
    ("vera.melnikova", "Вера", "Мельникова", "Томск"),
    ("roman.aleshin", "Роман", "Алешин", "Владивосток"),
]

BLEND_NAME_PREFIXES = [
    "Утренний",
    "Вечерний",
    "Туманный",
    "Горный",
    "Садовый",
    "Теплый",
    "Северный",
    "Пряный",
    "Лесной",
    "Медовый",
]
BLEND_NAME_SUFFIXES = [
    "Бриз",
    "Шелк",
    "Рассвет",
    "Ритм",
    "Акцент",
    "Баланс",
    "Купаж",
    "Настрой",
    "Тонус",
    "Вдох",
]


REVIEW_TITLES = [
    "Отличный вкус",
    "Очень понравился",
    "Интересный аромат",
    "Хороший на каждый день",
    "Неожиданно круто",
    "Беру повторно",
    "Сбалансированный чай",
    "Яркое послевкусие",
]

REVIEW_TEXTS = [
    "Плотный вкус и приятный аромат, хорошо раскрывается во втором проливе.",
    "Пил вечером, мягко бодрит и не горчит, хороший баланс.",
    "Для повседневного чаепития отличный вариант, цена/качество ок.",
    "Аромат чистый, вкус ровный, без лишней терпкости.",
    "Насыщенно, но аккуратно, понравилось и в гайвани, и в чайнике.",
    "Оставил хорошее впечатление, вернусь к этому варианту еще.",
]


async def init_db():
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={
            "models": [
                "app.models.user",
                "app.models.country",
                "app.models.tea",
                "app.models.ingredient",
                "app.models.blend",
                "app.models.order",
                "app.models.review",
            ]
        },
    )
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()


async def ensure_demo_users() -> List[User]:
    users: List[User] = []
    password_hash = get_password_hash(PASSWORD)
    profiles = DEMO_PROFILES[:USERS_TO_CREATE]
    for username, first_name, last_name, city in profiles:
        email = f"{username}@teastore.local"
        user = await User.get_or_none(email=email)
        if not user:
            user = await User.create(
                email=email,
                username=username,
                hashed_password=password_hash,
                first_name=first_name,
                last_name=last_name,
                city=city,
            )
            print(f"✓ Создан пользователь: {username} / пароль: {PASSWORD}")
        users.append(user)
    return users


async def cleanup_legacy_demo_names():
    """Переименовывает старые promo_* сущности в более живые названия."""
    legacy_users = await User.filter(email__startswith="promo_user_").order_by("id")
    for idx, user in enumerate(legacy_users):
        if idx >= len(DEMO_PROFILES):
            break
        username, first_name, last_name, city = DEMO_PROFILES[idx]
        user.username = f"{username}.legacy"
        user.email = f"legacy.{username}@teastore.local"
        user.first_name = first_name
        user.last_name = last_name
        user.city = city
        user.hashed_password = get_password_hash(PASSWORD)
        await user.save()

    legacy_blends = await CustomBlend.filter(name__startswith="Промо сбор #").order_by("id")
    for blend in legacy_blends:
        prefix = random.choice(BLEND_NAME_PREFIXES)
        suffix = random.choice(BLEND_NAME_SUFFIXES)
        blend.name = f"{prefix} {suffix}"
        blend.description = "Авторский купаж с мягким вкусом и выразительным ароматом."
        blend.is_public = True
        blend.is_approved = True
        await blend.save()

    if legacy_users or legacy_blends:
        print("✓ Обновлены старые demo-названия пользователей и сборов")


async def create_demo_blends(users: List[User]) -> List[CustomBlend]:
    teas = await Tea.filter(is_available=True).all()
    ingredients = await Ingredient.filter(is_available=True).all()
    if len(teas) < 3 or len(ingredients) < 6:
        raise RuntimeError("Недостаточно данных: нужны чаи и ингредиенты")

    blends_to_create = random.randint(BLENDS_MIN, BLENDS_MAX)
    created_blends: List[CustomBlend] = []

    for idx in range(blends_to_create):
        creator = random.choice(users)
        base_tea = random.choice(teas)
        name = f"{random.choice(BLEND_NAME_PREFIXES)} {random.choice(BLEND_NAME_SUFFIXES)} {idx + 1}"
        blend = await CustomBlend.create(
            creator_id=creator.id,
            name=name,
            description="Сбалансированный авторский купаж для ежедневного чаепития.",
            base_tea_id=base_tea.id,
            base_tea_type_id=base_tea.tea_type_id,
            is_public=True,
            is_approved=True,
            is_featured=bool(random.getrandbits(1)),
            price_per_100g=Decimal(str(round(random.uniform(420, 990), 2))),
            price_per_20g=Decimal(str(round(random.uniform(90, 230), 2))),
        )

        components = random.sample(ingredients, k=random.randint(2, 5))
        total_weight = Decimal("0")
        weights = []
        for _ in components:
            weight = Decimal(str(round(random.uniform(8, 38), 2)))
            weights.append(weight)
            total_weight += weight

        for order, (ingredient, weight) in enumerate(zip(components, weights)):
            percentage = (weight / total_weight) * Decimal("100")
            await BlendComponent.create(
                blend_id=blend.id,
                ingredient_id=ingredient.id,
                percentage=percentage.quantize(Decimal("0.01")),
                grams_per_100g=percentage.quantize(Decimal("0.01")),
                order=order,
            )
        created_blends.append(blend)

    print(f"✓ Создано сборов: {len(created_blends)}")
    return created_blends


async def create_reviews(users: List[User], teas: List[Tea], blends: List[CustomBlend]):
    tea_target = random.randint(TEA_REVIEWS_MIN, TEA_REVIEWS_MAX)
    blend_target = random.randint(BLEND_REVIEWS_MIN, BLEND_REVIEWS_MAX)

    tea_pairs = [(u.id, t.id) for u in users for t in teas]
    blend_pairs = [(u.id, b.id) for u in users for b in blends]
    random.shuffle(tea_pairs)
    random.shuffle(blend_pairs)

    tea_created = 0
    for user_id, tea_id in tea_pairs:
        if tea_created >= tea_target:
            break
        exists = await Review.get_or_none(user_id=user_id, tea_id=tea_id)
        if exists:
            continue
        await Review.create(
            user_id=user_id,
            tea_id=tea_id,
            rating=random.randint(3, 5),
            title=random.choice(REVIEW_TITLES),
            text=random.choice(REVIEW_TEXTS),
            is_approved=True,
        )
        tea_created += 1

    blend_created = 0
    for user_id, blend_id in blend_pairs:
        if blend_created >= blend_target:
            break
        exists = await Review.get_or_none(user_id=user_id, custom_blend_id=blend_id)
        if exists:
            continue
        await Review.create(
            user_id=user_id,
            custom_blend_id=blend_id,
            rating=random.randint(3, 5),
            title=random.choice(REVIEW_TITLES),
            text=random.choice(REVIEW_TEXTS),
            is_approved=True,
        )
        blend_created += 1

    print(f"✓ Создано отзывов для чаев: {tea_created}")
    print(f"✓ Создано отзывов для сборов: {blend_created}")


async def recalc_ratings():
    teas = await Tea.all()
    for tea in teas:
        reviews = await Review.filter(tea_id=tea.id, is_approved=True).all()
        if reviews:
            tea.review_count = len(reviews)
            tea.rating = sum(r.rating for r in reviews) / len(reviews)
        else:
            tea.review_count = 0
            tea.rating = 0.0
        await tea.save()

    blends = await CustomBlend.all()
    for blend in blends:
        reviews = await Review.filter(custom_blend_id=blend.id, is_approved=True).all()
        if reviews:
            blend.review_count = len(reviews)
            blend.rating = sum(r.rating for r in reviews) / len(reviews)
        else:
            blend.review_count = 0
            blend.rating = 0.0
        await blend.save()

    print("✓ Пересчитаны рейтинги и количество отзывов")


async def main():
    random.seed()
    await init_db()
    try:
        await cleanup_legacy_demo_names()
        users = await ensure_demo_users()
        teas = await Tea.filter(is_available=True).all()
        if len(teas) < 3:
            raise RuntimeError("Недостаточно чаев для генерации контента")
        blends = await create_demo_blends(users)
        await create_reviews(users, teas, blends)
        await recalc_ratings()
        print("✅ Демо-контент успешно сгенерирован")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
