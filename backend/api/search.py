"""
API и функциональность для поиска заметок.
"""
import os
import sys
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.logger import setup_logger
from backend.core.config import NOTES_DIR
from backend.models.note import SearchQuery, SearchResult, SearchResponse
from backend.services.notes import notes_service
from backend.api.auth import get_current_user

# Настройка логирования
logger = setup_logger("backend.api.search")

# Создание роутера
router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Результаты не найдены"}},
)


class NotesSearcher:
    """Класс для поиска по заметкам."""
    
    def __init__(self, notes_dir: str = None):
        """
        Инициализация поисковика заметок.
        
        Args:
            notes_dir (str, optional): Путь к директории с заметками
        """
        self.notes_dir = Path(notes_dir) if notes_dir else Path(NOTES_DIR)
        logger.info(f"Поисковик заметок инициализирован. Директория: {self.notes_dir}")
    
    def search(self, query: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Поиск заметок по запросу и диапазону дат.
        
        Args:
            query (str): Поисковый запрос
            start_date (Optional[datetime]): Начальная дата для фильтрации
            end_date (Optional[datetime]): Конечная дата для фильтрации
            
        Returns:
            List[Dict[str, Any]]: Список результатов поиска
        """
        results = []
        
        try:
            # Проверка существования директории с заметками
            if not self.notes_dir.exists():
                logger.warning(f"Директория с заметками не найдена: {self.notes_dir}")
                return []
            
            # Подготовка запроса для поиска
            query = query.lower().strip()
            logger.info(f"Выполнение поиска по запросу: '{query}', диапазон дат: {start_date} - {end_date}")
            
            # Получение всех JSON-файлов в директории заметок
            json_files = list(self.notes_dir.glob("*.json"))
            
            for file_path in json_files:
                try:
                    # Чтение содержимого файла
                    with open(file_path, 'r', encoding='utf-8') as f:
                        note_data = json.load(f)
                    
                    # Проверка даты, если указан диапазон
                    note_date = datetime.fromisoformat(note_data.get('date')) if isinstance(note_data.get('date'), str) else note_data.get('date')
                    
                    if start_date and note_date < start_date:
                        continue
                    
                    if end_date and note_date > end_date:
                        continue
                    
                    # Поиск запроса в тексте заметки
                    transcript = note_data.get('transcript', '').lower()
                    
                    if query in transcript:
                        # Вычисление релевантности (простая метрика - количество вхождений)
                        relevance = transcript.count(query) / len(transcript) * 100
                        
                        # Создание результата поиска
                        result = {
                            'id': file_path.stem,
                            'date': note_date,
                            'transcript': self._get_context(transcript, query),
                            'relevance': relevance,
                            'tags': note_data.get('tags', [])
                        }
                        
                        results.append(result)
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {file_path}: {e}")
            
            # Сортировка результатов по релевантности
            results.sort(key=lambda x: x['relevance'], reverse=True)
            
            logger.info(f"Найдено {len(results)} результатов по запросу '{query}'")
            return results
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return []
    
    def _get_context(self, text: str, query: str, context_size: int = 100) -> str:
        """
        Получение контекста вокруг найденного запроса.
        
        Args:
            text (str): Полный текст
            query (str): Поисковый запрос
            context_size (int): Размер контекста в символах
            
        Returns:
            str: Текст с контекстом вокруг запроса
        """
        # Поиск первого вхождения запроса
        index = text.find(query)
        
        if index == -1:
            return text[:200] + "..."
        
        # Определение начала и конца контекста
        start = max(0, index - context_size)
        end = min(len(text), index + len(query) + context_size)
        
        # Формирование контекста
        context = text[start:end]
        
        # Добавление многоточий, если контекст обрезан
        if start > 0:
            context = "..." + context
        
        if end < len(text):
            context = context + "..."
        
        return context


# Создание экземпляра поисковика
searcher = NotesSearcher()


@router.post("/", response_model=SearchResponse)
async def search_notes(query: SearchQuery, current_user: dict = Depends(get_current_user)):
    """
    Поиск заметок по запросу и диапазону дат.
    
    Args:
        query (SearchQuery): Параметры поиска
        current_user (dict): Информация о текущем пользователе
        
    Returns:
        SearchResponse: Результаты поиска
    """
    logger.info(f"Запрос на поиск от пользователя {current_user.get('email')}: '{query.query}'")
    
    try:
        # Выполнение поиска
        results = searcher.search(query.query, query.start_date, query.end_date)
        
        # Преобразование результатов в модель SearchResult
        search_results = [
            SearchResult(
                id=result['id'],
                date=result['date'],
                transcript=result['transcript'],
                relevance=result['relevance'],
                tags=result['tags']
            )
            for result in results
        ]
        
        # Создание ответа
        response = SearchResponse(
            query=query.query,
            results=search_results,
            total=len(search_results)
        )
        
        logger.info(f"Поиск выполнен успешно. Найдено {len(search_results)} результатов.")
        return response
    except Exception as e:
        logger.error(f"Ошибка при выполнении поиска: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выполнении поиска"
        ) 