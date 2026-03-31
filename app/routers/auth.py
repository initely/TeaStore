"""
Роутер для аутентификации пользователей
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models import User, UserRole, CustomBlend, BlendComponent
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user_from_cookie,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    timedelta,
)
from app.templates import render_template
from datetime import datetime

router = APIRouter()


class RegisterRequest(BaseModel):
    """Запрос на регистрацию"""
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Запрос на вход"""
    email: str
    password: str


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    # Проверяем, не авторизован ли уже пользователь
    user = await get_current_user_from_cookie(request.cookies.get("access_token"))
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    return render_template("register.html", {})


@router.post("/api/register")
async def register(request: RegisterRequest):
    """API для регистрации"""
    # Проверяем, не занят ли email
    existing_user = await User.get_or_none(email=request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Проверяем, не занят ли username
    existing_username = await User.get_or_none(username=request.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    # Создаем пользователя
    hashed_password = get_password_hash(request.password)
    user = await User.create(
        email=request.email,
        username=request.username,
        hashed_password=hashed_password,
        first_name=request.first_name,
        last_name=request.last_name,
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    
    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},  # sub должен быть строкой
        expires_delta=access_token_expires
    )
    
    # Создаем ответ с cookie
    response_data = {
        "success": True,
        "user_id": user.id,
        "username": user.username,
    }
    
    response = JSONResponse(content=response_data)
    
    # Устанавливаем cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        path="/",
    )
    
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    # Проверяем, не авторизован ли уже пользователь
    user = await get_current_user_from_cookie(request.cookies.get("access_token"))
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    return render_template("login.html", {})


@router.post("/api/login")
async def login(request: LoginRequest):
    """API для входа"""
    # Ищем пользователя по email
    user = await User.get_or_none(email=request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Проверяем пароль
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Проверяем, активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован"
        )
    
    # Обновляем last_login
    user.last_login = datetime.utcnow()
    await user.save()
    
    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},  # sub должен быть строкой
        expires_delta=access_token_expires
    )
    
    # Создаем ответ с cookie
    response_data = {
        "success": True,
        "user_id": user.id,
        "username": user.username,
    }
    
    response = JSONResponse(content=response_data)
    
    # Устанавливаем cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        path="/",
    )
    
    return response


@router.get("/logout")
async def logout_page(response: Response):
    """Страница выхода (редирект)"""
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token", path="/")
    return response


@router.get("/api/me")
async def get_current_user_info(request: Request):
    """Получение информации о текущем пользователе"""
    access_token = request.cookies.get("access_token")
    
    # Отладочное логирование
    print(f"DEBUG /api/me: cookies = {dict(request.cookies)}")
    print(f"DEBUG /api/me: access_token = {access_token[:20] + '...' if access_token else None}")
    
    user = await get_current_user_from_cookie(access_token)
    
    print(f"DEBUG /api/me: user = {user}")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "is_admin": user.role == 2,  # UserRole.ADMIN = 2
    }


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница личного кабинета"""
    user = await get_current_user_from_cookie(request.cookies.get("access_token"))
    
    if not user:
        return RedirectResponse(url="/login?next=/profile", status_code=status.HTTP_302_FOUND)
    
    context = {
        "user": user,
    }
    
    return render_template("profile.html", context)


@router.get("/api/profile/blends")
async def get_user_blends(request: Request):
    """Получение сохраненных сборов пользователя"""
    user = await get_current_user_from_cookie(request.cookies.get("access_token"))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован"
        )
    
    # Получаем все сборы пользователя
    blends = await CustomBlend.filter(creator=user).prefetch_related(
        "base_tea_type", "base_tea", "components__ingredient", "components__tea"
    ).order_by("-created_at")
    
    blends_data = []
    for blend in blends:
        # Получаем компоненты
        components = await BlendComponent.filter(blend=blend).prefetch_related(
            "ingredient", "tea"
        ).order_by("order")
        
        components_data = []
        for comp in components:
            if comp.ingredient:
                components_data.append({
                    "id": comp.ingredient.id,
                    "name": comp.ingredient.name,
                    "weight": float(comp.grams_per_100g),
                    "type": "ingredient"
                })
            elif comp.tea:
                components_data.append({
                    "id": comp.tea.id,
                    "name": comp.tea.name,
                    "weight": float(comp.grams_per_100g),
                    "type": "tea"
                })
        
        blends_data.append({
            "id": blend.id,
            "name": blend.name,
            "description": blend.description,
            "base_tea_type": {
                "id": blend.base_tea_type.id,
                "name": blend.base_tea_type.name,
            } if blend.base_tea_type else None,
            "base_tea": {
                "id": blend.base_tea.id,
                "name": blend.base_tea.name,
                "slug": blend.base_tea.slug,
            } if blend.base_tea else None,
            "components": components_data,
            "price_per_100g": float(blend.price_per_100g) if blend.price_per_100g else None,
            "price_per_20g": float(blend.price_per_20g) if blend.price_per_20g else None,
            "created_at": blend.created_at.isoformat() if blend.created_at else None,
            "rating": blend.rating,
            "review_count": blend.review_count,
        })
    
    return {"blends": blends_data}


@router.post("/api/logout")
async def logout_api():
    """API для выхода"""
    response = JSONResponse(content={"success": True, "message": "Вы успешно вышли"})
    response.delete_cookie(key="access_token", path="/")
    return response

