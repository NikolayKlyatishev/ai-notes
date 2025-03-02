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
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Импорт констант из модуля конфигурации
import config
from config import AUDIO_DIR, NOTES_DIR

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
    "start_time": None,
    "duration": 0,
    "current_file": None,
    "last_activity": None,
    "audio_level": 0,
    "recent_files": []
}

# Добавляем импорт функции транскрибации
from transcriber import transcribe_audio


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
        
        # Обновляем статус
        recorder_status["running"] = True
        recorder_status["start_time"] = datetime.now().isoformat()
        recorder_status["duration"] = 0
        recorder_status["model"] = model
        
        logger.info(f"Рекордер запущен с параметрами: continuous={continuous}, model={model}")
        return {"status": "success", "message": "Рекордер запущен"}
    except Exception as e:
        logger.error(f"Ошибка при запуске рекордера: {e}")
        return {"status": "error", "message": f"Ошибка при запуске рекордера: {e}"}


def stop_recorder() -> Dict[str, Any]:
    """Остановка рекордера"""
    global recorder_process, recorder_status
    
    if recorder_process is None or recorder_process.poll() is not None:
        recorder_status["running"] = False
        return {"status": "error", "message": "Рекордер не запущен"}
    
    try:
        # Отправка сигнала SIGTERM для корректного завершения
        recorder_process.send_signal(signal.SIGTERM)
        
        # Ожидание завершения процесса (с таймаутом)
        try:
            recorder_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Если процесс не завершился, отправляем SIGKILL
            recorder_process.send_signal(signal.SIGKILL)
            recorder_process.wait(timeout=2)
        
        # Обновление статуса
        recorder_status["running"] = False
        
        # Запускаем транскрибацию последнего файла
        transcribe_untranscribed_files()
        
        return {"status": "success", "message": "Рекордер остановлен"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка остановки рекордера: {str(e)}"}


def get_status() -> Dict[str, Any]:
    """Получение текущего статуса рекордера"""
    global recorder_status
    
    # Проверяем, что процесс всё ещё работает
    if recorder_process is not None and recorder_process.poll() is None:
        # Обновляем длительность записи
        if recorder_status["start_time"]:
            start_time = datetime.fromisoformat(recorder_status["start_time"])
            duration_seconds = (datetime.now() - start_time).total_seconds()
            recorder_status["duration"] = int(duration_seconds)
    else:
        recorder_status["running"] = False
    
    # Обновляем список последних файлов
    if not recorder_status.get("recent_files"):
        recorder_status["recent_files"] = get_recordings()["recordings"]
    
    return recorder_status


def _monitor_recorder_output() -> None:
    """Мониторинг вывода рекордера и обновление статуса"""
    global recorder_process, recorder_status
    
    if recorder_process is None:
        return
    
    # Регулярные выражения для извлечения информации из вывода
    file_pattern = re.compile(r"Запись аудио в файл: (.+\.wav)")
    transcribing_pattern = re.compile(r"Транскрибирование файла: (.+\.wav)")
    audio_level_pattern = re.compile(r"Уровень аудио: (\d+)%")
    completion_pattern = re.compile(r"Файл (.+\.txt) сохранен")
    
    for line in iter(recorder_process.stdout.readline, ''):
        # Обновляем время последней активности
        recorder_status["last_activity"] = datetime.now().isoformat()
        
        # Проверяем, содержит ли строка информацию о записи файла
        file_match = file_pattern.search(line)
        if file_match:
            current_file = file_match.group(1)
            recorder_status["current_file"] = os.path.basename(current_file)
            continue
        
        # Проверяем, содержит ли строка информацию о транскрибировании
        transcribing_match = transcribing_pattern.search(line)
        if transcribing_match:
            recorder_status["current_file"] = os.path.basename(transcribing_match.group(1))
            continue
        
        # Проверяем, содержит ли строка информацию об уровне аудио
        audio_level_match = audio_level_pattern.search(line)
        if audio_level_match:
            recorder_status["audio_level"] = int(audio_level_match.group(1))
            continue
        
        # Проверяем, содержит ли строка информацию о завершении транскрибирования
        completion_match = completion_pattern.search(line)
        if completion_match:
            # Обновляем список последних файлов
            recorder_status["recent_files"] = get_recordings()["recordings"]
            continue
    
    # Если мы вышли из цикла, значит процесс завершился
    recorder_status["running"] = False


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
        
        # Получаем текст транскрипции, если есть
        transcript_text = ""
        if has_transcript:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    note_data = json.load(f)
                    transcript_text = note_data.get('transcript', '')[:100] + '...' if len(note_data.get('transcript', '')) > 100 else note_data.get('transcript', '')
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
            "type": "audio"
        })
    
    return {"recordings": recordings}


def transcribe_untranscribed_files() -> List[str]:
    """
    Транскрибирует все аудиофайлы, которые еще не были транскрибированы.
    
    Returns:
        List[str]: Список путей к созданным заметкам
    """
    logger.info("Запуск транскрибации необработанных аудиофайлов")
    
    # Создаем директории, если они не существуют
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(NOTES_DIR, exist_ok=True)
    
    # Получаем список всех WAV файлов
    wav_files = glob.glob(os.path.join(AUDIO_DIR, "*.wav"))
    
    # Получаем список всех JSON файлов
    json_files = glob.glob(os.path.join(NOTES_DIR, "*.json"))
    json_basenames = [os.path.splitext(os.path.basename(f))[0] for f in json_files]
    
    # Находим файлы, которые еще не были транскрибированы
    untranscribed_files = []
    for wav_file in wav_files:
        basename = os.path.splitext(os.path.basename(wav_file))[0]
        if basename not in json_basenames:
            untranscribed_files.append(wav_file)
    
    # Транскрибируем каждый файл
    transcribed_notes = []
    for wav_file in untranscribed_files:
        logger.info(f"Транскрибирую файл: {wav_file}")
        try:
            note_path = transcribe_audio(wav_file)
            if note_path:
                transcribed_notes.append(note_path)
                logger.info(f"Создана заметка: {note_path}")
            else:
                logger.warning(f"Не удалось создать заметку для {wav_file}")
        except Exception as e:
            logger.error(f"Ошибка при транскрибации {wav_file}: {e}")
    
    # Обновляем список последних файлов
    if transcribed_notes:
        recorder_status["recent_files"] = get_recordings()["recordings"]
    
    return transcribed_notes 