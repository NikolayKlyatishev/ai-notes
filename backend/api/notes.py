"""
API для работы с заметками.
"""
import os
import sys
import logging
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.logger import setup_logger
from backend.models.note import NoteCreate, NoteUpdate, NoteResponse
from backend.services.notes import notes_service
from backend.api.auth import get_current_user

# Настройка логирования
logger = setup_logger("backend.api.notes")

# Создание роутера
router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={404: {"description": "Заметка не найдена"}},
)


@router.get("/", response_model=List[NoteResponse])
async def get_notes(current_user: dict = Depends(get_current_user)):
    """
    Получение списка всех заметок.
    
    Args:
        current_user (dict): Информация о текущем пользователе
        
    Returns:
        List[NoteResponse]: Список всех заметок
    """
    logger.info(f"Запрос на получение всех заметок от пользователя {current_user.get('email')}")
    
    try:
        notes = notes_service.get_all_notes()
        return notes
    except Exception as e:
        logger.error(f"Ошибка при получении заметок: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении заметок"
        )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str, current_user: dict = Depends(get_current_user)):
    """
    Получение заметки по идентификатору.
    
    Args:
        note_id (str): Идентификатор заметки
        current_user (dict): Информация о текущем пользователе
        
    Returns:
        NoteResponse: Заметка
    """
    logger.info(f"Запрос на получение заметки {note_id} от пользователя {current_user.get('email')}")
    
    try:
        note = notes_service.get_note_by_id(note_id)
        
        if not note:
            logger.warning(f"Заметка с идентификатором {note_id} не найдена")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заметка с идентификатором {note_id} не найдена"
            )
        
        # Создание объекта NoteResponse
        note_response = NoteResponse(
            id=note_id,
            date=note.date,
            transcript=note.transcript,
            tags=note.tags,
            keyphrases=note.keyphrases,
            categories=note.categories
        )
        
        return note_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении заметки {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении заметки {note_id}"
        )


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate, current_user: dict = Depends(get_current_user)):
    """
    Создание новой заметки.
    
    Args:
        note (NoteCreate): Данные для создания заметки
        current_user (dict): Информация о текущем пользователе
        
    Returns:
        dict: Идентификатор созданной заметки
    """
    logger.info(f"Запрос на создание заметки от пользователя {current_user.get('email')}")
    
    try:
        note_id = notes_service.create_note(note)
        
        if not note_id:
            logger.error("Не удалось создать заметку")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось создать заметку"
            )
        
        logger.info(f"Заметка успешно создана с идентификатором {note_id}")
        return {"id": note_id, "message": "Заметка успешно создана"}
    except Exception as e:
        logger.error(f"Ошибка при создании заметки: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании заметки"
        )


@router.put("/{note_id}", response_model=dict)
async def update_note(note_id: str, note: NoteUpdate, current_user: dict = Depends(get_current_user)):
    """
    Обновление существующей заметки.
    
    Args:
        note_id (str): Идентификатор заметки
        note (NoteUpdate): Данные для обновления заметки
        current_user (dict): Информация о текущем пользователе
        
    Returns:
        dict: Сообщение об успешном обновлении
    """
    logger.info(f"Запрос на обновление заметки {note_id} от пользователя {current_user.get('email')}")
    
    try:
        # Проверка существования заметки
        existing_note = notes_service.get_note_by_id(note_id)
        
        if not existing_note:
            logger.warning(f"Заметка с идентификатором {note_id} не найдена")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заметка с идентификатором {note_id} не найдена"
            )
        
        # Обновление заметки
        success = notes_service.update_note(note_id, note)
        
        if not success:
            logger.error(f"Не удалось обновить заметку {note_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось обновить заметку {note_id}"
            )
        
        logger.info(f"Заметка {note_id} успешно обновлена")
        return {"message": f"Заметка {note_id} успешно обновлена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении заметки {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении заметки {note_id}"
        )


@router.delete("/{note_id}", response_model=dict)
async def delete_note(note_id: str, current_user: dict = Depends(get_current_user)):
    """
    Удаление заметки.
    
    Args:
        note_id (str): Идентификатор заметки
        current_user (dict): Информация о текущем пользователе
        
    Returns:
        dict: Сообщение об успешном удалении
    """
    logger.info(f"Запрос на удаление заметки {note_id} от пользователя {current_user.get('email')}")
    
    try:
        # Проверка существования заметки
        existing_note = notes_service.get_note_by_id(note_id)
        
        if not existing_note:
            logger.warning(f"Заметка с идентификатором {note_id} не найдена")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заметка с идентификатором {note_id} не найдена"
            )
        
        # Удаление заметки
        success = notes_service.delete_note(note_id)
        
        if not success:
            logger.error(f"Не удалось удалить заметку {note_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось удалить заметку {note_id}"
            )
        
        logger.info(f"Заметка {note_id} успешно удалена")
        return {"message": f"Заметка {note_id} успешно удалена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении заметки {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении заметки {note_id}"
        ) 