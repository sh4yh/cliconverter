#!/bin/bash

# Set the required Python version
REQUIRED_PYTHON_VERSION="3.8"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ "$(echo -e "$PYTHON_VERSION\n$REQUIRED_PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_PYTHON_VERSION" ]; then
            echo "Python $PYTHON_VERSION is installed and meets requirements."
            return 0
        else
            echo "Python $PYTHON_VERSION is installed but version $REQUIRED_PYTHON_VERSION or higher is required."
            return 1
        fi
    else
        echo "Python 3 is not installed."
        return 1
    fi
}

# Function to install Python on macOS
install_python_mac() {
    echo "Installing Python using Homebrew..."
    if ! command_exists brew; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python@3.11
}

# Function to install Python on Linux
install_python_linux() {
    echo "Installing Python..."
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command_exists dnf; then
        sudo dnf install -y python3 python3-pip python3-virtualenv
    else
        echo "Unable to install Python. Please install Python $REQUIRED_PYTHON_VERSION or higher manually."
        exit 1
    fi
}

# Function to install FFmpeg
install_ffmpeg() {
    echo "Installing FFmpeg..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command_exists brew; then
            echo "Installing Homebrew..."
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
            echo "Unable to install FFmpeg. Please install FFmpeg manually from https://ffmpeg.org/download.html"
            exit 1
        fi
    fi
}

# Main installation process
main() {
    echo "Starting installation process..."
    
    # Check Python version and install if needed
    if ! check_python_version; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            install_python_mac
        else
            install_python_linux
        fi
        
        # Verify Python installation
        if ! check_python_version; then
            echo "Failed to install Python. Please install Python $REQUIRED_PYTHON_VERSION or higher manually."
            exit 1
        fi
    fi
    
    # Check and install FFmpeg
    if ! command_exists ffmpeg; then
        echo "FFmpeg not found. Installing..."
        install_ffmpeg
        
        if ! command_exists ffmpeg; then
            echo "Failed to install FFmpeg. Please install FFmpeg manually from https://ffmpeg.org/download.html"
            exit 1
        fi
    else
        echo "FFmpeg is already installed."
    fi
    
    # Create and activate virtual environment
    echo "Creating Python virtual environment..."
    if [ -d "venv" ]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    if [ ! -f "venv/bin/activate" ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    if pip install -r requirements.txt; then
        echo "Dependencies installed successfully."
    else
        echo "Failed to install dependencies."
        exit 1
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo "Creating .env file..."
        echo "FFMPEG_PATH=$(which ffmpeg)" > .env
        echo "DEFAULT_OUTPUT_FORMAT=mp4" >> .env
        echo "DEFAULT_PROFILE=h264_web_optimized" >> .env
        echo "Created .env file."
    fi
    
    echo "Installation completed successfully!"
    echo "To start using the converter, run: source venv/bin/activate && python src/cli.py"
}

# Run the installation
main 