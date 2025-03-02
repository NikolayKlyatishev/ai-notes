"""
API для управления рекордером через веб-интерфейс.
"""
import os
import json
import time
import signal
import threading
import logging
import subprocess
import re
import glob
import sys
from typing import Dict, Optional, List, Any, Tuple, Callable
from datetime import datetime, timedelta
from pathlib import Path
import whisper

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from backend.tagging import generate_tags  # Импортируем модуль тегирования
from backend.config import AUDIO_DIR, NOTES_DIR, VAD_AGGRESSIVENESS, FRAME_DURATION_MS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные для отслеживания состояния
recorder_process: Optional[subprocess.Popen] = None
recorder_status: Dict[str, Any] = {
    "running": False,
    "status": "stopped",
    "start_time": None,
    "duration": 0,
    "current_file": None,
    "last_activity": None,
    "audio_level": 0,
    "recent_files": [],
    "transcribing": False,
    "transcribe_progress": {
        "total_files": 0,
        "processed_files": 0,
        "current_file": None
    }
}
recorder_output_thread = None

# Добавляем импорт функции транскрибации
from transcriber import transcribe_audio as transcriber_transcribe_audio

# Коллбэк для внешних модулей, которым нужно знать об обновлении статуса
# (будет установлен из web_app.py)
status_update_callback = None

def set_status_update_callback(callback: Callable):
    """Устанавливает функцию обратного вызова для оповещения о изменении статуса"""
    global status_update_callback
    status_update_callback = callback

def notify_status_update():
    """Уведомляет всех заинтересованных о том, что статус обновился"""
    global status_update_callback
    if status_update_callback:
        status_update_callback()

def start_recorder(continuous: bool = True, model: str = "base") -> Dict[str, Any]:
    """Запуск рекордера в отдельном процессе."""
    global recorder_process, recorder_status
    
    if recorder_process is not None and recorder_process.poll() is None:
        return {"status": "error", "message": "Рекордер уже запущен"}
    
    # Формируем команду запуска
    recorder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorder.py")
    cmd = [sys.executable, recorder_path, "--start"]
    if continuous:
        cmd.append("--continuous")
    if model:
        cmd.extend(["--model", model])
    
    # Запускаем процесс
    try:
        recorder_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Устанавливаем начальное состояние
        recorder_status["running"] = True
        recorder_status["status"] = "recording"
        recorder_status["start_time"] = time.time()
        recorder_status["duration"] = 0
        recorder_status["audio_level"] = 0
        recorder_status["model"] = model  # Сохраняем выбранную модель
        
        # Запускаем мониторинг вывода процесса
        threading.Thread(target=_monitor_recorder_output, daemon=True).start()
        
        # Уведомляем об обновлении статуса
        notify_status_update()
        
        return {"status": "success", "message": "Рекордер запущен"}
    except Exception as e:
        logger.error("Ошибка при запуске рекордера: %s", str(e))
        return {"status": "error", "message": f"Ошибка при запуске рекордера: {str(e)}"}


def stop_recorder(background_tasks=None) -> Dict[str, Any]:
    """Остановка рекордера и опционально запуск транскрибации в фоне."""
    global recorder_process, recorder_status
    
    if recorder_process is None or recorder_process.poll() is not None:
        return {"status": "error", "message": "Рекордер не запущен"}
    
    try:
        # Получаем текущий файл перед остановкой
        current_file = recorder_status.get("current_file")
        # Получаем текущую выбранную модель
        current_model = recorder_status.get("model", "base")
        
        # Останавливаем процесс
        recorder_process.terminate()
        recorder_process.wait(timeout=5)  # Даем 5 секунд на завершение
        recorder_process = None
        
        # Обновляем статус
        recorder_status["running"] = False
        recorder_status["status"] = "stopped"
        recorder_status["duration"] = 0
        recorder_status["current_file"] = None
        
        # Уведомляем об обновлении статуса
        notify_status_update()
        
        # Обновляем список файлов
        recorder_status["recent_files"] = get_recordings()["recordings"]
        
        # Если передан объект background_tasks, запускаем транскрибацию в фоне
        if background_tasks is not None and current_file:
            logger.info("Запуск транскрипции для файла %s в фоновом режиме", current_file)
            background_tasks.add_task(
                transcriber_transcribe_audio, 
                os.path.join(AUDIO_DIR, current_file),
                current_model
            )
        elif current_file:
            # Если фоновые задачи не поддерживаются, запускаем синхронно
            logger.info("Запуск транскрипции для файла %s синхронно", current_file)
            try:
                transcriber_transcribe_audio(os.path.join(AUDIO_DIR, current_file), current_model)
            except Exception as e:
                logger.error("Ошибка при транскрипции файла: %s", str(e))
        
        logger.info("Рекордер остановлен")
        return {"status": "success", "message": "Рекордер успешно остановлен"}
    except Exception as e:
        logger.error("Ошибка при остановке рекордера: %s", str(e))
        return {"status": "error", "message": f"Ошибка при остановке рекордера: {str(e)}"}


