#!/usr/bin/env python3
"""
Файл запуска приложения из корневого каталога.
Запускает бэкенд-сервер, который обслуживает фронтенд.
"""
import os
import sys
import argparse

# Добавляем каталог backend в путь поиска модулей
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.append(backend_dir)

# Импортируем функцию запуска из backend/app.py
from backend.app import main

if __name__ == "__main__":
    # Запускаем приложение
    main() 