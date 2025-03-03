"""
Главный модуль приложения AI Notes, интегрирующий API-сервер и сервисы для работы с заметками.
"""
import os
import sys
import time
import signal
import logging
import argparse
import threading
from pathlib import Path

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.core.logger import setup_logger
from backend.core.config import WEB_HOST, WEB_PORT

# Настройка логирования
logger = setup_logger("backend.app")

# Флаг для отслеживания состояния приложения
running = True


def signal_handler(sig, frame):
    """
    Обработчик сигналов для корректного завершения приложения.
    
    Args:
        sig: Сигнал
        frame: Фрейм выполнения
    """
    global running
    logger.info(f"Получен сигнал {sig}, завершение работы...")
    running = False


def parse_args():
    """
    Парсинг аргументов командной строки.
    
    Returns:
        argparse.Namespace: Аргументы командной строки
    """
    parser = argparse.ArgumentParser(description="AI Notes - система автоматической фиксации разговоров")
    
    # Создание группы взаимоисключающих аргументов
    group = parser.add_mutually_exclusive_group(required=True)
    
    # Добавление аргументов
    group.add_argument("--all", action="store_true", help="Запустить API-сервер и фоновые сервисы")
    group.add_argument("--api", action="store_true", help="Запустить только API-сервер")
    group.add_argument("--recorder", action="store_true", help="Запустить только рекордер")
    group.add_argument("--recorder-continuous", action="store_true", help="Запустить рекордер в непрерывном режиме")
    
    return parser.parse_args()


def import_api():
    """
    Импорт API-сервера.
    
    Returns:
        module: API-приложение
    """
    try:
        from backend.web.app import app as api_app
        return api_app
    except ImportError as e:
        logger.error(f"Ошибка импорта API-модуля: {e}")
        return None


def import_recorder():
    """
    Импорт модуля рекордера.
    
    Returns:
        module: Модуль рекордера
    """
    try:
        from backend.services.recorder import record_and_transcribe
        return record_and_transcribe
    except ImportError as e:
        logger.error(f"Ошибка импорта модуля рекордера: {e}")
        return None


def run_api():
    """
    Запуск API-сервера.
    
    Returns:
        bool: True, если запуск успешен, иначе False
    """
    try:
        api_app = import_api()
        
        if not api_app:
            logger.error("Не удалось импортировать API-модуль")
            return False
        
        import uvicorn
        
        logger.info(f"Запуск API-сервера на {WEB_HOST}:{WEB_PORT}")
        uvicorn.run(api_app, host=WEB_HOST, port=WEB_PORT)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске API-сервера: {e}")
        return False


def run_recorder(continuous=False):
    """
    Запуск рекордера.
    
    Args:
        continuous (bool): Флаг непрерывного режима
        
    Returns:
        bool: True, если запуск успешен, иначе False
    """
    try:
        record_and_transcribe = import_recorder()
        
        if not record_and_transcribe:
            logger.error("Не удалось импортировать модуль рекордера")
            return False
        
        logger.info(f"Запуск рекордера в {'непрерывном' if continuous else 'обычном'} режиме")
        
        while running:
            record_and_transcribe(continuous=continuous)
            
            if not continuous:
                break
            
            # Пауза между записями в непрерывном режиме
            time.sleep(1)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске рекордера: {e}")
        return False


def run_all():
    """
    Запуск всех компонентов приложения.
    
    Returns:
        bool: True, если запуск успешен, иначе False
    """
    try:
        # Запуск API-сервера в отдельном потоке
        api_thread = threading.Thread(target=run_api)
        api_thread.daemon = True
        api_thread.start()
        
        logger.info("API-сервер запущен в отдельном потоке")
        
        # Запуск рекордера в основном потоке
        run_recorder(continuous=True)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске всех компонентов: {e}")
        return False


def main():
    """
    Основная функция приложения.
    """
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Парсинг аргументов командной строки
    args = parse_args()
    
    try:
        if args.all:
            logger.info("Запуск API-сервера и фоновых сервисов")
            run_all()
        elif args.api:
            logger.info("Запуск только API-сервера")
            run_api()
        elif args.recorder:
            logger.info("Запуск только рекордера")
            run_recorder(continuous=False)
        elif args.recorder_continuous:
            logger.info("Запуск рекордера в непрерывном режиме")
            run_recorder(continuous=True)
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершение работы...")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")
    finally:
        logger.info("Приложение завершило работу")


if __name__ == "__main__":
    main() 