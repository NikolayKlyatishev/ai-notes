"""
Модуль для транскрибации аудио с помощью Whisper с улучшенной поддержкой русского языка.
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.logger import setup_logger
from backend.core.config import (
    NOTES_DIR, WHISPER_MODEL, WHISPER_LANGUAGE, NOTE_TEMPLATE
)

# Обновляем импорт Whisper
try:
    import whisper
    has_local_whisper = True
except Exception as e:
    has_local_whisper = False
    print(f"Ошибка импорта локального whisper: {e}")

# Настройка логирования
logger = setup_logger("backend.services.transcriber")


class Transcriber:
    """Класс для транскрибации аудио."""
    
    def __init__(self, model_name=None):
        """Инициализация транскрайбера с улучшенной моделью Whisper."""
        model_name = model_name or WHISPER_MODEL
        self.language = WHISPER_LANGUAGE
        self.model_name = model_name
        
        if not has_local_whisper:
            logger.error("Локальная модель Whisper не найдена или повреждена!")
            raise ImportError(
                "Не удалось импортировать whisper. Установите его через "
                "pip install git+https://github.com/openai/whisper.git"
            )
            
        logger.info(f"Загрузка локальной модели Whisper: {model_name}")
        try:
            # Проверяем наличие метода load_model
            if hasattr(whisper, 'load_model'):
                self.model = whisper.load_model(model_name)
            # В противном случае используем другой способ загрузки модели
            else:
                # Попробуем создать модель напрямую
                logger.info("Метод load_model не найден, пробуем альтернативный способ загрузки")
                from whisper import available_models
                if model_name in available_models():
                    self.model = whisper.Whisper.from_pretrained(model_name)
                else:
                    raise ValueError(f"Модель {model_name} недоступна")
                    
            logger.info(f"Модель Whisper {model_name} успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели Whisper: {e}")
            raise
    
    def transcribe(self, audio_file):
        """
        Транскрибация аудио-файла.
        
        Args:
            audio_file (str): Путь к аудио-файлу
            
        Returns:
            str: Транскрибированный текст
        """
        if not os.path.exists(audio_file):
            logger.error(f"Аудио-файл не найден: {audio_file}")
            return None
        
        try:
            logger.info(f"Начало транскрибации файла: {audio_file}")
            
            # Транскрибация с явным указанием языка
            result = self.model.transcribe(
                audio_file,
                language=self.language,
                task="transcribe"
            )
            
            logger.info(f"Транскрибация завершена успешно: {audio_file}")
            return result["text"]
        except Exception as e:
            logger.error(f"Ошибка при транскрибации: {e}")
            return None


def save_transcription(transcription, audio_file):
    """
    Сохранение транскрипции в JSON-файл.
    
    Args:
        transcription (str): Транскрибированный текст
        audio_file (str): Путь к аудио-файлу
        
    Returns:
        str: Путь к сохраненному JSON-файлу или None в случае ошибки
    """
    if not transcription:
        logger.error("Невозможно сохранить пустую транскрипцию")
        return None
    
    try:
        # Создание директории для заметок, если она не существует
        os.makedirs(NOTES_DIR, exist_ok=True)
        
        # Создание имени файла заметки на основе имени аудио-файла
        audio_basename = os.path.basename(audio_file)
        note_filename = os.path.splitext(audio_basename)[0] + ".json"
        note_path = os.path.join(NOTES_DIR, note_filename)
        
        # Получение метаданных
        timestamp = datetime.now().isoformat()
        
        # Создание структуры заметки
        note = NOTE_TEMPLATE.copy()
        note["date"] = timestamp
        note["transcript"] = transcription
        note["audio_file"] = audio_file
        
        # Сохранение в JSON-файл
        with open(note_path, 'w', encoding='utf-8') as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Транскрипция сохранена в файл: {note_path}")
        return note_path
    except Exception as e:
        logger.error(f"Ошибка при сохранении транскрипции: {e}")
        return None


def transcribe_audio(audio_file, model_name=None):
    """
    Транскрибация аудио-файла и сохранение результата.
    
    Args:
        audio_file (str): Путь к аудио-файлу
        model_name (str, optional): Имя модели Whisper
        
    Returns:
        str: Транскрибированный текст или None в случае ошибки
    """
    if not os.path.exists(audio_file):
        logger.error(f"Аудио-файл не найден: {audio_file}")
        return None
    
    try:
        # Проверка наличия Whisper
        if not has_local_whisper:
            logger.error("Whisper не установлен, транскрибация невозможна")
            return None
        
        logger.info(f"Начало транскрибации аудио: {audio_file}")
        
        # Создание экземпляра транскрайбера
        transcriber = Transcriber(model_name)
        
        # Транскрибация
        transcription = transcriber.transcribe(audio_file)
        
        if transcription:
            # Сохранение транскрипции
            save_transcription(transcription, audio_file)
            
            # Генерация тегов в фоновом режиме
            try:
                from backend.services.tagging import generate_tags
                generate_tags(transcription, os.path.join(NOTES_DIR, os.path.splitext(os.path.basename(audio_file))[0] + ".json"))
            except Exception as e:
                logger.error(f"Ошибка при генерации тегов: {e}")
            
            logger.info(f"Транскрибация аудио завершена успешно: {audio_file}")
            return transcription
        else:
            logger.error(f"Транскрибация вернула пустой результат: {audio_file}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при транскрибации: {e}")
        return None


if __name__ == "__main__":
    # Пример использования
    import sys
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        result = transcribe_audio(audio_path)
        print(f"Результат транскрибации: {result}")
    else:
        print("Необходимо указать путь к аудио-файлу в качестве аргумента") 