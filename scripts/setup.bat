@echo off
REM Instala dependencias, cria o .env (1a vez), gera/aplica migrations e carrega dados essenciais.
REM Uso: scripts\setup.bat [--dev-data]
cd /d "%~dp0\.."
if not exist venv ( py -3 -m venv venv || python -m venv venv )
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || exit /b 1
if not exist .env (
  copy .env.example .env >nul
  for /f %%i in ('python -c "import secrets;print(secrets.token_urlsafe(50))"') do set SECRET=%%i
  powershell -Command "(Get-Content .env) -replace '^SECRET_KEY=.*','SECRET_KEY=%SECRET%' | Set-Content .env"
  echo .env criado. Edite DB_USER/DB_PASSWORD/DB_NAME e rode scripts\setup.bat novamente.
  echo Antes, crie o banco: mysql -u root -p ^< sql\00_create_database.sql
  exit /b 0
)
python manage.py check || exit /b 1
python manage.py makemigrations || exit /b 1
python manage.py migrate || exit /b 1
python manage.py bootstrap || exit /b 1
if "%1"=="--dev-data" python manage.py seed_dev
python manage.py collectstatic --noinput
echo Pronto. Inicie com scripts\start.bat
