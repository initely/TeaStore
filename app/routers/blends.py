"""
Роутер для конструктора авторских сборов
"""
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from app.models import TeaType, Ingredient, IngredientCategory, CustomBlend, BlendComponent, User, Tea
from app.auth import get_current_user_from_cookie
from app.templates import render_template

router = APIRouter(tags=["blends"])


class BlendIngredient(BaseModel):
    """Ингредиент сбора"""
    id: int
    weight: float  # Вес в граммах


class SaveBlendRequest(BaseModel):
    """Запрос на сохранение сбора"""
    name: str
    base_tea_type_id: int
    base_tea_id: Optional[int] = None  # Конкретный чай (опционально)
    ingredients: List[BlendIngredient]
    base_weight: float  # Вес основы в граммах


@router.get("/blend-constructor", response_class=HTMLResponse)
async def blend_constructor_page(request: Request):
    """Страница конструктора авторских сборов"""
    # Получаем типы чая для основы
    tea_types = await TeaType.all().order_by("name")
    
    # Получаем категории ингредиентов
    categories = await IngredientCategory.all().order_by("name")
    
    # Получаем все ингредиенты, сгруппированные по категориям
    ingredients_by_category = {}
    for category in categories:
        ingredients = await Ingredient.filter(
            category=category,
            is_available=True
        ).order_by("name")
        if ingredients:
            ingredients_by_category[category.name] = [
                {
                    "id": ing.id,
                    "name": ing.name,
                    "name_en": ing.name_en,
                    "price_per_100g": float(ing.price_per_100g),
                    "price_per_20g": float(ing.price_per_20g) if ing.price_per_20g else None,
                    "description": ing.description,
                    "flavor_profile": ing.flavor_profile,
                }
                for ing in ingredients
            ]
    
    context = {
        "tea_types": tea_types,
        "categories": categories,
        "ingredients_by_category": ingredients_by_category,
    }
    
    return render_template("blend_constructor.html", context)


@router.get("/api/tea-types")
async def get_tea_types():
    """API для получения типов чая"""
    tea_types = await TeaType.all().order_by("name")
    return {
        "tea_types": [
            {
                "id": tt.id,
                "name": tt.name,
                "name_en": tt.name_en,
                "description": tt.description,
            }
            for tt in tea_types
        ]
    }


@router.get("/api/ingredients")
async def get_ingredients(category_id: int = Query(None)):
    """API для получения ингредиентов"""
    query = Ingredient.filter(is_available=True)
    
    if category_id:
        query = query.filter(category_id=category_id)
    
    ingredients = await query.order_by("name").prefetch_related("category")
    
    return {
        "ingredients": [
            {
                "id": ing.id,
                "name": ing.name,
                "name_en": ing.name_en,
                "category": {
                    "id": ing.category.id,
                    "name": ing.category.name,
                },
                "price_per_100g": float(ing.price_per_100g),
                "price_per_20g": float(ing.price_per_20g) if ing.price_per_20g else None,
                "description": ing.description,
                "flavor_profile": ing.flavor_profile,
            }
            for ing in ingredients
        ]
    }


@router.get("/api/ingredient-categories")
async def get_ingredient_categories():
    """API для получения категорий ингредиентов"""
    categories = await IngredientCategory.all().order_by("name")
    return {
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "name_en": cat.name_en,
                "description": cat.description,
                "icon": cat.icon,
            }
            for cat in categories
        ]
    }


@router.get("/api/teas/by-type/{tea_type_id}")
async def get_teas_by_type(tea_type_id: int):
    """API для получения чаев по типу (для конструктора)"""
    teas = await Tea.filter(
        tea_type_id=tea_type_id,
        is_available=True
    ).order_by("name").prefetch_related("country", "region", "tea_type")
    
    return {
        "teas": [
            {
                "id": tea.id,
                "name": tea.name,
                "name_en": tea.name_en,
                "price_per_100g": float(tea.price_per_100g),
                "price_per_20g": float(tea.price_per_20g) if tea.price_per_20g else None,
                "country": tea.country.name if tea.country else None,
                "region": tea.region.name if tea.region else None,
            }
            for tea in teas
        ]
    }


