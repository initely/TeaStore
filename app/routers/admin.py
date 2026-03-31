"""
Роутер для админ-панели
"""
from fastapi import APIRouter, Request, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import Order, OrderItem, OrderStatus, User, Tea, CustomBlend
from app.auth import get_current_user_from_cookie
from app.templates import render_template

router = APIRouter()


async def update_purchase_counts(order: Order):
    """Обновить счетчики покупок для товаров в доставленном заказе"""
    items = await OrderItem.filter(order_id=order.id).prefetch_related("tea", "custom_blend")
    
    for item in items:
        if item.tea_id:
            tea = await Tea.get(id=item.tea_id)
            tea.purchase_count += 1
            await tea.save()
        elif item.custom_blend_id:
            blend = await CustomBlend.get(id=item.custom_blend_id)
            blend.purchase_count += 1
            await blend.save()


async def check_admin(request: Request) -> User:
    """Проверка, что пользователь является администратором"""
    user = await get_current_user_from_cookie(request.cookies.get("access_token"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )
    if user.role != 2:  # UserRole.ADMIN = 2
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора"
        )
    return user


@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Страница админ-панели"""
    await check_admin(request)
    return render_template("admin.html")


@router.get("/api/admin/orders")
async def get_all_orders(
    request: Request,
    status_filter: Optional[int] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Получение всех заказов с фильтрацией"""
    await check_admin(request)
    
    query = Order.all().prefetch_related("user", "items__tea", "items__custom_blend")
    
    if status_filter is not None:
        query = query.filter(status=status_filter)
    
    total = await query.count()
    total_pages = (total + page_size - 1) // page_size
    
    orders = await query.order_by("-created_at").offset((page - 1) * page_size).limit(page_size)
    
    orders_data = []
    for order in orders:
        items = await OrderItem.filter(order=order).prefetch_related("tea", "custom_blend")
        items_data = []
        for item in items:
            product_name = item.tea.name if item.tea else (item.custom_blend.name if item.custom_blend else "Товар удален")
            items_data.append({
                "id": item.id,
                "product_name": product_name,
                "product_type": "tea" if item.tea else "blend",
                "quantity": item.quantity,
                "size": item.size,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
            })
        
        orders_data.append({
            "id": order.id,
            "order_number": order.order_number,
            "user": {
                "id": order.user.id,
                "username": order.user.username,
                "email": order.user.email,
            },
            "status": order.status.value,
            "status_name": order.status.name,
            "total_amount": float(order.total_amount),
            "shipping_cost": float(order.shipping_cost),
            "delivery_city": order.delivery_city,
            "delivery_address": order.delivery_address,
            "delivery_phone": order.delivery_phone,
            "delivery_postal_code": order.delivery_postal_code,
            "items": items_data,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        })
    
    return {
        "orders": orders_data,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total": total,
            "page_size": page_size,
        }
    }


class UpdateOrderStatusRequest(BaseModel):
    """Запрос на изменение статуса заказа"""
    status: int


@router.put("/api/admin/orders/{order_id}/status")
async def update_order_status(
    request: Request,
    order_id: int,
    status_data: UpdateOrderStatusRequest
):
    """Изменение статуса заказа"""
    await check_admin(request)
    
    # Проверяем, что статус валидный
    try:
        new_status = OrderStatus(status_data.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный статус заказа"
        )
    
    order = await Order.get_or_none(id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Обновляем статус и даты в зависимости от статуса
    order.status = new_status
    now = datetime.utcnow()
    
    if new_status == OrderStatus.PAID and not order.paid_at:
        order.paid_at = now
    elif new_status == OrderStatus.SHIPPED and not order.shipped_at:
        order.shipped_at = now
    elif new_status == OrderStatus.DELIVERED and not order.delivered_at:
        order.delivered_at = now
        # Обновляем счетчики покупок для товаров в заказе
        await update_purchase_counts(order)
    
    await order.save()
    
    return {
        "success": True,
        "order_id": order.id,
        "status": order.status.value,
        "status_name": order.status.name,
    }


@router.get("/api/admin/statistics")
async def get_statistics(request: Request):
    """Получение статистики для админ-панели"""
    await check_admin(request)
    
    # Общая статистика заказов
    total_orders = await Order.all().count()
    pending_orders = await Order.filter(status=OrderStatus.PENDING).count()
    processing_orders = await Order.filter(status=OrderStatus.PROCESSING).count()
    shipped_orders = await Order.filter(status=OrderStatus.SHIPPED).count()
    delivered_orders = await Order.filter(status=OrderStatus.DELIVERED).count()
    
    # Общая сумма всех заказов
    all_orders = await Order.all()
    total_revenue = sum(float(order.total_amount) for order in all_orders)
    
    # Статистика за сегодня
    from datetime import date
    today = date.today()
    today_orders = await Order.filter(created_at__gte=datetime.combine(today, datetime.min.time())).count()
    
    # Статистика пользователей
    total_users = await User.all().count()
    active_users = await User.filter(is_active=True).count()
    
    # Статистика товаров
    total_teas = await Tea.filter(is_available=True).count()
    total_blends = await CustomBlend.all().count()
    
    return {
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "processing": processing_orders,
            "shipped": shipped_orders,
            "delivered": delivered_orders,
            "today": today_orders,
        },
        "revenue": {
            "total": total_revenue,
        },
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "products": {
            "teas": total_teas,
            "blends": total_blends,
        }
    }

