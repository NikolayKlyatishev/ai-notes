.PHONY: help setup clean run run-web build install test install-deps-macos install-deps-linux install-deps-windows

# Определяем Python интерпретатор
PYTHON := python3
VENV_NAME := venv
VENV_ACTIVATE := $(VENV_NAME)/bin/activate
OS := $(shell uname -s)

# Windows-специфичные настройки
ifeq ($(OS),Windows_NT)
	VENV_ACTIVATE := $(VENV_NAME)/Scripts/activate
	PYTHON := python
endif

# Проверка наличия python3
PYTHON3_EXISTS := $(shell command -v python3 2> /dev/null)
PYTHON_EXISTS := $(shell command -v python 2> /dev/null)

# Выбор интерпретатора Python
ifndef PYTHON3_EXISTS
	ifndef PYTHON_EXISTS
		$(error "Не найден интерпретатор Python. Пожалуйста, установите Python 3.")
	else
		PYTHON := python
	endif
endif

help:
	@echo "Доступные команды:"
	@echo "  make setup     - Создание виртуального окружения и установка зависимостей"
	@echo "  make install   - Установка зависимостей в текущее окружение"
	@echo "  make run       - Запуск приложения записи"
	@echo "  make run-web   - Запуск веб-интерфейса"
	@echo "  make build     - Сборка исполняемых файлов"
	@echo "  make test      - Запуск тестов"
	@echo "  make clean     - Удаление временных файлов и артефактов сборки"
	@echo "  make install-deps-macos   - Установка системных зависимостей для macOS (через Homebrew)"
	@echo "  make install-deps-linux   - Установка системных зависимостей для Linux (Ubuntu/Debian)"
	@echo "  make install-deps-windows - Советы по установке зависимостей на Windows"

setup:
	@echo "Используемый интерпретатор Python: $(PYTHON)"
	@echo "Создание виртуального окружения..."
	@$(PYTHON) -m venv $(VENV_NAME)
	@echo "Установка зависимостей..."
	@. $(VENV_ACTIVATE) && pip install -r requirements.txt || { \
		echo ""; \
		echo "ВНИМАНИЕ: Возникли проблемы при установке зависимостей."; \
		echo ""; \
		if [ "$(OS)" = "Darwin" ]; then \
			echo "Для macOS выполните:"; \
			echo "  make install-deps-macos"; \
		elif [ "$(OS)" = "Linux" ]; then \
			echo "Для Linux выполните:"; \
			echo "  make install-deps-linux"; \
		else \
			echo "Для Windows выполните:"; \
			echo "  make install-deps-windows"; \
		fi; \
		echo "Затем повторите 'make setup'"; \
		exit 1; \
	}
	@echo "Настройка завершена. Активируйте окружение: source $(VENV_ACTIVATE)"

install-deps-macos:
	@echo "Установка системных зависимостей для macOS..."
	@echo "Проверка наличия Homebrew..."
	@command -v brew >/dev/null 2>&1 || { \
		echo "Homebrew не установлен. Пожалуйста, установите Homebrew:"; \
		echo "/bin/bash -c \"\$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""; \
		exit 1; \
	}
	@echo "Установка PortAudio с помощью Homebrew..."
	@brew install portaudio
	@echo "Системные зависимости установлены."

install-deps-linux:
	@echo "Установка системных зависимостей для Linux (Ubuntu/Debian)..."
	@echo "Для установки требуются права суперпользователя (sudo)."
	@sudo apt-get update
	@sudo apt-get install -y python3-pyaudio portaudio19-dev
	@echo "Системные зависимости установлены."

install-deps-windows:
	@echo "Советы по установке PyAudio на Windows:"
	@echo "Вариант 1: Установите PyAudio через pipwin (рекомендуется):"
	@echo "  pip install pipwin"
	@echo "  pipwin install pyaudio"
	@echo ""
	@echo "Вариант 2: Загрузите и установите соответствующий wheel-файл:"
	@echo "  1. Посетите https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio"
	@echo "  2. Загрузите подходящий для вашей версии Python wheel-файл"
	@echo "  3. Установите его: pip install [путь к wheel-файлу]"

install:
	@echo "Установка зависимостей..."
	@pip install -r backend/requirements.txt || { \
		echo ""; \
		echo "ВНИМАНИЕ: Возникли проблемы при установке зависимостей."; \
		echo "См. команды 'make install-deps-*' для решения проблем с системными зависимостями."; \
		exit 1; \
	}

run:
	@echo "Запуск приложения записи..."
	@$(PYTHON) backend/recorder.py --start

run-continuous:
	@echo "Запуск приложения записи в непрерывном режиме..."
	@$(PYTHON) backend/recorder.py --start --continuous

run-web:
	@echo "Запуск веб-интерфейса..."
	@$(PYTHON) app.py

build:
	@echo "Сборка исполняемых файлов..."
	@$(PYTHON) backend/build.py

build-windows: install
	@echo "Сборка для Windows..."
	@$(PYTHON) build.py

build-linux: install
	@echo "Сборка для Linux..."
	@$(PYTHON) build.py

test:
	@echo "Запуск тестов..."
	@$(PYTHON) -m unittest discover -s tests

clean:
	@echo "Очистка временных файлов..."
	@rm -rf build/ dist/ __pycache__/ *.spec
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@echo "Очистка завершена" 