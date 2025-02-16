@echo off

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate

REM Install Python dependencies
pip install -r requirements.txt

REM Check if ffmpeg is installed
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo FFmpeg not found. Please install FFmpeg manually from https://ffmpeg.org/download.html
    echo After installation, add FFmpeg to your system PATH
    pause
) 