@router.post("/api/blends/save")
async def save_blend(request: SaveBlendRequest, http_request: Request):
    """API для сохранения авторского сбора"""
    # Проверяем авторизацию
    access_token = http_request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Необходима авторизация для сохранения сборов"
        )
    
    # Валидация
    if not request.name or len(request.name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Название сбора не может быть пустым")
    
    if len(request.name) > 200:
        raise HTTPException(status_code=400, detail="Название сбора слишком длинное (максимум 200 символов)")
    
    if request.base_weight <= 0:
        raise HTTPException(status_code=400, detail="Вес основы должен быть больше 0")
    
    if len(request.ingredients) == 0:
        raise HTTPException(status_code=400, detail="Добавьте хотя бы один ингредиент")
    
    if len(request.ingredients) > 5:
        raise HTTPException(status_code=400, detail="Можно добавить максимум 5 ингредиентов")
    
    # Проверяем тип чая
    tea_type = await TeaType.get_or_none(id=request.base_tea_type_id)
    if not tea_type:
        raise HTTPException(status_code=404, detail="Тип чая не найден")
    
    # Проверяем конкретный чай, если указан
    base_tea = None
    if request.base_tea_id:
        base_tea = await Tea.get_or_none(id=request.base_tea_id, is_available=True)
        if not base_tea:
            raise HTTPException(status_code=404, detail="Чай не найден")
        # Проверяем, что чай соответствует выбранному типу
        if base_tea.tea_type_id != request.base_tea_type_id:
            raise HTTPException(status_code=400, detail="Выбранный чай не соответствует типу основы")
    
    # Проверяем ингредиенты
    total_weight = request.base_weight
    ingredient_objects = []
    for ing_data in request.ingredients:
        if ing_data.weight <= 0:
            raise HTTPException(status_code=400, detail=f"Вес ингредиента должен быть больше 0")
        
        ingredient = await Ingredient.get_or_none(id=ing_data.id, is_available=True)
        if not ingredient:
            raise HTTPException(status_code=404, detail=f"Ингредиент с ID {ing_data.id} не найден")
        
        ingredient_objects.append((ingredient, ing_data.weight))
        total_weight += ing_data.weight
    
    # Рассчитываем цену
    # Используем цену конкретного чая, если выбран, иначе базовую цену типа
    if base_tea:
        base_price_per_100g = base_tea.price_per_100g
    else:
        base_price_per_100g = Decimal("300.00")  # Базовая цена типа чая
    total_price = (base_price_per_100g * Decimal(str(request.base_weight))) / Decimal("100")
    
    for ingredient, weight in ingredient_objects:
        ingredient_price = (ingredient.price_per_100g * Decimal(str(weight))) / Decimal("100")
        total_price += ingredient_price
    
    # Средняя цена за 100г
    price_per_100g = (total_price / Decimal(str(total_weight))) * Decimal("100") if total_weight > 0 else Decimal("0")
    price_per_20g = price_per_100g * Decimal("0.2")
    
    # Создаем сбор
    blend = await CustomBlend.create(
        name=request.name.strip(),
        base_tea_type=tea_type,
        base_tea=base_tea,  # Сохраняем конкретный чай, если выбран
        creator=user,
        price_per_100g=price_per_100g,
        price_per_20g=price_per_20g,
        is_approved=False,
        is_public=False,
    )
    
    # Создаем компоненты
    order = 0
    
    # Основа (как компонент, но отдельно не сохраняем, только тип)
    # Компоненты - только ингредиенты
    for ingredient, weight in ingredient_objects:
        # Вычисляем процент и граммы на 100г
        percentage = (Decimal(str(weight)) / Decimal(str(total_weight))) * Decimal("100")
        grams_per_100g = (Decimal(str(weight)) / Decimal(str(total_weight))) * Decimal("100")
        
        await BlendComponent.create(
            blend=blend,
            ingredient=ingredient,
            tea=None,
            percentage=percentage,
            grams_per_100g=grams_per_100g,
            order=order,
        )
        order += 1
    
    return {
        "success": True,
        "blend_id": blend.id,
        "message": "Сбор успешно сохранен",
    }


@router.get("/blend/{blend_id}", response_class=HTMLResponse)
async def blend_detail_page(request: Request, blend_id: int):
    """Страница детальной информации о сборе"""
    blend = await CustomBlend.filter(id=blend_id).prefetch_related(
        "base_tea_type", "base_tea", "creator", "components__ingredient"
    ).first()
    
    if not blend:
        return render_template("404.html", {"message": "Сбор не найден"})
    
    # Увеличиваем счетчик просмотров
    blend.view_count += 1
    await blend.save()
    
    # Получаем компоненты с ингредиентами
    components = await BlendComponent.filter(blend_id=blend_id).prefetch_related("ingredient").order_by("order")
    
    # Преобразуем компоненты в словари с float значениями для шаблона
    components_data = []
    total_weight = 0.0
    for comp in components:
        if comp.grams_per_100g:
            weight = float(comp.grams_per_100g)
            total_weight += weight
            components_data.append({
                "ingredient": comp.ingredient,
                "grams_per_100g": weight,
            })
    
    context = {
        "blend": blend,
        "components": components_data,
        "total_weight": total_weight,
    }
    
    return render_template("blend_detail.html", context)


@router.get("/api/blends/popular")
async def get_popular_blends(limit: int = Query(6, ge=1, le=20)):
    """API для получения популярных публичных сборов"""
    # Пробуем получить одобренные публичные сборы
    blends_query = CustomBlend.filter(
        is_public=True,
        is_approved=True
    )
    
    # Проверяем, есть ли такие сборы
    count = await blends_query.count()
    
    if count == 0:
        # Если одобренных публичных нет, показываем просто публичные (для тестирования)
        blends_query = CustomBlend.filter(is_public=True)
        count = await blends_query.count()
        
        if count == 0:
            # Если и публичных нет, показываем последние созданные (для тестирования)
            blends_query = CustomBlend.all()
    
    blends = await blends_query.order_by(
        "-purchase_count", "-rating", "-view_count", "-created_at"
    ).limit(limit).prefetch_related(
        "base_tea_type", "base_tea", "creator"
    )
    
    return {
        "blends": [
            {
                "id": blend.id,
                "name": blend.name,
                "description": blend.description,
                "price_per_100g": float(blend.price_per_100g) if blend.price_per_100g else None,
                "price_per_20g": float(blend.price_per_20g) if blend.price_per_20g else None,
                "rating": blend.rating,
                "review_count": blend.review_count,
                "purchase_count": blend.purchase_count,
                "view_count": blend.view_count,
                "creator": {
                    "id": blend.creator.id,
                    "username": blend.creator.username,
                },
                "base_tea_type": {
                    "id": blend.base_tea_type.id,
                    "name": blend.base_tea_type.name,
                } if blend.base_tea_type else None,
                "base_tea": {
                    "id": blend.base_tea.id,
                    "name": blend.base_tea.name,
                    "slug": blend.base_tea.slug,
                } if blend.base_tea else None,
            }
            for blend in blends
        ]
    }
