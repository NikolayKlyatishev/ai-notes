"""
REST API для системы автоматической фиксации разговоров AI Notes.
Сервер API для работы с React-фронтендом.
"""
import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.core.logger import setup_logger
from backend.core.config import JWT_SECRET_KEY
from backend.api.auth import router as auth_router, setup_oauth
from backend.api.recorder import router as recorder_router
from backend.api.search import router as search_router
from backend.api.notes import router as notes_router

# Настройка логирования
logger = setup_logger("backend.web.app")

# Настройка разрешенных источников для CORS
# В продакшене необходимо указать реальные домены приложения
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Dev React
    "http://localhost:8000",  # Dev Backend
    "http://localhost:5173",  # Dev React (Vite порт)
    "http://localhost:5174",  # Vite альтернативный порт
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Создание приложения FastAPI для самостоятельного запуска
standalone_app = FastAPI(
    title="AI Notes API", 
    description="REST API для системы автоматической фиксации разговоров",
    version="0.1.0"
)

def add_status_endpoints(app: FastAPI):
    """
    Добавляет статусные эндпоинты к экземпляру FastAPI.
    Используется для экспорта эндпоинтов в главное приложение.
    
    Args:
        app (FastAPI): Экземпляр приложения FastAPI
    """
    # Проверяем, есть ли уже такие маршруты
    routes_paths = [route.path for route in app.routes]
    logger.info(f"Текущие маршруты в приложении: {routes_paths}")
    
    # Вместо проверки добавим маршруты напрямую через функции,
    # которые используются для создания декораторов
    from fastapi.routing import APIRoute
    
    async def get_status():
        """
        Проверка статуса API.
        
        Returns:
            dict: Статус API
        """
        return {
            "status": "ok",
            "version": "0.1.0",
            "api": "AI Notes API"
        }

    async def get_auth_status(request: Request):
        """
        Проверка статуса аутентификации.
        
        Args:
            request (Request): Запрос
            
        Returns:
            dict: Статус аутентификации
        """
        try:
            from backend.api.auth import get_current_user
            user = await get_current_user(request)
            return {
                "authenticated": True,
                "user": user
            }
        except HTTPException:
            return {
                "authenticated": False,
                "user": None
            }
        except Exception as e:
            logger.error(f"Ошибка при проверке аутентификации: {e}")
            return {
                "authenticated": False,
                "user": None,
                "error": "Ошибка сервера аутентификации"
            }

    if "/api/status" not in routes_paths:
        app.add_api_route("/api/status", get_status, methods=["GET"])
        logger.info("Добавлен маршрут /api/status")
    
    if "/api/auth/status" not in routes_paths:
        app.add_api_route("/api/auth/status", get_auth_status, methods=["GET"])
        logger.info("Добавлен маршрут /api/auth/status")

def setup_api_routes(app: FastAPI):
    """
    Настраивает маршруты API для переданного экземпляра FastAPI.
    
    Args:
        app (FastAPI): Экземпляр приложения FastAPI
    """
    # Добавление middleware для сессий
    if "SessionMiddleware" not in [m.__class__.__name__ for m in app.user_middleware]:
        app.add_middleware(
            SessionMiddleware,
            secret_key=JWT_SECRET_KEY,
            max_age=3600,  # 1 час
        )
    
    # Инициализация OAuth
    setup_oauth(app)
    
    # Подключение API-маршрутов
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(recorder_router, prefix="/api/recorder", tags=["recorder"])
    app.include_router(search_router, prefix="/api/search", tags=["search"])
    app.include_router(notes_router, prefix="/api/notes", tags=["notes"])
    
    # Добавляем статусные эндпоинты
    add_status_endpoints(app)

# Настройка для автономной работы
# Добавление middleware для CORS
standalone_app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка маршрутов для автономного приложения
setup_api_routes(standalone_app)

# Точка входа для запуска веб-приложения напрямую
def start_web_app():
    """
    Запуск веб-приложения напрямую через uvicorn
    """
    import uvicorn
    
    try:
        uvicorn.run("backend.web.app:standalone_app", host="0.0.0.0", port=8000, reload=True)
    except OSError as e:
        if "Address already in use" in str(e):
            alt_port = 8001
            logger.info(f"Порт 8000 уже используется. Пробуем порт {alt_port}...")
            uvicorn.run("backend.web.app:standalone_app", host="0.0.0.0", port=alt_port, reload=True)
        else:
            raise

if __name__ == "__main__":
    start_web_app() 