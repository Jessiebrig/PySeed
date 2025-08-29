import itertools
import logging
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from appmanager import config





class BuildEngine:
    """Handles the core build execution and PyInstaller operations."""

    def __init__(self):
        self.platform = config.get_platform()

    def ensure_pyinstaller(self):
        """Checks if PyInstaller is installed and installs it if not."""
        try:
            import PyInstaller
            print("-> PyInstaller is already installed.")
        except ImportError:
            print("-> PyInstaller not found. Installing...")
            try:
                from appmanager import utils
                utils.spin_start("-> Installing PyInstaller")
                subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                             check=True, capture_output=True, text=True)
                utils.spin_stop("-> PyInstaller installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to install PyInstaller: {e}")
                raise

    def ensure_gitignore(self):
        """Ensures .gitignore has build-related entries."""
        gitignore_path = config.PROJECT_ROOT / ".gitignore"
        entries = ["builds/", "__pycache__/", "*.pyc", ".venv/", "venv/"]
        
        if gitignore_path.exists():
            content = gitignore_path.read_text().strip()
            lines = content.split('\n') if content else []
        else:
            lines = []
        
        added = []
        for entry in entries:
            if entry not in lines:
                lines.append(entry)
                added.append(entry)
        
        if added:
            gitignore_path.write_text('\n'.join(lines) + '\n')
            print(f"Added to .gitignore: {', '.join(added)}")

    def clean_previous_builds(self):
        """Removes previous build artifacts to ensure a clean build."""
        self.ensure_gitignore()
        config.BUILDS_ROOT.mkdir(exist_ok=True)
        
        removed_dirs = []
        if config.DIST_DIR.exists():
            shutil.rmtree(config.DIST_DIR)
            removed_dirs.append("dist")
        if config.BUILD_DIR.exists():
            shutil.rmtree(config.BUILD_DIR)
            removed_dirs.append("build")
        if config.SPEC_DIR.exists():
            shutil.rmtree(config.SPEC_DIR)
            removed_dirs.append("specs")
        
        if removed_dirs:
            logging.info(f"Removing build artifacts: {', '.join(removed_dirs)}")
            
        config.DIST_DIR.mkdir(parents=True, exist_ok=True)
        config.BUILD_DIR.mkdir(parents=True, exist_ok=True)
        config.SPEC_DIR.mkdir(parents=True, exist_ok=True)


    


    def run_with_progress(self, command, is_onefile=False):
        """Runs PyInstaller with spinning animation."""
        from appmanager import utils
        
        from appmanager import utils
        utils.hammer_start("🔨 Building")
        try:
            subprocess.run(command, cwd=config.PROJECT_ROOT, check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            utils.hammer_stop("✅ Build completed successfully!")
        except subprocess.CalledProcessError as e:
            utils.hammer_stop("❌ Build failed")
            print(f"\n❌ Build failed (exit code: {e.returncode})")
            logging.error(f"PyInstaller failed: {e}")
            raise

    def move_build_artifacts(self, exe_name, custom_name, build_choice):
        """Moves build artifacts to the project folder."""
        # For directory builds, PyInstaller creates a folder with the app name
        # For single-file builds, it creates just the executable file
        if build_choice == '2':  # Directory build
            exe_path = config.DIST_DIR / custom_name  # This is a directory
        else:  # Single-file build
            exe_path = config.DIST_DIR / exe_name  # This is a file
            
        if not exe_path.exists():
            return None
            
        if exe_path.is_dir():
            # Directory build - move contents to project folder
            print(f"📁 Moving directory build contents to project folder...")
            
            final_exe_path = config.PROJECT_DIR / exe_name
            internal_dir = config.PROJECT_DIR / "_internal"
            
            if final_exe_path.exists():
                if final_exe_path.is_dir():
                    shutil.rmtree(final_exe_path)
                else:
                    final_exe_path.unlink()
            if internal_dir.exists():
                shutil.rmtree(internal_dir)
            
            for item in exe_path.iterdir():
                dest = config.PROJECT_DIR / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            
            exe_path.rmdir()
            final_exe_path = config.PROJECT_DIR / exe_name
        else:
            # Single-file build - move executable to project folder
            final_exe_path = config.PROJECT_DIR / exe_name
            if final_exe_path.exists():
                final_exe_path.unlink()
            shutil.move(str(exe_path), str(final_exe_path))
        
        return final_exe_path