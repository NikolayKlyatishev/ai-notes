"""
API для аутентификации пользователей.
"""
import os
import sys
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.logger import setup_logger
from backend.core.config import (
    JWT_SECRET_KEY,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    YANDEX_CLIENT_ID,
    YANDEX_CLIENT_SECRET,
    YANDEX_REDIRECT_URI,
    FRONTEND_URL
)

# Настройка логирования
logger = setup_logger("backend.api.auth")

# Создание роутера
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# Инициализация OAuth
oauth = OAuth()

def setup_oauth() -> None:
    """
    Настройка OAuth клиентов для аутентификации.
    """
    # Регистрация Google OAuth клиента
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile",
                "prompt": "select_account",  # Принудительно показывать выбор аккаунта
                "access_type": "offline",    # Получить refresh token для длительного доступа
                "include_granted_scopes": "true"  # Включить ранее предоставленные разрешения
            }
        )
        logger.info("Google OAuth клиент зарегистрирован")
    else:
        logger.warning("Google OAuth клиент не настроен: отсутствуют учетные данные")

    # Регистрация Yandex OAuth клиента
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
        logger.info("Yandex OAuth клиент зарегистрирован")
    else:
        logger.warning("Yandex OAuth клиент не настроен: отсутствуют учетные данные")

# Настройка OAuth при импорте модуля
setup_oauth()

def create_token(user_data: Dict[str, Any]) -> str:
    """
    Создает JWT токен для пользователя.
    
    Args:
        user_data (Dict[str, Any]): Данные пользователя для включения в токен
        
    Returns:
        str: JWT токен
    """
    # Установка срока действия токена (1 день)
    expiration = datetime.utcnow() + timedelta(days=1)
    
    # Создание полезной нагрузки токена
    payload = {
        "sub": user_data.get("id", ""),
        "email": user_data.get("email", ""),
        "name": user_data.get("name", ""),
        "picture": user_data.get("picture", ""),
        "provider": user_data.get("provider", ""),
        "exp": expiration
    }
    
    # Создание JWT токена
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    
    logger.info(f"Создан токен для пользователя {user_data.get('email')}")
    return token

def decode_token(token: str) -> Dict[str, Any]:
    """
    Декодирует JWT токен.
    
    Args:
        token (str): JWT токен для декодирования
        
    Returns:
        Dict[str, Any]: Данные пользователя из токена
        
    Raises:
        HTTPException: Если токен недействителен или истек срок его действия
    """
    try:
        # Декодирование JWT токена
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        
        # Создание объекта с данными пользователя
        user_data = {
            "id": payload.get("sub", ""),
            "email": payload.get("email", ""),
            "name": payload.get("name", ""),
            "picture": payload.get("picture", ""),
            "provider": payload.get("provider", "")
        }
        
        return user_data
    except jwt.ExpiredSignatureError:
        logger.warning("Попытка использования токена с истекшим сроком действия")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек"
        )
    except jwt.InvalidTokenError:
        logger.warning("Попытка использования недействительного токена")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен аутентификации"
        )

