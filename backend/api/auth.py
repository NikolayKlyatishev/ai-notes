"""
Модуль аутентификации для API.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI, APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import jwt
from authlib.integrations.starlette_client import OAuth

from backend.core.logger import setup_logger
from backend.core.config import (
    JWT_SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET
)

# Настройка логирования
logger = setup_logger("backend.api.auth")

# Создаем роутер
router = APIRouter()

# Настройки JWT токена
TOKEN_EXPIRE_DAYS = 7  # Срок действия токена в днях


def create_token(data: Dict[str, Any]) -> str:
    """
    Создание JWT токена.
    
    Args:
        data (Dict[str, Any]): Данные для включения в токен
        
    Returns:
        str: JWT токен
    """
    expiration = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = data.copy()
    payload.update({"exp": expiration})
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    
    logger.info(f"Создан токен для пользователя {data.get('email')}")
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Декодирование JWT токена.
    
    Args:
        token (str): JWT токен
        
    Returns:
        Dict[str, Any]: Данные из токена
        
    Raises:
        HTTPException: Если токен недействителен или истек срок его действия
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Попытка использования токена с истекшим сроком действия")
        raise HTTPException(status_code=401, detail="Срок действия токена истек")
    except jwt.InvalidTokenError:
        logger.warning("Попытка использования недействительного токена")
        raise HTTPException(status_code=401, detail="Недействительный токен")


async def login_required(request: Request) -> Dict[str, Any]:
    """
    Проверка аутентификации пользователя.
    
    Args:
        request (Request): Запрос
        
    Returns:
        Dict[str, Any]: Данные пользователя
        
    Raises:
        HTTPException: Если пользователь не аутентифицирован
    """
    # Проверка наличия токена в сессии
    token = request.session.get("token")
    
    if not token:
        logger.warning("Попытка доступа без токена в сессии")
        raise HTTPException(status_code=401, detail="Требуется аутентификация")
    
    try:
        # Декодирование токена
        user_data = decode_token(token)
        return user_data
    except HTTPException as e:
        logger.warning(f"Ошибка аутентификации: {e.detail}")
        # Удаляем недействительный токен из сессии
        request.session.pop("token", None)
        raise


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Получение данных текущего аутентифицированного пользователя.
    Функция-синоним для login_required для обратной совместимости.
    
    Args:
        request (Request): Запрос
        
    Returns:
        Dict[str, Any]: Данные пользователя
        
    Raises:
        HTTPException: Если пользователь не аутентифицирован
    """
    return await login_required(request)


# Инициализация OAuth
oauth = OAuth()


def setup_oauth(app: FastAPI) -> None:
    """
    Настройка OAuth аутентификации.
    
    Args:
        app (FastAPI): Приложение FastAPI
    """
    print(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")
    print(f"GOOGLE_CLIENT_SECRET: {GOOGLE_CLIENT_SECRET}")
    
    # Настройка Google OAuth
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"}
        )
        logger.info("Настроена аутентификация через Google")
        print(f"Google OAuth клиент зарегистрирован: {oauth._clients}")
    else:
        logger.warning("Отсутствуют учетные данные для Google OAuth")
        print("Отсутствуют учетные данные для Google OAuth")
    
    # Настройка Yandex OAuth
    if YANDEX_CLIENT_ID and YANDEX_CLIENT_SECRET:
        oauth.register(
            name="yandex",
            client_id=YANDEX_CLIENT_ID,
            client_secret=YANDEX_CLIENT_SECRET,
            authorize_url="https://oauth.yandex.ru/authorize",
            access_token_url="https://oauth.yandex.ru/token",
            api_base_url="https://login.yandex.ru/info",
            client_kwargs={"scope": "login:email login:info"}
        )
        logger.info("Настроена аутентификация через Yandex")
    else:
        logger.warning("Отсутствуют учетные данные для Yandex OAuth")
    
    # Регистрация маршрутов для аутентификации
    app.include_router(router, prefix="/auth", tags=["auth"])


