@echo off
REM Inicia o servidor ASGI. Uso: scripts\start.bat [dev]
cd /d "%~dp0\.."
call venv\Scripts\activate.bat
if "%1"=="dev" ( python manage.py runserver 0.0.0.0:8000 ) else ( daphne -b 0.0.0.0 -p 8000 config.asgi:application )
