@echo off
setlocal enabledelayedexpansion

:: Set the required Python version
set REQUIRED_PYTHON_VERSION=3.8

:: Color codes for Windows console
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set NC=[0m

:: Function to print colored messages
:print_message
echo %~2%~1%NC%
exit /b

:: Check if Python is installed and meets version requirement
:check_python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_message "Python is not installed." %RED%
    exit /b 1
)

for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% lss 3 (
    call :print_message "Python version %PYTHON_VERSION% is too old. Version %REQUIRED_PYTHON_VERSION% or higher is required." %RED%
    exit /b 1
)

if %MAJOR% equ 3 (
    if %MINOR% lss 8 (
        call :print_message "Python version %PYTHON_VERSION% is too old. Version %REQUIRED_PYTHON_VERSION% or higher is required." %RED%
        exit /b 1
    )
)

call :print_message "Python %PYTHON_VERSION% is installed and meets requirements." %GREEN%
exit /b 0

:: Check if FFmpeg is installed
:check_ffmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_message "FFmpeg is not installed." %RED%
    exit /b 1
)
call :print_message "FFmpeg is installed." %GREEN%
exit /b 0

:: Main installation process
:main
call :print_message "Starting installation process..." %YELLOW%

:: Check Python installation
call :check_python
if %errorlevel% neq 0 (
    call :print_message "Please install Python %REQUIRED_PYTHON_VERSION% or higher from https://www.python.org/downloads/" %YELLOW%
    call :print_message "Make sure to check 'Add Python to PATH' during installation." %YELLOW%
    pause
    exit /b 1
)

:: Check FFmpeg installation
call :check_ffmpeg
if %errorlevel% neq 0 (
    call :print_message "Please install FFmpeg from https://ffmpeg.org/download.html" %YELLOW%
    call :print_message "1. Download the latest release for Windows" %YELLOW%
    call :print_message "2. Extract the archive" %YELLOW%
    call :print_message "3. Add the bin folder to your system PATH" %YELLOW%
    call :print_message "4. Restart this installer after installing FFmpeg" %YELLOW%
    pause
    exit /b 1
)

:: Remove existing virtual environment if it exists
if exist venv (
    call :print_message "Removing existing virtual environment..." %YELLOW%
    rmdir /s /q venv
)

:: Create virtual environment
call :print_message "Creating Python virtual environment..." %YELLOW%
python -m venv venv
if %errorlevel% neq 0 (
    call :print_message "Failed to create virtual environment." %RED%
    pause
    exit /b 1
)

:: Activate virtual environment
call :print_message "Activating virtual environment..." %YELLOW%
call venv\Scripts\activate
if %errorlevel% neq 0 (
    call :print_message "Failed to activate virtual environment." %RED%
    pause
    exit /b 1
)

:: Upgrade pip
call :print_message "Upgrading pip..." %YELLOW%
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    call :print_message "Failed to upgrade pip." %RED%
    pause
    exit /b 1
)

:: Install dependencies
call :print_message "Installing Python dependencies..." %YELLOW%
pip install -r requirements.txt
if %errorlevel% neq 0 (
    call :print_message "Failed to install dependencies." %RED%
    pause
    exit /b 1
)

:: Create .env file if it doesn't exist
if not exist .env (
    call :print_message "Creating .env file..." %YELLOW%
    echo FFMPEG_PATH=ffmpeg > .env
    echo DEFAULT_OUTPUT_FORMAT=mp4 >> .env
    echo DEFAULT_PROFILE=h264_web_optimized >> .env
    call :print_message "Created .env file." %GREEN%
)

call :print_message "Installation completed successfully!" %GREEN%
call :print_message "To start using the converter:" %YELLOW%
call :print_message "1. Open a new Command Prompt" %YELLOW%
call :print_message "2. Navigate to this directory" %YELLOW%
call :print_message "3. Run: venv\Scripts\activate" %YELLOW%
call :print_message "4. Run: python src\cli.py" %YELLOW%

pause
exit /b 0

:: Start the installation
call :main 