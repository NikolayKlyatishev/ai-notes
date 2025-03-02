"""
Модуль для транскрибации аудио с помощью Whisper с улучшенной поддержкой русского языка.
"""
import os
import logging
import json
from datetime import datetime
import whisper
from pydub import AudioSegment

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
        
        logger.info(f"Загрузка модели Whisper: {model_name}")
        try:
            self.model = whisper.load_model(model_name)
            logger.info(f"Модель Whisper {model_name} успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели Whisper: {e}")
            raise

    def transcribe(self, audio_file_path):
        """Транскрибирует аудиофайл и возвращает текст с временными метками."""
        if not os.path.exists(audio_file_path):
            logger.error(f"Аудиофайл не найден: {audio_file_path}")
            return None

        try:
            logger.info(f"Начало транскрипции файла: {audio_file_path}")
            
            # Преобразование файла в нужный формат, если это не WAV
            if not audio_file_path.lower().endswith('.wav'):
                logger.info(f"Конвертация файла {audio_file_path} в WAV формат")
                audio = AudioSegment.from_file(audio_file_path)
                wav_path = os.path.splitext(audio_file_path)[0] + ".wav"
                audio.export(wav_path, format="wav")
                audio_file_path = wav_path
                logger.info(f"Файл конвертирован в {wav_path}")
            
            # Оптимизированные настройки для быстрой транскрипции русского языка
            result = self.model.transcribe(
                audio_file_path,
                fp16=True,  # Используем fp16 для ускорения, если поддерживается
                language=self.language,
                initial_prompt="Это разговор на русском языке.",
                beam_size=3,    # Уменьшаем размер луча для ускорения
                best_of=1,      # Ускоряем, не генерируя множество вариантов
                temperature=0.0, # Делаем детерминированным для скорости
                condition_on_previous_text=True,  # Учитываем предыдущий текст
                verbose=False    # Отключаем подробный вывод для скорости
            )
            
            logger.info(f"Транскрипция завершена успешно")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при транскрибировании: {e}")
            return None

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