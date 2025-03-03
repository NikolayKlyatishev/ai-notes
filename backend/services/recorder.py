"""
Модуль для записи аудио с микрофона.
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.logger import setup_logger
from backend.core.config import (
    AUDIO_DIR, SAMPLE_RATE, CHANNELS, SILENCE_THRESHOLD, 
    FRAME_DURATION_MS, VAD_AGGRESSIVENESS
)
from backend.services.transcriber import transcribe_audio

# Глобальные переменные
running = True

# Настройка логирования
logger = setup_logger("backend.services.recorder")


class AudioRecorder:
    """Класс для записи аудио с микрофона."""
    
    def __init__(self):
        """Инициализация рекордера."""
        logger.info("Инициализация AudioRecorder")
        
        # Динамически импортируем зависимости
        # Это позволяет приложению работать даже если не все зависимости установлены
        try:
            global pyaudio, wave, webrtcvad, collections, array, struct
            import pyaudio
            import wave
            import webrtcvad
            import collections
            import array
            import struct
            self.dependencies_loaded = True
        except ImportError as e:
            logger.error(f"Не удалось загрузить зависимости для AudioRecorder: {e}")
            self.dependencies_loaded = False
            return
        
        # Инициализация PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self.frames = []
        self.silence_frames = 0
        self.max_silence_frames = int(SILENCE_THRESHOLD * (SAMPLE_RATE / 1024))  # примерно 2 минуты тишины
        self.recording = False
        self.done_recording = False
        
        # Создание директории для аудио, если она не существует
        os.makedirs(AUDIO_DIR, exist_ok=True)
    
    def start_recording(self):
        """Запуск записи аудио."""
        if not self.dependencies_loaded:
            logger.error("Невозможно начать запись, зависимости не загружены")
            return False
        
        try:
            logger.info("Начало записи аудио")
            
            # Открытие аудио потока
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=1024
            )
            
            self.frames = []
            self.silence_frames = 0
            self.recording = True
            self.done_recording = False
            
            logger.info("Запись аудио начата успешно")
            return True
        except Exception as e:
            logger.error(f"Ошибка при запуске записи: {e}")
            return False
    
    def process_audio(self):
        """Обработка аудио потока с определением голосовой активности."""
        if not self.recording or not self.dependencies_loaded:
            return False
        
        try:
            # Чтение чанка аудио данных
            data = self.stream.read(1024)
            self.frames.append(data)
            
            # Проверка голосовой активности
            if len(data) == 2048:  # 1024 сэмплов * 2 байта на сэмпл
                is_speech = self.vad.is_speech(data, SAMPLE_RATE)
                if not is_speech:
                    self.silence_frames += 1
                else:
                    self.silence_frames = 0  # Сбрасываем счетчик при обнаружении речи
                
                # Проверка на длительную тишину
                if self.silence_frames >= self.max_silence_frames:
                    logger.info(f"Обнаружена тишина в течение {SILENCE_THRESHOLD} секунд, останавливаем запись")
                    self.stop_recording()
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио: {e}")
            self.stop_recording()
            return False
    
    def stop_recording(self):
        """Остановка записи аудио."""
        if not self.recording or not self.dependencies_loaded:
            return None
        
        try:
            logger.info("Остановка записи аудио")
            
            # Закрытие аудио потока
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            self.recording = False
            self.done_recording = True
            
            # Если записаны кадры, сохраняем их в файл
            if self.frames:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(AUDIO_DIR, f"recording_{timestamp}.wav")
                
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(b''.join(self.frames))
                
                logger.info(f"Аудио сохранено в файл: {filename}")
                return filename
            
            return None
        except Exception as e:
            logger.error(f"Ошибка при остановке записи: {e}")
            return None
    
    def cleanup(self):
        """Очистка ресурсов."""
        try:
            if self.stream:
                self.stream.close()
            
            if self.audio:
                self.audio.terminate()
            
            logger.info("Ресурсы AudioRecorder освобождены")
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов: {e}")


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
        tuple: (аудио_файл, транскрипция) или (None, None) в случае ошибки
    """
    global running
    recorder = AudioRecorder()
    
    if not recorder.dependencies_loaded:
        logger.error("Невозможно начать запись, зависимости не загружены")
        return None, None
    
    audio_file = None
    transcription = None
    
    try:
        logger.info("Начало сеанса записи")
        
        while running:
            # Запускаем запись
            if not recorder.start_recording():
                break
            
            logger.info("Запись начата. Говорите...")
            
            # Обрабатываем аудио поток
            while recorder.recording and running:
                if not recorder.process_audio():
                    break
                time.sleep(0.01)  # Небольшая задержка для предотвращения высокой загрузки ЦП
            
            # Останавливаем запись
            audio_file = recorder.stop_recording()
            
            if audio_file:
                logger.info(f"Запись завершена и сохранена: {audio_file}")
                
                # Транскрибация записи
                try:
                    transcription = transcribe_audio(audio_file)
                    logger.info(f"Транскрипция завершена: {transcription[:100]}...")
                except Exception as e:
                    logger.error(f"Ошибка при транскрибации: {e}")
                    transcription = None
            
            # Если не в режиме постоянной записи, завершаем
            if not continuous:
                break
        
        logger.info("Сеанс записи завершен")
    except Exception as e:
        logger.error(f"Ошибка в процессе записи: {e}")
    finally:
        # Освобождаем ресурсы
        recorder.cleanup()
    
    return audio_file, transcription


def main():
    """Основная функция для однократной записи и транскрипции."""
    try:
        record_and_transcribe(continuous=False)
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")


def main_continuous():
    """Основная функция для непрерывной записи и транскрипции."""
    try:
        record_and_transcribe(continuous=True)
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")


if __name__ == "__main__":
    main_continuous() 