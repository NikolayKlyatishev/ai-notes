# Простой Makefile для проекта AI Notes

# Переменные
PYTHON = python
PIP = pip
NPM = npm
VENV = venv
BACKEND_PORT = 8080
BACKEND_HOST = 0.0.0.0
FRONTEND_PORT = 5173
SHELL = /bin/bash

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
RED = \033[0;31m
NC = \033[0m # No Color

# Проверка наличия директории logs
ensure-logs-dir:
	@mkdir -p logs
	@mkdir -p backend/notes
	@mkdir -p backend/audio

# 1. Сборка и запуск бэкенда
backend: ensure-logs-dir
	@echo "$(BLUE)Установка и запуск бэкенда...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(BLUE)Создание виртуального окружения...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)Виртуальное окружение создано!$(NC)"; \
	fi
	@echo "$(BLUE)Установка зависимостей бэкенда...$(NC)"
	@bash -c '. $(VENV)/bin/activate && cd backend && $(PIP) install -e .'
	@echo "$(GREEN)Зависимости бэкенда установлены!$(NC)"
	@echo "$(BLUE)Запуск бэкенда...$(NC)"
	@bash -c '. $(VENV)/bin/activate && cd backend && $(PYTHON) app.py --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload > ../logs/backend.log 2>&1 & echo $$! > ../backend.pid'
	@sleep 2
	@if curl -s http://$(BACKEND_HOST):$(BACKEND_PORT)/api/health > /dev/null; then \
		echo "$(GREEN)Бэкенд успешно запущен на http://$(BACKEND_HOST):$(BACKEND_PORT)!$(NC)"; \
	else \
		echo "$(RED)Ошибка запуска бэкенда. Проверьте логи: logs/backend.log$(NC)"; \
		cat logs/backend.log | tail -n 20; \
		exit 1; \
	fi
	@echo "$(YELLOW)Логи доступны в файле logs/backend.log$(NC)"

# Установка дополнительных зависимостей для транскрибации
transcription:
	@echo "$(BLUE)Установка зависимостей для транскрибации...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(BLUE)Создание виртуального окружения...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)Виртуальное окружение создано!$(NC)"; \
	fi
	@bash -c '. $(VENV)/bin/activate && cd backend && $(PIP) install -e ".[transcription]"'
	@echo "$(GREEN)Зависимости для транскрибации установлены!$(NC)"

# 2. Сборка и запуск фронтенда
frontend: ensure-logs-dir
	@echo "$(BLUE)Установка и запуск фронтенда...$(NC)"
	@echo "$(BLUE)Установка зависимостей фронтенда...$(NC)"
	cd frontend && $(NPM) install
	@echo "$(BLUE)Запуск фронтенда...$(NC)"
	cd frontend && $(NPM) run dev > ../logs/frontend.log 2>&1 & echo $$! > ../frontend.pid
	@echo "$(GREEN)Фронтенд запущен на http://localhost:$(FRONTEND_PORT)!$(NC)"
	@echo "$(YELLOW)Логи доступны в файле logs/frontend.log$(NC)"

# 3. Сборка и запуск всего проекта
all: ensure-logs-dir
	@echo "$(BLUE)Установка и запуск всего проекта...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(BLUE)Создание виртуального окружения...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)Виртуальное окружение создано!$(NC)"; \
	fi
	@echo "$(BLUE)Установка зависимостей бэкенда...$(NC)"
	@bash -c '. $(VENV)/bin/activate && cd backend && $(PIP) install -e .'
	@echo "$(GREEN)Зависимости бэкенда установлены!$(NC)"
	@echo "$(BLUE)Установка зависимостей фронтенда...$(NC)"
	cd frontend && $(NPM) install
	@echo "$(BLUE)Запуск бэкенда...$(NC)"
	@bash -c '. $(VENV)/bin/activate && cd backend && $(PYTHON) app.py --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload > ../logs/backend.log 2>&1 & echo $$! > ../backend.pid'
	@sleep 2
	@if ! curl -s http://$(BACKEND_HOST):$(BACKEND_PORT)/api/health > /dev/null; then \
		echo "$(RED)Ошибка запуска бэкенда. Проверьте логи: logs/backend.log$(NC)"; \
		cat logs/backend.log | tail -n 20; \
		exit 1; \
	fi
	@echo "$(BLUE)Запуск фронтенда...$(NC)"
	cd frontend && $(NPM) run dev > ../logs/frontend.log 2>&1 & echo $$! > ../frontend.pid
	@echo "$(GREEN)Проект запущен!$(NC)"
	@echo "$(YELLOW)Бэкенд доступен по адресу: http://$(BACKEND_HOST):$(BACKEND_PORT)$(NC)"
	@echo "$(YELLOW)Фронтенд доступен по адресу: http://localhost:$(FRONTEND_PORT)$(NC)"
	@echo "$(YELLOW)Логи доступны в директории logs/$(NC)"
	@echo "$(YELLOW)Для остановки используйте: make stop$(NC)"

# 4. Остановка бэкенда и фронтенда
stop:
	@if [ -f backend.pid ]; then \
		echo "$(BLUE)Остановка бэкенда...$(NC)"; \
		PID=`cat backend.pid` && \
		kill -15 $$PID 2>/dev/null || true; \
		sleep 2; \
		if ps -p $$PID > /dev/null; then \
			echo "$(YELLOW)Бэкенд не остановился, применяю принудительную остановку...$(NC)"; \
			kill -9 $$PID 2>/dev/null || true; \
		fi; \
		rm backend.pid; \
		echo "$(GREEN)Бэкенд остановлен!$(NC)"; \
	else \
		echo "$(YELLOW)Файл backend.pid не найден. Возможно, бэкенд не запущен.$(NC)"; \
		pkill -f "python.*app.py" 2>/dev/null || true; \
	fi
	@if [ -f frontend.pid ]; then \
		echo "$(BLUE)Остановка фронтенда...$(NC)"; \
		kill -9 `cat frontend.pid` 2>/dev/null || true; \
		rm frontend.pid; \
		echo "$(GREEN)Фронтенд остановлен!$(NC)"; \
	else \
		echo "$(YELLOW)Файл frontend.pid не найден. Возможно, фронтенд не запущен.$(NC)"; \
	fi
	@echo "$(GREEN)Все процессы остановлены!$(NC)"

# 5. Перезапуск бэкенда и фронтенда
restart: stop all

# Помощь
help:
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@echo "  $(BLUE)make backend$(NC) - Сборка и запуск бэкенда"
	@echo "  $(BLUE)make frontend$(NC) - Сборка и запуск фронтенда"
	@echo "  $(BLUE)make all$(NC) - Сборка и запуск всего проекта"
	@echo "  $(BLUE)make stop$(NC) - Остановка бэкенда и фронтенда"
	@echo "  $(BLUE)make restart$(NC) - Перезапуск всего проекта"
	@echo "  $(BLUE)make transcription$(NC) - Установка зависимостей для транскрибации"
	@echo "  $(BLUE)make help$(NC) - Вывод справки по доступным командам"

.PHONY: ensure-logs-dir backend frontend all stop restart transcription help 