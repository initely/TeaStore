"""
Роутер для фейковой оплаты заказов (демо)
"""
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.auth import get_current_user_from_cookie
from app.models import Order, OrderStatus
from app.templates import render_template

router = APIRouter(tags=["payment"])

# In-memory хранилище mock-платежей: order_id -> данные сессии оплаты
payment_sessions: Dict[int, dict] = {}


class StartPaymentRequest(BaseModel):
    method: str  # "sbp" | "card"


@router.get("/payment", response_class=HTMLResponse)
async def payment_info_page(request: Request):
    """Инфостраница оплаты (из футера)"""
    return render_template("payment.html", {"is_info_page": True})


@router.get("/payment/{order_id}", response_class=HTMLResponse)
async def payment_page(order_id: int, request: Request):
    """Страница оплаты заказа"""
    access_token = request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    if not user:
        return RedirectResponse(url=f"/login?next=/payment/{order_id}", status_code=302)

    order = await Order.get_or_none(id=order_id, user_id=user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    return render_template(
        "payment.html",
        {
            "is_info_page": False,
            "order_id": order.id,
            "order_number": order.order_number,
            "order_total": float(order.total_amount),
            "order_status": order.status.name,
        },
    )


@router.post("/api/payment/{order_id}/start")
async def start_payment(order_id: int, payload: StartPaymentRequest, request: Request):
    """Запуск mock-оплаты"""
    access_token = request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    order = await Order.get_or_none(id=order_id, user_id=user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if order.status == OrderStatus.PAID:
        return {"success": True, "status": "paid", "message": "Заказ уже оплачен"}

    method = payload.method.lower().strip()
    if method not in {"sbp", "card"}:
        raise HTTPException(status_code=400, detail="Неверный способ оплаты")

    now = datetime.utcnow()
    payment_sessions[order_id] = {
        "method": method,
        "started_at": now,
        "paid_at": now + timedelta(seconds=5) if method == "sbp" else now,
    }

    response = {
        "success": True,
        "status": "pending" if method == "sbp" else "paid",
        "method": method,
        "message": "Ожидаем подтверждение оплаты",
    }
    if method == "sbp":
        response["qr_payload"] = f"SBP://payment/order/{order.order_number}"
        response["expires_in"] = 5
        return response

    # card в демо считаем оплаченной сразу
    order.status = OrderStatus.PAID
    order.paid_at = datetime.utcnow()
    await order.save()
    response["message"] = "Оплата картой успешно принята"
    return response


@router.get("/api/payment/{order_id}/status")
async def payment_status(order_id: int, request: Request):
    """Статус mock-оплаты"""
    access_token = request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    order = await Order.get_or_none(id=order_id, user_id=user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Если уже оплачен в БД, сразу возвращаем paid
    if order.status == OrderStatus.PAID:
        return {"status": "paid", "order_status": "PAID"}

    session = payment_sessions.get(order_id)
    if not session:
        return {"status": "idle", "order_status": order.status.name}

    # Для СБП через 5 секунд переводим в paid
    if session["method"] == "sbp" and datetime.utcnow() >= session["paid_at"]:
        order.status = OrderStatus.PAID
        order.paid_at = datetime.utcnow()
        await order.save()
        return {"status": "paid", "order_status": "PAID"}

    return {"status": "pending", "order_status": order.status.name, "method": session["method"]}
