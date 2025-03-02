FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . /app/

# Создание необходимых директорий
RUN mkdir -p /app/audio /app/notes /app/frontend/templates /app/frontend/static/css

# Установка зависимостей
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Установка ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Предварительная загрузка модели Whisper (опционально)
RUN python -c "import whisper; whisper.load_model('base')"

# Добавляем healthcheck для веб-приложения
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Порт для веб-интерфейса
EXPOSE 8000

# Сохранение данных в том
VOLUME ["/app/audio", "/app/notes"]

# Запуск веб-интерфейса по умолчанию
CMD ["python", "app.py"]

# Для запуска рекордера используйте:
# docker run --device /dev/snd:/dev/snd -v ./audio:/app/audio -v ./notes:/app/notes ai-notes python backend/recorder.py --start 