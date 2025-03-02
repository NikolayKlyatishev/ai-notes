"""
Модуль для поиска по сохраненным заметкам.
"""
import os
import json
import logging
from datetime import datetime, timedelta
import re

import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotesSearcher:
    def __init__(self):
        """Инициализация поисковика по заметкам."""
        self.notes_dir = config.NOTES_DIR
        logger.info(f"Инициализирован поиск по директории {self.notes_dir}")
        
    def load_notes(self):
        """Загружает все заметки из директории."""
        notes = []
        try:
            for filename in os.listdir(self.notes_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.notes_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            note_data = json.load(f)
                            note_data['file_path'] = file_path
                            notes.append(note_data)
                    except Exception as e:
                        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
            logger.info(f"Загружено {len(notes)} заметок")
            return notes
        except Exception as e:
            logger.error(f"Ошибка при загрузке заметок: {e}")
            return []
            
    def search_by_keywords(self, keywords, date_from=None, date_to=None):
        """
        Поиск по ключевым словам и диапазону дат.
        
        Args:
            keywords (str): Строка ключевых слов для поиска
            date_from (str): Начальная дата в формате YYYY-MM-DD
            date_to (str): Конечная дата в формате YYYY-MM-DD
            
        Returns:
            list: Список найденных заметок
        """
        notes = self.load_notes()
        if not notes:
            return []
            
        # Подготовка ключевых слов
        if isinstance(keywords, str):
            keywords = keywords.lower().split()
        
        # Фильтрация по дате
        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Неверный формат начальной даты: {date_from}")
                date_from = None
                
        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d")
                # Включаем весь день
                date_to = date_to + timedelta(days=1)
            except ValueError:
                logger.warning(f"Неверный формат конечной даты: {date_to}")
                date_to = None
        
        results = []
        for note in notes:
            # Проверка даты
            note_date = None
            try:
                note_date = datetime.strptime(note['date'], "%Y-%m-%d_%H-%M-%S")
            except (ValueError, KeyError):
                continue
                
            if date_from and note_date < date_from:
                continue
            if date_to and note_date > date_to:
                continue
            
            # Проверка ключевых слов
            if keywords:
                matches = 0
                # Поиск в транскрипте
                transcript = note.get('transcript', '').lower()
                for keyword in keywords:
                    if keyword in transcript:
                        matches += 1
                
                # Поиск в тегах
                tags = [tag.lower() for tag in note.get('tags', [])]
                for keyword in keywords:
                    if keyword in tags:
                        matches += 2  # Теги имеют больший вес
                
                # Добавляем, если есть совпадения
                if matches > 0:
                    note['relevance'] = matches
                    results.append(note)
            else:
                # Если ключевые слова не указаны, включаем все подходящие по дате
                results.append(note)
        
        # Сортировка по релевантности
        results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        logger.info(f"Найдено {len(results)} заметок по запросу")
        return results

    def format_results(self, results):
        """Форматирует результаты поиска для вывода."""
        formatted = []
        for i, note in enumerate(results, 1):
            date_str = note.get('date', 'Дата неизвестна')
            tags = ', '.join(note.get('tags', []))
            transcript = note.get('transcript', '')
            
            # Обрезаем длинный текст
            if len(transcript) > 200:
                transcript = transcript[:197] + '...'
            
            formatted.append(f"Результат #{i}:")
            formatted.append(f"Дата: {date_str}")
            formatted.append(f"Теги: {tags}")
            formatted.append(f"Текст: {transcript}")
            formatted.append(f"Файл: {note.get('file_path')}")
            formatted.append('-' * 50)
            
        return '\n'.join(formatted)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Поиск по заметкам')
    parser.add_argument('--query', '-q', type=str, help='Поисковый запрос')
    parser.add_argument('--date-from', '-f', type=str, help='Начальная дата (YYYY-MM-DD)')
    parser.add_argument('--date-to', '-t', type=str, help='Конечная дата (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    searcher = NotesSearcher()
    results = searcher.search_by_keywords(args.query, args.date_from, args.date_to)
    
    if results:
        print(searcher.format_results(results))
    else:
        print("Ничего не найдено") 