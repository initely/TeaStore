#!/usr/bin/env python3
"""
Скрипт для автоматической загрузки изображений чаев через Unsplash API

Использование:
    python scripts/load_tea_images.py

Скрипт автоматически найдет все чаи без изображений и:
1. Скачает изображения из Unsplash
2. Сохранит их в static/images/teas/
3. Обновит пути к изображениям в базе данных

Если DOWNLOAD_IMAGES=False, то только сохранит URL-адреса (изображения будут загружаться с Unsplash).
"""
import asyncio
import aiohttp
import os
import sys
import re
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, close_db
from app.models import Tea
import urllib.parse

# Флаг: скачивать ли изображения локально (True) или использовать только URL (False)
DOWNLOAD_IMAGES = True  # Измените на False, если хотите только URL

# Флаг: обновлять ли все чаи (True) или только те, у которых нет изображений (False)
UPDATE_ALL_TEAS = True  # Измените на False, чтобы обновлять только чаи без изображений


async def download_image(url: str, save_path: Path, session: aiohttp.ClientSession) -> bool:
    """
    Скачивает изображение по URL и сохраняет локально
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                # Создаем директорию если её нет
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Сохраняем изображение
                with open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                return True
    except Exception as e:
        print(f"    ⚠ Ошибка скачивания: {e}")
        return False
    return False


def create_placeholder_image(tea_name: str, output_path: Path, tea_type: str = None):
    """
    Создает простое placeholder изображение с текстом
    Использует PIL (Pillow) для создания изображения
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Размеры изображения
        width, height = 400, 300
        
        # Цвета в зависимости от типа чая
        color_map = {
            "Зеленый": "#8BC34A",
            "Черный": "#424242",
            "Белый": "#FAFAFA",
            "Улун": "#FF9800",
            "Пуэр": "#5D4037",
            "Желтый": "#FFEB3B",
            "Красный": "#F44336",
        }
        
        bg_color = color_map.get(tea_type, "#607D8B")  # Серый по умолчанию
        text_color = "#FFFFFF" if tea_type != "Белый" else "#000000"
        
        # Создаем изображение
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Пытаемся использовать системный шрифт
        try:
            # Для Linux
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            try:
                # Альтернативный путь
                font_large = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 32)
                font_small = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 18)
            except:
                # Используем стандартный шрифт
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
        
        # Рисуем текст
        text = tea_name[:20]  # Ограничиваем длину
        bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 20
        
        draw.text((x, y), text, fill=text_color, font=font_large)
        
        if tea_type:
            type_text = tea_type
            bbox_small = draw.textbbox((0, 0), type_text, font=font_small)
            type_width = bbox_small[2] - bbox_small[0]
            type_x = (width - type_width) // 2
            type_y = y + text_height + 10
            draw.text((type_x, type_y), type_text, fill=text_color, font=font_small)
        
        # Сохраняем
        img.save(output_path, 'JPEG', quality=85)
        return True
    except ImportError:
        print("    ⚠ Pillow не установлен. Установите: pip install Pillow")
        return False
    except Exception as e:
        print(f"    ⚠ Ошибка создания изображения: {e}")
        return False


async def get_tea_image_from_yandex(tea_name: str, tea_type: str = None, session: aiohttp.ClientSession = None):
    """
    Получает URL первой картинки из Яндекс.Картинок по поисковому запросу
    """
    # Формируем поисковый запрос
    query = f"{tea_name} чай"
    if tea_type:
        query = f"{tea_name} {tea_type} чай"
    
    # Кодируем запрос
    encoded_query = urllib.parse.quote(query)
    
    # URL для поиска изображений в Яндексе
    search_url = f"https://yandex.ru/images/search?text={encoded_query}"
    
    try:
        # Устанавливаем User-Agent, чтобы выглядеть как обычный браузер
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                html = await response.text()
                
                # Пробуем использовать BeautifulSoup для более надежного парсинга
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем изображения разными способами
                    # 1. Ищем в data-bem атрибутах (основной способ Яндекса)
                    for item in soup.find_all(attrs={'data-bem': True}):
                        data_bem = item.get('data-bem', '')
                        # Ищем img_href в JSON
                        img_match = re.search(r'"img_href":"([^"]+)"', data_bem)
                        if img_match:
                            img_url = img_match.group(1).replace('\\/', '/')
                            if img_url.startswith('http'):
                                return img_url
                    
                    # 2. Ищем img теги с src
                    for img in soup.find_all('img', src=True):
                        src = img.get('src', '')
                        if src.startswith('http') and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            # Пропускаем маленькие иконки
                            if 'logo' not in src.lower() and 'icon' not in src.lower():
                                return src
                    
                    # 3. Ищем в data-src
                    for img in soup.find_all(attrs={'data-src': True}):
                        src = img.get('data-src', '')
                        if src.startswith('http') and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            if 'logo' not in src.lower() and 'icon' not in src.lower():
                                return src
                                
                except ImportError:
                    # Если BeautifulSoup не установлен, используем regex
                    pass
                
                # Fallback: используем regex парсинг
                # Ищем в JSON данных
                img_patterns = [
                    r'"img_href":"([^"]+)"',  # img_href в JSON
                    r'"orig":"([^"]+)"',  # orig в JSON
                    r'"url":"([^"]+\.(jpg|jpeg|png|webp))"',  # прямой URL
                    r'data-src="([^"]+\.(jpg|jpeg|png|webp))"',  # data-src атрибут
                    r'src="(https://[^"]+\.(jpg|jpeg|png|webp))"',  # src атрибут
                ]
                
                for pattern in img_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        # Берем первый найденный URL
                        img_url = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
                        # Очищаем URL от экранирования
                        img_url = img_url.replace('\\/', '/').replace('\\u002F', '/').replace('\\/', '/')
                        if img_url.startswith('http') and 'logo' not in img_url.lower() and 'icon' not in img_url.lower():
                            return img_url
                        
    except Exception as e:
        print(f"    ⚠ Ошибка поиска в Яндексе: {e}")
    
    return None


