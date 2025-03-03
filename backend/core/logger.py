"""
Модуль для настройки логирования в приложении.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.core.config import LOG_LEVEL, LOG_FORMAT, BACKEND_DIR


def setup_logger(name, log_file=None):
    """
    Настройка и получение логгера с указанным именем.
    
    Args:
        name (str): Имя логгера
        log_file (str, optional): Имя файла для логирования. По умолчанию используется имя модуля.
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Определение уровня логирования
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    
    # Создание логгера
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Если у логгера уже есть обработчики, возвращаем его
    if logger.handlers:
        return logger
    
    # Определение файла для логов
    if log_file is None:
        log_file = f"{name.split('.')[-1]}.log"
    
    log_path = BACKEND_DIR / log_file
    
    # Создание обработчиков
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=3
    )
    console_handler = logging.StreamHandler()
    
    # Установка форматирования
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Добавление обработчиков к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 