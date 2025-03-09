"""
AI Notes - приложение для аудиозаписи и транскрибации речи.

Основные компоненты:
- recorder: Запись аудио с микрофона
- transcriber: Преобразование аудио в текст
- web: Веб-интерфейс для управления и просмотра записей
- tagging: Анализ и тегирование заметок
- search: Поиск по заметкам
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Версия приложения
__version__ = "0.1.0"

# Экспорт основных компонентов для удобного импорта
from backend.core.config import (
    NOTES_DIR,
    AUDIO_DIR,
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    OPENAI_API_KEY
)
from backend.core.logger import setup_logger, get_logger

# Настройка базового логгера
logger = get_logger("backend") 