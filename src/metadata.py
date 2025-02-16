from typing import Dict, Optional
import json
import subprocess
from pathlib import Path

class MetadataHandler:
    def __init__(self):
        pass

    def read_metadata(self, file_path: str) -> Optional[Dict]:
        """Read metadata from a media file using FFprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception:
            return None

    def write_metadata(self, file_path: str, metadata: Dict) -> bool:
        """Write metadata to a media file."""
        # TODO: Implement metadata writing
        return True

    def display_metadata(self, metadata: Dict):
        """Display metadata in a user-friendly format."""
        if not metadata:
            print("No metadata available")
            return

        print("\nFile Metadata:")
        if 'format' in metadata:
            fmt = metadata['format']
            print("\nFormat Information:")
            print(f"Format: {fmt.get('format_name', 'Unknown')}")
            print(f"Duration: {fmt.get('duration', 'Unknown')} seconds")
            print(f"Size: {fmt.get('size', 'Unknown')} bytes")
            print(f"Bitrate: {fmt.get('bit_rate', 'Unknown')} bits/s")

        if 'streams' in metadata:
            print("\nStreams:")
            for stream in metadata['streams']:
                print(f"\nStream #{stream.get('index', '?')}:")
                print(f"Type: {stream.get('codec_type', 'Unknown')}")
                print(f"Codec: {stream.get('codec_name', 'Unknown')}")
                if stream.get('codec_type') == 'video':
                    print(f"Resolution: {stream.get('width', '?')}x{stream.get('height', '?')}")
                    print(f"FPS: {stream.get('r_frame_rate', 'Unknown')}")
                elif stream.get('codec_type') == 'audio':
                    print(f"Sample Rate: {stream.get('sample_rate', 'Unknown')} Hz")
                    print(f"Channels: {stream.get('channels', 'Unknown')}")

    def get_metadata(self, file_path):
        try:
            audio = File(file_path, easy=True)
            if audio is None:
                audio = File(file_path)
            return audio
        except Exception as e:
            return None

    def display_info(self, file_path):
        metadata = self.get_metadata(file_path)
        if metadata:
            # Implementation for displaying metadata
            pass
        
    def update_metadata(self, file_path, metadata_dict):
        try:
            audio = EasyID3(file_path)
            for key, value in metadata_dict.items():
                audio[key] = value
            audio.save()
            return True
        except Exception as e:
            return False 