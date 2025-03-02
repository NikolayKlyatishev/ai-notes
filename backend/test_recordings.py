#!/usr/bin/env python
"""
Тестовый скрипт для проверки функции get_recordings
"""
import json
import os
import sys
import logging
import glob
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Определяем пути к директориям
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(SCRIPT_DIR, "audio")
NOTES_DIR = os.path.join(SCRIPT_DIR, "notes")

def get_recordings_test(limit: int = 10):
    """Упрощенная версия функции get_recordings для тестирования"""
    # Создаем директории, если они не существуют
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(NOTES_DIR, exist_ok=True)
    
    # Получаем список WAV файлов, отсортированных по времени изменения (новые вначале)
    wav_files = sorted(
        glob.glob(os.path.join(AUDIO_DIR, "*.wav")),
        key=os.path.getmtime,
        reverse=True
    )[:limit]
    
    recordings = []
    
    for wav_file in wav_files:
        base_name = os.path.basename(wav_file)
        file_name_without_ext = os.path.splitext(base_name)[0]
        
        # Ищем соответствующий JSON файл
        json_file = os.path.join(NOTES_DIR, f"{file_name_without_ext}.json")
        has_transcript = os.path.exists(json_file)
        
        # Получаем размер файла и время создания
        file_size = os.path.getsize(wav_file) / (1024 * 1024)  # В МБ
        file_time = datetime.fromtimestamp(os.path.getmtime(wav_file))
        
        # Получаем текст транскрипции и метаданные, если есть
        transcript_text = ""
        tags = []
        categories = []
        purpose = ""
        topics = []
        
        if has_transcript:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    note_data = json.load(f)
                    transcript_text = note_data.get('transcript', '')[:100] + '...' if len(note_data.get('transcript', '')) > 100 else note_data.get('transcript', '')
                    
                    # Получаем теги и метаданные
                    tags = note_data.get('tags', [])
                    categories = note_data.get('categories', [])
                    purpose = note_data.get('purpose', '')
                    topics = note_data.get('topics', [])
            except Exception as e:
                logger.error(f"Ошибка при чтении транскрипта {json_file}: {e}")
        
        # Добавляем информацию о записи
        recordings.append({
            "audio_file": base_name,
            "created_at": file_time.isoformat(),
            "size_mb": round(file_size, 2),
            "has_transcript": has_transcript,
            "transcript_file": os.path.basename(json_file) if has_transcript else None,
            "transcript_text": transcript_text if has_transcript else "",
            "type": "audio",
            "tags": tags,
            "categories": categories,
            "purpose": purpose,
            "topics": topics
        })
    
    return {"recordings": recordings}

def test_get_recordings():
    """Тестирует функцию get_recordings и выводит результаты"""
    logger.info("Получение списка записей...")
    result = get_recordings_test(limit=5)
    
    if not result or "recordings" not in result:
        logger.error("Ошибка: Функция get_recordings вернула некорректные данные")
        return
    
    recordings = result["recordings"]
    logger.info(f"Найдено {len(recordings)} записей")
    
    # Выводим информацию о каждой записи
    for i, recording in enumerate(recordings):
        logger.info(f"\nЗапись #{i+1}: {recording.get('audio_file', 'Неизвестно')}")
        logger.info(f"  Дата создания: {recording.get('created_at', 'Неизвестно')}")
        logger.info(f"  Размер: {recording.get('size_mb', 0)} МБ")
        logger.info(f"  Транскрибирован: {recording.get('has_transcript', False)}")
        
        # Проверяем наличие тегов и метаданных
        if recording.get('has_transcript', False):
            logger.info(f"  Транскрипт: {recording.get('transcript_text', '')[:50]}...")
            
            # Проверяем теги
            tags = recording.get('tags', [])
            if tags:
                logger.info(f"  Теги: {', '.join(tags)}")
            else:
                logger.info("  Теги: Отсутствуют")
            
            # Проверяем категории
            categories = recording.get('categories', [])
            if categories:
                logger.info(f"  Категории: {', '.join(categories)}")
            else:
                logger.info("  Категории: Отсутствуют")
            
            # Проверяем назначение
            purpose = recording.get('purpose', '')
            if purpose:
                logger.info(f"  Назначение: {purpose}")
            else:
                logger.info("  Назначение: Не определено")
            
            # Проверяем темы
            topics = recording.get('topics', [])
            if topics:
                logger.info(f"  Темы: {', '.join(topics)}")
            else:
                logger.info("  Темы: Отсутствуют")
        else:
            logger.info("  Нет транскрипции и метаданных")
    
    # Выводим полные данные первой записи для отладки
    if recordings:
        logger.info("\nПолные данные первой записи:")
        logger.info(json.dumps(recordings[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_get_recordings() 