@echo off
cd /d "%~dp0\.."
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
python -m unittest tests.engine.test_game tests.test_pure_rules -v || exit /b 1
if "%1"=="--django" ( set DB_ENGINE=sqlite && python manage.py test tests.django_tests -v 2 )
