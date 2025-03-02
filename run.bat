@echo off
rem Скрипт для быстрого запуска приложения на Windows

rem Проверка наличия python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
) else (
    echo ОШИБКА: Python не найден. Пожалуйста, установите Python 3.
    pause
    exit /b 1
)

echo Используется интерпретатор: %PYTHON%

rem Функция установки зависимостей с обработкой ошибок
:install_dependencies
echo Установка зависимостей...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ВНИМАНИЕ: Возникла ошибка при установке зависимостей. Возможно проблема с PyAudio.
    echo Для Windows, попробуйте:
    echo 1. Установить PyAudio из предварительно скомпилированных бинарных файлов:
    echo    pip install pipwin
    echo    pipwin install pyaudio
    echo 2. Или загрузите соответствующий wheel-файл с https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo    и установите его с помощью pip: pip install [путь к wheel-файлу]
    echo После установки PyAudio, попробуйте снова запустить скрипт.
    
    set /p answer=Хотите продолжить без установки PyAudio? (y/n):
    if /i "%answer%"=="y" (
        echo Продолжение без полной установки зависимостей. Некоторые функции могут быть недоступны.
        goto :dependency_exit_success
    ) else (
        echo Установка прервана.
        exit /b 1
    )
)
:dependency_exit_success
exit /b 0

rem Проверяем наличие виртуального окружения
if exist venv\ (
    echo Найдено виртуальное окружение, активирую...
    call venv\Scripts\activate.bat
) else (
    echo Виртуальное окружение не найдено.
    set /p answer=Хотите создать виртуальное окружение и установить зависимости? (y/n):
    if /i "%answer%"=="y" (
        echo Создание виртуального окружения...
        %PYTHON% -m venv venv
        call venv\Scripts\activate.bat
        
        rem Вызов функции установки зависимостей
        call :install_dependencies
        if %ERRORLEVEL% NEQ 0 (
            exit /b 1
        )
    ) else (
        echo Продолжение без виртуального окружения.
    )
)

rem Показать справку, если нет параметров
if "%~1"=="" (
    goto :help
)

rem Обработка параметров
if "%~1"=="recorder" (
    echo Запуск приложения записи...
    %PYTHON% backend\recorder.py --start
    goto :eof
)

if "%~1"=="recorder-continuous" (
    echo Запуск приложения записи в непрерывном режиме...
    %PYTHON% backend\recorder.py --start --continuous
    goto :eof
)

if "%~1"=="web" (
    echo Запуск веб-интерфейса...
    %PYTHON% app.py
    goto :eof
)

if "%~1"=="build" (
    echo Сборка исполняемых файлов...
    %PYTHON% build.py
    goto :eof
)

if "%~1"=="help" (
    goto :help
) else (
    echo Неизвестный параметр: %~1
    goto :help
)

:help
echo Использование: run.bat [параметр]
echo Параметры:
echo   recorder     - запуск рекордера
echo   recorder-continuous - запуск рекордера в непрерывном режиме
echo   web          - запуск веб-интерфейса
echo   build        - сборка исполняемых файлов
echo   help         - показать эту справку
echo.
echo Пример: run.bat recorder

:eof
rem Конец скрипта 