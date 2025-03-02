#!/bin/bash
# Скрипт для быстрого запуска приложения на macOS/Linux

# Функция для проверки наличия команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Функция для установки зависимостей с обработкой ошибок
install_dependencies() {
    echo "Установка зависимостей..."
    pip install -r backend/requirements.txt
    
    # Проверка наличия ошибок установки PyAudio
    if [ $? -ne 0 ]; then
        echo "ВНИМАНИЕ: Возникла ошибка при установке зависимостей. Возможно проблема с PyAudio."
        echo "Для macOS, попробуйте установить PortAudio перед установкой PyAudio:"
        echo "  brew install portaudio"
        echo "Для Ubuntu/Debian:"
        echo "  sudo apt-get install python3-pyaudio"
        echo "  sudo apt-get install portaudio19-dev"
        echo "После установки PortAudio, попробуйте снова запустить скрипт."
        
        # Спрашиваем пользователя, хочет ли он продолжить без PyAudio
        echo "Хотите продолжить без установки PyAudio? (y/n)"
        read -r answer
        if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
            echo "Продолжение без полной установки зависимостей. Некоторые функции могут быть недоступны."
            return 0
        else
            echo "Установка прервана."
            return 1
        fi
    fi
    
    return 0
}

# Определяем используемый Python
if command_exists python3; then
    PYTHON="python3"
elif command_exists python; then
    PYTHON="python"
else
    echo "ОШИБКА: Python не найден. Пожалуйста, установите Python 3."
    exit 1
fi

echo "Используется интерпретатор: $PYTHON"

# Проверяем наличие виртуального окружения
if [ -d "venv" ]; then
    # Активируем виртуальное окружение
    echo "Найдено виртуальное окружение, активирую..."
    source venv/bin/activate
else
    echo "Виртуальное окружение не найдено."
    echo "Хотите создать виртуальное окружение и установить зависимости? (y/n)"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        echo "Создание виртуального окружения..."
        $PYTHON -m venv venv
        source venv/bin/activate
        # Вызов функции установки зависимостей с обработкой ошибок
        install_dependencies
        if [ $? -ne 0 ]; then
            exit 1
        fi
    else
        echo "Продолжение без виртуального окружения."
    fi
fi

# Функция вывода справки
show_help() {
    echo "Использование: ./run.sh [параметр]"
    echo "Параметры:"
    echo "  recorder     - запуск рекордера"
    echo "  recorder-continuous - запуск рекордера в непрерывном режиме"
    echo "  web          - запуск веб-интерфейса"
    echo "  build        - сборка исполняемых файлов"
    echo "  help         - показать эту справку"
    echo ""
    echo "Пример: ./run.sh recorder"
}

# Проверяем параметры командной строки
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# Обработка параметров
case "$1" in
    "recorder")
        echo "Запуск приложения записи..."
        $PYTHON backend/recorder.py --start
        ;;
    "recorder-continuous")
        echo "Запуск приложения записи в непрерывном режиме..."
        $PYTHON backend/recorder.py --start --continuous
        ;;
    "web")
        echo "Запуск веб-интерфейса..."
        $PYTHON app.py
        ;;
    "build")
        echo "Сборка исполняемых файлов..."
        $PYTHON build.py
        ;;
    "help")
        show_help
        ;;
    *)
        echo "Неизвестный параметр: $1"
        show_help
        exit 1
        ;;
esac 