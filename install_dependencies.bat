@echo off
setlocal enabledelayedexpansion

:: Set the required Python version
set REQUIRED_PYTHON_VERSION=3.8

:: Check if winget is available
:check_winget
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Winget is not available on this system.
    echo Please ensure you are running Windows 10 1809 or later
    echo and have App Installer installed from the Microsoft Store.
    pause
    exit /b 1
)

:: Check if Python is installed and meets version requirement
:check_python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Installing Python using winget...
    winget install -e --id Python.Python.3.11
    if %errorlevel% neq 0 (
        echo Failed to install Python. Please try installing manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    :: Refresh environment variables
    echo Refreshing environment variables...
    call RefreshEnv.cmd
    if %errorlevel% neq 0 (
        echo Please close this window and run the installer again for the PATH changes to take effect.
        pause
        exit /b 1
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

:: Check if FFmpeg is installed
:check_ffmpeg
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
    :: Refresh environment variables
    echo Refreshing environment variables...
    call RefreshEnv.cmd
    if %errorlevel% neq 0 (
        echo Please close this window and run the installer again for the PATH changes to take effect.
        pause
        exit /b 1
    )
)

echo FFmpeg is installed.

:: Main installation process
:main
echo Starting installation process...

:: Remove existing virtual environment if it exists
if exist venv (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

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
    echo FFMPEG_PATH=ffmpeg > .env
    echo DEFAULT_OUTPUT_FORMAT=mp4 >> .env
    echo DEFAULT_PROFILE=h264_web_optimized >> .env
    echo Created .env file.
)

echo Installation completed successfully!
echo To start using the converter:
echo 1. Open a new Command Prompt
echo 2. Navigate to this directory
echo 3. Run: venv\Scripts\activate
echo 4. Run: python src\cli.py

pause
exit /b 0

:: Start the installation
call :main 