#!/bin/bash

# Set the required Python version
REQUIRED_PYTHON_VERSION="3.8"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ "$(echo -e "$PYTHON_VERSION\n$REQUIRED_PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_PYTHON_VERSION" ]; then
            print_message "✓ Python $PYTHON_VERSION is installed and meets the minimum requirement." "$GREEN"
            return 0
        else
            print_message "✗ Python $PYTHON_VERSION is installed but version $REQUIRED_PYTHON_VERSION or higher is required." "$RED"
            return 1
        fi
    else
        print_message "✗ Python 3 is not installed." "$RED"
        return 1
    fi
}

# Function to install Python on macOS
install_python_mac() {
    print_message "Installing Python using Homebrew..." "$YELLOW"
    if ! command_exists brew; then
        print_message "Installing Homebrew..." "$YELLOW"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python@3.11
}

# Function to install Python on Linux
install_python_linux() {
    print_message "Installing Python..." "$YELLOW"
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command_exists dnf; then
        sudo dnf install -y python3 python3-pip python3-virtualenv
    else
        print_message "Unable to install Python. Please install Python $REQUIRED_PYTHON_VERSION or higher manually." "$RED"
        exit 1
    fi
}

# Function to install FFmpeg
install_ffmpeg() {
    print_message "Installing FFmpeg..." "$YELLOW"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command_exists brew; then
            print_message "Installing Homebrew..." "$YELLOW"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install ffmpeg
    else
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif command_exists dnf; then
            sudo dnf install -y ffmpeg
        else
            print_message "Unable to install FFmpeg. Please install FFmpeg manually from https://ffmpeg.org/download.html" "$RED"
            exit 1
        fi
    fi
}

# Main installation process
main() {
    print_message "Starting installation process..." "$YELLOW"
    
    # Check Python version and install if needed
    if ! check_python_version; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            install_python_mac
        else
            install_python_linux
        fi
        
        # Verify Python installation
        if ! check_python_version; then
            print_message "Failed to install Python. Please install Python $REQUIRED_PYTHON_VERSION or higher manually." "$RED"
            exit 1
        fi
    fi
    
    # Check and install FFmpeg
    if ! command_exists ffmpeg; then
        print_message "FFmpeg not found. Installing..." "$YELLOW"
        install_ffmpeg
        
        if ! command_exists ffmpeg; then
            print_message "Failed to install FFmpeg. Please install FFmpeg manually from https://ffmpeg.org/download.html" "$RED"
            exit 1
        fi
    else
        print_message "✓ FFmpeg is already installed." "$GREEN"
    fi
    
    # Create and activate virtual environment
    print_message "Creating Python virtual environment..." "$YELLOW"
    if [ -d "venv" ]; then
        print_message "Removing existing virtual environment..." "$YELLOW"
        rm -rf venv
    fi
    
    python3 -m venv venv
    if [ ! -f "venv/bin/activate" ]; then
        print_message "Failed to create virtual environment." "$RED"
        exit 1
    fi
    
    print_message "Activating virtual environment..." "$YELLOW"
    source venv/bin/activate
    
    # Upgrade pip
    print_message "Upgrading pip..." "$YELLOW"
    pip install --upgrade pip
    
    # Install Python dependencies
    print_message "Installing Python dependencies..." "$YELLOW"
    if pip install -r requirements.txt; then
        print_message "✓ Dependencies installed successfully." "$GREEN"
    else
        print_message "Failed to install dependencies." "$RED"
        exit 1
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_message "Creating .env file..." "$YELLOW"
        echo "FFMPEG_PATH=$(which ffmpeg)" > .env
        echo "DEFAULT_OUTPUT_FORMAT=mp4" >> .env
        echo "DEFAULT_PROFILE=h264_web_optimized" >> .env
        print_message "✓ Created .env file." "$GREEN"
    fi
    
    print_message "✓ Installation completed successfully!" "$GREEN"
    print_message "To start using the converter, run: source venv/bin/activate && python src/cli.py" "$YELLOW"
}

# Run the installation
main 