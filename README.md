# Media File Converter

A powerful command-line tool for converting audio and video files with customizable profiles and settings.

## Features

- Convert video and audio files to various formats
- Customizable conversion profiles
- Speed control for both audio and video
- Batch file processing
- Interactive command-line interface
- Progress tracking with detailed status
- Profile management system

## Requirements

- Python 3.8 or higher
- FFmpeg

## Installation

### Windows

1. Extract the zip file
2. Run `install_dependencies.bat`
3. Follow the on-screen instructions
4. If FFmpeg is not installed, the script will guide you through the installation process

### macOS/Linux

1. Extract the zip file
2. Open Terminal in the extracted directory
3. Make the installer executable:
   ```bash
   chmod +x install_dependencies.sh
   ```
4. Run the installer:
   ```bash
   ./install_dependencies.sh
   ```
5. The script will automatically install FFmpeg if it's not present

## Usage

### Windows

1. Open Command Prompt in the installation directory
2. Activate the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
3. Run the converter:
   ```cmd
   python src\cli.py
   ```

### macOS/Linux

1. Open Terminal in the installation directory
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Run the converter:
   ```bash
   python src/cli.py
   ```

## Features Guide

### Converting Files

1. Select "Convert Files" from the main menu
2. Navigate through directories to select files
3. Choose a conversion profile
4. Wait for the conversion to complete

### Managing Profiles

1. Select "Settings" from the main menu
2. Choose "Manage Profiles"
3. You can:
   - View existing profiles
   - Create new profiles
   - Edit profile parameters
   - Delete profiles
   - Create profiles from reference files

### Supported Formats

#### Video
- Containers: MP4, MKV, AVI, MOV, WebM
- Codecs: H.264, H.265, VP9, MPEG-4
- Resolutions: Up to 4K
- Frame rates: 23.976 to 60 fps

#### Audio
- Containers: MP3, M4A, FLAC, WAV, OGG
- Codecs: MP3, AAC, FLAC, Opus, Vorbis
- Bit rates: 96k to 512k
- Sample rates: 22050 to 96000 Hz

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Make sure FFmpeg is installed and added to your system PATH
   - Reinstall FFmpeg following the installer's instructions

2. **Python version error**
   - Install Python 3.8 or higher from python.org
   - Make sure Python is added to your system PATH

3. **Conversion fails**
   - Check if input files are not corrupted
   - Ensure you have enough disk space
   - Verify FFmpeg installation

### Getting Help

If you encounter any issues:
1. Check the error message in the console
2. Verify all requirements are met
3. Try reinstalling the dependencies
4. Check if your input files are supported

## License

This project is licensed under the MIT License - see the LICENSE file for details. 