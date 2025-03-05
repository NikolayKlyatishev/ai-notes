#!/usr/bin/env python3
"""
Файл запуска бэкенд-приложения.
Запускает бэкенд-сервер, который обслуживает API.
"""
import os
import sys
import argparse
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse

# Создаем экземпляр FastAPI
app = FastAPI(
    title="AI Notes API",
    description="API для системы автоматической фиксации разговоров",
    version="0.1.0"
)

# Настройка разрешенных источников для CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Dev React (стандартный порт)
    "http://localhost:8000",  # Dev Backend
    "http://localhost:5173",  # Dev React (Vite порт)
    "http://localhost:5174",  # Vite альтернативный порт
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Добавление middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавление middleware для сессий
from backend.core.config import JWT_SECRET_KEY
app.add_middleware(
    SessionMiddleware,
    secret_key=JWT_SECRET_KEY,
    max_age=3600,  # 1 час
)

# Корневой маршрут перенаправляет на /docs
@app.get("/")
async def root():
    """
    Корневой маршрут перенаправляет на документацию API.
    """
    return RedirectResponse(url="/docs")

# Маршрут проверки работоспособности
@app.get("/api/health")
async def health_check():
    """
    Проверка работоспособности API.
    """
    return {"status": "ok", "message": "API работает"}

# Маршрут для проверки статуса API
@app.get("/api/status")
async def api_status():
    """
    Возвращает информацию о статусе API.
    """
    return {
        "status": "ok",
        "version": app.version,
        "name": app.title,
    }

# Маршрут для проверки статуса аутентификации
@app.get("/api/auth/status")
async def auth_status(request: Request):
    """
    Проверка статуса аутентификации пользователя.
    """
    token = request.session.get("token")
    if not token:
        return {"authenticated": False}
    
    try:
        from backend.api.auth import decode_token
        user_data = decode_token(token)
        return {
            "authenticated": True,
            "user": user_data
        }
    except Exception:
        request.session.pop("token", None)
        return {"authenticated": False}

# Маршруты OAuth для Google
@app.get("/api/auth/login/google")
async def api_login_google(request: Request):
    """
    Начало процесса аутентификации через Google.
    """
    from backend.api.auth import oauth
    print(f"OAuth clients: {oauth._clients}")
    print(f"OAuth clients keys: {list(oauth._clients.keys())}")
    print(f"OAuth clients values: {list(oauth._clients.values())}")
    
    # Проверяем, что клиент Google существует
    if "google" not in oauth._clients:
        # Пробуем инициализировать клиент Google напрямую
        from backend.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            oauth.register(
                name="google",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"}
            )
            print(f"Google OAuth клиент зарегистрирован напрямую: {oauth._clients}")
        else:
            return {"error": "Аутентификация через Google не настроена"}
    
    redirect_uri = f"http://localhost:8080/api/auth/auth/google"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/api/auth/auth/google")
async def api_auth_google(request: Request):
    """
    Завершение процесса аутентификации через Google.
    """
    from backend.api.auth import oauth, create_token
    try:
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.parse_id_token(request, token)
        
        # Сохраняем информацию о пользователе в сессии
        user_data = {
            "id": user.get("sub", ""),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "picture": user.get("picture", ""),
            "provider": "google"
        }
        
        session_token = create_token(user_data)
        request.session["token"] = session_token
        
        # Редирект на главную страницу после успешной аутентификации
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/")
    except Exception as e:
        print(f"Google OAuth ошибка: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/login?error=auth_failed")

# Маршруты OAuth для Yandex
@app.get("/api/auth/login/yandex")
async def api_login_yandex(request: Request):
    """
    Начало процесса аутентификации через Yandex.
    """
    from backend.api.auth import oauth
    print(f"OAuth clients: {oauth._clients}")
    
    # Проверяем, что клиент Yandex существует
    if "yandex" not in oauth._clients:
        # Пробуем инициализировать клиент Yandex напрямую
        from backend.core.config import YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET
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
            print(f"Yandex OAuth клиент зарегистрирован напрямую: {oauth._clients}")
        else:
            return {"error": "Аутентификация через Yandex не настроена"}
    
    redirect_uri = f"http://localhost:8080/api/auth/auth/yandex"
    return await oauth.yandex.authorize_redirect(request, redirect_uri)

@app.get("/api/auth/auth/yandex")
async def api_auth_yandex(request: Request):
    """
    Завершение процесса аутентификации через Yandex.
    """
    from backend.api.auth import oauth, create_token
    try:
        token = await oauth.yandex.authorize_access_token(request)
        resp = await oauth.yandex.get("", token=token)
        user_info = resp.json()
        
        # Сохраняем информацию о пользователе в сессии
        user_data = {
            "id": str(user_info.get("id", "")),
            "email": user_info.get("default_email", ""),
            "name": user_info.get("real_name", user_info.get("display_name", "")),
            "picture": "",  # Yandex не предоставляет аватар напрямую
            "provider": "yandex"
        }
        
        session_token = create_token(user_data)
        request.session["token"] = session_token
        
        # Редирект на главную страницу после успешной аутентификации
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/")
    except Exception as e:
        print(f"Yandex OAuth ошибка: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/login?error=auth_failed")

def init_api_routes():
    """
    Инициализирует и подключает все API маршруты
    """
    try:
        # Импорт необходимых модулей
        from backend.core.config import JWT_SECRET_KEY
        from backend.api.auth import router as auth_router, setup_oauth
        from backend.api.recorder import router as recorder_router
        from backend.api.search import router as search_router
        from backend.api.notes import router as notes_router
        
        # Добавление middleware для сессий если еще не добавлен
        if "SessionMiddleware" not in [m.__class__.__name__ for m in app.user_middleware]:
            app.add_middleware(
                SessionMiddleware,
                secret_key=JWT_SECRET_KEY,
                max_age=3600,  # 1 час
            )
        
        # Инициализация OAuth
        setup_oauth(app)
        
        # Подключение API-маршрутов
        app.include_router(recorder_router, prefix="/api/recorder", tags=["recorder"])
        app.include_router(search_router, prefix="/api/search", tags=["search"])
        app.include_router(notes_router, prefix="/api/notes", tags=["notes"])
        
        print("API маршруты успешно инициализированы")
    except ImportError as e:
        print(f"Ошибка при инициализации API маршрутов: {e}")
        # Продолжаем работу с базовыми маршрутами

def main():
    """
    Основная функция запуска приложения
    """
    parser = argparse.ArgumentParser(description="Запуск бэкенд-сервера AI Notes")
    parser.add_argument("--api", action="store_true", help="Запустить только API-сервер")
    parser.add_argument("--port", type=int, default=8080, help="Порт для запуска API-сервера")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Хост для запуска API-сервера")
    args = parser.parse_args()
    
    print("Запуск бэкенд-сервера в режиме API" if args.api else "Запуск полного бэкенд-сервера")
    
    # Обработка ошибки с whisper
    try:
        import whisper
    except ImportError:
        print("Ошибка импорта локального whisper: No module named 'whisper'")
        print("Функции транскрипции будут недоступны")
    
    # Инициализация маршрутов API
    init_api_routes()
    
    try:
        # Запускаем uvicorn сервер
        uvicorn.run(
            "backend.app:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )
    except OSError as e:
        if "Address already in use" in str(e):
            alt_port = args.port + 1
            print(f"Порт {args.port} уже используется. Пробуем порт {alt_port}...")
            uvicorn.run(
                "backend.app:app",
                host=args.host,
                port=alt_port,
                reload=True,
                log_level="info"
            )
        else:
            raise

if __name__ == "__main__":
    # Запускаем приложение
    main() 