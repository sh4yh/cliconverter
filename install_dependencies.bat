@echo off
setlocal enabledelayedexpansion

goto main

:: Set the required Python version
set REQUIRED_PYTHON_VERSION=3.8

:: Function to add to PATH
:add_to_path
set "DIR_TO_ADD=%~1"
if "%DIR_TO_ADD%"=="" goto :eof
set "CURRENT_PATH=%PATH%"
echo "%CURRENT_PATH%" | findstr /I /C:"%DIR_TO_ADD%" >nul
if errorlevel 1 (
    setx PATH "%DIR_TO_ADD%;%PATH%"
    set "PATH=%DIR_TO_ADD%;%PATH%"
    echo Added to PATH: %DIR_TO_ADD%
)
goto :eof

:: Main installation process
:main
echo Starting installation process...

:: Check winget
call :check_winget
if errorlevel 1 exit /b 1

:: Check Python
call :check_python
if errorlevel 1 exit /b 1

:: Check FFmpeg
call :check_ffmpeg
if errorlevel 1 exit /b 1

:: Setup virtual environment and install dependencies
call :setup_environment
if errorlevel 1 exit /b 1

echo Installation completed successfully!
echo To start using the converter:
echo 1. Double-click run.bat
echo or
echo 1. Open a new Command Prompt
echo 2. Navigate to this directory
echo 3. Run: venv\Scripts\activate
echo 4. Run: python src\cli.py

pause
exit /b 0

:: Check if winget is available
:check_winget
echo Checking for winget...
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Winget is not available on this system.
    echo Please ensure you are running Windows 10 1809 or later
    echo and have App Installer installed from the Microsoft Store.
    pause
    exit /b 1
)
echo Winget is available.
goto :eof

:: Check if Python is installed and meets version requirement
:check_python
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Installing Python using winget...
    winget install -e --id Python.Python.3.11
    if %errorlevel% neq 0 (
        echo Failed to install Python. Please try installing manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    :: Add Python to PATH
    echo Adding Python to PATH...
    for /f "tokens=*" %%i in ('where python') do (
        set "PYTHON_PATH=%%~dpi"
        call :add_to_path "!PYTHON_PATH!"
        call :add_to_path "!PYTHON_PATH!Scripts"
    )
)

:: Verify Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% lss 3 (
    echo Python version %PYTHON_VERSION% is too old. Version %REQUIRED_PYTHON_VERSION% or higher is required.
    echo Installing latest Python version...
    winget install -e --id Python.Python.3.11
    pause
    exit /b 1
)

if %MAJOR% equ 3 (
    if %MINOR% lss 8 (
        echo Python version %PYTHON_VERSION% is too old. Version %REQUIRED_PYTHON_VERSION% or higher is required.
        echo Installing latest Python version...
        winget install -e --id Python.Python.3.11
        pause
        exit /b 1
    )
)

echo Python %PYTHON_VERSION% is installed and meets requirements.
goto :eof

:: Check if FFmpeg is installed
:check_ffmpeg
echo Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg is not installed. Installing FFmpeg using winget...
    winget install -e --id Gyan.FFmpeg
    if %errorlevel% neq 0 (
        echo Failed to install FFmpeg automatically.
        echo Please install FFmpeg manually:
        echo 1. Go to https://ffmpeg.org/download.html
        echo 2. Download the latest release for Windows
        echo 3. Extract the archive
        echo 4. Add the bin folder to your system PATH
        pause
        exit /b 1
    )
    
    :: Add FFmpeg to PATH
    echo Adding FFmpeg to PATH...
    for /f "tokens=*" %%i in ('where ffmpeg') do (
        set "FFMPEG_PATH=%%~dpi"
        if not "!FFMPEG_PATH!"=="" call :add_to_path "!FFMPEG_PATH!"
    )
)

echo FFmpeg is installed.
goto :eof

:: Setup virtual environment and install dependencies
:setup_environment
echo Setting up Python environment...

:: Check if virtual environment exists and is valid
if exist venv\Scripts\python.exe (
    echo Found existing virtual environment.
    echo Activating existing virtual environment...
    call venv\Scripts\activate
    if !errorlevel! neq 0 (
        echo Failed to activate existing virtual environment.
        echo Creating new virtual environment...
        rmdir /s /q venv
        goto create_venv
    )
    goto install_deps
)

:create_venv
:: Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:install_deps
:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

:: Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

:: Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    for /f "tokens=*" %%i in ('where ffmpeg') do (
        echo FFMPEG_PATH=%%i> .env
        goto env_created
    )
    :env_created
    echo DEFAULT_OUTPUT_FORMAT=mp4>> .env
    echo DEFAULT_PROFILE=h264_web_optimized>> .env
    echo Created .env file.
)

goto :eof 