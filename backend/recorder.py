#!/usr/bin/env python
"""
Основной исполняемый файл для автоматической фиксации разговоров.
"""
import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime

import config
from audio_recorder import AudioRecorder
from transcriber import transcribe_audio

# Переменная для отслеживания состояния
running = True

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "recorder.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Обработчик сигналов для корректного завершения
def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения работы."""
    global running
    logger.info(f"Получен сигнал {sig}, завершение работы...")
    running = False

# Регистрация обработчиков сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def record_and_transcribe(continuous=False):
    """
    Запись и транскрибация аудио.
    
    Args:
        continuous (bool): Если True, то продолжать запись после транскрибации
        
    Returns:
        str: Путь к сохраненной заметке или None
    """
    global running
    recorder = AudioRecorder()
    transcriber_model = config.WHISPER_MODEL
    
    try:
        while running:
            logger.info("Начало сессии записи")
            
            # Запись аудио
            audio_file = recorder.start_recording()
            
            # Проверяем, не было ли получено сигнала остановки во время записи
            if not running:
                logger.info("Запись прервана по сигналу остановки")
                break
                
            if not audio_file:
                logger.warning("Запись не была создана")
                if not continuous:
                    return None
                time.sleep(1)  # Пауза перед повторной попыткой
                continue
                
            logger.info(f"Аудио сохранено в {audio_file}")
            
            # Транскрибация
            logger.info("Начало транскрибации")
            note_path = transcribe_audio(audio_file, transcriber_model)
            
            if note_path:
                logger.info(f"Заметка сохранена в {note_path}")
            else:
                logger.error("Транскрибация не удалась")
                
            # Если режим не continuous, то выходим
            if not continuous:
                return note_path
                
            # Проверяем состояние перед повторной записью
            if not running:
                logger.info("Запись остановлена по сигналу")
                break
                
            logger.info("Ожидание новой сессии записи...")
            time.sleep(1)  # Небольшая пауза перед новой сессией
            
    except KeyboardInterrupt:
        logger.info("Запись остановлена пользователем")
        return None
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return None
    
    logger.info("Завершение процесса записи")
    return None


def main():
    """Основная функция для запуска."""
    parser = argparse.ArgumentParser(description='Система автоматической фиксации разговоров')
    parser.add_argument('--start', action='store_true', help='Запуск записи')
    parser.add_argument('--continuous', action='store_true', help='Непрерывный режим записи')
    parser.add_argument('--model', type=str, default=None, help='Модель Whisper для транскрибации')
    
    args = parser.parse_args()
    
    if args.model:
        config.WHISPER_MODEL = args.model
        
    if args.start:
        print("Запуск автоматической записи разговоров.")
        print("Для остановки нажмите Ctrl+C")
        
        if args.continuous:
            print("Включен непрерывный режим. Система будет работать до ручной остановки.")
            
        note_path = record_and_transcribe(args.continuous)
        
        if note_path:
            print(f"Заметка сохранена в: {note_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 