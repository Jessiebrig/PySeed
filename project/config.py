"""
Configuration settings for the main project.
"""

import os
from pathlib import Path


class Config:
    """Configuration class for project settings."""
    
    # ==========================================================================
    # CORE PATHS & PROJECT INFO
    # ==========================================================================
    
    # Import constants from __main__.py (safe from user modifications)
    try:
        from project.__main__ import PROJECT_ROOT, PROJECT_DIR, PROJECT_NAME, VERSION
    except ImportError:
        # Fallback if __main__.py is not available
        PROJECT_ROOT = Path(__file__).parent.parent.resolve()
        PROJECT_DIR = Path(__file__).parent
        PROJECT_NAME = PROJECT_ROOT.name
        VERSION = "1.0.0"
    
    # ==========================================================================
    # CHROME CONFIGURATION
    # ==========================================================================
    
    DEFAULT_PROFILE_NAME = f"{PROJECT_NAME}_profile"
    
    @classmethod
    def get_chrome_profile_path(cls):
        """Get the Chrome profile path from appmanager config."""
        try:
            import sys
            sys.path.insert(0, str(cls.PROJECT_ROOT))
            from appmanager import config as app_config
            return app_config.APP_DATA_DIR / "ChromeProfiles" / f"{cls.DEFAULT_PROFILE_NAME}"
        except ImportError:
            # Fallback for built executables - use same logic as appmanager
            import os
            import platform
            
            system = platform.system()
            if system == "Windows":
                app_data = os.environ.get("LOCALAPPDATA")
                if not app_data:
                    raise RuntimeError("LOCALAPPDATA environment variable not found.")
                base_path = Path(app_data)
            elif system == "Linux":
                xdg_data_home = os.environ.get("XDG_DATA_HOME")
                base_path = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
            else:
                base_path = Path.home()
                project_name = cls.PROJECT_ROOT.name.lower()
                return base_path / f".{project_name}" / "ChromeProfiles" / f"{cls.DEFAULT_PROFILE_NAME}"
            
            project_name = cls.PROJECT_ROOT.name.lower()
            return base_path / project_name / "ChromeProfiles" / f"{cls.DEFAULT_PROFILE_NAME}"
    
    # ==========================================================================
    # APPLICATION SETTINGS
    # ==========================================================================
    
    # URLs
    YOUTUBE_URL = "https://www.youtube.com"
    
    # Search settings
    DEFAULT_SEARCH_TERM = "What's New"
    
    # Timeouts (in seconds)
    PAGE_LOAD_TIMEOUT = 10
    ELEMENT_WAIT_TIMEOUT = 10