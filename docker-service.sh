#!/bin/bash
# Скрипт для управления Docker-сервисами проекта

# Установка цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

print_help() {
    echo -e "${YELLOW}Использование:${NC} ./docker-service.sh [команда]"
    echo
    echo "Команды:"
    echo -e "  ${GREEN}start${NC}              - запуск веб-интерфейса с интегрированным рекордером"
    echo -e "  ${GREEN}stop${NC}               - остановка всех сервисов"
    echo -e "  ${GREEN}restart${NC}            - перезапуск веб-интерфейса"
    echo -e "  ${GREEN}logs${NC}               - показать логи веб-интерфейса"
    echo -e "  ${GREEN}status${NC}             - показать статус сервисов"
    echo -e "  ${GREEN}rebuild${NC}            - пересобрать образы"
    echo -e "  ${GREEN}start-standalone${NC}   - запуск автономного рекордера без веб-интерфейса"
    echo -e "  ${GREEN}stop-standalone${NC}    - остановка автономного рекордера"
    echo -e "  ${GREEN}logs-standalone${NC}    - показать логи автономного рекордера"
    echo -e "  ${GREEN}help${NC}               - показать эту справку"
}

check_docker() {
    if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Ошибка: Docker и/или Docker Compose не установлены${NC}"
        echo "Установите Docker и Docker Compose перед использованием этого скрипта"
        exit 1
    fi
}

# Проверяем наличие Docker
check_docker

# Обработка команд
case "$1" in
    "start")
        echo -e "${GREEN}Запуск веб-интерфейса с интегрированным рекордером...${NC}"
        docker-compose up -d webapp
        echo -e "${GREEN}Веб-интерфейс запущен и доступен по адресу http://localhost:8000${NC}"
        echo -e "${YELLOW}Для управления рекордером перейдите по адресу: http://localhost:8000/recorder${NC}"
        ;;
    "stop")
        echo -e "${YELLOW}Остановка всех сервисов...${NC}"
        docker-compose stop
        echo -e "${GREEN}Все сервисы остановлены${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}Перезапуск веб-интерфейса...${NC}"
        docker-compose restart webapp
        echo -e "${GREEN}Веб-интерфейс перезапущен${NC}"
        ;;
    "logs")
        echo -e "${GREEN}Логи веб-интерфейса:${NC}"
        docker-compose logs --tail=100 -f webapp
        ;;
    "start-standalone")
        echo -e "${GREEN}Запуск автономного рекордера без веб-интерфейса...${NC}"
        docker-compose up -d recorder
        echo -e "${GREEN}Автономный рекордер запущен в фоновом режиме${NC}"
        ;;
    "stop-standalone")
        echo -e "${YELLOW}Остановка автономного рекордера...${NC}"
        docker-compose stop recorder
        echo -e "${GREEN}Автономный рекордер остановлен${NC}"
        ;;
    "logs-standalone")
        echo -e "${GREEN}Логи автономного рекордера:${NC}"
        docker-compose logs --tail=100 -f recorder
        ;;
    "status")
        echo -e "${GREEN}Статус сервисов:${NC}"
        docker-compose ps
        ;;
    "rebuild")
        echo -e "${YELLOW}Пересборка образов...${NC}"
        docker-compose build
        echo -e "${GREEN}Образы пересобраны${NC}"
        ;;
    "help"|*)
        print_help
        ;;
esac 