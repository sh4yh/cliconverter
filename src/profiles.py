import json
from pathlib import Path
from typing import Dict, Optional, List, Union, Any
import subprocess
import re

class FormatProfiles:
    def __init__(self, config_path: str = "config/profiles.json"):
        self.config_path = Path(config_path)
        self._load_profiles()

    def _load_profiles(self):
        """Load profiles from JSON file. Create default if doesn't exist."""
        if not self.config_path.exists():
            # Initialize with default schema and profiles
            self.profiles = {
                "audio": {
                    "mp3_high": {
                        "container": "mp3",
                        "audio": {
                            "codec": "libmp3lame",
                            "bitrate": "320k",
                            "sample_rate": "44100",
                            "channels": "2",
                            "audio_speed": "1x"
                        }
                    },
                    "aac_high": {
                        "container": "m4a",
                        "audio": {
                            "codec": "aac",
                            "bitrate": "256k",
                            "sample_rate": "48000",
                            "channels": "2",
                            "audio_speed": "1x"
                        }
                    },
                    "double_speed": {
                        "container": "mp3",
                        "audio": {
                            "codec": "libmp3lame",
                            "bitrate": "320k",
                            "sample_rate": "44100",
                            "channels": "2",
                            "audio_speed": "2x"
                        }
                    },
                    "half_speed": {
                        "container": "mp3",
                        "audio": {
                            "codec": "libmp3lame",
                            "bitrate": "320k",
                            "sample_rate": "44100",
                            "channels": "2",
                            "audio_speed": "0.5x"
                        }
                    }
                },
                "video": {
                    "youtube_1080p": {
                        "container": "mp4",
                        "video": {
                            "codec": "libx264",
                            "resolution": "1920x1080",
                            "bitrate": "copy",
                            "crf": "21",
                            "fps": "30",
                            "pixel_format": "yuv420p",
                            "gop": "60",
                            "preset": "slow",
                            "tune": "film",
                            "speed_control": "1x"
                        },
                        "audio": {
                            "codec": "aac",
                            "bitrate": "128k",
                            "sample_rate": "48000",
                            "channels": "2"
                        }
                    },
                    "youtube_4k": {
                        "container": "mp4",
                        "video": {
                            "codec": "libx264",
                            "resolution": "3840x2160",
                            "bitrate": "copy",
                            "crf": "18",
                            "fps": "30",
                            "pixel_format": "yuv420p",
                            "gop": "60",
                            "preset": "slow",
                            "tune": "film",
                            "speed_control": "1x"
                        },
                        "audio": {
                            "codec": "aac",
                            "bitrate": "192k",
                            "sample_rate": "48000",
                            "channels": "2",
                            "audio_speed": "1x"
                        }
                    },
                    "h264_web_optimized": {
                        "container": "mp4",
                        "video": {
                            "codec": "libx264",
                            "resolution": "1920x1080",
                            "bitrate": "2M",
                            "crf": "23",
                            "fps": "30",
                            "pixel_format": "yuv420p",
                            "gop": "60",
                            "preset": "medium",
                            "tune": "film",
                            "speed_control": "1x"
                        },
                        "audio": {
                            "codec": "aac",
                            "bitrate": "192k",
                            "sample_rate": "48000",
                            "channels": "2",
                            "audio_speed": "1x"
                        }
                    },
                    "fast_motion": {
                        "container": "mp4",
                        "video": {
                            "codec": "libx264",
                            "resolution": "1920x1080",
                            "bitrate": "2M",
                            "crf": "23",
                            "fps": "30",
                            "pixel_format": "yuv420p",
                            "gop": "60",
                            "preset": "medium",
                            "tune": "film",
                            "speed_control": "2x"
                        },
                        "audio": {
                            "codec": "aac",
                            "bitrate": "192k",
                            "sample_rate": "48000",
                            "channels": "2",
                            "audio_speed": "2x"
                        }
                    },
                    "slow_motion": {
                        "container": "mp4",
                        "video": {
                            "codec": "libx264",
                            "resolution": "1920x1080",
                            "bitrate": "2M",
                            "crf": "23",
                            "fps": "30",
                            "pixel_format": "yuv420p",
                            "gop": "60",
                            "preset": "medium",
                            "tune": "film",
                            "speed_control": "0.5x"
                        },
                        "audio": {
                            "codec": "aac",
                            "bitrate": "192k",
                            "sample_rate": "48000",
                            "channels": "2",
                            "audio_speed": "0.5x"
                        }
                    }
                },
                "schema": {
                    "video_codecs": ["copy", "libx264", "libx265", "libvpx-vp9", "mpeg4", "prores"],
                    "resolutions": ["copy", "3840x2160", "2560x1440", "1920x1080", "1280x720", "854x480", "640x360", "custom (e.g., 720x1280)"],
                    "video_bitrates": ["copy", "1M", "2M", "4M", "6M", "8M", "10M", "12M", "15M", "20M"],
                    "crf_values": ["copy", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28"],
                    "framerates": ["copy", "23.976", "24", "25", "29.97", "30", "48", "50", "59.94", "60"],
                    "pixel_formats": ["copy", "yuv420p", "yuv422p", "yuv444p", "rgb24", "yuv420p10le", "yuv422p10le"],
                    "gop_sizes": ["copy", "30", "60", "120"],
                    "presets": ["copy", "ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"],
                    "tune_options": ["copy", "film", "animation", "grain", "stillimage", "fastdecode", "zerolatency"],
                    "speed_controls": ["0.25x", "0.5x", "0.75x", "1x", "1.25x", "1.5x", "1.75x", "2x", "4x", "10x"],
                    "audio_codecs": ["copy", "aac", "libmp3lame", "flac", "opus", "pcm_s16le", "pcm_s24le", "vorbis"],
                    "audio_bitrates": ["copy", "96k", "128k", "160k", "192k", "224k", "256k", "320k", "384k", "448k", "512k"],
                    "sample_rates": ["copy", "22050", "32000", "44100", "48000", "88200", "96000"],
                    "channel_layouts": ["copy", "1", "2", "2.1", "3", "4", "5.0", "5.1", "6.1", "7.1"],
                    "audio_speeds": ["0.25x", "0.5x", "0.75x", "1x", "1.25x", "1.5x", "1.75x", "2x", "4x", "10x"],
                    "containers": ["mp4", "mkv", "mov", "webm", "avi", "ts", "mxf", "mp3", "m4a", "flac", "wav", "ogg"]
                }
            }
            self._save_profiles()
        else:
            try:
                with open(self.config_path, 'r') as f:
                    self.profiles = json.load(f)
                    
                # Update existing profiles to match new schema
                for category, profiles in self.profiles.items():
                    if category == "schema":
                        continue
                        
                    for profile_name, profile in profiles.items():
                        if category == "video":
                            # Ensure video profile has speed_control
                            if "video" in profile:
                                if "speed_control" not in profile["video"]:
                                    # If audio_speed exists, use that value, otherwise default to "1x"
                                    speed = profile.get("audio", {}).get("audio_speed", "1x")
                                    profile["video"]["speed_control"] = speed
                                
                                # Remove audio_speed from audio settings in video profiles
                                if "audio" in profile and "audio_speed" in profile["audio"]:
                                    profile["audio"]["audio_speed"] = profile["video"]["speed_control"]
                        
                        elif category == "audio":
                            # Ensure audio profile has audio_speed
                            if "audio" in profile and "audio_speed" not in profile["audio"]:
                                profile["audio"]["audio_speed"] = "1x"
                
                # Save the updated profiles
                self._save_profiles()
                
            except (json.JSONDecodeError, FileNotFoundError):
                print(f"Error loading profiles from {self.config_path}, creating new file")
                self._load_profiles()  # Recursively call to create new file

    def _save_profiles(self):
        """Save profiles to JSON file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.profiles, f, indent=4)

    def _validate_profile(self, category: str, settings: Dict) -> bool:
        """Validate profile settings against schema."""
        schema = self.profiles.get("schema", {})
        if not schema:
            return True  # Skip validation if schema is not defined

        # Validate container format first
        if settings.get("container") not in schema.get("containers", []):
            print(f"Invalid container format: {settings.get('container')}")
            return False

        if category == "video":
            video_settings = settings.get("video", {})
            audio_settings = settings.get("audio", {})
            
            # Get speed from video settings
            speed_control = video_settings.get("speed_control", "1x")
            if speed_control not in schema.get("speed_controls", []):
                print(f"Invalid speed control: {speed_control}")
                return False
            
            # Ensure audio speed matches video speed for synchronization
            if "audio" in settings:
                audio_settings["audio_speed"] = speed_control

            # Validate video settings
            for param, value in video_settings.items():
                if param == "speed_control":
                    continue  # Already validated
                param_type = f"video_{param}s"
                if param_type in schema and value != "copy" and value not in schema[param_type]:
                    print(f"Invalid video {param}: {value}")
                    return False

            # Validate audio settings
            for param, value in audio_settings.items():
                if param == "audio_speed":
                    continue  # Skip as it's synchronized with video speed
                param_type = f"audio_{param}s" if param != "codec" else "audio_codecs"
                if param_type in schema and value != "copy" and value not in schema[param_type]:
                    print(f"Invalid audio {param}: {value}")
                    return False

        elif category == "audio":
            audio_settings = settings.get("audio", {})
            
            # Validate audio settings
            for param, value in audio_settings.items():
                param_type = f"audio_{param}s" if param != "codec" else "audio_codecs"
                if param_type in schema and value != "copy" and value not in schema[param_type]:
                    print(f"Invalid audio {param}: {value}")
                    return False

        return True

    def get_profile(self, category: str, profile_name: str) -> Optional[Dict]:
        """Get a profile by category and name."""
        if category not in self.profiles:
            return None
        return self.profiles[category].get(profile_name)

    def add_profile(self, category: str, name: str, settings: Dict) -> bool:
        """Add or update a profile in the specified category."""
        if category not in ["audio", "video"]:
            return False
            
        if not self._validate_profile(category, settings):
            return False
        
        if category not in self.profiles:
            self.profiles[category] = {}
        
        self.profiles[category][name] = settings
        self._save_profiles()
        return True

    def remove_profile(self, category: str, name: str) -> bool:
        """Remove a profile from the specified category."""
        if category in self.profiles and name in self.profiles[category]:
            del self.profiles[category][name]
            self._save_profiles()
            return True
        return False

    def list_profiles(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """List all profiles, optionally filtered by category."""
        if category:
            if category not in self.profiles:
                return {}
            return {category: list(self.profiles[category].keys())}
        return {cat: list(profiles.keys()) for cat, profiles in self.profiles.items() if cat != "schema"}

    def get_categories(self) -> List[str]:
        """Get list of available categories."""
        return [cat for cat in self.profiles.keys() if cat != "schema"]

    def get_schema(self) -> Dict[str, List[str]]:
        """Get the profile schema containing valid options for each parameter."""
        return self.profiles.get("schema", {})

    def import_profile(self, profile_path: str) -> Optional[Dict]:
        """Import a profile from a JSON file."""
        try:
            with open(profile_path, 'r') as f:
                new_profile = json.load(f)
                if not isinstance(new_profile, dict):
                    return None
                return new_profile
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def export_profile(self, category: str, profile_name: str, export_path: str) -> bool:
        """Export a profile to a JSON file."""
        profile = self.get_profile(category, profile_name)
        if not profile:
            return False
        
        try:
            with open(export_path, 'w') as f:
                json.dump(profile, f, indent=4)
            return True
        except:
            return False

    def create_profile_from_reference(self, file_path: str, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Create a new profile from a reference file.
        Returns the created profile if successful, None otherwise.
        """
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', 
                  '-show_format', '-show_streams', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("Error: Failed to analyze the file with ffprobe")
                return None
                
            metadata = json.loads(result.stdout)
            if not metadata or 'streams' not in metadata or 'format' not in metadata:
                print("Error: Invalid or incomplete metadata from ffprobe")
                return None

            # Determine category based on streams present
            has_video = any(s.get('codec_type') == 'video' for s in metadata['streams'])
            category = "video" if has_video else "audio"
            
            # Get container format
            container = metadata['format']['format_name'].split(',')[0].lower()
            # If container not in supported list, default to mp4/m4a
            if container not in self.get_schema()['containers']:
                container = 'mp4' if category == "video" else 'm4a'
            
            # Create profile structure
            profile = {"container": container}
            
            # Add video settings if it's a video file
            if category == "video":
                video_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
                if video_stream:
                    profile["video"] = {
                        "codec": "libx264",  # Default to h264 for compatibility
                        "resolution": f"{video_stream.get('width', '1920')}x{video_stream.get('height', '1080')}",
                        "bitrate": "copy",
                        "crf": "23",
                        "fps": video_stream.get('r_frame_rate', '30').split('/')[0],
                        "pixel_format": "yuv420p",  # Default to common format
                        "gop": "60",
                        "preset": "medium",
                        "tune": "film",
                        "speed_control": "1x"
                    }

            # Add audio settings
            audio_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'audio'), None)
            if audio_stream:
                profile["audio"] = {
                    "codec": "aac" if category == "video" else "libmp3lame",  # Default to AAC for video, MP3 for audio
                    "bitrate": "192k",  # Default to common bitrate
                    "sample_rate": "48000",  # Default to common sample rate
                    "channels": "2",  # Default to stereo
                    "audio_speed": "1x"
                }
            
            # Validate and add the profile
            if self.add_profile(category, profile_name, profile):
                print(f"\nProfile '{profile_name}' created successfully in {category} category!")
                return profile
            else:
                print(f"\nFailed to create profile: validation failed")
                return None

        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
            print(f"Error creating profile: {str(e)}")
            return None

    def edit_profile_parameter(self, category: str, profile_name: str, 
                             parameter_path: str, new_value: str) -> bool:
        """
        Edit a specific parameter in a profile.
        parameter_path format: "section.parameter" (e.g., "video.codec" or "audio.bitrate")
        Returns True if successful, False otherwise.
        """
        if category not in self.profiles:
            return False

        profile = self.profiles[category].get(profile_name)
        if not profile:
            return False

        # Split the parameter path
        section, param = parameter_path.split('.')
        if section not in profile or param not in profile[section]:
            return False

        # Validate the new value against schema
        schema = self.get_schema()
        param_type = f"{section}_{param}s"  # e.g., video_codecs, audio_bitrates
        
        if param_type in schema:
            if new_value != "copy" and new_value not in schema[param_type]:
                return False
        
        # Create a copy of the profile to modify
        updated_profile = dict(profile)
        updated_profile[section] = dict(profile[section])
        
        # Update the parameter
        updated_profile[section][param] = new_value
        
        # Save the updated profile
        self.profiles[category][profile_name] = updated_profile
        self._save_profiles()
        
        return True

    def get_parameter_options(self, parameter_path: str) -> List[str]:
        """
        Get available options for a specific parameter from the schema.
        parameter_path format: "section.parameter" (e.g., "video.codec" or "audio.bitrate")
        """
        schema = self.get_schema()
        section, param = parameter_path.split('.')
        
        # Special handling for speed parameters
        if param == "speed_control":
            return schema.get("speed_controls", [])
        elif param == "audio_speed":
            return schema.get("audio_speeds", [])
            
        # For other parameters
        param_type = f"{section}_{param}s"
        return schema.get(param_type, [])

    def get_editable_parameters(self, category: str) -> Dict[str, List[str]]:
        """
        Get a list of all editable parameters for a category (video or audio).
        Returns a dictionary of sections with their parameters.
        """
        if category == "video":
            return {
                "video": [
                    "codec", "resolution", "bitrate", "crf", "fps",
                    "pixel_format", "gop", "preset", "tune", "speed_control"
                ],
                "audio": [
                    "codec", "bitrate", "sample_rate", "channels"
                ]
            }
        elif category == "audio":
            return {
                "audio": [
                    "codec", "bitrate", "sample_rate", "channels", "audio_speed"
                ]
            }
        return {}

    def extract_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from a media file using FFmpeg."""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', 
                  '-show_format', '-show_streams', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
                
            metadata = json.loads(result.stdout)
            
            # Extract relevant information
            video_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'audio'), None)
            
            # Get container format
            container = metadata['format']['format_name'].split(',')[0]
            if container not in self.get_schema()['containers']:
                container = 'mp4'  # Default to mp4 if container not supported
            
            profile = {
                "container": container,
                "video": {},
                "audio": {}
            }
            
            if video_stream:
                profile["video"] = {
                    "codec": video_stream.get('codec_name', 'copy'),
                    "resolution": f"{video_stream.get('width', 'copy')}x{video_stream.get('height', 'copy')}",
                    "bitrate": str(int(metadata['format'].get('bit_rate', 0)) // 1000) + 'k' if 'bit_rate' in metadata['format'] else 'copy',
                    "fps": video_stream.get('r_frame_rate', 'copy').split('/')[0] if 'r_frame_rate' in video_stream else 'copy',
                    "pixel_format": video_stream.get('pix_fmt', 'copy'),
                    "crf": "copy",
                    "gop": "copy",
                    "preset": "medium",  # Default to medium preset
                    "tune": "copy",
                    "speed_control": "1x"
                }
                
            if audio_stream:
                profile["audio"] = {
                    "codec": audio_stream.get('codec_name', 'copy'),
                    "bitrate": str(int(audio_stream.get('bit_rate', 0)) // 1000) + 'k' if 'bit_rate' in audio_stream else 'copy',
                    "sample_rate": str(audio_stream.get('sample_rate', 'copy')),
                    "channels": str(audio_stream.get('channels', 'copy')),
                    "audio_speed": "1x"
                }
                
            return profile
            
        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
            print(f"Error extracting metadata: {str(e)}")
            return None

    def generate_ffmpeg_command(self, input_file: str, output_file: str, 
                              category: str, profile_name: str) -> Optional[str]:
        """Generate FFmpeg command from profile settings."""
        profile = self.get_profile(category, profile_name)
        if not profile:
            return None
            
        cmd = ['ffmpeg', '-i', input_file]
        
        # Track if we need to combine filters
        video_filters = []
        audio_filters = []
        
        # Add video parameters
        if category == "video" and "video" in profile:
            video = profile["video"]
            if video.get("codec") != "copy":
                cmd.extend(['-c:v', video["codec"]])
                if video.get("bitrate") != "copy":
                    cmd.extend(['-b:v', video["bitrate"]])
                if video.get("resolution") != "copy":
                    cmd.extend(['-s', video["resolution"]])
                if video.get("fps") != "copy":
                    cmd.extend(['-r', video["fps"]])
                if video.get("pixel_format") != "copy":
                    cmd.extend(['-pix_fmt', video["pixel_format"]])
                if video.get("preset") != "copy":
                    cmd.extend(['-preset', video["preset"]])
                if video.get("tune") != "copy":
                    cmd.extend(['-tune', video["tune"]])
                if video.get("speed_control", "1x") != "1x":
                    speed = float(video["speed_control"].replace('x', ''))
                    video_filters.append(f'setpts={1/speed}*PTS')
            else:
                cmd.extend(['-c:v', 'copy'])

        # Add audio parameters
        if "audio" in profile:
            audio = profile["audio"]
            if audio.get("codec") != "copy":
                cmd.extend(['-c:a', audio["codec"]])
                if audio.get("bitrate") != "copy":
                    cmd.extend(['-b:a', audio["bitrate"]])
                if audio.get("sample_rate") != "copy":
                    cmd.extend(['-ar', audio["sample_rate"]])
                if audio.get("channels") != "copy":
                    cmd.extend(['-ac', audio["channels"]])
                if audio.get("audio_speed", "1x") != "1x":
                    speed = float(audio["audio_speed"].replace('x', ''))
                    # For speeds > 2x or < 0.5x, we need to chain multiple atempo filters
                    if speed > 2:
                        stages = []
                        remaining_speed = speed
                        while remaining_speed > 2:
                            stages.append("atempo=2.0")
                            remaining_speed /= 2
                        stages.append(f"atempo={remaining_speed}")
                        audio_filters.append(','.join(stages))
                    elif speed < 0.5:
                        stages = []
                        remaining_speed = speed
                        while remaining_speed < 0.5:
                            stages.append("atempo=0.5")
                            remaining_speed *= 2
                        stages.append(f"atempo={remaining_speed}")
                        audio_filters.append(','.join(stages))
                    else:
                        audio_filters.append(f'atempo={speed}')
            else:
                cmd.extend(['-c:a', 'copy'])

        # Add filters if any
        if video_filters:
            cmd.extend(['-filter:v', ','.join(video_filters)])
        if audio_filters:
            cmd.extend(['-filter:a', ','.join(audio_filters)])

        # Add output file
        cmd.append(output_file)
        
        return ' '.join(cmd) 