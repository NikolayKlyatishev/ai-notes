"""
Модуль для настройки логирования в приложении.
"""
import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.config import LOG_LEVEL, LOG_FORMAT

# Максимальный размер файла лога (10 МБ)
MAX_LOG_SIZE = 10 * 1024 * 1024
# Количество файлов для ротации
BACKUP_COUNT = 5


def setup_logger(name: str, log_file: str = None, level: str = None) -> logging.Logger:
    """
    Настройка логгера с заданным именем и файлом.
    
    Args:
        name (str): Имя логгера
        log_file (str, optional): Путь к файлу лога. Если не указан, используется имя логгера
        level (str, optional): Уровень логирования. Если не указан, используется значение из конфигурации
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Получение или создание логгера
    logger = logging.getLogger(name)
    
    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger
    
    # Определение уровня логирования
    log_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Определение пути к файлу лога
    if log_file is None:
        # Используем имя логгера для создания имени файла
        module_name = name.split('.')[-1]
        log_file = f"{module_name}.log"
    
    # Создание директории для логов, если она не существует
    log_dir = Path(Path(__file__).resolve().parent.parent, "logs")
    log_dir.mkdir(exist_ok=True)
    
    log_path = log_dir / log_file
    
    # Создание обработчика для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # Создание обработчика для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Создание форматтера
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Установка форматтера для обработчиков
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Добавление обработчиков к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Отключение распространения логов на родительские логгеры
    logger.propagate = False
    
    logger.debug(f"Логгер {name} настроен с уровнем {log_level}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получение настроенного логгера по имени.
    Если логгер с таким именем не существует, он будет создан.
    
    Args:
        name (str): Имя логгера
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    # Если логгер не настроен, настраиваем его
    if not logger.handlers:
        logger = setup_logger(name)
    
    return logger 