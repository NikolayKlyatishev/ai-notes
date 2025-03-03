"""
API для управления рекордером.
"""
import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.core.logger import setup_logger
from backend.core.config import AUDIO_DIR, NOTES_DIR
from backend.api.auth import login_required
from backend.services.recorder import record_and_transcribe

# Настройка логирования
logger = setup_logger("backend.api.recorder")

# Создаем роутер
router = APIRouter()

# Глобальные переменные для управления рекордером
recorder_process = None
recorder_status = {
    "status": "stopped",
    "message": "Рекордер остановлен",
    "timestamp": datetime.now().isoformat()
}
active_clients = set()


# Модели данных
class RecorderStartParams(BaseModel):
    continuous: bool = True
    model: str = "base"  # Параметр для выбора модели Whisper


class RecorderTranscribeParams(BaseModel):
    model: str = "base"  # Параметр для выбора модели Whisper


class RecorderResponse(BaseModel):
    status: str
    message: str


# Обновление статуса рекордера
def update_recorder_status(status, message):
    """
    Обновление статуса рекордера.
    
    Args:
        status (str): Статус рекордера ("recording", "stopped", "error", и т.д.)
        message (str): Сообщение о статусе
    """
    global recorder_status
    recorder_status = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    # Оповещаем клиентов об обновлении статуса
    broadcast_status_update_sync()


# Запуск рекордера в отдельном потоке
def run_recorder_thread(continuous=False, model=None):
    """
    Запуск рекордера в отдельном потоке.
    
    Args:
        continuous (bool): Если True, то рекордер будет работать в режиме постоянной записи
        model (str): Модель Whisper для транскрибации
    """
    global recorder_process
    
    try:
        # Обновляем статус
        if continuous:
            update_recorder_status("recording", "Рекордер запущен в режиме постоянной записи")
        else:
            update_recorder_status("recording", "Рекордер запущен в режиме однократной записи")
        
        # Запуск записи и транскрибации
        audio_file, transcription = record_and_transcribe(continuous=continuous)
        
        # Обновляем статус после завершения записи
        if audio_file:
            if transcription:
                update_recorder_status(
                    "completed",
                    f"Запись завершена и транскрибирована: {os.path.basename(audio_file)}"
                )
            else:
                update_recorder_status(
                    "completed_no_transcription",
                    f"Запись завершена, но не транскрибирована: {os.path.basename(audio_file)}"
                )
        else:
            update_recorder_status("error", "Ошибка при записи")
    except Exception as e:
        logger.error(f"Ошибка в потоке рекордера: {e}")
        update_recorder_status("error", f"Ошибка: {str(e)}")
    finally:
        # Сбрасываем глобальную переменную процесса
        recorder_process = None


# Broadcast для обновления статуса всем подключенным клиентам
def broadcast_status_update_sync():
    """
    Синхронная функция для оповещения всех клиентов об обновлении статуса.
    """
    # Используем asyncio для запуска асинхронной функции из синхронного кода
    if active_clients:
        asyncio.run_coroutine_threadsafe(
            _broadcast(),
            asyncio.get_event_loop()
        )


async def _broadcast():
    """
    Асинхронная функция для отправки события всем клиентам.
    """
    # Создаем копию множества клиентов, чтобы избежать изменения во время итерации
    clients = active_clients.copy()
    
    # Формируем данные события
    event_data = f"data: {json.dumps(recorder_status)}\n\n"
    
    # Отправляем всем клиентам
    for queue in clients:
        try:
            await queue.put(event_data)
        except Exception as e:
            logger.error(f"Ошибка при отправке данных клиенту: {e}")
            # Удаляем клиента из списка активных
            try:
                active_clients.remove(queue)
            except KeyError:
                pass


# Регулярное обновление статуса для keepalive соединений
async def status_updater():
    """
    Функция для периодического обновления статуса рекордера.
    """
    while True:
        # Отправляем текущий статус всем клиентам каждые 15 секунд
        await _broadcast()
        await asyncio.sleep(15)


# API маршруты
@router.get("/status/stream")
async def stream_status(user = Depends(login_required)):
    """
    Стриминг статуса рекордера через SSE (Server-Sent Events).
    """
    async def event_generator():
        # Создаем очередь для текущего клиента
        queue = asyncio.Queue()
        
        # Добавляем клиента в список активных
        active_clients.add(queue)
        
        try:
            # Отправляем текущий статус при подключении
            await queue.put(f"data: {json.dumps(recorder_status)}\n\n")
            
            # Бесконечный цикл для отправки обновлений
            while True:
                # Ждем новых данных
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            # Если соединение закрыто, удаляем клиента из списка активных
            logger.info("Клиент отключен от потока статуса")
        finally:
            active_clients.remove(queue)
    
    # Возвращаем стрим с правильными заголовками для SSE
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/status")
async def get_recorder_status(user = Depends(login_required)):
    """
    Получение текущего статуса рекордера.
    """
    # Дополнительные данные для frontend
    additional_data = {}
    
    # Получение списка записанных аудио
    if os.path.exists(AUDIO_DIR):
        audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".wav")]
        additional_data["audio_files"] = sorted(audio_files, reverse=True)
    else:
        additional_data["audio_files"] = []
    
    # Получение списка заметок
    if os.path.exists(NOTES_DIR):
        note_files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".json")]
        additional_data["note_files"] = sorted(note_files, reverse=True)
    else:
        additional_data["note_files"] = []
    
    # Объединяем данные
    result = {**recorder_status, **additional_data}
    
    return result


