# Audio/Video Converter Tool Architecture

## Overview
This tool is a command-line application for converting audio and video files between different formats and codecs, while also providing metadata management capabilities. The architecture follows a modular design with clear separation of concerns.

## Core Components

### 1. CLI Interface (`src/cli.py`)
- Main entry point for the application
- Handles user interaction and command parsing
- Uses tqdm for progress visualization
- Orchestrates interactions between other components
- Environment configuration via .env file

### 2. Converter Engine (`src/converter.py`)
- Manages all FFmpeg operations
- Handles file format conversion
- Validates FFmpeg installation
- Processes conversion with specified profiles
- Error handling for conversion operations

### 3. Metadata Handler (`src/metadata.py`)
- Manages audio/video file metadata using mutagen
- Provides metadata reading and writing capabilities
- Supports various metadata formats (ID3, etc.)
- Displays file information

### 4. Format Profiles (`src/profiles.py`)
- Manages conversion profiles and presets through JSON configuration
- Provides categorized profiles for audio and video formats
- Supports profile import/export capabilities
- Allows dynamic profile management (add/remove/modify)
- Stores profiles in `config/profiles.json`
- Maintains separate configurations for audio and video formats
- Supports profile backup and sharing through JSON files

## Dependencies

### External Tools
- FFmpeg: Required for audio/video conversion
- Python 3.x: Runtime environment

### Python Libraries
- python-dotenv: Environment configuration
- tqdm: Progress bar visualization
- mutagen: Metadata handling

## Configuration

### Environment Variables (.env)
- FFMPEG_PATH: Path to FFmpeg executable
- DEFAULT_OUTPUT_FORMAT: Default conversion format
- DEFAULT_PROFILE: Default conversion profile

### Profile Configuration (config/profiles.json)
- Structured JSON format for profile storage
- Categorized into audio and video sections
- Each profile contains format-specific parameters
- Supports dynamic updates without code changes
- Maintains default profiles for common use cases

### Installation Scripts
- install_dependencies.sh: Unix/Mac installation
- install_dependencies.bat: Windows installation

## Data Flow
1. User input → CLI Interface
2. CLI validates input and selects profile from JSON configuration
3. Profile system loads appropriate settings from config/profiles.json
4. Converter processes file using selected profile
5. Metadata handler processes tags
6. Progress reported back to CLI
7. Output file generated with updated metadata

## Cross-Platform Compatibility
- Platform-agnostic path handling
- Separate installation scripts for different OS
- Environment-based configuration
- Virtual environment isolation

## Extension Points
- New format profiles can be added via JSON configuration
- Profile import/export for sharing configurations
- Category-based profile organization
- Custom profile creation and modification
- Profile backup and restoration
- Additional metadata formats can be supported
- Custom conversion parameters
- New CLI commands and options

## Error Handling
- Profile validation and JSON integrity checking
- FFmpeg availability checking
- Metadata validation
- File access permissions
- Conversion error handling
- Input validation
- Profile configuration validation

## Future Considerations
- Profile template system for quick profile creation
- Profile version control and migration
- Profile dependency management
- Profile validation rules
- Profile inheritance and composition
- Batch processing capabilities
- Custom profile creation via CLI
- Format auto-detection
- Advanced metadata editing
- Queue management for multiple conversions 