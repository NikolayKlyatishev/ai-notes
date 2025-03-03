# AI Notes

Система автоматической фиксации разговоров с использованием искусственного интеллекта.

## Структура проекта

Проект состоит из двух основных частей:

1. **Backend** - API-сервер на Python с использованием FastAPI
2. **Frontend** - Клиентское приложение на React с TypeScript

### Структура Backend

```
backend/
├── api/            # API-эндпоинты
├── core/           # Конфигурация и общие компоненты
├── models/         # Модели данных
├── services/       # Бизнес-логика
├── web/            # Веб-интерфейс
└── app.py          # Основной файл приложения
```

### Структура Frontend

```
frontend/
├── public/         # Статические файлы
├── src/            # Исходный код
│   ├── api/        # API-клиенты
│   ├── components/ # React-компоненты
│   ├── context/    # React-контексты
│   ├── hooks/      # Пользовательские хуки
│   ├── pages/      # Страницы приложения
│   ├── types/      # TypeScript типы
│   ├── utils/      # Вспомогательные функции
│   └── App.tsx     # Основной компонент
└── package.json    # Зависимости
```

## Требования

- Python 3.8+
- Node.js 14+
- FFmpeg (для записи и обработки аудио)
- Whisper (для транскрибации)
- Доступ к микрофону

## Быстрый старт

### Установка и запуск Backend

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/yourusername/ai-notes.git
   cd ai-notes
   ```

2. Создайте и активируйте виртуальное окружение:

   ```bash
   python -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   ```

3. Установите зависимости:

   ```bash
   pip install -e ".[transcription]"
   ```

4. Запустите сервер:
   ```bash
   python -m backend.app web
   ```

### Установка и запуск Frontend

1. Перейдите в директорию frontend:

   ```bash
   cd frontend
   ```

2. Установите зависимости:

   ```bash
   npm install
   ```

3. Запустите приложение в режиме разработки:

   ```bash
   npm start
   ```

4. Откройте [http://localhost:3000](http://localhost:3000) в браузере.

## Команды для запуска

### Backend

- Запуск всех компонентов:

  ```bash
  python -m backend.app --all
  ```

- Запуск только веб-интерфейса:

  ```bash
  python -m backend.app --web
  ```

- Запуск только рекордера:

  ```bash
  python -m backend.app --recorder
  ```

- Запуск рекордера в непрерывном режиме:
  ```bash
  python -m backend.app --recorder-continuous
  ```

### Frontend

- Запуск в режиме разработки:

  ```bash
  npm start
  ```

- Сборка для продакшена:

  ```bash
  npm run build
  ```

- Запуск тестов:
  ```bash
  npm test
  ```

## Веб-интерфейс

После запуска веб-интерфейс будет доступен по адресу:

- Backend API: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:3000](http://localhost:3000)

## Лицензия

MIT
