#!/usr/bin/env python
"""
Этот скрипт обновляет теги во всех существующих транскрипциях,
добавляя новые категории, классификации и темы с использованием
улучшенной системы тегирования.
"""
import os
import json
import argparse
import logging
from typing import List, Dict, Any

from tagging import generate_tags

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_notes_dir() -> str:
    """Возвращает путь к директории с записями."""
    # Импортируем локально, чтобы избежать циклических импортов
    import config
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                       config.NOTES_DIR if hasattr(config, 'NOTES_DIR') else "notes")

def get_all_transcriptions() -> List[str]:
    """Получает список всех файлов транскрипций."""
    notes_dir = get_notes_dir()
    if not os.path.exists(notes_dir):
        logger.warning(f"Директория с записями не найдена: {notes_dir}")
        return []
    
    # Ищем все JSON файлы в директории с записями
    transcriptions = []
    for root, _, files in os.walk(notes_dir):
        for file in files:
            if file.endswith('.json'):
                transcriptions.append(os.path.join(root, file))
    
    logger.info(f"Найдено {len(transcriptions)} файлов транскрипций")
    return transcriptions

def update_transcription_tags(file_path: str, force: bool = False) -> bool:
    """
    Обновляет теги в файле транскрипции.
    
    Args:
        file_path (str): Путь к файлу транскрипции
        force (bool): Принудительно обновить все теги, даже если они уже существуют
        
    Returns:
        bool: True, если теги были обновлены, False в противном случае
    """
    try:
        # Читаем файл транскрипции
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Получаем текст транскрипции
        text = data.get('transcript', data.get('text', ''))
        if not text:
            logger.warning(f"Пустой текст в файле: {file_path}")
            return False
        
        # Проверяем, нужно ли обновлять теги
        should_update = force or (
            'categories' not in data or 
            'topics' not in data or 
            'purpose' not in data
        )
        
        if not should_update:
            logger.info(f"Теги в файле {file_path} уже актуальны, пропускаем")
            return False
        
        # Генерируем новые теги
        logger.info(f"Обновляем теги в файле: {file_path}")
        tags_data = generate_tags(text, classify=True)
        
        # Обновляем данные транскрипции
        data["tags"] = tags_data["keywords"]
        data["keyphrases"] = tags_data["keyphrases"]
        data["categories"] = tags_data["categories"]
        data["topics"] = tags_data["topics"]
        data["purpose"] = tags_data["purpose"]
        data["purpose_details"] = tags_data["purpose_details"]
        
        # Сохраняем обновленные данные
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Теги успешно обновлены в файле: {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении тегов в файле {file_path}: {e}")
        return False

def update_all_transcriptions(force: bool = False) -> Dict[str, Any]:
    """
    Обновляет теги во всех файлах транскрипций.
    
    Args:
        force (bool): Принудительно обновить все теги, даже если они уже существуют
        
    Returns:
        Dict[str, Any]: Статистика процесса обновления
    """
    # Получаем список всех транскрипций
    transcriptions = get_all_transcriptions()
    
    # Статистика обновления
    stats = {
        "total": len(transcriptions),
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    # Обрабатываем каждую транскрипцию
    for file_path in transcriptions:
        try:
            updated = update_transcription_tags(file_path, force)
            if updated:
                stats["updated"] += 1
            else:
                stats["skipped"] += 1
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_path}: {e}")
            stats["errors"] += 1
    
    # Выводим статистику
    logger.info(f"Обновление завершено. "
                f"Всего: {stats['total']}, "
                f"Обновлено: {stats['updated']}, "
                f"Пропущено: {stats['skipped']}, "
                f"Ошибок: {stats['errors']}")
    
    return stats

if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Обновление тегов во всех транскрипциях")
    parser.add_argument("--force", action="store_true", help="Принудительно обновить все теги")
    args = parser.parse_args()
    
    # Запускаем обновление
    update_all_transcriptions(force=args.force) 