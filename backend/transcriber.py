"""
Модуль для транскрибации аудио с помощью Whisper с улучшенной поддержкой русского языка.
"""
import os
import logging
import json
from datetime import datetime
# Обновляем импорт Whisper
try:
    import whisper
    has_local_whisper = True
except Exception as e:
    has_local_whisper = False
    print(f"Ошибка импорта локального whisper: {e}")

import config
from tagging import generate_tags

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, model_name=None):
        """Инициализация транскрайбера с улучшенной моделью Whisper."""
        model_name = model_name or config.WHISPER_MODEL
        self.language = config.WHISPER_LANGUAGE if hasattr(config, 'WHISPER_LANGUAGE') else "ru"
        self.model_name = model_name
        
        if not has_local_whisper:
            logger.error("Локальная модель Whisper не найдена или повреждена!")
            raise ImportError("Не удалось импортировать whisper. Установите его через pip install git+https://github.com/openai/whisper.git")
            
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
                    logger.error(f"Модель {model_name} не найдена. Доступные модели: {available_models()}")
                    raise ValueError(f"Модель {model_name} не найдена.")
                
            logger.info(f"Модель Whisper {model_name} успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке локальной модели Whisper: {e}")
            raise

    def transcribe(self, audio_file_path):
        """Транскрибирует аудиофайл и возвращает текст с временными метками."""
        if not os.path.exists(audio_file_path):
            logger.error(f"Аудиофайл не найден: {audio_file_path}")
            return None

        try:
            logger.info(f"Начало транскрипции файла: {audio_file_path}")
            
            # Проверяем, что файл в формате WAV
            if not audio_file_path.lower().endswith('.wav'):
                logger.error(f"Файл {audio_file_path} не в формате WAV. Поддерживаются только WAV файлы.")
                return None
            
            # Используем локальную модель
            # Оптимизированные настройки для быстрой транскрипции русского языка
            # Обрабатываем разные версии API Whisper
            try:
                # Пробуем стандартный API
                result = self.model.transcribe(
                    audio_file_path,
                    language=self.language,
                    initial_prompt="Это разговор на русском языке."
                )
            except TypeError as e:
                # Если стандартный API не работает, пробуем упрощенный вызов
                logger.info(f"Используем упрощенный API вызов для Whisper: {e}")
                result = self.model.transcribe(audio_file_path)
                # Если результат не словарь, создаем совместимый формат
                if not isinstance(result, dict):
                    result = {"text": str(result), "segments": []}
            
            logger.info(f"Транскрипция завершена успешно")
            return result
                
        except Exception as e:
            logger.error(f"Ошибка при транскрибировании: {e}")
            # Возвращаем пустой результат вместо None для совместимости
            return {"text": "", "segments": []}

    def save_transcript(self, transcript_data, audio_file_path):
        """Сохраняет транскрипт в JSON файл."""
        if not transcript_data:
            logger.warning("Нет данных для сохранения")
            return None
            
        # Создаем имя файла на основе аудиофайла
        base_name = os.path.basename(audio_file_path)
        note_name = os.path.splitext(base_name)[0]
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Формируем путь для сохранения
        json_path = os.path.join(config.NOTES_DIR, f"{note_name}.json")
        
        # Подготавливаем данные
        note_data = config.NOTE_TEMPLATE.copy()
        note_data["date"] = timestamp
        note_data["transcript"] = transcript_data["text"]
        
        # Сохраняем информацию о сегментах, если есть
        if "segments" in transcript_data:
            note_data["segments"] = []
            for segment in transcript_data["segments"]:
                segment_info = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"]
                }
                note_data["segments"].append(segment_info)
        
        # Используем интеллектуальную генерацию тегов
        logger.info("Генерация тегов для транскрипта")
        tags_data = generate_tags(transcript_data["text"])
        
        # Сохраняем ключевые слова и фразы отдельно
        note_data["tags"] = tags_data["keywords"]
        note_data["keyphrases"] = tags_data["keyphrases"]
        
        # Добавляем категории, цели и темы из генератора тегов
        if "categories" in tags_data:
            note_data["categories"] = tags_data["categories"]
        if "purpose" in tags_data:
            note_data["purpose"] = tags_data["purpose"]
        if "topics" in tags_data:
            note_data["topics"] = tags_data["topics"]
        
        try:
            logger.info(f"Сохранение транскрипта в {json_path}")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(note_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Транскрипт успешно сохранен")
            return json_path
        except Exception as e:
            logger.error(f"Ошибка при сохранении транскрипта: {e}")
            return None


def transcribe_audio(audio_file_path, model_name=None):
    """Удобная функция для транскрибации аудиофайла и сохранения результата."""
    transcriber = Transcriber(model_name)
    transcript_data = transcriber.transcribe(audio_file_path)
    if transcript_data:
        return transcriber.save_transcript(transcript_data, audio_file_path)
    return None


if __name__ == "__main__":
    # Тестирование
    import sys
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        note_path = transcribe_audio(audio_path)
        if note_path:
            print(f"Транскрипт сохранен в {note_path}")
        else:
            print("Не удалось создать транскрипт")
    else:
        print("Пожалуйста, укажите путь к аудиофайлу") 