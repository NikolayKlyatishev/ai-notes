#!/bin/bash

# Скрипт для запуска проекта AI Notes с использованием tmux
# Позволяет запустить бэкенд и фронтенд в одном терминале

# Цвета для вывода
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Проверка наличия tmux
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}Ошибка: tmux не установлен. Установите его с помощью:${NC}"
    echo -e "  ${BLUE}make install-tmux-mac${NC} (macOS)"
    echo -e "  ${BLUE}make install-tmux-linux${NC} (Linux)"
    echo -e "Или вручную:"
    echo -e "  ${BLUE}brew install tmux${NC} (macOS)"
    echo -e "  ${BLUE}apt-get install tmux${NC} (Ubuntu/Debian)"
    exit 1
fi

# Проверка наличия директории logs
if [ ! -d "logs" ]; then
    echo -e "${BLUE}Создание директории logs...${NC}"
    mkdir -p logs
    echo -e "${GREEN}Директория logs создана!${NC}"
fi

# Название сессии
SESSION_NAME="ai-notes"

# Проверка, существует ли сессия
tmux has-session -t $SESSION_NAME 2>/dev/null

# Если сессия существует, присоединяемся к ней
if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Сессия $SESSION_NAME уже существует, присоединяемся...${NC}"
    tmux attach-session -t $SESSION_NAME
    exit 0
fi

# Проверка наличия Makefile
if [ ! -f "Makefile" ]; then
    echo -e "${RED}Ошибка: Makefile не найден в текущей директории.${NC}"
    echo -e "${YELLOW}Убедитесь, что вы запускаете скрипт из корневой директории проекта.${NC}"
    exit 1
fi

# Создаем новую сессию
echo -e "${BLUE}Создание новой сессии $SESSION_NAME...${NC}"
tmux new-session -d -s $SESSION_NAME

# Переименовываем первое окно и запускаем бэкенд
tmux rename-window -t $SESSION_NAME:0 'backend'
tmux send-keys -t $SESSION_NAME:0 'make backend' C-m

# Создаем второе окно и запускаем фронтенд
tmux new-window -t $SESSION_NAME:1 -n 'frontend'
tmux send-keys -t $SESSION_NAME:1 'make frontend' C-m

# Возвращаемся к первому окну
tmux select-window -t $SESSION_NAME:0

# Присоединяемся к сессии
echo -e "${GREEN}Запуск проекта AI Notes...${NC}"
echo -e "${YELLOW}Используйте ${BLUE}Ctrl+b n${YELLOW} для переключения между окнами (backend и frontend)${NC}"
echo -e "${YELLOW}Используйте ${BLUE}Ctrl+b d${YELLOW} для отсоединения от сессии (процессы продолжат работать)${NC}"
echo -e "${YELLOW}Для повторного подключения используйте: ${BLUE}./run.sh${NC}"

tmux attach-session -t $SESSION_NAME 