@router.post("/start", response_model=RecorderResponse)
async def start_recorder(params: RecorderStartParams, user = Depends(login_required)):
    """
    Запуск рекордера.
    """
    global recorder_process
    
    # Проверяем, не запущен ли уже рекордер
    if recorder_process and recorder_process.is_alive():
        return RecorderResponse(
            status="error",
            message="Рекордер уже запущен"
        )
    
    try:
        # Создаем и запускаем поток для рекордера
        recorder_thread = threading.Thread(
            target=run_recorder_thread,
            kwargs={
                "continuous": params.continuous,
                "model": params.model
            }
        )
        recorder_thread.daemon = True
        recorder_thread.start()
        
        # Сохраняем поток в глобальной переменной
        recorder_process = recorder_thread
        
        return RecorderResponse(
            status="success",
            message=f"Рекордер запущен{' в режиме постоянной записи' if params.continuous else ''}"
        )
    except Exception as e:
        logger.error(f"Ошибка при запуске рекордера: {e}")
        update_recorder_status("error", f"Ошибка запуска: {str(e)}")
        return RecorderResponse(
            status="error",
            message=f"Ошибка при запуске рекордера: {str(e)}"
        )


@router.post("/stop", response_model=RecorderResponse)
async def stop_recorder(background_tasks: BackgroundTasks, user = Depends(login_required)):
    """
    Остановка рекордера.
    """
    global recorder_process
    
    # Обновляем статус
    update_recorder_status("stopping", "Остановка рекордера...")
    
    # Сигнал для остановки рекордера
    from backend.services.recorder import running
    backend.services.recorder.running = False
    
    return RecorderResponse(
        status="success",
        message="Команда на остановку рекордера отправлена"
    )


@router.post("/transcribe")
async def transcribe_all(
    params: RecorderTranscribeParams,
    background_tasks: BackgroundTasks,
    user = Depends(login_required)
) -> Dict[str, Any]:
    """
    Транскрибация всех записанных аудио-файлов.
    """
    from backend.services.transcriber import transcribe_audio
    
    # Проверка существования директории с аудио
    if not os.path.exists(AUDIO_DIR):
        raise HTTPException(status_code=404, detail="Директория с аудио-файлами не найдена")
    
    # Получение списка WAV-файлов
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".wav")]
    
    if not audio_files:
        return {"status": "warning", "message": "Не найдено аудио-файлов для транскрибации"}
    
    # Запускаем транскрибацию в фоновом режиме для каждого файла
    for audio_file in audio_files:
        file_path = os.path.join(AUDIO_DIR, audio_file)
        
        # Проверка наличия соответствующего JSON-файла
        json_file = os.path.join(NOTES_DIR, audio_file.replace(".wav", ".json"))
        if os.path.exists(json_file):
            continue  # Пропускаем уже транскрибированные файлы
        
        # Добавляем задачу в фоновые задачи
        background_tasks.add_task(transcribe_audio, file_path, params.model)
    
    return {
        "status": "success",
        "message": f"Запущена транскрибация {len(audio_files)} аудио-файлов",
        "files": audio_files
    }


@router.get("/recordings")
async def get_recordings(user = Depends(login_required)):
    """
    Получение списка записанных аудио-файлов и соответствующих заметок.
    """
    # Проверка существования директорий
    if not os.path.exists(AUDIO_DIR):
        raise HTTPException(status_code=404, detail="Директория с аудио-файлами не найдена")
    
    if not os.path.exists(NOTES_DIR):
        raise HTTPException(status_code=404, detail="Директория с заметками не найдена")
    
    # Получение списка WAV-файлов
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".wav")]
    
    # Получение списка JSON-файлов
    note_files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".json")]
    
    # Формирование результата
    recordings = []
    
    for audio_file in audio_files:
        base_name = os.path.splitext(audio_file)[0]
        note_file = base_name + ".json"
        
        recording = {
            "audio_file": audio_file,
            "audio_path": os.path.join(AUDIO_DIR, audio_file),
            "transcribed": note_file in note_files
        }
        
        if recording["transcribed"]:
            # Добавляем информацию из заметки
            try:
                with open(os.path.join(NOTES_DIR, note_file), "r", encoding="utf-8") as f:
                    note = json.load(f)
                    recording["note"] = note
            except Exception as e:
                logger.error(f"Ошибка при чтении заметки {note_file}: {e}")
                recording["note_error"] = str(e)
        
        recordings.append(recording)
    
    # Сортировка по имени файла (по дате создания)
    recordings.sort(key=lambda x: x["audio_file"], reverse=True)
    
    return {
        "status": "success",
        "recordings": recordings
    } 