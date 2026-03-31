"""
Роутер для работы с корзиной и заказами
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import json
import uuid

from app.models import Tea, CustomBlend, Order, OrderItem, OrderStatus, User
from app.auth import get_current_user_from_cookie
from app.templates import render_template

router = APIRouter()


class CartItem(BaseModel):
    """Элемент корзины"""
    product_type: str  # "tea" или "blend"
    product_id: int
    quantity: int  # в граммах (20 или 100)
    size: str  # "20g" или "100g"


def get_cart_from_session(request: Request) -> List[dict]:
    """Получает корзину из сессии"""
    cart = request.session.get("cart", [])
    return cart if isinstance(cart, list) else []


def save_cart_to_session(request: Request, cart: List[dict]):
    """Сохраняет корзину в сессию"""
    # В Starlette SessionMiddleware request.session - это обычный dict,
    # который автоматически сохраняется при изменении
    request.session["cart"] = cart


@router.post("/api/cart/add")
async def add_to_cart(request: Request, item: CartItem):
    """Добавление товара в корзину"""
    cart = get_cart_from_session(request)
    
    # Проверяем товар
    if item.product_type == "tea":
        product = await Tea.get_or_none(id=item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Чай не найден")
        price_value = product.price_per_20g if item.size == "20g" else product.price_per_100g
        if price_value is None:
            raise HTTPException(status_code=400, detail="Товар недоступен в выбранном размере")
        price = float(price_value)
        name = product.name
    elif item.product_type == "blend":
        product = await CustomBlend.get_or_none(id=item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Сбор не найден")
        price_value = product.price_per_20g if item.size == "20g" else product.price_per_100g
        if price_value is None:
            raise HTTPException(status_code=400, detail="Товар недоступен в выбранном размере")
        price = float(price_value)
        name = product.name
    else:
        raise HTTPException(status_code=400, detail="Неверный тип товара")
    
    # Проверяем, есть ли уже такой товар в корзине
    found = False
    for cart_item in cart:
        if (cart_item["product_type"] == item.product_type and 
            cart_item["product_id"] == item.product_id and 
            cart_item["size"] == item.size):
            cart_item["quantity"] += item.quantity
            found = True
            break
    
    if not found:
        cart_item_data = {
            "product_type": item.product_type,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "size": item.size,
            "name": name,
            "price": price,
        }
        # Добавляем slug для чая
        if item.product_type == "tea":
            cart_item_data["slug"] = product.slug
        cart.append(cart_item_data)
    
    save_cart_to_session(request, cart)
    
    # Получаем актуальное количество товаров через get_cart для правильного подсчета
    # Но для быстрого ответа используем len(cart)
    return {
        "success": True,
        "message": "Товар добавлен в корзину",
        "cart_count": len(cart)  # Количество элементов в корзине (не фильтрованное)
    }


@router.delete("/api/cart/remove")
async def remove_from_cart(request: Request, index: int = Query(...)):
    """Удаление товара из корзины"""
    cart = get_cart_from_session(request)
    
    if 0 <= index < len(cart):
        cart.pop(index)
        save_cart_to_session(request, cart)
        return {"success": True, "message": "Товар удален из корзины"}
    
    raise HTTPException(status_code=404, detail="Товар не найден в корзине")


@router.put("/api/cart/update")
async def update_cart_item(request: Request, index: int = Query(...), quantity: int = Query(...)):
    """Обновление количества товара в корзине"""
    cart = get_cart_from_session(request)
    
    if 0 <= index < len(cart):
        if quantity <= 0:
            cart.pop(index)
        else:
            cart[index]["quantity"] = quantity
        save_cart_to_session(request, cart)
        return {"success": True, "message": "Корзина обновлена"}
    
    raise HTTPException(status_code=404, detail="Товар не найден в корзине")


@router.get("/api/cart")
async def get_cart(request: Request):
    """Получение содержимого корзины"""
    cart = get_cart_from_session(request)
    
    # Обновляем информацию о товарах (цены могут измениться)
    updated_cart = []
    total = Decimal("0.00")
    
    for item in cart:
        try:
            # Используем сохраненные данные, если они есть
            if "name" in item and "price" in item and item.get("price") is not None:
                # Если товар уже был обработан ранее, используем сохраненные данные
                # Обновляем только slug для чая, если нужно
                try:
                    if item["product_type"] == "tea":
                        product = await Tea.get_or_none(id=item["product_id"])
                        if product and "slug" not in item:
                            item["slug"] = product.slug
                    elif item["product_type"] == "blend":
                        product = await CustomBlend.get_or_none(id=item["product_id"])
                        # Для сборов просто проверяем существование
                    
                    # Товар есть в корзине, добавляем его в updated_cart
                    item["available"] = True
                    item_total = Decimal(str(item["price"])) * Decimal(str(item["quantity"]))
                    total += item_total
                    updated_cart.append(item)
                    continue
                except Exception:
                    # Если проверка не удалась, загружаем данные заново
                    pass
            
            # Если данных нет, загружаем из БД
            if item["product_type"] == "tea":
                product = await Tea.get_or_none(id=item["product_id"])
                if product:
                    price_value = product.price_per_20g if item["size"] == "20g" else product.price_per_100g
                    if price_value is not None:
                        price = float(price_value)
                        item["price"] = price
                        item["name"] = product.name
                        item["slug"] = product.slug
                        item["available"] = True
                    else:
                        # Цены нет, но товар существует - используем сохраненную цену или помечаем как недоступный
                        item["available"] = False
                else:
                    # Товар не найден - помечаем как недоступный, но не удаляем из корзины
                    item["available"] = False
            elif item["product_type"] == "blend":
                product = await CustomBlend.get_or_none(id=item["product_id"])
                if product:
                    price_value = product.price_per_20g if item["size"] == "20g" else product.price_per_100g
                    if price_value is not None:
                        price = float(price_value)
                        item["price"] = price
                        item["name"] = product.name
                        item["available"] = True
                    else:
                        item["available"] = False
                else:
                    # Сбор не найден - помечаем как недоступный, но не удаляем из корзины
                    item["available"] = False
            else:
                item["available"] = False
            
            # Добавляем товар в updated_cart, даже если он недоступен
            # Это нужно для отображения в корзине с пометкой о недоступности
            if item.get("available", False):
                item_total = Decimal(str(item["price"])) * Decimal(str(item["quantity"]))
                total += item_total
            updated_cart.append(item)
        except Exception as e:
            # Логируем ошибку для отладки
            import logging
            logging.error(f"Ошибка при обработке товара в корзине: {e}, item: {item}")
            # Пытаемся сохранить товар, если есть базовая информация
            if "name" in item and "price" in item:
                try:
                    item_total = Decimal(str(item["price"])) * Decimal(str(item["quantity"]))
                    total += item_total
                    item["available"] = True  # Помечаем как доступный, если есть цена и название
                    updated_cart.append(item)
                except Exception:
                    # Если не удалось обработать, пропускаем товар
                    continue
            else:
                # Если нет базовой информации, пропускаем товар
                continue
    
    # Обновляем данные в оригинальной корзине для товаров, которые есть в updated_cart
    # Это нужно для сохранения актуальных цен и названий
    for item in cart:
        for updated_item in updated_cart:
            if (updated_item["product_type"] == item["product_type"] and
                updated_item["product_id"] == item["product_id"] and
                updated_item["size"] == item["size"]):
                # Обновляем данные в оригинальном элементе корзины
                item["name"] = updated_item.get("name", item.get("name"))
                item["price"] = updated_item.get("price", item.get("price"))
                if "slug" in updated_item:
                    item["slug"] = updated_item["slug"]
                break
    
    # Сохраняем обновленную корзину (со всеми товарами, даже если они временно недоступны)
    # Это важно, чтобы не потерять товары при следующем запросе
    save_cart_to_session(request, cart)
    
    return {
        "cart": updated_cart,  # Возвращаем все товары (с пометкой available)
        "total": float(total),
        "count": len(updated_cart)  # Считаем все товары в корзине
    }


@router.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    """Страница корзины"""
    return render_template("cart.html", {})


@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request):
    """Страница оформления заказа"""
    # Проверяем авторизацию
    access_token = request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    
    if not user:
        # Перенаправляем на страницу логина с возвратом в checkout
        return RedirectResponse(url="/login?next=/checkout", status_code=302)
    
    cart = get_cart_from_session(request)
    if not cart:
        # Если корзина пуста, перенаправляем на корзину
        return RedirectResponse(url="/cart", status_code=302)
    
    context = {
        "user": user
    }
    return render_template("checkout.html", context)


class CreateOrderRequest(BaseModel):
    """Запрос на создание заказа"""
    delivery_address: str
    delivery_city: str
    delivery_postal_code: Optional[str] = None
    delivery_phone: Optional[str] = None
    notes: Optional[str] = None


@router.post("/api/orders/create")
async def create_order(request: Request, order_data: CreateOrderRequest):
    """Создание заказа"""
    # Проверяем авторизацию
    access_token = request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    cart = get_cart_from_session(request)
    if not cart:
        raise HTTPException(status_code=400, detail="Корзина пуста")
    
    # Рассчитываем общую сумму
    total_amount = Decimal("0.00")
    shipping_cost = Decimal("300.00")  # Стоимость доставки
    
    # Проверяем товары и рассчитываем сумму
    order_items_data = []
    for item in cart:
        if item["product_type"] == "tea":
            product = await Tea.get_or_none(id=item["product_id"])
            if not product:
                continue
            price = product.price_per_20g if item["size"] == "20g" else product.price_per_100g
        elif item["product_type"] == "blend":
            product = await CustomBlend.get_or_none(id=item["product_id"])
            if not product:
                continue
            price = product.price_per_20g if item["size"] == "20g" else product.price_per_100g
        else:
            continue
        
        if not price:
            continue
        
        item_total = price * Decimal(str(item["quantity"]))
        total_amount += item_total
        
        order_items_data.append({
            "product_type": item["product_type"],
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "size": item["size"],
            "unit_price": price,
            "total_price": item_total,
        })
    
    if not order_items_data:
        raise HTTPException(status_code=400, detail="Нет доступных товаров для заказа")
    
    total_amount += shipping_cost
    
    # Генерируем номер заказа
    order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Создаем заказ
    order = await Order.create(
        user=user,
        order_number=order_number,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        shipping_cost=shipping_cost,
        delivery_address=order_data.delivery_address,
        delivery_city=order_data.delivery_city,
        delivery_postal_code=order_data.delivery_postal_code,
        delivery_phone=order_data.delivery_phone,
        notes=order_data.notes,
    )
    
    # Создаем элементы заказа
    for item_data in order_items_data:
        tea = None
        blend = None
        
        if item_data["product_type"] == "tea":
            tea = await Tea.get(id=item_data["product_id"])
        elif item_data["product_type"] == "blend":
            blend = await CustomBlend.get(id=item_data["product_id"])
        
        await OrderItem.create(
            order=order,
            tea=tea,
            custom_blend=blend,
            quantity=item_data["quantity"],
            size=item_data["size"],
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"],
        )
    
    # Очищаем корзину
    save_cart_to_session(request, [])
    
    return {
        "success": True,
        "order_id": order.id,
        "order_number": order_number,
        "message": "Заказ успешно создан"
    }


@router.get("/api/orders")
async def get_user_orders(request: Request):
    """Получение заказов пользователя"""
    access_token = request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    orders = await Order.filter(user_id=user.id).prefetch_related("items__tea", "items__custom_blend").order_by("-created_at")
    
    orders_data = []
    for order in orders:
        items_data = []
        for item in order.items:
            product_name = item.tea.name if item.tea else item.custom_blend.name
            product_slug = None
            if item.tea:
                # Получаем slug напрямую из базы данных
                # prefetch_related может не загружать все поля
                tea = await Tea.get(id=item.tea.id)
                product_slug = tea.slug
                # Отладочный вывод
                print(f"DEBUG Order item tea: id={tea.id}, name={tea.name}, slug={product_slug}")
            
            items_data.append({
                "id": item.id,
                "product_name": product_name,
                "product_type": "tea" if item.tea else "blend",
                "product_id": item.tea.id if item.tea else item.custom_blend.id,
                "product_slug": product_slug,  # Slug для чая
                "quantity": item.quantity,
                "size": item.size,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
            })
        
        orders_data.append({
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "status_name": order.status.name,
            "total_amount": float(order.total_amount),
            "shipping_cost": float(order.shipping_cost),
            "delivery_address": order.delivery_address,
            "delivery_city": order.delivery_city,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "items": items_data,
        })
    
    return {"orders": orders_data}

