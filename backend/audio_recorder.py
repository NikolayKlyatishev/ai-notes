"""
Модуль для записи аудио с определением голосовой активности (VAD).
"""
import os
import time
import wave
import logging
import numpy as np
import webrtcvad
import sounddevice as sd
from datetime import datetime

import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self):
        """Инициализация рекордера аудио с VAD."""
        self.vad = webrtcvad.Vad(config.VAD_AGGRESSIVENESS)
        self.sample_rate = config.SAMPLE_RATE
        self.frame_duration_ms = config.FRAME_DURATION_MS
        self.silence_threshold = config.SILENCE_THRESHOLD
        self.audio_buffer = []
        self.is_recording = False
        self.last_voice_time = 0
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        logger.info("Инициализирован AudioRecorder с параметрами: "
                   f"sample_rate={self.sample_rate}, "
                   f"frame_duration_ms={self.frame_duration_ms}, "
                   f"silence_threshold={self.silence_threshold}s")

    def is_speech(self, audio_frame):
        """Определяет, содержит ли аудио-фрейм речь."""
        # Преобразуем float32 [-1.0, 1.0] в int16 для VAD
        audio_int16 = (audio_frame * 32768).astype(np.int16)
        # Конвертируем в bytes для WebRTC VAD
        audio_bytes = audio_int16.tobytes()
        try:
            return self.vad.is_speech(audio_bytes, self.sample_rate)
        except Exception as e:
            logger.error(f"Ошибка при определении речи: {e}")
            return False

    def callback(self, indata, frames, time_info, status):
        """Функция обратного вызова для потока аудио."""
        if status:
            logger.warning(f"Status в callback: {status}")
            
        # Проверяем наличие речи
        if self.is_speech(indata.flatten()):
            if not self.is_recording:
                logger.info("Обнаружена речь, начинаем запись")
                self.is_recording = True
            self.last_voice_time = time.time()
        
        # Если мы записываем, добавляем данные в буфер
        if self.is_recording:
            self.audio_buffer.append(indata.copy())
            
            # Проверяем, прошло ли достаточно времени без речи для остановки
            if time.time() - self.last_voice_time > self.silence_threshold:
                logger.info(f"Тишина более {self.silence_threshold} секунд, останавливаем запись")
                self.is_recording = False
                # Сигнал для остановки потока
                raise sd.CallbackStop()

    def start_recording(self):
        """Запускает поток записи аудио с VAD."""
        self.audio_buffer = []
        self.is_recording = False
        self.last_voice_time = 0
        
        try:
            logger.info("Ожидание речи для начала записи...")
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=config.CHANNELS,
                callback=self.callback,
                blocksize=self.frame_size
            ):
                # Ждем, пока поток не остановится через CallbackStop
                sd.sleep(1000 * 60 * 60)  # Максимальное время ожидания - 1 час
        except Exception as e:
            logger.error(f"Ошибка при записи: {e}")
        
        return self.save_audio() if self.audio_buffer else None

    def save_audio(self):
        """Сохраняет записанное аудио в файл WAV."""
        if not self.audio_buffer:
            logger.warning("Буфер аудио пуст, нечего сохранять")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(config.AUDIO_DIR, f"recording_{timestamp}.wav")
        
        try:
            logger.info(f"Сохранение аудио в {filename}")
            audio_data = np.concatenate(self.audio_buffer, axis=0)
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(config.CHANNELS)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                # Преобразуем float32 [-1.0, 1.0] в int16 для WAV
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
                
            logger.info(f"Аудио успешно сохранено в {filename}")
            return filename
        except Exception as e:
            logger.error(f"Ошибка при сохранении аудио: {e}")
            return None


if __name__ == "__main__":
    # Тестирование
    recorder = AudioRecorder()
    audio_file = recorder.start_recording()
    if audio_file:
        print(f"Аудио сохранено в {audio_file}")
    else:
        print("Запись не была сохранена") 