async def get_tea_image_url(tea_name: str, tea_type: str = None, country: str = None, session: aiohttp.ClientSession = None):
    """
    Получает URL изображения чая из Яндекса или создает placeholder
    """
    # Пробуем найти изображение в Яндексе
    yandex_image = await get_tea_image_from_yandex(tea_name, tea_type, session)
    if yandex_image:
        print(f"    ✓ Найдено в Яндексе: {yandex_image[:80]}...")
        return yandex_image
    else:
        print(f"    ⚠ Не найдено в Яндексе, используется placeholder")
    
    # Если не нашли, используем placeholder
    color_map = {
        "Зеленый": "8BC34A",
        "Черный": "424242", 
        "Белый": "FAFAFA",
        "Улун": "FF9800",
        "Пуэр": "5D4037",
        "Желтый": "FFEB3B",
        "Красный": "F44336",
    }
    
    bg_color = color_map.get(tea_type, "607D8B")
    text_color = "FFFFFF" if tea_type != "Белый" else "000000"
    
    # Кодируем название чая для URL
    encoded_name = urllib.parse.quote(tea_name[:30])  # Ограничиваем длину
    
    # Используем placeholder.com - надежный сервис
    image_url = f"https://via.placeholder.com/400x300/{bg_color}/{text_color}?text={encoded_name}"
    
    return image_url


async def update_tea_images():
    """
    Обновляет изображения для всех чаев без изображений
    """
    await init_db()
    
    # Получаем чаи в зависимости от флага
    if UPDATE_ALL_TEAS:
        teas = await Tea.all().prefetch_related("tea_type", "country")
        print(f"Найдено {len(teas)} чаев (обновление всех)")
    else:
        teas = await Tea.filter(main_image_url__isnull=True).prefetch_related("tea_type", "country")
        print(f"Найдено {len(teas)} чаев без изображений")
    
    if DOWNLOAD_IMAGES:
        print("Режим: СОЗДАНИЕ placeholder изображений локально в static/images/teas/")
        # Создаем директорию для изображений
        images_dir = Path("static/images/teas")
        images_dir.mkdir(parents=True, exist_ok=True)
        print("Будут созданы простые цветные изображения с названием чая")
    else:
        print("Режим: ТОЛЬКО URL (изображения будут загружаться с placeholder.com)")
    
    print("Используется Яндекс.Картинки для поиска изображений")
    print("Если изображение не найдено, будет использован placeholder\n")
    
    updated_count = 0
    failed_count = 0
    
    async with aiohttp.ClientSession() as session:
        for tea in teas:
            try:
                tea_type_name = tea.tea_type.name if tea.tea_type else None
                country_name = tea.country.name if tea.country else None
                
                # Получаем URL изображения
                image_url = await get_tea_image_url(
                    tea_name=tea.name,
                    tea_type=tea_type_name,
                    country=country_name,
                    session=session
                )
                
                if DOWNLOAD_IMAGES:
                    # Создаем безопасное имя файла из названия чая
                    safe_name = "".join(c for c in tea.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_name = safe_name.replace(' ', '_').lower()
                    file_name = f"{tea.id}_{safe_name}.jpg"
                    save_path = Path("static/images/teas") / file_name
                    
                    # Пробуем создать placeholder изображение локально
                    if create_placeholder_image(tea.name, save_path, tea_type_name):
                        # Сохраняем относительный путь для использования в HTML
                        tea.main_image_url = f"/static/images/teas/{file_name}"
                        await tea.save()
                        
                        updated_count += 1
                        print(f"✓ [{updated_count}/{len(teas)}] {tea.name}")
                        print(f"  Создано: {save_path}")
                    else:
                        # Если не удалось создать, скачиваем с placeholder.com
                        if await download_image(image_url, save_path, session):
                            tea.main_image_url = f"/static/images/teas/{file_name}"
                            await tea.save()
                            updated_count += 1
                            print(f"✓ [{updated_count}/{len(teas)}] {tea.name}")
                            print(f"  Скачано: {save_path}")
                        else:
                            # Если не удалось скачать, сохраняем URL
                            tea.main_image_url = image_url
                            await tea.save()
                            updated_count += 1
                            print(f"✓ [{updated_count}/{len(teas)}] {tea.name} (использован URL)")
                            print(f"  URL: {image_url}")
                else:
                    # Просто сохраняем URL
                    tea.main_image_url = image_url
                    await tea.save()
                    
                    updated_count += 1
                    print(f"✓ [{updated_count}/{len(teas)}] {tea.name}")
                    print(f"  URL: {image_url}")
                
                # Небольшая задержка, чтобы не перегружать API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                print(f"✗ Ошибка для {tea.name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Готово! Обновлено: {updated_count}, Ошибок: {failed_count}")
    if DOWNLOAD_IMAGES:
        print(f"Изображения сохранены в: static/images/teas/")
    print(f"{'='*60}")
    
    await close_db()


async def main():
    """
    Главная функция
    """
    print("="*60)
    print("Загрузка изображений для чаев")
    print("="*60)
    
    if DOWNLOAD_IMAGES:
        print("\n⚠ ВАЖНО: Изображения будут скачаны локально в static/images/teas/")
        print("   Это может занять некоторое время.\n")
    else:
        print("\n⚠ Режим: только URL (изображения не скачиваются)\n")
    
    await update_tea_images()


if __name__ == "__main__":
    asyncio.run(main())

