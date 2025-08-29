#!/usr/bin/env python3
"""
Project Entry Point

This allows the project package to be run as a module:
python -m project

This script handles virtual environment setup automatically.
"""

import sys
from pathlib import Path

# Fix Windows Unicode encoding issues
if sys.platform == "win32":
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, io.UnsupportedOperation):
        # Fallback for older Python versions or when reconfigure isn't available
        pass

# ==========================================================================
# PROJECT CONSTANTS (Safe from user config.py modifications)
# ==========================================================================

# Core paths
if getattr(sys, 'frozen', False):
    # Running as executable - use executable's directory
    PROJECT_ROOT = Path(sys.executable).parent
    PROJECT_DIR = PROJECT_ROOT
else:
    # Running as script - use normal path resolution
    PROJECT_ROOT = Path(__file__).parent.parent.resolve()
    PROJECT_DIR = Path(__file__).parent

def _get_project_name():
    """Get project name from folder."""
    if getattr(sys, 'frozen', False):
        # Running as executable - use parent directory name (the actual project root)
        return PROJECT_ROOT.parent.name
    else:
        # Running as script - use project root name
        return PROJECT_ROOT.name

def _get_version():
    """Get version from appmanager config with dynamic path support."""
    if getattr(sys, 'frozen', False):
        # Running as executable - check PyInstaller bundle first
        try:
            bundle_dir = Path(sys._MEIPASS)
            possible_bundled_paths = []
            
            # Try to read project config to get dynamic paths
            try:
                import json
                config_file = bundle_dir / "project_config.json"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    project_mode = config_data.get('project_mode', 'PYSEED_PROJECT')
                    
                    if project_mode == "EXTERNAL_REPO":
                        custom_path = config_data.get('project_paths', {}).get('version_txt')
                        if custom_path:
                            possible_bundled_paths.append(bundle_dir / "project" / custom_path)
                    
                    # Always try PYSEED_PROJECT structure as fallback
                    possible_bundled_paths.append(bundle_dir / "project" / "requirements" / "version.txt")
                else:
                    # No config found, assume PYSEED_PROJECT
                    possible_bundled_paths.append(bundle_dir / "project" / "requirements" / "version.txt")
            except:
                # Config reading failed, use default
                possible_bundled_paths.append(bundle_dir / "project" / "requirements" / "version.txt")
            
            for bundled_version in possible_bundled_paths:
                if bundled_version.exists():
                    return bundled_version.read_text().strip()
        except:
            pass
        
        # Fallback to external file locations
        possible_paths = [
            PROJECT_ROOT.parent / "requirements" / "version.txt",  # Standard PySeed
            PROJECT_ROOT.parent / "version.txt",  # Root level
            PROJECT_ROOT / "version.txt"  # Same directory as executable
        ]
        for version_file in possible_paths:
            if version_file.exists():
                try:
                    return version_file.read_text().strip()
                except:
                    continue
        return "1.0.0"  # Fallback
    else:
        # Running as script - use appmanager's dynamic version detection
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from appmanager import utils
            return utils.get_version()
        except ImportError:
            return "1.0.0"  # Fallback

PROJECT_NAME = _get_project_name()
VERSION = _get_version()



# Import environment manager for bootstrap
from appmanager.environment import VenvManager

def main():
    """Main entry point for the application."""
    # Check if running as executable (PyInstaller sets sys.frozen)
    if getattr(sys, 'frozen', False):
        # Running as executable - skip venv setup
        from project.core import MainApplication
        app = MainApplication()
        app.run()
    else:
        # Running as script - ensure virtual environment is active
        venv_manager = VenvManager()
        venv_manager.ensure_active()
        
        # Import and run project after venv is active
        from project.core import MainApplication
        app = MainApplication()
        app.run()


if __name__ == "__main__":
    main()