"""
Роутер для чайной карты (Tea Traveler)
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from app.models import Country, Region
from app.templates import render_template

router = APIRouter()


@router.get("/tea-map", response_class=HTMLResponse)
async def tea_map_page(request: Request):
    """Страница с интерактивной чайной картой"""
    # Получаем страны с регионами для карты
    countries = await Country.filter(is_active=True)
    
    # Подготавливаем данные для карты
    map_data = []
    for country in countries:
        # Загружаем регионы для страны
        regions = await Region.filter(country_id=country.id, is_active=True)
        
        if regions:  # Только страны с активными регионами
            regions_data = [
                {
                    "id": region.id,
                    "name": region.name,
                }
                for region in regions
            ]
            
            map_data.append({
                "id": country.id,
                "name": country.name,
                "flag": country.flag_emoji or "🌍",
                "regions": regions_data,
            })
    
    context = {
        "countries": map_data,
    }
    
    return render_template("tea_map.html", context)


@router.get("/api/tea-map/countries")
async def get_tea_map_countries():
    """API для получения данных стран для карты"""
    countries = await Country.filter(is_active=True)
    
    result = []
    for country in countries:
        # Загружаем регионы для страны
        regions = await Region.filter(country_id=country.id, is_active=True)
        
        if regions:
            result.append({
                "id": country.id,
                "name": country.name,
                "name_en": country.name_en,
                "flag": country.flag_emoji or "🌍",
                "regions": [
                    {
                        "id": r.id,
                        "name": r.name,
                    }
                    for r in regions
                ],
            })
    
    return {"countries": result}