# Маршруты для аутентификации
@router.get("/login/google")
async def login_google(request: Request):
    """
    Начало процесса аутентификации через Google.
    """
    if "google" not in oauth._clients:
        logger.error("Аутентификация через Google не настроена")
        return JSONResponse(
            status_code=503,
            content={"error": "Аутентификация через Google не настроена"}
        )
    
    redirect_uri = request.url_for("auth_google")
    logger.info(f"Google OAuth redirect URI: {redirect_uri}")
    
    # Исправляем URL обратного вызова, чтобы использовать правильный путь
    redirect_uri = str(redirect_uri).replace("/auth/", "/api/auth/")
    logger.info(f"Corrected Google OAuth redirect URI: {redirect_uri}")
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google")
async def auth_google(request: Request):
    """
    Завершение процесса аутентификации через Google.
    """
    try:
        logger.info(f"Получен обратный вызов от Google: {request.url}")
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.parse_id_token(request, token)
        
        # Создание JWT токена
        jwt_token = create_token({
            "email": user["email"],
            "name": user.get("name", ""),
            "picture": user.get("picture", ""),
            "provider": "google"
        })
        
        # Сохранение токена в сессии
        request.session["token"] = jwt_token
        
        logger.info(f"Успешная аутентификация через Google: {user['email']}")
        
        # Перенаправление на главную страницу
        return RedirectResponse(url="/")
    except Exception as e:
        logger.error(f"Ошибка при аутентификации через Google: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Ошибка при аутентификации через Google: {str(e)}"}
        )


@router.get("/login/yandex")
async def login_yandex(request: Request):
    """
    Начало процесса аутентификации через Yandex.
    """
    if "yandex" not in oauth._clients:
        logger.error("Аутентификация через Yandex не настроена")
        return JSONResponse(
            status_code=503,
            content={"error": "Аутентификация через Yandex не настроена"}
        )
    
    redirect_uri = request.url_for("auth_yandex")
    logger.info(f"Yandex OAuth redirect URI: {redirect_uri}")
    
    # Исправляем URL обратного вызова, чтобы использовать правильный путь
    redirect_uri = str(redirect_uri).replace("/auth/", "/api/auth/")
    logger.info(f"Corrected Yandex OAuth redirect URI: {redirect_uri}")
    
    return await oauth.yandex.authorize_redirect(request, redirect_uri)


@router.get("/auth/yandex")
async def auth_yandex(request: Request):
    """
    Завершение процесса аутентификации через Yandex.
    """
    try:
        logger.info(f"Получен обратный вызов от Yandex: {request.url}")
        token = await oauth.yandex.authorize_access_token(request)
        
        # Получение информации о пользователе
        resp = await oauth.yandex.get("", token=token)
        user_info = resp.json()
        
        # Создание JWT токена
        jwt_token = create_token({
            "email": user_info.get("default_email", ""),
            "name": user_info.get("real_name", ""),
            "picture": user_info.get("default_avatar_id", ""),
            "provider": "yandex"
        })
        
        # Сохранение токена в сессии
        request.session["token"] = jwt_token
        
        logger.info(f"Успешная аутентификация через Yandex: {user_info.get('default_email', '')}")
        
        # Перенаправление на главную страницу
        return RedirectResponse(url="/")
    except Exception as e:
        logger.error(f"Ошибка при аутентификации через Yandex: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Ошибка при аутентификации через Yandex: {str(e)}"}
        )


@router.get("/logout")
async def logout(request: Request):
    """
    Выход из системы.
    """
    # Удаление токена из сессии
    request.session.pop("token", None)
    
    logger.info("Пользователь вышел из системы")
    
    # Перенаправление на страницу логина
    return RedirectResponse(url="/")


@router.get("/me")
async def get_me(user: Dict[str, Any] = Depends(login_required)):
    """
    Получение информации о текущем пользователе.
    """
    return user 