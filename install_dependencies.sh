#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install ffmpeg
    else
        # Linux
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    fi
fi 