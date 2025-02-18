@echo off
cd /d "%~dp0"
cmd /k "call venv\Scripts\activate.bat"
cmd /k "python src\cli.py" 
