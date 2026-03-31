"""
Роутер для отзывов на чаи и сборы
"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import Review, Tea, CustomBlend, Order, OrderItem, OrderStatus
from app.auth import get_current_user_from_cookie

router = APIRouter(tags=["reviews"])


class CreateReviewRequest(BaseModel):
    """Запрос на создание отзыва"""
    product_type: str = Field(..., description="Тип продукта: 'tea' или 'blend'")
    product_id: int = Field(..., description="ID продукта")
    rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5")
    title: Optional[str] = Field(None, max_length=200, description="Заголовок отзыва")
    text: Optional[str] = Field(None, description="Текст отзыва")


@router.get("/api/reviews/{product_type}/{product_id}", response_model=None)
async def get_reviews(product_type: str, product_id: int, request: Request):
    """Получить отзывы для продукта"""
    if product_type not in ["tea", "blend"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный тип продукта. Используйте 'tea' или 'blend'"
        )
    
    # Проверяем существование продукта
    if product_type == "tea":
        product = await Tea.get_or_none(id=product_id)
    else:
        product = await CustomBlend.get_or_none(id=product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Продукт не найден"
        )
    
    # Получаем одобренные отзывы
    if product_type == "tea":
        reviews = await Review.filter(
            tea_id=product_id,
            is_approved=True
        ).prefetch_related("user").order_by("-created_at")
    else:
        reviews = await Review.filter(
            custom_blend_id=product_id,
            is_approved=True
        ).prefetch_related("user").order_by("-created_at")
    
    # Проверяем, оставил ли текущий пользователь отзыв и может ли он оставить отзыв
    user_review = None
    can_review = False
    is_authenticated = False
    access_token = request.cookies.get("access_token")
    
    # Отладочное логирование
    print(f"DEBUG /api/reviews: cookies = {dict(request.cookies)}")
    print(f"DEBUG /api/reviews: access_token = {access_token[:20] + '...' if access_token else None}")
    
    user = await get_current_user_from_cookie(access_token)
    
    print(f"DEBUG /api/reviews: user = {user}")
    
    if user:
        is_authenticated = True
        # Проверяем, оставил ли пользователь уже отзыв
        if product_type == "tea":
            user_review = await Review.get_or_none(
                user_id=user.id,
                tea_id=product_id
            )
        else:
            user_review = await Review.get_or_none(
                user_id=user.id,
                custom_blend_id=product_id
            )
        
        # Проверяем, может ли пользователь оставить отзыв (есть ли доставленный заказ с этим товаром)
        if not user_review:
            delivered_orders = await Order.filter(
                user_id=user.id,
                status=OrderStatus.DELIVERED
            ).prefetch_related("items")
            
            has_delivered_order = False
            for order in delivered_orders:
                for item in order.items:
                    if product_type == "tea" and item.tea_id == product_id:
                        has_delivered_order = True
                        break
                    elif product_type == "blend" and item.custom_blend_id == product_id:
                        has_delivered_order = True
                        break
                if has_delivered_order:
                    break
            
            can_review = has_delivered_order
    
    result = {
        "reviews": [
            {
                "id": review.id,
                "user": {
                    "id": review.user.id,
                    "username": review.user.username,
                },
                "rating": review.rating,
                "title": review.title,
                "text": review.text,
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
            for review in reviews
        ],
        "user_has_review": bool(user_review is not None),
        "can_review": bool(can_review),
        "is_authenticated": bool(is_authenticated)
    }
    
    # Отладочный вывод
    print(f"DEBUG /api/reviews response: is_authenticated={is_authenticated}, user_has_review={user_review is not None}, can_review={can_review}")
    print(f"DEBUG /api/reviews result dict: {result}")
    
    response = JSONResponse(content=result)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@router.post("/api/reviews")
async def create_review(request: Request, review_data: CreateReviewRequest):
    """Создать отзыв (только для пользователей с доставленными заказами)"""
    access_token = request.cookies.get("access_token")
    user = await get_current_user_from_cookie(access_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )
    
    # Проверяем существование продукта
    if review_data.product_type == "tea":
        product = await Tea.get_or_none(id=review_data.product_id)
    else:
        product = await CustomBlend.get_or_none(id=review_data.product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Продукт не найден"
        )
    
    # Проверяем, есть ли у пользователя доставленный заказ с этим товаром
    delivered_orders = await Order.filter(
        user_id=user.id,
        status=OrderStatus.DELIVERED
    ).prefetch_related("items")
    
    has_delivered_order = False
    for order in delivered_orders:
        for item in order.items:
            if review_data.product_type == "tea" and item.tea_id == review_data.product_id:
                has_delivered_order = True
                break
            elif review_data.product_type == "blend" and item.custom_blend_id == review_data.product_id:
                has_delivered_order = True
                break
        if has_delivered_order:
            break
    
    if not has_delivered_order:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете оставить отзыв только на товары, которые вы получили (заказ доставлен)"
        )
    
    # Проверяем, не оставлял ли пользователь уже отзыв на этот товар
    if review_data.product_type == "tea":
        existing_review = await Review.get_or_none(
            user_id=user.id,
            tea_id=review_data.product_id
        )
    else:
        existing_review = await Review.get_or_none(
            user_id=user.id,
            custom_blend_id=review_data.product_id
        )
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже оставили отзыв на этот товар"
        )
    
    # Создаем отзыв
    review = Review(
        user_id=user.id,
        rating=review_data.rating,
        title=review_data.title,
        text=review_data.text,
        is_approved=True,  # Автоматически одобряем отзывы от пользователей с доставленными заказами
    )
    
    if review_data.product_type == "tea":
        review.tea_id = review_data.product_id
    else:
        review.custom_blend_id = review_data.product_id
    
    await review.save()
    
    # Обновляем рейтинг и количество отзывов продукта
    await update_product_rating(review_data.product_type, review_data.product_id)
    
    return {
        "success": True,
        "review": {
            "id": review.id,
            "user": {
                "id": user.id,
                "username": user.username,
            },
            "rating": review.rating,
            "title": review.title,
            "text": review.text,
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
    }


async def update_product_rating(product_type: str, product_id: int):
    """Обновить рейтинг и количество отзывов продукта"""
    if product_type == "tea":
        reviews = await Review.filter(tea_id=product_id, is_approved=True).all()
        product = await Tea.get(id=product_id)
    else:
        reviews = await Review.filter(custom_blend_id=product_id, is_approved=True).all()
        product = await CustomBlend.get(id=product_id)
    
    if reviews:
        total_rating = sum(r.rating for r in reviews)
        product.rating = total_rating / len(reviews)
        product.review_count = len(reviews)
    else:
        product.rating = 0.0
        product.review_count = 0
    
    await product.save()


