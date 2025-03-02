"""
Модуль конфигурации для системы автоматической фиксации разговоров.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent
NOTES_DIR = BASE_DIR / "notes"
AUDIO_DIR = BASE_DIR / "audio"

# Создание директорий, если они не существуют
NOTES_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# Параметры аудиозаписи
SAMPLE_RATE = 16000  # Частота дискретизации в Гц
CHANNELS = 1  # Моно запись
SILENCE_THRESHOLD = 2 * 60  # Секунды тишины для остановки записи
FRAME_DURATION_MS = 30  # Длительность фрейма для VAD в миллисекундах
VAD_AGGRESSIVENESS = 3  # Агрессивность VAD (0-3, где 3 - наиболее агрессивный)

# Параметры Whisper
WHISPER_MODEL = "medium"  # Используем medium вместо large-v3 для баланса скорости/качества
WHISPER_LANGUAGE = "ru"  # Явное указание языка для улучшения точности

# API ключ OpenAI, замените на свой или используйте переменную окружения
# OPENAI_API_KEY = "your-api-key"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Формат заметки
NOTE_TEMPLATE = {
    "date": None,
    "transcript": "",
    "tags": [],
    "keyphrases": [],  # Отдельное поле для ключевых фраз
    "speakers": [],    # Информация о говорящих
    "categories": [],  # Категории записи (бизнес, технический, образовательный)
    "purpose": "",     # Цель разговора (брейнсторм, обсуждение проблемы, планирование)
    "topics": []       # Основные темы разговора
} 