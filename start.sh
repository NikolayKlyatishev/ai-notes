#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Директория для логов
LOGS_DIR="./logs"

# Порты для приложений
API_PORT=8080
REACT_PORT=5173

# Декларация массива для хранения PIDs фоновых процессов
declare -a PIDS

# Функция для проверки наличия команды
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Ошибка: $1 не найден. Пожалуйста, установите $1.${NC}"
        exit 1
    fi
}

# Функция для проверки занятости порта
check_port() {
    local port=$1
    if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Функция для корректного завершения всех процессов
cleanup() {
    echo -e "\n${YELLOW}Завершение работы приложения...${NC}"
    
    # Завершение всех запущенных процессов
    for pid in "${PIDS[@]}"; do
        if ps -p $pid > /dev/null; then
            echo -e "Останавливаю процесс с PID: $pid"
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null
        fi
    done
    
    echo -e "${GREEN}Все процессы остановлены. Выход.${NC}"
    exit 0
}

# Регистрация обработчиков сигналов
trap cleanup SIGINT SIGTERM EXIT

# Проверка наличия необходимых команд
check_command python3.11
check_command npm
check_command tail
check_command lsof

# Создание директории для логов
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo -e "${GREEN}Создана директория для логов: $LOGS_DIR${NC}"
fi

# Используем виртуальное окружение Python 3.11
echo -e "${YELLOW}Активация виртуального окружения Python 3.11...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Создаем виртуальное окружение...${NC}"
    python3.11 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Ошибка при создании виртуального окружения. Убедитесь, что Python 3.11 установлен.${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Устанавливаем зависимости...${NC}"
    . venv/bin/activate
    
    # Установка основных зависимостей из pyproject.toml в директории backend
    echo -e "${YELLOW}Устанавливаем основные зависимости...${NC}"
    python -m pip install -e ./backend
    
    # Пробуем установить зависимости для транскрипции
    echo -e "${YELLOW}Пробуем установить модули для транскрипции...${NC}"
    python -m pip install -e "./backend[transcription]" || echo -e "${YELLOW}Модули транскрипции не удалось установить. Функция транскрипции будет недоступна.${NC}"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Ошибка при установке зависимостей.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Виртуальное окружение найдено.${NC}"
    . venv/bin/activate
fi
echo -e "${GREEN}Виртуальное окружение активировано.${NC}"

# Проверка занятости порта API
if ! check_port $API_PORT; then
    echo -e "${RED}Порт $API_PORT уже используется. Завершите процесс, использующий этот порт, и попробуйте снова.${NC}"
    echo -e "${YELLOW}Вы можете найти процесс командой: lsof -i :$API_PORT${NC}"
    echo -e "${YELLOW}И завершить его командой: kill -9 <PID>${NC}"
    exit 1
fi

# Запуск бэкенда в фоновом режиме с перенаправлением вывода в лог-файл
echo -e "${YELLOW}Запуск API-сервера...${NC}"
python -m backend.app --api > "$LOGS_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
PIDS+=($BACKEND_PID)
echo -e "${GREEN}API-сервер запущен с PID: $BACKEND_PID${NC}"

# Запуск tail для мониторинга логов бэкенда
echo -e "${BLUE}Запуск мониторинга логов API-сервера...${NC}"
tail -f "$LOGS_DIR/backend.log" | sed -e "s/^/${BLUE}[BACKEND] ${NC}/" &
BACKEND_TAIL_PID=$!
PIDS+=($BACKEND_TAIL_PID)

# Проверка доступности API перед запуском фронтенда
echo -e "${YELLOW}Ожидание запуска API-сервера...${NC}"
API_READY=false
RETRY_COUNT=0
MAX_RETRIES=12  # Максимальное количество попыток (12 * 5 = 60 секунд)

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$API_READY" = false ]; do
    sleep 5
    # Проверяем доступность API
    if curl -s "http://localhost:$API_PORT/api/health" > /dev/null; then
        API_READY=true
        echo -e "${GREEN}API-сервер успешно запущен и отвечает на запросы.${NC}"
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${YELLOW}Ожидание запуска API-сервера... Попытка $RETRY_COUNT из $MAX_RETRIES${NC}"
    fi
done

if [ "$API_READY" = false ]; then
    echo -e "${RED}API-сервер не отвечает после $MAX_RETRIES попыток. Проверьте логи сервера.${NC}"
    echo -e "${RED}Запуск фронтенда может быть нестабильным без работающего API.${NC}"
fi

# Проверка занятости порта фронтенда
if ! check_port $REACT_PORT; then
    echo -e "${RED}Порт $REACT_PORT уже используется. React-фронтенд не будет запущен.${NC}"
    echo -e "${YELLOW}Вы можете найти процесс командой: lsof -i :$REACT_PORT${NC}"
    echo -e "${YELLOW}И завершить его командой: kill -9 <PID>${NC}"
else
    # Переход в директорию фронтенда
    cd frontend

    # Установка зависимостей фронтенда
    echo -e "${YELLOW}Установка зависимостей фронтенда...${NC}"
    npm install
    echo -e "${GREEN}Зависимости фронтенда установлены.${NC}"

    # Запуск фронтенда с перенаправлением вывода в лог-файл
    echo -e "${YELLOW}Запуск React-фронтенда...${NC}"
    npm start > "../$LOGS_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    PIDS+=($FRONTEND_PID)
    echo -e "${GREEN}React-фронтенд запущен с PID: $FRONTEND_PID${NC}"

    # Запуск tail для мониторинга логов фронтенда
    echo -e "${BLUE}Запуск мониторинга логов фронтенда...${NC}"
    cd ..
    tail -f "$LOGS_DIR/frontend.log" | sed -e "s/^/${YELLOW}[FRONTEND] ${NC}/" &
    FRONTEND_TAIL_PID=$!
    PIDS+=($FRONTEND_TAIL_PID)
fi

echo -e "${GREEN}Приложение запущено:${NC}"
echo -e "API-сервер: ${YELLOW}http://localhost:$API_PORT${NC}"
echo -e "React-фронтенд: ${YELLOW}http://localhost:$REACT_PORT${NC}"
echo -e "${YELLOW}Для остановки нажмите Ctrl+C${NC}"
echo -e "${BLUE}Логи сохраняются в директории: $LOGS_DIR${NC}"

# Ожидание завершения всех процессов
wait 