def get_status() -> Dict[str, Any]:
    """Получение статуса рекордера."""
    global recorder_process, recorder_status
    
    # Обновляем данные о длительности записи, если рекордер запущен
    if recorder_status["running"] and recorder_status["start_time"]:
        current_time = time.time()
        elapsed_time = int(current_time - recorder_status["start_time"])
        recorder_status["duration"] = elapsed_time
    
    # Возвращаем копию статуса, чтобы избежать проблем с многопоточностью
    return recorder_status.copy()


def _monitor_recorder_output() -> None:
    """Мониторинг вывода процесса рекордера для обновления статуса."""
    global recorder_process, recorder_status
    
    if recorder_process is None:
        return
    
    try:
        for line in iter(recorder_process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Пытаемся распарсить строку как JSON
                data = json.loads(line)
                
                # Обновляем статус в зависимости от данных
                if "current_file" in data:
                    recorder_status["current_file"] = data["current_file"]
                if "audio_level" in data:
                    recorder_status["audio_level"] = data["audio_level"]
                if "status" in data:
                    recorder_status["status"] = data["status"]
                
                # Отправляем уведомление о важном обновлении (изменение файла или статуса)
                if "current_file" in data or "status" in data:
                    notify_status_update()
                
            except json.JSONDecodeError:
                # Если это не JSON, обрабатываем как обычный лог
                if "Recording to file" in line:
                    # Извлекаем имя файла
                    parts = line.split("Recording to file:")
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        recorder_status["current_file"] = os.path.basename(filename)
                        notify_status_update()
                elif "Audio level:" in line:
                    # Извлекаем уровень звука
                    parts = line.split("Audio level:")
                    if len(parts) > 1:
                        try:
                            level = float(parts[1].strip())
                            recorder_status["audio_level"] = int(level)
                        except ValueError:
                            pass
            
            # Проверяем, не завершился ли процесс
            if recorder_process.poll() is not None:
                break
    except Exception as e:
        logger.error("Ошибка при мониторинге вывода рекордера: %s", str(e))
    finally:
        # Если мы вышли из цикла, значит процесс завершился
        if recorder_status["running"]:
            recorder_status["running"] = False
            recorder_status["status"] = "stopped"
            notify_status_update()


def get_recordings(limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Получение списка последних записей"""
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


def transcribe_untranscribed_files(model=None):
    """
    Транскрибирует все файлы, для которых еще нет транскрипций.
    Обновляет статус транскрибации в recorder_status.

    Args:
        model (str, optional): Модель Whisper, которую нужно использовать. 
                              Если None, будет использована модель по умолчанию.
    
    Returns:
        list: Список путей к созданным JSON файлам с транскрипциями.
    """
    
    logger.info("Начало массовой транскрипции файлов")
    
    # Помечаем, что транскрипция началась
    recorder_status["transcribing"] = True
    
    try:
        # Получаем список аудиофайлов
        audio_files = glob.glob(os.path.join(AUDIO_DIR, "*.wav"))
        
        # Получаем список существующих заметок
        note_files = glob.glob(os.path.join(NOTES_DIR, "*.json"))
        note_basenames = [os.path.splitext(os.path.basename(nf))[0] for nf in note_files]
        
        # Находим файлы, которые нужно транскрибировать
        to_transcribe = []
        for audio_file in audio_files:
            audio_basename = os.path.splitext(os.path.basename(audio_file))[0]
            if audio_basename not in note_basenames:
                to_transcribe.append(audio_file)
        
        # Обновляем статус с информацией о прогрессе
        recorder_status["transcribe_progress"]["total_files"] = len(to_transcribe)
        recorder_status["transcribe_progress"]["processed_files"] = 0
        recorder_status["transcribe_progress"]["current_file"] = None
        
        # Отправляем уведомление о начале транскрипции
        notify_status_update()
        
        # Транскрибируем каждый файл
        transcribed = []
        for i, audio_file in enumerate(to_transcribe):
            try:
                # Обновляем статус
                current_file_name = os.path.basename(audio_file)
                recorder_status["transcribe_progress"]["current_file"] = current_file_name
                notify_status_update()
                
                logger.info(f"Транскрибирую файл {i+1}/{len(to_transcribe)}: {current_file_name}")
                
                # Запускаем транскрипцию
                result = transcriber_transcribe_audio(audio_file, model)
                
                if result:
                    transcribed.append(result)
                    logger.info(f"Транскрипция успешна: {result}")
                else:
                    logger.warning(f"Не удалось транскрибировать: {audio_file}")
                
                # Обновляем прогресс
                recorder_status["transcribe_progress"]["processed_files"] = i + 1
                notify_status_update()
                
            except Exception as e:
                logger.error(f"Ошибка при транскрипции {audio_file}: {str(e)}")
        
        return transcribed
    
    except Exception as e:
        logger.error(f"Ошибка при массовой транскрипции: {str(e)}")
        return []
    
    finally:
        # Помечаем, что транскрипция завершена
        recorder_status["transcribing"] = False
        recorder_status["transcribe_progress"]["current_file"] = None
        notify_status_update()
        
        # Обновляем список файлов
        recorder_status["recent_files"] = get_recordings()["recordings"] 

def transcribe_audio(audio_path: str, model: str = "base") -> Optional[Dict[str, Any]]:
    """
    Транскрибирует аудиофайл с помощью Whisper и сохраняет результат в JSON.
    
    Args:
        audio_path (str): Путь к аудиофайлу для транскрибации
        model (str): Модель Whisper для использования (tiny, base, small, medium, large)
        
    Returns:
        Optional[Dict[str, Any]]: Результат транскрибации или None в случае ошибки
    """
    try:
        logger.info(f"Транскрибирую файл: {audio_path} с моделью {model}")
        
        # Проверяем существование файла
        if not os.path.exists(audio_path):
            logger.error(f"Файл не найден: {audio_path}")
            return None
        
        # Получаем базовое имя файла без расширения
        basename = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = os.path.join(NOTES_DIR, f"{basename}.json")
        
        # Проверяем, существует ли уже транскрипция
        existing_data = None
        if os.path.exists(output_path):
            logger.info(f"Транскрипция уже существует: {output_path}, обновляем с тегами")
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # Если нужно транскрибировать заново
        if not existing_data or not existing_data.get('text'):
            # Загружаем модель Whisper
            logger.info(f"Загружаем модель Whisper: {model}")
            whisper_model = whisper.load_model(model)
            
            # Транскрибируем аудио
            logger.info("Начинаем транскрибацию...")
            result = whisper_model.transcribe(audio_path, language="ru")
            
            # Добавляем метаданные
            result["audio_file"] = os.path.basename(audio_path)
            result["created_at"] = datetime.now().isoformat()
        else:
            # Используем существующие данные
            result = existing_data
        
        # Генерируем теги для транскрипта, только если их еще нет или они пустые
        text_content = result.get('text', '')
        if text_content:
            logger.info("Генерация тегов для транскрипта")
            # Проверяем наличие тегов или необходимость их обновления
            should_update_tags = (
                'tags' not in result or 
                not result['tags'] or 
                'categories' not in result or 
                'topics' not in result or
                'purpose' not in result
            )
            
            if should_update_tags:
                # Генерируем расширенные теги с классификацией
                tags_data = generate_tags(text_content, classify=True)
                
                # Обновляем результат с новыми данными
                result["tags"] = tags_data["keywords"]
                result["keyphrases"] = tags_data["keyphrases"]
                result["categories"] = tags_data["categories"]
                result["topics"] = tags_data["topics"]
                result["purpose"] = tags_data["purpose"]
                result["purpose_details"] = tags_data["purpose_details"]
                
                logger.info(f"Сгенерированы теги: {tags_data['keywords']}")
                logger.info(f"Категории: {tags_data['categories']}")
                logger.info(f"Назначение: {tags_data['purpose']}")
            else:
                logger.info(f"Теги уже существуют: {result['tags']}")
            
            # Добавляем поле transcript для совместимости с поиском
            if 'transcript' not in result:
                result['transcript'] = text_content
        else:
            # Инициализируем пустые теги
            result["tags"] = []
            result["keyphrases"] = []
            result["categories"] = []
            result["topics"] = []
            result["purpose"] = "неизвестно"
            result["purpose_details"] = {}
            logger.warning("Пустой текст транскрипции, теги не генерируются")
        
        # Сохраняем результат в JSON
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Транскрипция сохранена в: {output_path}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при транскрипции: {str(e)}")
        logger.exception("Подробная информация об ошибке:")
        return None 