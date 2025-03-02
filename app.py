#!/usr/bin/env python3
"""
Файл запуска приложения из корневого каталога.
Запускает бэкенд-сервер, который обслуживает фронтенд.
"""
import os
import sys

# Добавляем каталог backend в путь поиска модулей
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.append(backend_dir)

# Импортируем функцию запуска из web_app.py
from web_app import run_web_app

if __name__ == "__main__":
    # Запускаем веб-приложение
    run_web_app(host="0.0.0.0", port=8000) 