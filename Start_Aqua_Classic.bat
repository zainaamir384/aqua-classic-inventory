@echo off
cd /d "%~dp0"
timeout /t 1 /nobreak > nul
start http://127.0.0.1:8000/login/
python manage.py runserver 0.0.0.0:8000
