#!/bin/bash

# Set color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Print colored message
print_message() {
    echo -e "${2}${1}${NC}"
}

# Set version and output filename
VERSION="1.0.0"
OUTFILE="media_converter_v${VERSION}.zip"

# Remove existing zip if it exists
if [ -f "$OUTFILE" ]; then
    print_message "Removing existing zip file..." "$YELLOW"
    rm "$OUTFILE"
fi

# Create temporary directory
TEMPDIR="temp_package"
print_message "Creating temporary directory..." "$YELLOW"
rm -rf "$TEMPDIR"
mkdir "$TEMPDIR"

# Copy necessary files
print_message "Copying files..." "$YELLOW"

# Create directory structure
mkdir -p "$TEMPDIR/src"
mkdir -p "$TEMPDIR/config"

# Copy source files
cp src/*.py "$TEMPDIR/src/"

# Copy config files
cp config/profiles.json "$TEMPDIR/config/"

# Copy installation files
cp install_dependencies.bat "$TEMPDIR/"
cp install_dependencies.sh "$TEMPDIR/"
cp requirements.txt "$TEMPDIR/"
cp README.md "$TEMPDIR/"
cp run.bat "$TEMPDIR/"


# Create empty directories
mkdir -p "$TEMPDIR/converted_files"
mkdir -p "$TEMPDIR/data"

# Create .env template
echo "FFMPEG_PATH=ffmpeg" > "$TEMPDIR/.env"
echo "DEFAULT_OUTPUT_FORMAT=mp4" >> "$TEMPDIR/.env"
echo "DEFAULT_PROFILE=h264_web_optimized" >> "$TEMPDIR/.env"

# Create zip archive
print_message "Creating zip archive..." "$YELLOW"
cd "$TEMPDIR"
zip -r "../$OUTFILE" ./* .env
cd ..

# Clean up
print_message "Cleaning up..." "$YELLOW"
rm -rf "$TEMPDIR"

print_message "✓ Package created successfully: $OUTFILE" "$GREEN"
print_message "Archive contents:" "$YELLOW"
unzip -l "$OUTFILE" 