"""
Сервис для работы с заметками: создание, чтение, обновление и удаление.
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.logger import setup_logger
from backend.core.config import NOTES_DIR
from backend.models.note import Note, NoteCreate, NoteUpdate, NoteResponse

# Настройка логирования
logger = setup_logger("backend.services.notes")


class NotesService:
    """Сервис для работы с заметками."""
    
    def __init__(self, notes_dir: str = None):
        """
        Инициализация сервиса заметок.
        
        Args:
            notes_dir (str, optional): Путь к директории с заметками
        """
        self.notes_dir = Path(notes_dir) if notes_dir else Path(NOTES_DIR)
        
        # Создание директории для заметок, если она не существует
        self.notes_dir.mkdir(exist_ok=True)
        
        logger.info(f"Сервис заметок инициализирован. Директория: {self.notes_dir}")
    
    def get_all_notes(self) -> List[NoteResponse]:
        """
        Получение всех заметок.
        
        Returns:
            List[NoteResponse]: Список всех заметок
        """
        notes = []
        
        try:
            # Получение всех JSON-файлов в директории заметок
            json_files = list(self.notes_dir.glob("*.json"))
            
            for file_path in json_files:
                try:
                    # Чтение содержимого файла
                    with open(file_path, 'r', encoding='utf-8') as f:
                        note_data = json.load(f)
                    
                    # Создание объекта Note
                    note = Note(**note_data)
                    
                    # Создание объекта NoteResponse
                    note_response = NoteResponse(
                        id=file_path.stem,
                        date=note.date,
                        transcript=note.transcript,
                        tags=note.tags,
                        keyphrases=note.keyphrases,
                        categories=note.categories
                    )
                    
                    notes.append(note_response)
                except Exception as e:
                    logger.error(f"Ошибка при чтении заметки {file_path}: {e}")
            
            # Сортировка заметок по дате (от новых к старым)
            notes.sort(key=lambda x: x.date, reverse=True)
            
            logger.info(f"Получено {len(notes)} заметок")
            return notes
        except Exception as e:
            logger.error(f"Ошибка при получении заметок: {e}")
            return []
    
    def get_note_by_id(self, note_id: str) -> Optional[Note]:
        """
        Получение заметки по идентификатору.
        
        Args:
            note_id (str): Идентификатор заметки (имя файла без расширения)
            
        Returns:
            Optional[Note]: Объект заметки или None, если заметка не найдена
        """
        try:
            # Формирование пути к файлу заметки
            note_path = self.notes_dir / f"{note_id}.json"
            
            # Проверка существования файла
            if not note_path.exists():
                logger.warning(f"Заметка с идентификатором {note_id} не найдена")
                return None
            
            # Чтение содержимого файла
            with open(note_path, 'r', encoding='utf-8') as f:
                note_data = json.load(f)
            
            # Создание объекта Note
            note = Note(**note_data)
            
            logger.info(f"Заметка с идентификатором {note_id} успешно получена")
            return note
        except Exception as e:
            logger.error(f"Ошибка при получении заметки {note_id}: {e}")
            return None
    
    def create_note(self, note_data: Union[NoteCreate, Dict[str, Any]]) -> Optional[str]:
        """
        Создание новой заметки.
        
        Args:
            note_data (Union[NoteCreate, Dict[str, Any]]): Данные для создания заметки
            
        Returns:
            Optional[str]: Идентификатор созданной заметки или None в случае ошибки
        """
        try:
            # Преобразование словаря в объект NoteCreate, если необходимо
            if isinstance(note_data, dict):
                note_data = NoteCreate(**note_data)
            
            # Создание идентификатора заметки на основе текущей даты и времени
            timestamp = datetime.now()
            note_id = f"note_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Создание полных данных заметки
            note = Note(
                date=timestamp,
                transcript=note_data.transcript,
                audio_file=note_data.audio_file,
                tags=[],
                keyphrases=[],
                speakers=[],
                categories=[],
                purpose=None,
                topics=[]
            )
            
            # Формирование пути к файлу заметки
            note_path = self.notes_dir / f"{note_id}.json"
            
            # Сохранение заметки в файл
            with open(note_path, 'w', encoding='utf-8') as f:
                json.dump(note.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Создана новая заметка с идентификатором {note_id}")
            return note_id
        except Exception as e:
            logger.error(f"Ошибка при создании заметки: {e}")
            return None
    
    def update_note(self, note_id: str, note_data: Union[NoteUpdate, Dict[str, Any]]) -> bool:
        """
        Обновление существующей заметки.
        
        Args:
            note_id (str): Идентификатор заметки
            note_data (Union[NoteUpdate, Dict[str, Any]]): Данные для обновления заметки
            
        Returns:
            bool: True, если заметка успешно обновлена, иначе False
        """
        try:
            # Получение существующей заметки
            existing_note = self.get_note_by_id(note_id)
            
            if not existing_note:
                logger.warning(f"Невозможно обновить заметку: заметка с идентификатором {note_id} не найдена")
                return False
            
            # Преобразование словаря в объект NoteUpdate, если необходимо
            if isinstance(note_data, dict):
                note_data = NoteUpdate(**note_data)
            
            # Обновление полей заметки
            note_dict = existing_note.dict()
            update_data = note_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if value is not None:
                    note_dict[field] = value
            
            # Создание обновленного объекта Note
            updated_note = Note(**note_dict)
            
            # Формирование пути к файлу заметки
            note_path = self.notes_dir / f"{note_id}.json"
            
            # Сохранение обновленной заметки в файл
            with open(note_path, 'w', encoding='utf-8') as f:
                json.dump(updated_note.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Заметка с идентификатором {note_id} успешно обновлена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении заметки {note_id}: {e}")
            return False
    
    def delete_note(self, note_id: str) -> bool:
        """
        Удаление заметки.
        
        Args:
            note_id (str): Идентификатор заметки
            
        Returns:
            bool: True, если заметка успешно удалена, иначе False
        """
        try:
            # Формирование пути к файлу заметки
            note_path = self.notes_dir / f"{note_id}.json"
            
            # Проверка существования файла
            if not note_path.exists():
                logger.warning(f"Невозможно удалить заметку: заметка с идентификатором {note_id} не найдена")
                return False
            
            # Удаление файла
            note_path.unlink()
            
            logger.info(f"Заметка с идентификатором {note_id} успешно удалена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении заметки {note_id}: {e}")
            return False


# Создание экземпляра сервиса для использования в других модулях
notes_service = NotesService()


if __name__ == "__main__":
    # Пример использования
    service = NotesService()
    
    # Получение всех заметок
    all_notes = service.get_all_notes()
    print(f"Всего заметок: {len(all_notes)}")
    
    # Создание новой заметки
    new_note_id = service.create_note({
        "transcript": "Это тестовая заметка для демонстрации работы сервиса.",
        "audio_file": "/path/to/test.wav"
    })
    
    if new_note_id:
        print(f"Создана новая заметка с ID: {new_note_id}")
        
        # Получение созданной заметки
        note = service.get_note_by_id(new_note_id)
        if note:
            print(f"Содержимое заметки: {note.transcript}")
            
            # Обновление заметки
            update_success = service.update_note(new_note_id, {
                "transcript": "Обновленный текст заметки.",
                "tags": ["тест", "демонстрация", "обновление"]
            })
            
            if update_success:
                print("Заметка успешно обновлена")
                
                # Получение обновленной заметки
                updated_note = service.get_note_by_id(new_note_id)
                if updated_note:
                    print(f"Обновленное содержимое: {updated_note.transcript}")
                    print(f"Теги: {updated_note.tags}")
            
            # Удаление заметки
            delete_success = service.delete_note(new_note_id)
            if delete_success:
                print("Заметка успешно удалена")
    else:
        print("Не удалось создать заметку") 