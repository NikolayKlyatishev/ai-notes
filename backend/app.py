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

# Импорты из проекта
from backend.core.config import (
    JWT_SECRET_KEY, 
    WEB_HOST, 
    WEB_PORT, 
    ALLOWED_ORIGINS
)
from backend.core.logger import setup_logger
from backend.api import auth, notes, search, recorder

# Настройка логирования
logger = setup_logger("backend.app")

def create_app() -> FastAPI:
    """
    Создает и настраивает экземпляр FastAPI приложения.
    
    Returns:
        FastAPI: Настроенное приложение FastAPI
    """
    # Создаем экземпляр FastAPI
    app = FastAPI(
        title="AI Notes API",
        description="API для системы автоматической фиксации разговоров",
        version="0.1.0"
    )

    # Добавление middleware для CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Добавление middleware для сессий
    app.add_middleware(
        SessionMiddleware,
        secret_key=JWT_SECRET_KEY,
        max_age=3600,  # 1 час
    )
    
    # Регистрация маршрутов
    register_routes(app)
    
    return app

def register_routes(app: FastAPI) -> None:
    """
    Регистрирует все маршруты API в приложении.
    
    Args:
        app (FastAPI): Экземпляр FastAPI приложения
    """
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
    
    # Регистрация маршрутов из модулей API
    app.include_router(auth.router, prefix="/api")
    app.include_router(notes.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(recorder.router, prefix="/api")
    
    logger.info("Все маршруты API зарегистрированы")

# Создание экземпляра приложения
app = create_app()

def main():
    """
    Основная функция для запуска сервера.
    """
    parser = argparse.ArgumentParser(description="Запуск бэкенд-сервера AI Notes")
    parser.add_argument("--host", type=str, default=WEB_HOST, help="Хост для запуска сервера")
    parser.add_argument("--port", type=int, default=WEB_PORT, help="Порт для запуска сервера")
    parser.add_argument("--reload", action="store_true", help="Включить автоматическую перезагрузку")
    
    args = parser.parse_args()
    
    logger.info(f"Запуск сервера на {args.host}:{args.port}")
    
    uvicorn.run(
        "backend.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main() 