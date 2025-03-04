# AI Notes - приложение для аудиозаписи и транскрибации речи

Приложение для автоматической записи аудио, транскрибации речи и поиска по заметкам с использованием OpenAI Whisper.

## Основные функции

- **Запись аудио**: Автоматическая запись речи с микрофона
- **Транскрибация**: Преобразование аудио в текст с помощью Whisper
- **Поиск по заметкам**: Веб-интерфейс для поиска по транскрибированным заметкам
- **Управление рекордером**: Веб-интерфейс для мониторинга и управления аудиозаписью

## Компоненты приложения

1. **Аудио рекордер**: Записывает аудио с микрофона, обнаруживает речь и сохраняет аудиофайлы
2. **Транскрибер**: Преобразует аудиофайлы в текстовые заметки с использованием Whisper
3. **Веб-интерфейс**:
   - Поиск по транскрибированным заметкам
   - Управление рекордером (запуск/остановка записи)
   - Мониторинг статуса рекордера
   - Просмотр списка записей

## Структура проекта

Проект разделен на бэкенд и фронтенд:

- **backend/**: Серверная часть, включающая Python-модули для обработки аудио, транскрибации и API
- **frontend/**: Клиентская часть, включающая HTML-шаблоны и статические файлы (CSS, JavaScript)
- **audio/**: Каталог для хранения аудиозаписей
- **notes/**: Каталог для хранения транскрибированных заметок

## Режимы работы

- **Локальный режим**: Запуск рекордера и веб-интерфейса на локальной машине
- **Docker-режим**: Запуск компонентов в контейнерах Docker
- **Сервисный режим**: Запуск в качестве системных служб с автоматическим перезапуском

## Варианты запуска

1. **Веб-интерфейс**:

   ```bash
   python app.py
   ```

   Доступ к веб-интерфейсу: http://localhost:8000

2. **Рекордер через командную строку**:

   ```bash
   python recorder.py --start
   ```

3. **Docker**:
   ```bash
   ./docker-service.sh start
   ```

## Требования

- Python 3.10+
- ffmpeg (для обработки аудио)
- PyAudio/sounddevice (для записи звука)
- Whisper (для транскрибации)
- FastAPI (для веб-интерфейса)

## Подробная документация

Подробное руководство по установке, настройке и использованию приложения смотрите в [README_USAGE.md](README_USAGE.md).
