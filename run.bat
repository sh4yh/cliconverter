@echo off
cd /d "%~dp0"
cmd /k "venv\Scripts\activate.bat && python src\cli.py" 