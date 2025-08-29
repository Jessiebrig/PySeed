import logging
import re
import subprocess
import sys
from pathlib import Path

from appmanager import config, utils
from appmanager.build_engine import BuildEngine


class BuildManager:
    """Main build manager that orchestrates the build process."""

    def __init__(self):
        self.platform = config.get_platform()
        self.engine = BuildEngine()
    
    def _check_icon_availability(self):
        """Check for available icon files and return status message."""
        icon_formats = ['.ico', '.png', '.svg']
        project_root = config.PROJECT_ROOT
        icons_dir = project_root / "Icons"
        
        # Check in Icons folder first
        if icons_dir.exists():
            for ext in icon_formats:
                icon_path = icons_dir / f"app_icon{ext}"
                if icon_path.exists():
                    return f"Found Icons/app_icon{ext}"
            
            # Check for other common names in Icons folder
            common_names = ['icon', 'logo', 'app']
            for name in common_names:
                for ext in icon_formats:
                    icon_path = icons_dir / f"{name}{ext}"
                    if icon_path.exists():
                        return f"Found Icons/{name}{ext}"
        
        # Fallback: Check in project root
        for ext in icon_formats:
            icon_path = project_root / f"app_icon{ext}"
            if icon_path.exists():
                return f"Found {icon_path.name}"
        
        return "No icon found (will build without icon)"
    
    def _get_suggested_name(self, folder_name):
        """Get a smart suggestion for app name based on folder name."""
        # Convert folder name to proper case
        if folder_name.lower() == folder_name:  # all lowercase
            return folder_name.title()  # Capitalize first letter of each word
        return folder_name  # Keep as-is if already has mixed case
    
    def _sanitize_app_name(self, name):
        """Sanitize app name for filesystem compatibility."""
        # Replace spaces with underscores
        sanitized = name.replace(" ", "_")
        # Remove special characters, keep alphanumeric, underscore, hyphen
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
        return sanitized
    
    def _get_file_size(self, file_path):
        """Get human-readable file size."""
        try:
            if file_path.is_dir():
                # For directory builds, get total size
                total_size = sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
            else:
                total_size = file_path.stat().st_size
            
            # Convert to human readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
        except Exception:
            return "Unknown size"



    def build_executable(self):
        """Guides the user through the build process and runs PyInstaller."""
        utils.clear_console()
        
        if not config.MAIN_SCRIPT_PATH.exists():
            print(f"\n❌ [ERROR] Main script not found at: {config.MAIN_SCRIPT_PATH}")
            print("Please ensure your project module has a __main__.py file.")
            return

        # Header with project info
        print(f"=== Building {config.PROJECT_ROOT.name} Executable ===")
        
        # Check dependencies and setup
        print("\n🔧 Preparing build environment...")
        self.engine.ensure_pyinstaller()
        self.engine.clean_previous_builds()
        
        # Icon detection
        icon_status = self._check_icon_availability()
        print(f"✅ Ready: PyInstaller, clean directories, {icon_status.lower()}")
        
        # Use root folder name as app name (preserve original case)
        app_name = config.PROJECT_ROOT.name

        # Build type selection with smart defaults
        print("\n🏗️  Build configuration:")
        print("[1] Single file (slower, for distribution)")
        print("[2] Directory (faster, for testing) [recommended]")
        build_choice = input("Choice [2]: ").strip() or '2'

        build_flags = []
        if build_choice == '1':
            build_flags.append("--onefile")

        # Add icon if available
        if config.APP_ICON.exists():
            build_flags.append(f"--icon={config.APP_ICON}")
        
        # Add version file and project config as data files for dynamic path support
        version_file = config.get_version_file_path()
        if version_file and version_file.exists():
            # Add version file to bundle so executable can find it
            relative_path = version_file.relative_to(config.PROJECT_ROOT)
            separator = ":" if self.platform != "Windows" else ";"
            build_flags.append(f"--add-data={version_file}{separator}{relative_path.parent}")
        
        # Add project config file so executable can read dynamic paths
        config_file = config.APP_DATA_DIR / "project_config.json"
        if config_file.exists():
            build_flags.append(f"--add-data={config_file}{separator}.")
        
        # Console apps always need console windows - no choice needed

        command = [
            sys.executable, "-m", "PyInstaller",
            f"--name={app_name}",
            f"--distpath={config.DIST_DIR}",
            f"--workpath={config.BUILD_DIR}",
            f"--specpath={config.SPEC_DIR}",
        ] + build_flags + [str(config.MAIN_SCRIPT_PATH)]

        logging.info(f"Running PyInstaller with command: {' '.join(str(c) for c in command)}")

        try:
            print(f"\n🔨 Building {app_name} executable...")
            estimated_time = "2-3 minutes" if build_choice == '1' else "1-2 minutes"
            print(f"⏱️  Estimated time: {estimated_time}\n")
            
            self.engine.run_with_progress(command, build_choice == '1')

            exe_name = f"{app_name}.exe" if self.platform == "Windows" else app_name
            final_exe_path = self.engine.move_build_artifacts(exe_name, app_name, build_choice)
            
            if final_exe_path:
                # Get file size for summary
                file_size = self._get_file_size(final_exe_path)
                
                print(f"\n🎉 Build completed successfully!")
                print(f"📦 Executable: project/{final_exe_path.name}")
                print(f"💾 Size: {file_size}")
                
                if build_choice == '2':
                    print(f"📁 Type: Directory build (includes _internal/ folder)")
                    print(f"📦 To distribute: Share the executable and _internal/ folder")
                else:
                    print(f"📁 Type: Single-file executable")
                    print(f"📦 To distribute: Share the {final_exe_path.name} file (including any required files)")
                
                print(f"🚀 Ready to run: ./{final_exe_path.name} (from project/ directory)")
                logging.info(f"Build successful: {final_exe_path}")
                

            else:
                print("\n❌ [ERROR] Build completed but executable not found.")
                print("Check the logs for details.")
                logging.error("Build command seemed to succeed, but the executable was not found.")
        except subprocess.CalledProcessError as e:
            print("\n❌ [ERROR] Build failed.")
            print("Check the logs for detailed error information.")
            logging.error("Build failed. See details below:")
            if hasattr(e, 'stdout') and e.stdout:
                logging.error(f"PyInstaller stdout:\n{e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                logging.error(f"PyInstaller stderr:\n{e.stderr}")