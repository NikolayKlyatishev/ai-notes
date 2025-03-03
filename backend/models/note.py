"""
Модели данных для заметок с использованием Pydantic.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Note(BaseModel):
    """Модель данных для заметки."""
    
    date: datetime = Field(..., description="Дата и время создания заметки")
    transcript: str = Field(..., description="Транскрибированный текст")
    tags: List[str] = Field(default_factory=list, description="Теги, извлеченные из текста")
    keyphrases: List[str] = Field(default_factory=list, description="Ключевые фразы из текста")
    speakers: List[str] = Field(default_factory=list, description="Информация о говорящих")
    categories: List[str] = Field(default_factory=list, description="Категории записи")
    purpose: Optional[str] = Field(None, description="Цель разговора")
    topics: List[str] = Field(default_factory=list, description="Основные темы разговора")
    audio_file: Optional[str] = Field(None, description="Путь к аудио-файлу")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "date": "2023-05-15T14:30:00",
                "transcript": "Это пример транскрибированного текста заметки.",
                "tags": ["пример", "заметка", "текст"],
                "keyphrases": ["пример заметки", "транскрибированный текст"],
                "speakers": ["Пользователь"],
                "categories": ["общий"],
                "purpose": "Демонстрация",
                "topics": ["Пример использования"],
                "audio_file": "/path/to/audio.wav"
            }
        }


class NoteCreate(BaseModel):
    """Модель для создания новой заметки."""
    
    transcript: str = Field(..., description="Транскрибированный текст")
    audio_file: Optional[str] = Field(None, description="Путь к аудио-файлу")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "transcript": "Это пример транскрибированного текста для новой заметки.",
                "audio_file": "/path/to/audio.wav"
            }
        }


class NoteUpdate(BaseModel):
    """Модель для обновления существующей заметки."""
    
    transcript: Optional[str] = Field(None, description="Транскрибированный текст")
    tags: Optional[List[str]] = Field(None, description="Теги, извлеченные из текста")
    keyphrases: Optional[List[str]] = Field(None, description="Ключевые фразы из текста")
    speakers: Optional[List[str]] = Field(None, description="Информация о говорящих")
    categories: Optional[List[str]] = Field(None, description="Категории записи")
    purpose: Optional[str] = Field(None, description="Цель разговора")
    topics: Optional[List[str]] = Field(None, description="Основные темы разговора")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "transcript": "Обновленный текст заметки.",
                "tags": ["обновление", "заметка"],
                "purpose": "Редактирование"
            }
        }


class NoteResponse(BaseModel):
    """Модель ответа с заметкой."""
    
    id: str = Field(..., description="Идентификатор заметки (имя файла без расширения)")
    date: datetime = Field(..., description="Дата и время создания заметки")
    transcript: str = Field(..., description="Транскрибированный текст")
    tags: List[str] = Field(default_factory=list, description="Теги, извлеченные из текста")
    keyphrases: List[str] = Field(default_factory=list, description="Ключевые фразы из текста")
    categories: List[str] = Field(default_factory=list, description="Категории записи")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "id": "note_20230515_143000",
                "date": "2023-05-15T14:30:00",
                "transcript": "Это пример транскрибированного текста заметки.",
                "tags": ["пример", "заметка", "текст"],
                "keyphrases": ["пример заметки", "транскрибированный текст"],
                "categories": ["общий"]
            }
        }


class SearchQuery(BaseModel):
    """Модель для поискового запроса."""
    
    query: str = Field(..., description="Поисковый запрос")
    start_date: Optional[datetime] = Field(None, description="Начальная дата для фильтрации")
    end_date: Optional[datetime] = Field(None, description="Конечная дата для фильтрации")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "query": "пример поиска",
                "start_date": "2023-01-01T00:00:00",
                "end_date": "2023-12-31T23:59:59"
            }
        }


class SearchResult(BaseModel):
    """Модель для результата поиска."""
    
    id: str = Field(..., description="Идентификатор заметки")
    date: datetime = Field(..., description="Дата и время создания заметки")
    transcript: str = Field(..., description="Транскрибированный текст или его фрагмент")
    relevance: float = Field(..., description="Релевантность результата поиска")
    tags: List[str] = Field(default_factory=list, description="Теги заметки")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "id": "note_20230515_143000",
                "date": "2023-05-15T14:30:00",
                "transcript": "...фрагмент текста с найденным запросом...",
                "relevance": 0.85,
                "tags": ["пример", "заметка", "текст"]
            }
        }


class SearchResponse(BaseModel):
    """Модель ответа на поисковый запрос."""
    
    query: str = Field(..., description="Исходный поисковый запрос")
    results: List[SearchResult] = Field(default_factory=list, description="Результаты поиска")
    total: int = Field(..., description="Общее количество найденных результатов")
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "query": "пример поиска",
                "results": [
                    {
                        "id": "note_20230515_143000",
                        "date": "2023-05-15T14:30:00",
                        "transcript": "...фрагмент текста с найденным запросом...",
                        "relevance": 0.85,
                        "tags": ["пример", "заметка", "текст"]
                    }
                ],
                "total": 1
            }
        } 