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
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# Создание приложения FastAPI
app = FastAPI(
    title="AI Notes API", 
    description="REST API для системы автоматической фиксации разговоров",
    version="0.1.0"
)

# Добавление middleware для сессий
app.add_middleware(
    SessionMiddleware,
    secret_key=JWT_SECRET_KEY,
    max_age=3600,  # 1 час
)

# Добавление middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация OAuth
setup_oauth(app)

# Подключение API-маршрутов
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(recorder_router, prefix="/api/recorder", tags=["recorder"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(notes_router, prefix="/api/notes", tags=["notes"])

@app.get("/api/status")
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

@app.get("/api/auth/status")
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