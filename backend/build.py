#!/usr/bin/env python3
"""
Скрипт для сборки приложения с помощью PyInstaller.
Создает исполняемые файлы для записи аудио и веб-интерфейса.
"""
import os
import platform
import subprocess
import shutil
import sys
from pathlib import Path

# Имена выходных файлов
RECORDER_OUTPUT = "ai-notes-recorder"
WEB_APP_OUTPUT = "ai-notes-webapp"

# Получаем текущую директорию
BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"

# Определяем используемый интерпретатор Python
PYTHON_CMD = sys.executable or "python3"
if not shutil.which(PYTHON_CMD):
    # Проверяем другие варианты Python
    for cmd in ["python3", "python"]:
        if shutil.which(cmd):
            PYTHON_CMD = cmd
            break
    else:
        print("ОШИБКА: Не найден интерпретатор Python. Пожалуйста, установите Python 3.")
        sys.exit(1)

print(f"Используемый интерпретатор Python: {PYTHON_CMD}")

# Очищаем директорию сборки, если она существует
if os.path.exists(DIST_DIR):
    print(f"Очистка директории dist: {DIST_DIR}")
    shutil.rmtree(DIST_DIR)

# Создаем директории для хранения данных
for dir_name in ["audio", "notes", "templates"]:
    os.makedirs(os.path.join(DIST_DIR, dir_name), exist_ok=True)

def build_recorder():
    """Сборка приложения для записи."""
    print("\n" + "=" * 50)
    print("Сборка приложения для записи аудио...")
    
    # Настройка параметров PyInstaller для recorder.py
    cmd = [
        PYTHON_CMD, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--clean",
        "--name", RECORDER_OUTPUT,
        "--add-data", f"templates{os.pathsep}templates",
        # Исключаем ненужные модули, которые добавляет PyInstaller по умолчанию
        "--exclude-module", "matplotlib",
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "wx",
        "recorder.py"
    ]
    
    # Запуск сборки
    subprocess.run(cmd)
    print("Сборка приложения для записи завершена.")

def build_webapp():
    """Сборка веб-приложения."""
    print("\n" + "=" * 50)
    print("Сборка веб-приложения...")
    
    # Настройка параметров PyInstaller для web_app.py
    cmd = [
        PYTHON_CMD, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--clean",
        "--name", WEB_APP_OUTPUT,
        "--add-data", f"templates{os.pathsep}templates",
        # Исключаем ненужные модули
        "--exclude-module", "matplotlib",
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "wx",
        "web_app.py"
    ]
    
    # Запуск сборки
    subprocess.run(cmd)
    print("Сборка веб-приложения завершена.")

def create_launcher_script():
    """Создание вспомогательного скрипта запуска."""
    print("\n" + "=" * 50)
    print("Создание скрипта запуска...")
    
    # Определяем расширение исполняемого файла в зависимости от ОС
    ext = ".exe" if platform.system() == "Windows" else ""
    
    # Создаем скрипт запуска для Windows
    if platform.system() == "Windows":
        with open(os.path.join(DIST_DIR, "start_recorder.bat"), "w") as f:
            f.write(f"@echo off\n")
            f.write(f"echo Запуск AI Notes Recorder...\n")
            f.write(f"{RECORDER_OUTPUT}{ext} --start\n")
            f.write(f"pause\n")
            
        with open(os.path.join(DIST_DIR, "start_webapp.bat"), "w") as f:
            f.write(f"@echo off\n")
            f.write(f"echo Запуск веб-интерфейса AI Notes...\n")
            f.write(f"echo Откройте http://localhost:8000 в вашем браузере\n")
            f.write(f"{WEB_APP_OUTPUT}{ext}\n")
            f.write(f"pause\n")
    
    # Создаем скрипт запуска для Linux/macOS
    else:
        with open(os.path.join(DIST_DIR, "start_recorder.sh"), "w") as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"echo 'Запуск AI Notes Recorder...'\n")
            f.write(f"./{RECORDER_OUTPUT}{ext} --start\n")
            
        with open(os.path.join(DIST_DIR, "start_webapp.sh"), "w") as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"echo 'Запуск веб-интерфейса AI Notes...'\n")
            f.write(f"echo 'Откройте http://localhost:8000 в вашем браузере'\n")
            f.write(f"./{WEB_APP_OUTPUT}{ext}\n")
            
        # Делаем скрипты исполняемыми
        os.chmod(os.path.join(DIST_DIR, "start_recorder.sh"), 0o755)
        os.chmod(os.path.join(DIST_DIR, "start_webapp.sh"), 0o755)
            
    print("Скрипты запуска созданы.")

def copy_readme():
    """Копирование инструкции в директорию сборки."""
    print("\n" + "=" * 50)
    print("Копирование инструкции...")
    
    with open(os.path.join(DIST_DIR, "README.txt"), "w", encoding="utf-8") as f:
        f.write("""AI Notes - Система автоматической фиксации разговоров

Запуск приложения:

1. Для записи аудио:
   - Windows: запустите start_recorder.bat
   - Linux/Mac: ./start_recorder.sh

2. Для веб-интерфейса поиска:
   - Windows: запустите start_webapp.bat
   - Linux/Mac: ./start_webapp.sh
   - Затем откройте в браузере адрес http://localhost:8000

Важные замечания:
- При первом запуске система скачает модель Whisper, что может занять время
- Записи сохраняются в папке 'audio', заметки - в папке 'notes'
- Для остановки записи нажмите Ctrl+C

Подробная документация доступна на GitHub: https://github.com/yourusername/auto-notes
""")
    
    print("Инструкция скопирована.")

def check_dependencies():
    """Проверка необходимых зависимостей для сборки."""
    print("Проверка зависимостей...")
    
    # Проверка наличия PyInstaller
    try:
        subprocess.run([PYTHON_CMD, "-m", "PyInstaller", "--version"], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("PyInstaller найден")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("PyInstaller не найден. Установка...")
        try:
            subprocess.run([PYTHON_CMD, "-m", "pip", "install", "pyinstaller"], check=True)
            print("PyInstaller успешно установлен")
        except subprocess.SubprocessError:
            print("ОШИБКА: Не удалось установить PyInstaller. Пожалуйста, установите его вручную.")
            print("pip install pyinstaller")
            return False
    
    return True

def main():
    """Основная функция сборки."""
    print("Начало сборки приложения...")
    
    try:
        # Проверка зависимостей
        if not check_dependencies():
            return 1
            
        # Сборка приложений
        build_recorder()
        build_webapp()
        
        # Создание вспомогательных файлов
        create_launcher_script()
        copy_readme()
        
        print("\n" + "=" * 50)
        print(f"Сборка успешно завершена! Исполняемые файлы находятся в директории: {DIST_DIR}")
        print("=" * 50)
        
    except Exception as e:
        print(f"Ошибка при сборке: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 