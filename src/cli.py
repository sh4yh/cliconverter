import os
import json
import tempfile
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
from dotenv import load_dotenv
from tqdm.auto import tqdm
import sys
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from colorama import init, Fore, Style as ColoramaStyle
from converter import MediaConverter
from metadata import MetadataHandler
from profiles import FormatProfiles
import platform

# Initialize colorama
init()

load_dotenv()

class ConverterCLI:
    SUPPORTED_EXTENSIONS = {
        'audio': {'.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg', '.wma'},
        'video': {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}
    }

    def __init__(self):
        """Initialize the CLI interface with proper encoding setup."""
        # Set up proper encoding for Windows
        if platform.system().lower() == "windows":
            # Ensure console can handle Unicode
            os.system("chcp 65001")
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        
        self.profiles = FormatProfiles()
        self.converter = MediaConverter(profiles=self.profiles)
        self.metadata = MetadataHandler()
        self.temp_file = Path(tempfile.gettempdir()) / 'converter_files.json'
        self.selected_files: List[str] = []
        self.output_directory: Path = Path("converted_files")
        self._load_selected_files()

    def _load_selected_files(self):
        """Load previously selected files from temp storage."""
        if self.temp_file.exists():
            try:
                with open(self.temp_file, 'r', encoding='utf-8') as f:
                    self.selected_files = json.load(f)
            except json.JSONDecodeError:
                self.selected_files = []

    def _save_selected_files(self):
        """Save selected files to temp storage."""
        with open(self.temp_file, 'w', encoding='utf-8') as f:
            json.dump(self.selected_files, f, ensure_ascii=False)

    def _clear_selected_files(self):
        """Clear the selected files list and temp storage."""
        self.selected_files = []
        if self.temp_file.exists():
            self.temp_file.unlink()

    def _is_supported_file(self, file_path: str) -> bool:
        """Check if a file has a supported extension."""
        ext = Path(file_path).suffix.lower()
        return any(ext in exts for exts in self.SUPPORTED_EXTENSIONS.values())

    def _get_files_in_directory(self, directory: str) -> List[str]:
        """Get all supported files in a directory with interactive progress bar."""
        files = []
        print("\nScanning directory for media files...")
        
        # Convert to Path object for proper Unicode handling
        directory_path = Path(directory)
        
        # First, count total files for progress bar
        total_files = sum([len(files) for _, _, files in os.walk(str(directory_path))])
        
        with tqdm(total=total_files, 
                 desc="Scanning directory", 
                 unit="files",
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                 dynamic_ncols=True,
                 mininterval=0.1) as pbar:
            for root, _, filenames in os.walk(str(directory_path)):
                root_path = Path(root)
                for filename in filenames:
                    file_path = str(root_path / filename)
                    if self._is_supported_file(file_path):
                        files.append(file_path)
                    pbar.update(1)
                    pbar.refresh()
        
        if files:
            print(f"\nFound {len(files)} supported media files")
        return files

    def _display_directory_contents(self, current_dir: str) -> List[str]:
        """Display directory contents and return list of items."""
        items = []
        choices = []
        
        # Convert to Path object for proper Unicode handling
        current_path = Path(current_dir)
        parent_dir = str(current_path.parent)
        
        # Add parent directory option
        if str(current_path) != parent_dir:
            items.append(("..", parent_dir))
            choices.append(Choice(value=("directory", parent_dir), name="📁 .."))

        # Add directories and files
        try:
            # Use Path.iterdir() for better Unicode support
            entries = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            dir_choices = []
            file_choices = []
            
            for entry in entries:
                if entry.is_dir():
                    items.append((f"📁 {entry.name}", str(entry)))
                    dir_choices.append(Choice(value=("directory", str(entry)), name=f"📁 {entry.name}"))
                elif entry.is_file() and self._is_supported_file(str(entry)):
                    items.append((f"📄 {entry.name}", str(entry)))
                    file_choices.append(Choice(value=("file", str(entry)), name=f"📄 {entry.name}"))

            # Combine choices with separators
            if dir_choices:
                choices.append(Separator("Directories"))
                choices.extend(dir_choices)
            if file_choices:
                choices.append(Separator("Files"))
                choices.extend(file_choices)

        except Exception as e:
            print(f"\nError reading directory contents: {str(e)}")
            return [], []

        print(f"\nCurrent directory: {current_dir}")
        return items, choices

    def _select_files_menu(self) -> bool:
        """Interactive file selection menu using InquirerPy."""
        current_dir = os.getcwd()
        
        while True:
            items, choices = self._display_directory_contents(current_dir)
            
            # Add action choices
            choices.extend([
                Separator("Actions"),
                Choice(value=("action", "select_dir"), name="📁 Select Directory (Add all media files)"),
                Choice(value=("action", "confirm"), name="✅ Confirm and Continue"),
                Choice(value=("action", "clear"), name="🗑️  Clear selection"),
                Choice(value=("action", "cancel"), name="❌ Cancel")
            ])

            action = inquirer.select(
                message=f"Select files to convert (Selected: {len(self.selected_files)}):",
                choices=choices,
                default=None,
                amark="→",
                pointer="❯"
            ).execute()

            if not action:
                continue

            action_type, value = action

            if action_type == "directory":
                current_dir = value
            elif action_type == "file":
                if value not in self.selected_files:
                    self.selected_files.append(value)
                    print(f"Added: {value}")
                    self._save_selected_files()
            elif action_type == "action":
                if value == "select_dir":
                    # Allow user to select a directory to add all media files from it
                    print("\nSelect directory to add media files from:")
                    selected_dir = self._browse_directory("Select directory:", allow_create=False)
                    if selected_dir:
                        # Get all supported files from the directory
                        files = self._get_files_in_directory(str(selected_dir))
                        if files:
                            # Add new files that aren't already selected
                            new_files = [f for f in files if f not in self.selected_files]
                            self.selected_files.extend(new_files)
                            print(f"\nAdded {len(new_files)} new files from directory")
                            self._save_selected_files()
                        else:
                            print("\nNo supported media files found in directory")
                elif value == "confirm":
                    if not self.selected_files:
                        print("No files selected!")
                        continue
                    return True
                elif value == "clear":
                    self.selected_files = []
                    self._save_selected_files()
                    print("Selection cleared!")
                elif value == "cancel":
                    return False

    def _settings_menu(self):
        """Settings menu interface."""
        while True:
            action = inquirer.select(
                message="Settings",
                choices=[
                    Choice(value="output", name="📁 Output Directory"),
                    Choice(value="profiles", name="⚙️  Manage Profiles"),
                    Choice(value="back", name="⬅️  Back to Main Menu")
                ],
                default=None,
                amark="→",
                pointer="❯"
            ).execute()

            if action == "back":
                break
            elif action == "output":
                self._select_output_directory()
            elif action == "profiles":
                self._manage_profiles()

    def _manage_profiles(self):
        """Profile management interface."""
        while True:
            # Get the latest profiles
            profiles = self.profiles.list_profiles()
            choices = []
            
            # Add existing profiles
            for category, profile_list in profiles.items():
                if category != "schema":
                    choices.append(Separator(f"{category.upper()} PROFILES"))
                    for profile in sorted(profile_list):  # Sort profiles alphabetically
                        choices.append(Choice(value=("profile", (category, profile)), name=f"{profile}"))
            
            # Add actions
            choices.extend([
                Separator("Actions"),
                Choice(value=("action", "add"), name="➕ Add New Profile"),
                Choice(value=("action", "add_ref"), name="📄 Add Profile from Reference"),
                Choice(value=("action", "back"), name="⬅️  Back")
            ])

            action = inquirer.select(
                message="Profile Management",
                choices=choices,
                default=None,
                amark="→",
                pointer="❯"
            ).execute()

            if not action:
                continue

            action_type, value = action

            if action_type == "profile":
                # Show profile submenu
                category, profile_name = value
                self._profile_submenu(category, profile_name)
            elif action_type == "action":
                if value == "back":
                    break
                elif value == "add":
                    self._add_new_profile()
                elif value == "add_ref":
                    self._add_profile_from_reference()

    def _profile_submenu(self, category: str, profile_name: str):
        """Submenu for individual profile management."""
        while True:
            action = inquirer.select(
                message=f"Profile: {profile_name}",
                choices=[
                    Choice(value="view", name="👀 View Details"),
                    Choice(value="rename", name="✏️  Rename"),
                    Choice(value="delete", name="🗑️  Delete"),
                    Choice(value="back", name="⬅️  Back")
                ],
                default=None,
                amark="→",
                pointer="❯"
            ).execute()

            if action == "back":
                break
            elif action == "view":
                self._view_profile_details(category, profile_name)
            elif action == "rename":
                self._rename_profile(category, profile_name)
            elif action == "delete":
                if self._delete_profile(category, profile_name):
                    break  # Exit submenu if profile was deleted

    def _view_profile_details(self, category: str, name: str):
        """View detailed settings of a profile."""
        profile = self.profiles.get_profile(category, name)
        if not profile:
            print("\nFailed to load profile!")
            return

        print(f"\nProfile: {name} ({category})")
        print(f"Container: {profile['container']}")
        
        if "video" in profile:
            print("\nVideo Settings:")
            for key, value in profile["video"].items():
                if key == "speed_control":
                    print(f"  {key}: {value}" + (f" ({float(value.replace('x', ''))}x speed)" if value != "copy" else ""))
                else:
                    print(f"  {key}: {value}")
        
        if "audio" in profile:
            print("\nAudio Settings:")
            for key, value in profile["audio"].items():
                if key == "audio_speed":
                    print(f"  {key}: {value}" + (f" ({float(value.replace('x', ''))}x speed)" if value != "copy" else ""))
                else:
                    print(f"  {key}: {value}")

        # Add option to edit parameters
        print("\nOptions:")
        action = inquirer.select(
            message="Select action:",
            choices=[
                Choice(value="edit", name="✏️  Edit parameters"),
                Choice(value="back", name="⬅️  Back")
            ]
        ).execute()

        if action == "edit":
            self._edit_profile_parameters(category, name, profile)

    def _rename_profile(self, category: str, old_name: str):
        """Rename an existing profile."""
        new_name = inquirer.text(
            message="Enter new profile name:",
            validate=lambda x: len(x) > 0
        ).execute()

        profile = self.profiles.get_profile(category, old_name)
        if profile and self.profiles.add_profile(category, new_name, profile):
            self.profiles.remove_profile(category, old_name)
            print(f"\nProfile renamed from '{old_name}' to '{new_name}'!")
        else:
            print("\nFailed to rename profile!")

    def _delete_profile(self, category: str, name: str) -> bool:
        """Delete an existing profile."""
        confirm = inquirer.confirm(
            message=f"Are you sure you want to delete profile '{name}'?",
            default=False
        ).execute()

        if confirm and self.profiles.remove_profile(category, name):
            print(f"\nProfile '{name}' deleted!")
            return True
        else:
            print("\nProfile deletion cancelled or failed!")
            return False

    def _select_profile(self) -> Optional[tuple[str, str]]:
        """Interactive profile selection."""
        # Get the latest profiles directly from our instance
        profiles = self.profiles.list_profiles()
        choices = []
        
        for category, profile_list in profiles.items():
            if category != "schema":
                choices.append(Separator(f"{category.upper()} PROFILES"))
                for profile in sorted(profile_list):  # Sort profiles alphabetically
                    choices.append(Choice(value=(category, profile), name=f"{profile}"))

        if not choices:
            print("\nNo profiles available. Please create a profile first.")
            return None

        result = inquirer.select(
            message="Select a profile to use:",
            choices=choices,
            default=None,
            amark="→",
            pointer="❯"
        ).execute()

        return result

    def _browse_directory(self, message: str, allow_create: bool = False) -> Optional[Path]:
        """Interactive directory browser."""
        current_dir = os.getcwd()
        
        while True:
            items = []
            choices = []
            
            # Add parent directory option
            parent_dir = str(Path(current_dir).parent)
            if current_dir != parent_dir:
                items.append(("..", parent_dir))
                choices.append(Choice(value=("up", parent_dir), name="📁 .."))

            # Add directories
            for item in sorted(os.listdir(current_dir)):
                full_path = os.path.join(current_dir, item)
                if os.path.isdir(full_path):
                    items.append((item, full_path))
                    choices.append(Choice(value=("dir", full_path), name=f"📁 {item}"))
            
            # Add actions
            choices.extend([
                Separator("Actions"),
                Choice(value=("select", current_dir), name="✅ Select this directory")
            ])
            
            if allow_create:
                choices.append(Choice(value=("create", None), name="➕ Create new directory here"))

            print(f"\nCurrent directory: {current_dir}")
            
            action = inquirer.select(
                message=message,
                choices=choices,
                default=None,
                amark="→",
                pointer="❯"
            ).execute()

            if not action:
                return None

            action_type, value = action

            if action_type == "up" or action_type == "dir":
                current_dir = value
            elif action_type == "select":
                return Path(value)
            elif action_type == "create":
                # Get new directory name
                new_dir_name = inquirer.text(
                    message="Enter new directory name:",
                    validate=lambda x: len(x) > 0 and "/" not in x and "\\" not in x
                ).execute()
                
                try:
                    new_dir = Path(current_dir) / new_dir_name
                    new_dir.mkdir(parents=True, exist_ok=True)
                    return new_dir
                except Exception as e:
                    print(f"\nError creating directory: {str(e)}")
                    continue

    def _select_output_directory(self):
        """Select output directory for converted files."""
        print("\nSelect output directory for converted files:")
        new_dir = self._browse_directory("Select output directory:", allow_create=True)
        if new_dir:
            self.output_directory = new_dir
            print(f"\nOutput directory set to: {self.output_directory.absolute()}")

    def _add_profile_from_reference(self):
        """Add a new profile based on a reference file."""
        print("\nSelect reference file:")
        current_dir = os.getcwd()
        
        while True:
            items = []
            choices = []
            
            # Add parent directory option
            parent_dir = str(Path(current_dir).parent)
            if current_dir != parent_dir:
                choices.append(Choice(value=("up", parent_dir), name="📁 .."))

            # Add directories and files
            dir_choices = []
            file_choices = []
            
            for item in sorted(os.listdir(current_dir)):
                full_path = os.path.join(current_dir, item)
                if os.path.isdir(full_path):
                    dir_choices.append(Choice(value=("dir", full_path), name=f"📁 {item}"))
                elif os.path.isfile(full_path) and self._is_supported_file(full_path):
                    file_choices.append(Choice(value=("file", full_path), name=f"📄 {item}"))

            # Combine choices with separators
            if dir_choices:
                choices.append(Separator("Directories"))
                choices.extend(dir_choices)
            if file_choices:
                choices.append(Separator("Files"))
                choices.extend(file_choices)

            choices.append(Separator("Actions"))
            choices.append(Choice(value=("cancel", None), name="❌ Cancel"))

            print(f"\nCurrent directory: {current_dir}")
            
            action = inquirer.select(
                message="Select reference file:",
                choices=choices,
                default=None,
                amark="→",
                pointer="❯"
            ).execute()

            if not action:
                return

            action_type, value = action

            if action_type == "up" or action_type == "dir":
                current_dir = value
            elif action_type == "file":
                while True:
                    # Get profile name
                    name = inquirer.text(
                        message="Enter profile name:",
                        validate=lambda x: len(x) > 0
                    ).execute()

                    # Check if profile already exists
                    existing_profiles = self.profiles.list_profiles()
                    profile_exists = False
                    for category in ["video", "audio"]:
                        if category in existing_profiles and name in existing_profiles[category]:
                            profile_exists = True
                            break

                    if profile_exists:
                        # Ask user what to do
                        action = inquirer.select(
                            message=f"Profile '{name}' already exists. What would you like to do?",
                            choices=[
                                Choice(value="overwrite", name="🔄 Overwrite existing profile"),
                                Choice(value="rename", name="✏️  Enter a different name"),
                                Choice(value="cancel", name="❌ Cancel")
                            ]
                        ).execute()

                        if action == "overwrite":
                            break
                        elif action == "rename":
                            continue
                        else:  # cancel
                            return
                    else:
                        break

                # Create profile
                profile = self.converter.create_profile_from_file(value, name)
                if profile:
                    print(f"\nProfile '{name}' created successfully from reference file!")
                else:
                    print("\nFailed to create profile from reference file!")
                return
            elif action_type == "cancel":
                return

    def _add_new_profile(self):
        """Add a new conversion profile."""
        # Get category
        category = inquirer.select(
            message="Select profile category:",
            choices=[
                Choice(value="video", name="🎥 Video"),
                Choice(value="audio", name="🔊 Audio")
            ]
        ).execute()

        # Get profile name
        name = inquirer.text(
            message="Enter profile name:",
            validate=lambda x: len(x) > 0
        ).execute()

        # Get container format
        container = inquirer.select(
            message="Select container format:",
            choices=[Choice(value=c) for c in self.profiles.get_schema()['containers']]
        ).execute()

        # Initialize profile
        profile = {"container": container}
        
        # Get settings based on category
        if category == "video":
            profile["video"] = {}
            profile["audio"] = {}
            
            # Video settings
            print("\nVideo Settings:")
            profile["video"]["codec"] = inquirer.select(
                message="Video codec:",
                choices=[Choice(value=c) for c in self.profiles.get_schema()['video_codecs']]
            ).execute()
            
            profile["video"]["resolution"] = inquirer.select(
                message="Resolution:",
                choices=[Choice(value=r) for r in self.profiles.get_schema()['resolutions']]
            ).execute()
            
            profile["video"]["bitrate"] = inquirer.select(
                message="Video bitrate:",
                choices=[Choice(value=b) for b in self.profiles.get_schema()['video_bitrates']]
            ).execute()

            profile["video"]["fps"] = inquirer.select(
                message="Framerate:",
                choices=[Choice(value=f) for f in self.profiles.get_schema()['framerates']]
            ).execute()

            profile["video"]["pixel_format"] = inquirer.select(
                message="Pixel format:",
                choices=[Choice(value=p) for p in self.profiles.get_schema()['pixel_formats']]
            ).execute()

            profile["video"]["preset"] = inquirer.select(
                message="Encoding preset:",
                choices=[Choice(value=p) for p in self.profiles.get_schema()['presets']]
            ).execute()

            profile["video"]["tune"] = inquirer.select(
                message="Tuning:",
                choices=[Choice(value=t) for t in self.profiles.get_schema()['tune_options']]
            ).execute()

            profile["video"]["speed_control"] = inquirer.select(
                message="Video speed:",
                choices=[Choice(value=s, name=f"{s} ({float(s.replace('x', ''))}x speed)" if s != "copy" else s) 
                        for s in self.profiles.get_schema()['speed_controls']]
            ).execute()
            
            # Audio settings
            print("\nAudio Settings:")
            profile["audio"]["codec"] = inquirer.select(
                message="Audio codec:",
                choices=[Choice(value=c) for c in self.profiles.get_schema()['audio_codecs']]
            ).execute()
            
            profile["audio"]["bitrate"] = inquirer.select(
                message="Audio bitrate:",
                choices=[Choice(value=b) for b in self.profiles.get_schema()['audio_bitrates']]
            ).execute()
            
            profile["audio"]["sample_rate"] = inquirer.select(
                message="Sample rate:",
                choices=[Choice(value=r) for r in self.profiles.get_schema()['sample_rates']]
            ).execute()

            profile["audio"]["channels"] = inquirer.select(
                message="Audio channels:",
                choices=[Choice(value=c) for c in self.profiles.get_schema()['channel_layouts']]
            ).execute()

            profile["audio"]["audio_speed"] = inquirer.select(
                message="Audio speed:",
                choices=[Choice(value=s, name=f"{s} ({float(s.replace('x', ''))}x speed)" if s != "copy" else s) 
                        for s in self.profiles.get_schema()['audio_speeds']]
            ).execute()
            
        else:  # Audio profile
            profile["audio"] = {}
            profile["audio"]["codec"] = inquirer.select(
                message="Audio codec:",
                choices=[Choice(value=c) for c in self.profiles.get_schema()['audio_codecs']]
            ).execute()
            
            profile["audio"]["bitrate"] = inquirer.select(
                message="Audio bitrate:",
                choices=[Choice(value=b) for b in self.profiles.get_schema()['audio_bitrates']]
            ).execute()

            profile["audio"]["sample_rate"] = inquirer.select(
                message="Sample rate:",
                choices=[Choice(value=r) for r in self.profiles.get_schema()['sample_rates']]
            ).execute()

            profile["audio"]["channels"] = inquirer.select(
                message="Audio channels:",
                choices=[Choice(value=c) for c in self.profiles.get_schema()['channel_layouts']]
            ).execute()

            profile["audio"]["audio_speed"] = inquirer.select(
                message="Audio speed:",
                choices=[Choice(value=s, name=f"{s} ({float(s.replace('x', ''))}x speed)" if s != "copy" else s) 
                        for s in self.profiles.get_schema()['audio_speeds']]
            ).execute()

        # Add the profile
        if self.profiles.add_profile(category, name, profile):
            print(f"\nProfile '{name}' created successfully!")
        else:
            print("\nFailed to create profile!")

    def _edit_profile_parameters(self, category: str, name: str, profile: Dict):
        """Edit profile parameters interactively."""
        while True:
            choices = []
            
            # Add video parameters if it's a video profile
            if "video" in profile:
                choices.append(Separator("Video Settings"))
                for param in self.profiles.get_editable_parameters(category)["video"]:
                    current_value = profile["video"].get(param, "N/A")
                    display_value = current_value
                    if param == "speed_control":
                        display_value = f"{current_value} ({float(current_value.replace('x', ''))}x speed)"
                    choices.append(Choice(
                        value=("video", param),
                        name=f"Video {param}: {display_value}"
                    ))

                # Add audio parameters (excluding audio_speed for video profiles)
                choices.append(Separator("Audio Settings"))
                for param in self.profiles.get_editable_parameters(category)["audio"]:
                    if param != "audio_speed":  # Skip audio_speed for video profiles
                        current_value = profile["audio"].get(param, "N/A")
                        choices.append(Choice(
                            value=("audio", param),
                            name=f"Audio {param}: {current_value}"
                        ))
            else:
                # Audio profile parameters
                choices.append(Separator("Audio Settings"))
                for param in self.profiles.get_editable_parameters(category)["audio"]:
                    current_value = profile["audio"].get(param, "N/A")
                    display_value = current_value
                    if param == "audio_speed":
                        display_value = f"{current_value} ({float(current_value.replace('x', ''))}x speed)"
                    choices.append(Choice(
                        value=("audio", param),
                        name=f"Audio {param}: {display_value}"
                    ))

            choices.extend([
                Separator(),
                Choice(value=("done", None), name="✅ Done editing")
            ])

            try:
                section_param = inquirer.select(
                    message="Select parameter to edit:",
                    choices=choices,
                    default=None,
                    amark="→",
                    pointer="❯"
                ).execute()

                if not section_param or section_param[0] == "done":
                    break

                section, param = section_param
                options = self.profiles.get_parameter_options(f"{section}.{param}")
                
                if not options:
                    print(f"No options available for {section} {param}")
                    continue

                # Create choices for parameter values
                param_choices = []
                for option in options:
                    if param in ["speed_control"]:
                        if option == "copy":
                            display_name = option
                        else:
                            speed_value = float(option.replace('x', ''))
                            display_name = f"{option} ({speed_value}x speed)"
                        param_choices.append(Choice(value=option, name=display_name))
                    else:
                        param_choices.append(Choice(value=option))

                new_value = inquirer.select(
                    message=f"Select new value for {section} {param}:",
                    choices=param_choices
                ).execute()

                if not new_value:
                    continue

                # Update the profile
                if self.profiles.edit_profile_parameter(category, name, f"{section}.{param}", new_value):
                    print(f"\nUpdated {section} {param} to: {new_value}")
                    # If this is a video profile and we're updating speed_control, update audio_speed too
                    if category == "video" and param == "speed_control":
                        self.profiles.edit_profile_parameter(category, name, "audio.audio_speed", new_value)
                    # Refresh profile data
                    profile = self.profiles.get_profile(category, name)
                else:
                    print(f"\nFailed to update {section} {param}")

            except KeyboardInterrupt:
                continue

        print("\nProfile updated successfully!")

    def _get_unique_output_path(self, base_path: Path) -> Path:
        """Get a unique output path by adding a number if the file exists."""
        if not base_path.exists():
            return base_path
            
        # If file exists, try adding numbers until we find a unique name
        counter = 1
        while True:
            new_path = base_path.parent / f"{base_path.stem}{counter}{base_path.suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def convert_files(self):
        """Select files and convert them with the selected profile."""
        # First, select files
        if not self._select_files_menu():
            return

        # Then select conversion profile
        profile_info = self._select_profile()
        if not profile_info:
            print("No profile selected!")
            return

        category, profile_name = profile_info
        profile = self.profiles.get_profile(category, profile_name)
        if not profile:
            print("Error: Could not load profile!")
            return
            
        # Create output directory if it doesn't exist
        self.output_directory.mkdir(exist_ok=True)

        # Check for existing files and get user preference
        existing_files = []
        output_paths = {}
        
        for input_file in self.selected_files:
            input_path = Path(input_file)
            output_extension = f".{profile['container']}"
            output_path = self.output_directory / f"{input_path.stem}{output_extension}"
            
            if output_path.exists():
                existing_files.append(input_file)
            output_paths[input_file] = output_path

        if existing_files:
            print("\nSome files already exist in the output directory:")
            for file in existing_files:
                print(f"- {output_paths[file].name}")
            
            action = inquirer.select(
                message="How would you like to handle existing files?",
                choices=[
                    Choice(value="skip", name="⏭️  Skip (don't convert existing files)"),
                    Choice(value="overwrite", name="🔄 Overwrite existing files"),
                    Choice(value="rename", name="📝 Rename (add numbers to filenames)"),
                    Choice(value="cancel", name="❌ Cancel conversion")
                ],
                default=None,
                amark="→",
                pointer="❯"
            ).execute()
            
            if action == "cancel":
                return
            elif action == "skip":
                # Remove existing files from the conversion list
                self.selected_files = [f for f in self.selected_files if f not in existing_files]
                if not self.selected_files:
                    print("No files to convert after skipping existing ones.")
                    return
            elif action == "rename":
                # Update output paths with unique names
                for input_file in existing_files:
                    output_paths[input_file] = self._get_unique_output_path(output_paths[input_file])
            # For overwrite, we'll just continue with the original paths

        # Convert files with interactive progress bar
        with tqdm(total=len(self.selected_files), 
                 desc="Overall Progress", 
                 unit="file",
                 bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                 dynamic_ncols=True,
                 position=0,
                 leave=True) as overall_pbar:
            
            for input_file in self.selected_files:
                try:
                    input_path = Path(input_file)
                    output_path = output_paths[input_file]
                    
                    # If overwriting, ensure the file is deleted first
                    if output_path.exists():
                        output_path.unlink()
                    
                    overall_pbar.set_description(f"Converting {input_path.name}")
                    
                    self.converter.convert_file_with_profile(
                        input_path,
                        output_path,
                        profile,
                        category
                    )
                    overall_pbar.update(1)
                except Exception as e:
                    print(f"\nError converting {input_file}: {str(e)}")
                    continue

        print("\nConversion completed!")
        print(f"Converted files are in: {self.output_directory.absolute()}")
        self._clear_selected_files()

    def main(self):
        """Main CLI interface with interactive menus."""
        try:
            while True:
                action = inquirer.select(
                    message="Leonid's Media Converter",
                    choices=[
                        Choice(value="convert", name="🔄 Convert Files"),
                        Choice(value="settings", name="⚙️  Settings"),
                        Choice(value="exit", name="🚪 Exit")
                    ],
                    default=None,
                    amark="→",
                    pointer="❯"
                ).execute()
                
                if action == "convert":
                    self.convert_files()
                elif action == "settings":
                    self._settings_menu()
                elif action == "exit":
                    self._clear_selected_files()
                    print("Goodbye!")
                    break

        except KeyboardInterrupt:
            print("\nOperation cancelled by user. Cleaning up...")
            self._clear_selected_files()
            sys.exit(0)

if __name__ == "__main__":
    cli = ConverterCLI()
    cli.main() 