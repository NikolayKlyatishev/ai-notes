"""
Веб-интерфейс для поиска по заметкам.
"""
import os
import json
import signal
import sys
import time
import asyncio
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Form, Query, Body, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
from pathlib import Path
from functools import lru_cache

# Добавляем каталог backend в путь поиска модулей
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from search import NotesSearcher
import config
from config import AUDIO_DIR, NOTES_DIR
import recorder_api as recorder_api

# Настройка логирования
log_file = os.path.join(os.path.dirname(__file__), "webapp.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создаем директорию для шаблонов
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "templates")
os.makedirs(templates_dir, exist_ok=True)

# Создаем базовый HTML шаблон только если он не существует
index_template_path = os.path.join(templates_dir, "index.html")
if not os.path.exists(index_template_path):
    with open(index_template_path, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Поиск по заметкам</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .search-form {
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .form-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .form-group label {
            width: 100px;
        }
        input, button {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        input[type="text"] {
            flex-grow: 1;
        }
        input[type="date"] {
            width: 150px;
        }
        button {
            background-color: #4285f4;
            color: white;
            cursor: pointer;
            border: none;
            padding: 10px 15px;
            margin-top: 10px;
            align-self: flex-end;
        }
        button:hover {
            background-color: #3367d6;
        }
        .results {
            margin-top: 20px;
        }
        .note {
            border-bottom: 1px solid #eee;
            padding: 15px 0;
        }
        .note:last-child {
            border-bottom: none;
        }
        .note-date {
            color: #666;
            font-size: 0.9em;
        }
        .tags {
            margin: 5px 0;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        .tag {
            background-color: #e0e0e0;
            border-radius: 3px;
            padding: 3px 8px;
            font-size: 0.8em;
            color: #333;
        }
        .transcript {
            margin-top: 10px;
            line-height: 1.5;
        }
        .no-results {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Поиск по заметкам</h1>
        
        <form class="search-form" method="post">
            <div class="form-group">
                <label for="query">Поиск:</label>
                <input type="text" id="query" name="query" placeholder="Введите ключевые слова" value="{{ query }}">
            </div>
            <div class="form-group">
                <label for="date_from">От:</label>
                <input type="date" id="date_from" name="date_from" value="{{ date_from }}">
                <label for="date_to">До:</label>
                <input type="date" id="date_to" name="date_to" value="{{ date_to }}">
            </div>
            <button type="submit">Найти</button>
        </form>
        
        <div class="results">
            {% if results %}
                {% for note in results %}
                    <div class="note">
                        <div class="note-date">{{ note.date }}</div>
                        <div class="tags">
                            {% for tag in note.tags %}
                                <span class="tag">{{ tag }}</span>
                            {% endfor %}
                        </div>
                        <div class="transcript">{{ note.transcript }}</div>
                    </div>
                {% endfor %}
            {% elif searched %}
                <div class="no-results">Ничего не найдено</div>
            {% endif %}
        </div>
    </div>
</body>
</html>""")

# Инициализация FastAPI
app = FastAPI(title="Поиск по заметкам и управление рекордером")

# Настройка шаблонов и статических файлов
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
templates = Jinja2Templates(directory=os.path.join(frontend_dir, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")
app.mount("/notes", StaticFiles(directory=NOTES_DIR), name="notes")

# Модели данных для API
class SearchQuery(BaseModel):
    query: str
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    date: str
    transcript: str
    audio_file: Optional[str] = None
    relevance: float

class RecorderStartParams(BaseModel):
    continuous: bool = True
    model: str = "base"

class RecorderTranscribeParams(BaseModel):
    model: str = "base"  # Параметр для выбора модели Whisper

class RecorderResponse(BaseModel):
    status: str
    message: str

# Кэш для статуса рекордера (время жизни 500ms)
last_status_time = 0
last_status_data = None
STATUS_CACHE_TTL = 0.5  # секунды

# Глобальная переменная для хранения активных SSE-клиентов
sse_clients = set()

@app.get("/", response_class=HTMLResponse)
async def get_search_page(request: Request):
    """Отображение страницы поиска."""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "query": "",
            "date_from": "",
            "date_to": "",
            "results": [],
            "searched": False
        }
    )

@app.get("/recorder", response_class=HTMLResponse)
async def get_recorder_page(request: Request):
    """Отображение страницы управления рекордером."""
    return templates.TemplateResponse(
        "recorder.html", 
        {
            "request": request
        }
    )

@app.post("/", response_class=HTMLResponse)
async def search_notes(
    request: Request,
    query: str = Form(""),
    date_from: str = Form(""),
    date_to: str = Form("")
):
    """Обработка поиска по заметкам."""
    searcher = NotesSearcher()
    results = searcher.search_by_keywords(query, date_from, date_to)
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "query": query,
            "date_from": date_from,
            "date_to": date_to,
            "results": results,
            "searched": True
        }
    )

# API для поиска по заметкам
@app.post("/api/search")
async def search(query: SearchQuery) -> Dict[str, List[SearchResult]]:
    try:
        # Здесь должна быть логика поиска по заметкам
        # В данном примере возвращаем пустой результат
        logger.info(f"Поисковый запрос: {query.query}")
        return {"results": []}
    except Exception as e:
        logger.error(f"Ошибка при поиске: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API для получения статуса рекордера
@app.get("/api/recorder/status/stream")
async def stream_status():
    """
    Эндпоинт для SSE (Server-Sent Events) - передает обновления статуса рекордера
    в режиме реального времени.
    """
    async def event_generator():
        # Добавляем клиента в список активных клиентов
        client_queue = asyncio.Queue()
        sse_clients.add(client_queue)
        
        # Отправляем текущий статус при подключении
        try:
            status = recorder_api.get_status()
            await client_queue.put(json.dumps(status))
            
            try:
                # Держим соединение открытым, пока клиент не отключится
                while True:
                    # Ждем новые данные в очереди клиента
                    data = await client_queue.get()
                    # Формируем SSE-сообщение
                    yield f"data: {data}\n\n"
            except asyncio.CancelledError:
                # Клиент отключился
                pass
            finally:
                # Удаляем клиента из списка
                sse_clients.remove(client_queue)
        except Exception as e:
            logger.error(f"Ошибка SSE: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            sse_clients.remove(client_queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

# Запускаем фоновую задачу для периодического обновления статуса
@app.on_event("startup")
async def start_status_updater():
    """Запускает фоновую задачу для периодического обновления статуса"""
    # Регистрируем наш коллбэк в recorder_api
    recorder_api.set_status_update_callback(broadcast_status_update_sync)
    # Запускаем периодическое обновление
    asyncio.create_task(status_updater())

# Функция для отправки обновлений всем подключенным клиентам
async def broadcast_status_update():
    """Отправляет обновление статуса всем подключенным SSE клиентам"""
    # Получаем текущий статус
    status = recorder_api.get_status()
    status_json = json.dumps(status)
    
    # Отправляем всем клиентам
    for client_queue in sse_clients:
        try:
            await client_queue.put(status_json)
        except Exception as e:
            logger.error(f"Ошибка при отправке обновления клиенту: {str(e)}")

# Функция-мост для синхронного вызова из recorder_api
def broadcast_status_update_sync():
    """Синхронный коллбэк для вызова из recorder_api"""
    try:
        # Используем нестандартный подход, так как находимся в фоновом потоке
        from asyncio.runners import Runner
        
        async def _broadcast():
            try:
                # Получаем статус рекордера и отправляем всем клиентам
                status = recorder_api.get_status()
                status_json = json.dumps(status)
                
                # Используем глобальную переменную из родительского скопа
                global sse_clients
                
                # Отправляем клиентам, если они есть
                if sse_clients:
                    for client_queue in list(sse_clients):
                        try:
                            # Неблокирующая отправка сообщения в очередь
                            await asyncio.wait_for(client_queue.put(status_json), timeout=0.1)
                        except Exception as e:
                            # Игнорируем ошибки при отправке
                            pass
            except Exception as e:
                # Безопасно логируем ошибки, которые могут возникнуть
                print(f"Ошибка при обновлении статуса в фоновом потоке: {e}")
        
        # Создаем и запускаем новый изолированный event loop
        with Runner() as runner:
            runner.run(_broadcast())
    except ImportError:
        # Для Python версий, где нет Runner
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(broadcast_status_update())
            loop.close()
        except Exception as e:
            # Безопасно логируем ошибки
            print(f"Ошибка при обновлении статуса в фоновом потоке: {e}")
    except Exception as e:
        # Перехватываем любые другие ошибки
        print(f"Ошибка при обновлении статуса в фоновом потоке: {e}")

async def status_updater():
    """Периодически отправляет обновления статуса всем подключенным клиентам"""
    while True:
        if sse_clients:  # Только если есть подключенные клиенты
            await broadcast_status_update()
        await asyncio.sleep(1)  # Обновление каждую секунду

# Старый эндпоинт можно оставить для совместимости, но со значительным кэшированием
@app.get("/api/recorder/status")
async def get_recorder_status():
    """
    Получение статуса рекордера.
    Использует кэширование для снижения нагрузки на сервер при частых запросах.
    """
    global last_status_time, last_status_data
    
    current_time = time.time()
    
    # Если кэш не устарел, возвращаем закэшированные данные
    if last_status_data and (current_time - last_status_time) < STATUS_CACHE_TTL:
        return last_status_data
    
    # Иначе получаем свежие данные и обновляем кэш
    try:
        status = recorder_api.get_status()
        last_status_data = status
        last_status_time = current_time
        return status
    except Exception as e:
        logger.error(f"Ошибка при получении статуса рекордера: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API для запуска рекордера
@app.post("/api/recorder/start")
async def start_recorder(params: RecorderStartParams) -> RecorderResponse:
    try:
        result = recorder_api.start_recorder(
            continuous=params.continuous,
            model=params.model
        )
        return result
    except Exception as e:
        logger.error(f"Ошибка при запуске рекордера: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API для остановки рекордера
@app.post("/api/recorder/stop")
async def stop_recorder(background_tasks: BackgroundTasks) -> RecorderResponse:
    try:
        result = recorder_api.stop_recorder(background_tasks)
        return result
    except Exception as e:
        logger.error(f"Ошибка при остановке рекордера: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API для ручной транскрибации всех файлов
@app.post("/api/recorder/transcribe")
async def transcribe_all(params: RecorderTranscribeParams, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    try:
        # Запускаем транскрибацию в фоновом режиме
        background_tasks.add_task(
            recorder_api.transcribe_untranscribed_files,
            model=params.model
        )
        return {
            "status": "success", 
            "message": "Транскрибирование запущено в фоновом режиме"
        }
    except Exception as e:
        logger.error(f"Ошибка при транскрибации: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API для получения списка записей
@app.get("/api/recorder/recordings")
async def get_recordings():
    try:
        return recorder_api.get_recordings()
    except Exception as e:
        logger.error(f"Ошибка при получении списка записей: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def run_web_app(host="0.0.0.0", port=8000):
    """Запуск веб-приложения."""
    # Настройка для корректного завершения работы
    def handle_exit(signum, frame):
        logger.info(f"Получен сигнал {signum}, завершение работы веб-приложения...")
        sys.exit(0)
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    logger.info(f"Запуск веб-интерфейса на http://{host}:{port}")
    
    # Запуск с настройками для работы в режиме сервиса
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info",
        access_log=True,
        reload=False
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Веб-интерфейс для поиска по заметкам')
    parser.add_argument('--host', type=str, default="0.0.0.0", help='Хост для запуска')
    parser.add_argument('--port', type=int, default=8000, help='Порт для запуска')
    
    args = parser.parse_args()
    
    print(f"Запуск веб-интерфейса на http://{args.host}:{args.port}")
    run_web_app(args.host, args.port) 