async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Получает текущего аутентифицированного пользователя из сессии.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        Dict[str, Any]: Данные текущего пользователя
        
    Raises:
        HTTPException: Если пользователь не аутентифицирован
    """
    # Получение токена из сессии
    token = request.session.get("token")
    
    if not token:
        logger.warning("Попытка доступа без аутентификации")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    
    try:
        # Декодирование токена и получение данных пользователя
        user_data = decode_token(token)
        return user_data
    except HTTPException:
        # Удаление недействительного токена из сессии
        request.session.pop("token", None)
        raise

@router.get("/status")
async def auth_status(request: Request):
    """
    Проверка статуса аутентификации пользователя.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        Dict: Статус аутентификации и данные пользователя (если аутентифицирован)
    """
    token = request.session.get("token")
    if not token:
        return {"authenticated": False}
    
    try:
        user_data = decode_token(token)
        return {
            "authenticated": True,
            "user": user_data
        }
    except Exception:
        request.session.pop("token", None)
        return {"authenticated": False}

@router.get("/login/google")
async def login_google(request: Request):
    """
    Начало процесса аутентификации через Google.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        RedirectResponse: Перенаправление на страницу аутентификации Google
    """
    # Проверка наличия клиента Google
    if "google" not in oauth._clients:
        logger.error("Google OAuth клиент не настроен")
        return {"error": "Аутентификация через Google не настроена"}
    
    logger.info(f"Начало аутентификации через Google. Redirect URI: {GOOGLE_REDIRECT_URI}")
    
    # Перенаправление на страницу аутентификации Google
    redirect_response = await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)
    return redirect_response

@router.get("/callback/google")
async def auth_google(request: Request):
    """
    Завершение процесса аутентификации через Google.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        RedirectResponse: Перенаправление на главную страницу после успешной аутентификации
    """
    try:
        # Получение токена доступа от Google
        token = await oauth.google.authorize_access_token(request)
        logger.debug(f"Получен токен от Google: {token}")
        
        # Получение информации о пользователе
        if 'userinfo' in token:
            user = token['userinfo']
        else:
            # Получение информации через userinfo endpoint
            resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            user = resp.json()
        
        # Создание объекта с данными пользователя
        user_data = {
            "id": user.get("sub", user.get("id", "")),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "picture": user.get("picture", ""),
            "provider": "google"
        }
        
        # Создание JWT токена и сохранение в сессии
        session_token = create_token(user_data)
        request.session["token"] = session_token
        
        logger.info(f"Успешная аутентификация через Google: {user_data['email']}")
        
        # Перенаправление на главную страницу
        return RedirectResponse(url=f"{FRONTEND_URL}/")
    except Exception as e:
        logger.error(f"Ошибка при аутентификации через Google: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=auth_failed")

@router.get("/login/yandex")
async def login_yandex(request: Request):
    """
    Начало процесса аутентификации через Yandex.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        RedirectResponse: Перенаправление на страницу аутентификации Yandex
    """
    # Проверка наличия клиента Yandex
    if "yandex" not in oauth._clients:
        logger.error("Yandex OAuth клиент не настроен")
        return {"error": "Аутентификация через Yandex не настроена"}
    
    logger.info(f"Начало аутентификации через Yandex. Redirect URI: {YANDEX_REDIRECT_URI}")
    
    # Перенаправление на страницу аутентификации Yandex
    return await oauth.yandex.authorize_redirect(request, YANDEX_REDIRECT_URI)

@router.get("/callback/yandex")
async def auth_yandex(request: Request):
    """
    Завершение процесса аутентификации через Yandex.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        RedirectResponse: Перенаправление на главную страницу после успешной аутентификации
    """
    try:
        # Получение токена доступа от Yandex
        token = await oauth.yandex.authorize_access_token(request)
        
        # Получение информации о пользователе
        resp = await oauth.yandex.get("", token=token)
        user_info = resp.json()
        
        # Создание объекта с данными пользователя
        user_data = {
            "id": str(user_info.get("id", "")),
            "email": user_info.get("default_email", ""),
            "name": user_info.get("real_name", user_info.get("display_name", "")),
            "picture": "",  # Yandex не предоставляет аватар напрямую
            "provider": "yandex"
        }
        
        # Создание JWT токена и сохранение в сессии
        session_token = create_token(user_data)
        request.session["token"] = session_token
        
        logger.info(f"Успешная аутентификация через Yandex: {user_data['email']}")
        
        # Перенаправление на главную страницу
        return RedirectResponse(url=f"{FRONTEND_URL}/")
    except Exception as e:
        logger.error(f"Ошибка при аутентификации через Yandex: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=auth_failed")

@router.get("/logout")
async def logout(request: Request):
    """
    Выход пользователя из системы.
    
    Args:
        request (Request): Объект запроса FastAPI
        
    Returns:
        Dict: Сообщение об успешном выходе
    """
    # Удаление токена из сессии
    request.session.pop("token", None)
    
    logger.info("Пользователь вышел из системы")
    
    return {"message": "Выход выполнен успешно"} 