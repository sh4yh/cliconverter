import os
import re
import subprocess
import time
import select
import platform
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Union
from tqdm.auto import tqdm
from profiles import FormatProfiles

class MediaConverter:
    def __init__(self, profiles: Optional[FormatProfiles] = None):
        """Initialize the converter with optional profiles instance."""
        self.ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
        self.profiles = profiles or FormatProfiles()

    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available and working."""
        try:
            subprocess.run([self.ffmpeg_path, '-version'], 
                         capture_output=True, 
                         check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_media_info(self, input_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Get media file information using profiles' metadata extraction."""
        return self.profiles.extract_metadata(str(input_path))

    def create_profile_from_file(self, input_path: Union[str, Path], profile_name: str) -> Optional[Dict[str, Any]]:
        """Create a new profile based on input file's properties."""
        return self.profiles.create_profile_from_reference(str(input_path), profile_name)

    def _get_duration(self, input_file: str) -> Optional[float]:
        """Get media file duration using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(input_file)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration_str = result.stdout.strip()
            
            # Handle 'N/A' or empty duration
            if not duration_str or duration_str == 'N/A':
                # Try alternative method using streams
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-select_streams', 'v:0',  # Select first video stream
                    '-show_entries', 'stream=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(input_file)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                duration_str = result.stdout.strip()
                
                # If still no duration, try with frames and frame rate
                if not duration_str or duration_str == 'N/A':
                    cmd = [
                        'ffprobe',
                        '-v', 'error',
                        '-select_streams', 'v:0',
                        '-count_frames',
                        '-show_entries', 'stream=nb_frames,r_frame_rate',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        str(input_file)
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        nb_frames = lines[0].strip()
                        frame_rate = lines[1].strip()
                        
                        if nb_frames.isdigit() and '/' in frame_rate:
                            num, den = map(float, frame_rate.split('/'))
                            if den != 0:  # Avoid division by zero
                                fps = num / den
                                if fps > 0:  # Avoid division by zero
                                    return float(nb_frames) / fps
            
            # Try to convert the duration string to float if we got one
            if duration_str and duration_str != 'N/A':
                return float(duration_str)
                
            # If all methods fail, return a default duration
            return 0
            
        except (subprocess.SubprocessError, ValueError):
            return 0

    def _parse_time(self, time_str: str) -> Optional[float]:
        """Parse FFmpeg time string into seconds."""
        try:
            if ':' in time_str:
                h, m, s = time_str.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
            return float(time_str)
        except (ValueError, TypeError):
            return None

    def convert_file(self, 
                    input_path: Union[str, Path], 
                    output_path: Union[str, Path], 
                    profile_name: str,
                    category: Optional[str] = None) -> subprocess.CompletedProcess:
        """Convert a media file using the specified profile with interactive progress tracking."""
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg first.")

        # Get file duration for progress calculation
        duration = self._get_duration(input_path)
        if not duration:
            print("Warning: Could not determine file duration. Progress may be inaccurate.")
            duration = 0

        # If category not provided, detect from input file
        if category is None:
            media_info = self.get_media_info(input_path)
            if not media_info:
                raise ValueError("Could not detect media type from input file")
            category = "video" if media_info.get("video") else "audio"

        # Get the FFmpeg command from profiles
        cmd = self.profiles.generate_ffmpeg_command(
            str(input_path),
            str(output_path),
            category,
            profile_name
        )
        
        if not cmd:
            raise ValueError(f"Profile '{profile_name}' not found in category '{category}'")

        # Split the command string into list and replace ffmpeg path
        cmd_parts = cmd.split()
        cmd_parts[0] = self.ffmpeg_path
        
        # Add progress monitoring parameters
        cmd_parts.insert(1, '-progress')
        cmd_parts.insert(2, 'pipe:1')
        cmd_parts.insert(3, '-nostats')

        try:
            # Start the conversion process
            process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Initialize progress bar with enhanced format
            with tqdm(total=100,
                     desc=f"Converting {Path(input_path).name}",
                     unit="%",
                     bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}% [{elapsed}<{remaining}]",
                     dynamic_ncols=True,
                     position=1,
                     leave=False) as pbar:
                
                current_time = 0
                last_progress = 0

                # Monitor progress
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    
                    if line.startswith('out_time='):
                        time_str = line.split('=')[1].strip()
                        current_time = self._parse_time(time_str) or current_time
                        if duration > 0:
                            progress = min(100, int(100 * current_time / duration))
                            # Only update if progress has changed
                            if progress > last_progress:
                                pbar.update(progress - last_progress)
                                last_progress = progress
                                pbar.refresh()

            # Check for errors
            if process.returncode != 0:
                error_output = process.stderr.read()
                raise subprocess.CalledProcessError(
                    process.returncode, cmd_parts, stderr=error_output
                )

            return subprocess.CompletedProcess(cmd_parts, process.returncode)

        except subprocess.CalledProcessError as e:
            # Enhance error message with FFmpeg output
            error_msg = f"Conversion failed: {str(e)}\nFFmpeg output:\n{e.stderr}"
            raise subprocess.SubprocessError(error_msg)

    def convert_file_with_profile(self, 
                                input_path: Union[str, Path], 
                                output_path: Union[str, Path],
                                profile: Dict[str, Any],
                                category: str) -> subprocess.CompletedProcess:
        """Convert a media file using the provided profile with interactive progress tracking."""
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg first.")

        # Get file duration for progress calculation
        duration = self._get_duration(input_path)
        if not duration:
            print("Warning: Could not determine file duration. Progress may be inaccurate.")
            duration = 0

        # Initialize filter chains
        video_filters = []
        audio_filters = []

        # Add video parameters
        cmd = ['ffmpeg', '-i', str(input_path)]
        
        # Get the target speed from either video or audio settings
        target_speed = "1x"
        if category == "video" and "video" in profile:
            target_speed = profile["video"].get("speed_control", "1x")
            # Ensure audio speed matches video speed for synchronization
            if "audio" in profile:
                profile["audio"]["audio_speed"] = target_speed
        elif "audio" in profile:
            target_speed = profile["audio"].get("audio_speed", "1x")

        if category == "video" and "video" in profile:
            video = profile["video"]
            
            # Handle video speed first
            if target_speed != "1x":
                speed = float(target_speed.replace('x', ''))
                video_filters.append(f'setpts={1/speed}*PTS')
                # If codec is copy and we have speed change, switch to h264
                if video.get("codec") == "copy":
                    video["codec"] = "libx264"
            
            # Add video parameters
            cmd.extend(['-c:v', video.get("codec", "copy")])
            if video.get("codec") != "copy":
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
                if video.get("crf") != "copy":
                    cmd.extend(['-crf', video["crf"]])

        # Handle audio parameters
        if "audio" in profile:
            audio = profile["audio"]
            
            # Handle audio speed first
            if target_speed != "1x":
                speed = float(target_speed.replace('x', ''))
                # If codec is copy and we have speed change, switch to aac
                if audio.get("codec") == "copy":
                    audio["codec"] = "aac"
                # For speeds > 2x or < 0.5x, chain multiple atempo filters
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

            # Add audio parameters
            cmd.extend(['-c:a', audio.get("codec", "copy")])
            if audio.get("codec") != "copy":
                if audio.get("bitrate") != "copy":
                    cmd.extend(['-b:a', audio["bitrate"]])
                if audio.get("sample_rate") != "copy":
                    cmd.extend(['-ar', audio["sample_rate"]])
                if audio.get("channels") != "copy":
                    cmd.extend(['-ac', audio["channels"]])

        # Add filters if any
        if video_filters:
            cmd.extend(['-filter:v', ','.join(video_filters)])
        if audio_filters:
            cmd.extend(['-filter:a', ','.join(audio_filters)])

        # Add output file
        cmd.append(str(output_path))
        
        # Add progress monitoring parameters
        cmd.insert(1, '-progress')
        cmd.insert(2, 'pipe:1')
        cmd.insert(3, '-nostats')
        
        # Add overwrite flag
        cmd.insert(1, '-y')

        try:
            # Print the command for debugging
            print(f"\nExecuting FFmpeg command:\n{' '.join(cmd)}\n")
            
            # Start the conversion process with shell=True on Windows
            is_windows = platform.system().lower() == "windows"
            
            if is_windows:
                # Ensure proper encoding for Windows
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
                
                # For Windows, use a temporary file for progress monitoring
                progress_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
                progress_path = progress_file.name
                progress_file.close()
                
                # Use string command for Windows with proper quoting
                cmd_str = ' '.join(f'"{x}"' if ' ' in str(x) or any(c in str(x) for c in '()[]{}$&^=;!\'`~') else str(x) for x in cmd)
                # Replace pipe:1 with the temporary file path
                cmd_str = cmd_str.replace('pipe:1', f'"{progress_path}"')
                
                process = subprocess.Popen(
                    cmd_str,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    universal_newlines=True,
                    bufsize=1,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                # Initialize progress bar with enhanced format
                with tqdm(total=100,
                         desc=f"Converting {Path(input_path).name}",
                         unit="%",
                         bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}% [{elapsed}<{remaining}]",
                         dynamic_ncols=True,
                         position=1,
                         leave=False) as pbar:
                    
                    current_time = 0
                    last_progress = 0
                    error_output = []
                    last_size = 0

                    while process.poll() is None:
                        # Read progress from the temporary file
                        try:
                            if os.path.exists(progress_path):
                                current_size = os.path.getsize(progress_path)
                                if current_size > last_size:
                                    with open(progress_path, 'r', encoding='utf-8') as f:
                                        f.seek(last_size)
                                        for line in f:
                                            if line.startswith('out_time='):
                                                time_str = line.split('=')[1].strip()
                                                current_time = self._parse_time(time_str) or current_time
                                                if duration > 0:
                                                    progress = min(100, int(100 * current_time / duration))
                                                    if progress > last_progress:
                                                        pbar.update(progress - last_progress)
                                                        last_progress = progress
                                                        pbar.refresh()
                                    last_size = current_size
                        except Exception as e:
                            print(f"Warning: Error reading progress file: {e}")
                        
                        # Check stderr for errors
                        stderr_line = process.stderr.readline()
                        if stderr_line:
                            error_output.append(stderr_line.strip())
                        
                        # Add a small sleep to prevent CPU overload
                        time.sleep(0.1)

                # Clean up the temporary file
                try:
                    os.unlink(progress_path)
                except:
                    pass

            else:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    universal_newlines=True,
                    bufsize=1
                )

                # Initialize progress bar with enhanced format
                with tqdm(total=100,
                         desc=f"Converting {Path(input_path).name}",
                         unit="%",
                         bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}% [{elapsed}<{remaining}]",
                         dynamic_ncols=True,
                         position=1,
                         leave=False) as pbar:
                    
                    current_time = 0
                    last_progress = 0
                    error_output = []

                    while process.poll() is None:
                        # Unix systems can use select
                        reads = [process.stdout.fileno(), process.stderr.fileno()]
                        ret = select.select(reads, [], [], 1.0)

                        for fd in ret[0]:
                            if fd == process.stdout.fileno():
                                stdout_line = process.stdout.readline()
                                if stdout_line.startswith('out_time='):
                                    time_str = stdout_line.split('=')[1].strip()
                                    current_time = self._parse_time(time_str) or current_time
                                    if duration > 0:
                                        progress = min(100, int(100 * current_time / duration))
                                        if progress > last_progress:
                                            pbar.update(progress - last_progress)
                                            last_progress = progress
                                            pbar.refresh()
                            elif fd == process.stderr.fileno():
                                stderr_line = process.stderr.readline()
                                if stderr_line:
                                    error_output.append(stderr_line.strip())

                        # Add a small sleep to prevent CPU overload
                        time.sleep(0.1)

            # Get the return code
            return_code = process.wait()

            # Capture any remaining stderr output
            remaining_stderr = process.stderr.read()
            if remaining_stderr:
                error_output.append(remaining_stderr)

            # If conversion failed, raise an error with the captured output
            if return_code != 0:
                error_msg = "\n".join(error_output)
                raise subprocess.CalledProcessError(return_code, cmd, stderr=error_msg)

            # Check if output file exists and has size greater than 0
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                error_msg = "\n".join(error_output)
                raise subprocess.SubprocessError(f"FFmpeg failed to create output file. Error output:\n{error_msg}")

            return subprocess.CompletedProcess(cmd, return_code)

        except subprocess.CalledProcessError as e:
            # Enhance error message with FFmpeg output
            error_msg = f"Conversion failed with return code {e.returncode}:\n{e.stderr}"
            raise subprocess.SubprocessError(error_msg)
        except Exception as e:
            # Handle any other exceptions
            error_msg = f"Conversion failed with error: {str(e)}"
            raise subprocess.SubprocessError(error_msg)

    def list_profiles(self, category: Optional[str] = None) -> Dict[str, list]:
        """List available conversion profiles."""
        return self.profiles.list_profiles(category)

    def edit_profile(self, 
                    category: str,
                    profile_name: str,
                    parameter: str,
                    value: str) -> bool:
        """
        Edit a profile parameter.
        
        Args:
            category: Profile category (video/audio)
            profile_name: Name of the profile to edit
            parameter: Parameter path (e.g., "video.codec" or "audio.bitrate")
            value: New value for the parameter
        
        Returns:
            bool: True if edit was successful
        """
        return self.profiles.edit_profile_parameter(category, profile_name, parameter, value)

    def get_profile_details(self, category: str, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed settings for a profile."""
        return self.profiles.get_profile(category, profile_name)

    def get_parameter_options(self, parameter: str) -> list:
        """Get available options for a specific parameter."""
        return self.profiles.get_parameter_options(parameter)

    def get_editable_parameters(self, category: str) -> Dict[str, list]:
        """Get list of editable parameters for a category."""
        return self.profiles.get_editable_parameters(category) 