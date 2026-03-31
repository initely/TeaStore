"""
Роутер для работы с чаями и каталогом
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from tortoise.expressions import Q
from app.models import Tea, Country, Region, TeaType, TeaFlavor, CustomBlend, BlendComponent
from app.templates import render_template

router = APIRouter(tags=["teas"])


@router.get("/catalog", response_class=HTMLResponse)
async def catalog_page(
    request: Request,
    page: int = Query(1, ge=1),
    country_id: str = Query(None),
    region_id: str = Query(None),
    tea_type_id: str = Query(None),
    flavor_id: str = Query(None),
    search: str = Query(None),
    sort: str = Query("newest"),  # newest, price_asc, price_desc, popular
    tab: str = Query("teas"),  # teas или blends
):
    """Страница каталога чаев и сборов"""
    # Преобразуем строковые параметры в int, если они не пустые
    country_id = int(country_id) if country_id and country_id.strip() else None
    region_id = int(region_id) if region_id and region_id.strip() else None
    tea_type_id = int(tea_type_id) if tea_type_id and tea_type_id.strip() else None
    flavor_id = int(flavor_id) if flavor_id and flavor_id.strip() else None
    search = search.strip() if search else None
    
    # Получаем фильтры для шаблона
    countries = await Country.all().filter(is_active=True)
    tea_types = await TeaType.all()
    flavors = await TeaFlavor.all()
    
    # Строим запрос с фильтрами
    query = Tea.filter(is_available=True)
    
    if country_id:
        query = query.filter(country_id=country_id)
    if region_id:
        query = query.filter(region_id=region_id)
    if tea_type_id:
        query = query.filter(tea_type_id=tea_type_id)
    if flavor_id:
        query = query.filter(flavors__id=flavor_id)
    if search:
        # Поиск только по названию чая (частичное совпадение)
        search_clean = search.strip()
        if search_clean:
            # Для SQLite используем icontains (должен работать через LIKE)
            # Если не работает, можно использовать contains с разными регистрами
            query = query.filter(
                Q(name__icontains=search_clean) | 
                Q(name_en__icontains=search_clean)
            )
    
    # Сортировка
    if sort == "price_asc":
        query = query.order_by("price_per_100g")
    elif sort == "price_desc":
        query = query.order_by("-price_per_100g")
    elif sort == "popular":
        query = query.order_by("-purchase_count", "-rating")
    else:  # newest
        query = query.order_by("-created_at")
    
    # Пагинация
    page_size = 12
    total = await query.count()
    total_pages = (total + page_size - 1) // page_size
    
    teas = await query.offset((page - 1) * page_size).limit(page_size).prefetch_related(
        "country", "region", "tea_type", "flavors"
    )
    
    # Получаем регионы для выбранной страны
    regions = []
    if country_id:
        regions = await Region.filter(country_id=country_id, is_active=True)
    
    context = {
        "teas": teas,
        "countries": countries,
        "regions": regions,
        "tea_types": tea_types,
        "flavors": flavors,
        "current_page": page,
        "total_pages": total_pages,
        "total": total,
        "current_tab": tab,
        "filters": {
            "country_id": country_id,
            "region_id": region_id,
            "tea_type_id": tea_type_id,
            "flavor_id": flavor_id,
            "search": search,
            "sort": sort,
        }
    }
    
    return render_template("catalog.html", context)


@router.get("/api/teas")
async def get_teas_api(
    page: int = Query(1, ge=1),
    country_id: str = Query(None),
    region_id: str = Query(None),
    tea_type_id: str = Query(None),
    flavor_id: str = Query(None),
    search: str = Query(None),
    sort: str = Query("newest"),
    page_size: int = Query(12, ge=1, le=50),
):
    """API endpoint для получения списка чаев"""
    # Преобразуем строковые параметры в int, если они не пустые
    country_id = int(country_id) if country_id and country_id.strip() else None
    region_id = int(region_id) if region_id and region_id.strip() else None
    tea_type_id = int(tea_type_id) if tea_type_id and tea_type_id.strip() else None
    flavor_id = int(flavor_id) if flavor_id and flavor_id.strip() else None
    search = search.strip() if search else None
    
    query = Tea.filter(is_available=True)
    
    if country_id:
        query = query.filter(country_id=country_id)
    if region_id:
        query = query.filter(region_id=region_id)
    if tea_type_id:
        query = query.filter(tea_type_id=tea_type_id)
    if flavor_id:
        query = query.filter(flavors__id=flavor_id)
    if search:
        # Поиск только по названию чая (частичное совпадение)
        search_clean = search.strip()
        if search_clean:
            # Для SQLite используем icontains (должен работать через LIKE)
            # Если не работает, можно использовать contains с разными регистрами
            query = query.filter(
                Q(name__icontains=search_clean) | 
                Q(name_en__icontains=search_clean)
            )
    
    # Сортировка
    if sort == "price_asc":
        query = query.order_by("price_per_100g")
    elif sort == "price_desc":
        query = query.order_by("-price_per_100g")
    elif sort == "popular":
        query = query.order_by("-purchase_count", "-rating")
    else:
        query = query.order_by("-created_at")
    
    total = await query.count()
    total_pages = (total + page_size - 1) // page_size
    
    teas = await query.offset((page - 1) * page_size).limit(page_size).prefetch_related(
        "country", "region", "tea_type", "flavors"
    )
    
    return {
        "teas": [
            {
                "id": tea.id,
                "name": tea.name,
                "name_en": tea.name_en,
                "slug": tea.slug,
                "description": tea.description,
                "short_description": tea.short_description,
                "price_per_100g": float(tea.price_per_100g),
                "price_per_20g": float(tea.price_per_20g) if tea.price_per_20g else None,
                "rating": tea.rating,
                "review_count": tea.review_count,
                "country": {
                    "id": tea.country.id,
                    "name": tea.country.name,
                } if tea.country else None,
                "region": {
                    "id": tea.region.id,
                    "name": tea.region.name,
                } if tea.region else None,
                "tea_type": {
                    "id": tea.tea_type.id,
                    "name": tea.tea_type.name,
                },
                "flavors": [{"id": f.id, "name": f.name} for f in tea.flavors],
                "main_image_url": tea.main_image_url,
            }
            for tea in teas
        ],
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total": total,
            "page_size": page_size,
        }
    }


@router.get("/api/countries/{country_id}/regions")
async def get_regions_by_country(country_id: int):
    """API endpoint для получения регионов по стране"""
    regions = await Region.filter(country_id=country_id, is_active=True).order_by("name")
    return {
        "regions": [
            {
                "id": region.id,
                "name": region.name,
                "name_en": region.name_en,
            }
            for region in regions
        ]
    }


@router.get("/api/teas/popular")
async def get_popular_teas(limit: int = Query(8, ge=1, le=20)):
    """API для получения популярных чаев"""
    # Получаем чаи, сортируя по покупкам, рейтингу и дате создания
    # Если покупок/рейтингов нет, просто сортируем по дате создания
    teas = await Tea.filter(is_available=True).order_by(
        "-purchase_count", "-rating", "-created_at"
    ).limit(limit).prefetch_related("country", "region", "tea_type")
    
    return {
        "teas": [
            {
                "id": tea.id,
                "name": tea.name,
                "slug": tea.slug,
                "price_per_100g": float(tea.price_per_100g),
                "price_per_20g": float(tea.price_per_20g) if tea.price_per_20g else None,
                "rating": tea.rating,
                "review_count": tea.review_count,
                "purchase_count": tea.purchase_count,
                "country": {
                    "id": tea.country.id,
                    "name": tea.country.name,
                } if tea.country else None,
                "region": {
                    "id": tea.region.id,
                    "name": tea.region.name,
                } if tea.region else None,
                "tea_type": {
                    "id": tea.tea_type.id,
                    "name": tea.tea_type.name,
                },
                "main_image_url": tea.main_image_url,
            }
            for tea in teas
        ]
    }


@router.get("/api/map/countries")
async def get_map_countries():
    """API для получения стран с чаями для чайной карты"""
    try:
        countries = await Country.filter(is_active=True).all()
        
        result = []
        for country in countries:
            # Подсчитываем количество доступных чаев
            tea_count = await Tea.filter(country_id=country.id, is_available=True).count()
            
            if tea_count > 0:  # Показываем только страны с чаями
                result.append({
                    "id": country.id,
                    "name": country.name,
                    "name_en": country.name_en,
                    "code": country.code,
                    "latitude": float(country.latitude) if country.latitude else None,
                    "longitude": float(country.longitude) if country.longitude else None,
                    "flag_emoji": country.flag_emoji,
                    "tea_count": tea_count,
                })
        
        return {"countries": result}
    except Exception as e:
        # В случае ошибки возвращаем пустой список
        import logging
        logging.error(f"Ошибка при загрузке стран для карты: {e}")
        return {"countries": []}


@router.get("/api/blends")
async def get_blends_api(
    page: int = Query(1, ge=1),
    tea_type_id: str = Query(None),
    search: str = Query(None),
    sort: str = Query("newest"),
    page_size: int = Query(12, ge=1, le=50),
):
    """API для получения публичных сборов"""
    # Преобразуем строковые параметры в int
    tea_type_id = int(tea_type_id) if tea_type_id and tea_type_id.strip() else None
    search = search.strip() if search else None
    
    # Получаем все сборы (или можно показывать только публичные/одобренные)
    # Пока показываем все для тестирования, потом можно добавить фильтр
    query = CustomBlend.all().prefetch_related(
        "base_tea_type", "base_tea", "creator", "components__ingredient"
    )
    
    if tea_type_id:
        query = query.filter(base_tea_type_id=tea_type_id)
    
    if search:
        search_clean = search.strip()
        if search_clean:
            query = query.filter(
                Q(name__icontains=search_clean) | 
                Q(description__icontains=search_clean)
            )
    
    # Сортировка
    if sort == "price_asc":
        query = query.order_by("price_per_100g")
    elif sort == "price_desc":
        query = query.order_by("-price_per_100g")
    elif sort == "popular":
        query = query.order_by("-purchase_count", "-rating")
    else:  # newest
        query = query.order_by("-created_at")
    
    total = await query.count()
    total_pages = (total + page_size - 1) // page_size
    
    blends = await query.offset((page - 1) * page_size).limit(page_size)
    
    blends_data = []
    for blend in blends:
        # Получаем компоненты с ингредиентами для каждого сбора
        components = await BlendComponent.filter(blend_id=blend.id).prefetch_related("ingredient").order_by("order")
        ingredients = []
        for comp in components:
            if comp.ingredient:
                ingredients.append({
                    "id": comp.ingredient.id,
                    "name": comp.ingredient.name,
                })
        
        blends_data.append({
            "id": blend.id,
            "name": blend.name,
            "description": blend.description,
            "short_description": blend.description[:150] + "..." if blend.description and len(blend.description) > 150 else blend.description,
            "price_per_100g": float(blend.price_per_100g) if blend.price_per_100g else None,
            "price_per_20g": float(blend.price_per_20g) if blend.price_per_20g else None,
            "rating": blend.rating,
            "review_count": blend.review_count,
            "purchase_count": blend.purchase_count,
            "base_tea_type": {
                "id": blend.base_tea_type.id,
                "name": blend.base_tea_type.name,
            } if blend.base_tea_type else None,
            "base_tea": {
                "id": blend.base_tea.id,
                "name": blend.base_tea.name,
            } if blend.base_tea else None,
            "creator": {
                "id": blend.creator.id,
                "username": blend.creator.username,
            } if blend.creator else None,
            "created_at": blend.created_at.isoformat() if blend.created_at else None,
            "is_featured": blend.is_featured,
            "ingredients": ingredients,
        })
    
    return {
        "blends": blends_data,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total": total,
            "page_size": page_size,
        }
    }


@router.get("/tea/{slug}", response_class=HTMLResponse)
async def tea_detail_page(request: Request, slug: str):
    """Страница детальной информации о чае"""
    tea = await Tea.filter(slug=slug, is_available=True).prefetch_related(
        "country", "region", "tea_type", "flavors"
    ).first()
    
    if not tea:
        return render_template("404.html", {"message": "Чай не найден"})
    
    # Загружаем полную информацию о стране и регионе, если они есть
    if tea.country_id:
        tea.country = await Country.get(id=tea.country_id)
    if tea.region_id:
        tea.region = await Region.get(id=tea.region_id)
    
    # Похожие чаи
    similar_teas = await Tea.filter(
        tea_type=tea.tea_type,
        is_available=True
    ).exclude(id=tea.id).limit(4).prefetch_related("country", "tea_type")
    
    context = {
        "tea": tea,
        "similar_teas": similar_teas,
    }
    
    return render_template("tea_detail.html", context)

