import os
import platform
import sys
from pathlib import Path


# =============================================================================
# CORE CONSTANTS & PLATFORM DETECTION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Handle PyInstaller executable case where PROJECT_ROOT.name is a temp folder
if hasattr(sys, 'frozen') and sys.frozen:
    # Running as PyInstaller executable - get project name from executable location
    # The executable is in the project folder, so use its parent directory name
    PROJECT_NAME = Path(sys.executable).parent.parent.name.lower()
else:
    # Running as script - use directory name
    PROJECT_NAME = PROJECT_ROOT.name.lower()

PROJECT_DIR = PROJECT_ROOT / "project"


def get_platform() -> str:
    """Returns the name of the operating system ('Windows', 'Linux', etc.)."""
    return platform.system()


def get_app_data_dir() -> Path:
    """Gets the cross-platform application data directory."""
    system = get_platform()
    if system == "Windows":
        app_data = os.environ.get("LOCALAPPDATA")
        if not app_data:
            raise RuntimeError("LOCALAPPDATA environment variable not found.")
        base_path = Path(app_data)
    elif system == "Linux":
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        base_path = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    else:  # Generic fallback for other Unix-like systems
        base_path = Path.home()
        return base_path / f".{PROJECT_NAME}"
    return base_path / PROJECT_NAME


# =============================================================================
# USER CONFIGURABLE SETTINGS
# =============================================================================

def _get_version_from_file() -> str:
    """Read version from version.txt file using dynamic path detection."""
    try:
        # Use dynamic path detection
        version_file = get_version_file_path()
        if version_file and version_file.exists():
            version = version_file.read_text().strip()
            if version:
                return version
    except:
        # Fallback to default PySeed location to avoid circular imports
        version_file = PROJECT_ROOT / "project" / "requirements" / "version.txt"
        if version_file.exists():
            try:
                version = version_file.read_text().strip()
                if version:
                    return version
            except:
                pass
    
    return "0.0.0"

def get_project_config() -> dict:
    """Load project configuration from app data directory."""
    try:
        import json
        config_path = APP_DATA_DIR / "project_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def get_version_file_path():
    """Get version.txt path from config with fallback."""
    try:
        from appmanager.project_setup import get_project_mode
        project_mode = get_project_mode()
        
        # PYSEED_PROJECT always uses standard structure
        if project_mode == "PYSEED_PROJECT":
            return PROJECT_ROOT / "project" / "requirements" / "version.txt"
        
        # EXTERNAL_REPO uses custom paths if configured
        if project_mode == "EXTERNAL_REPO":
            custom_path = get_custom_path('version_txt')
            if custom_path:
                # Map online repo path to local project folder
                return PROJECT_ROOT / "project" / custom_path
            # Fallback to standard PySeed structure for EXTERNAL_REPO
            return PROJECT_ROOT / "project" / "requirements" / "version.txt"
    except ImportError:
        pass  # Avoid circular import during initialization
    
    # Fallback to default PySeed structure
    return PROJECT_ROOT / "project" / "requirements" / "version.txt"

def get_requirements_file_path():
    """Get requirements.txt path from config with fallback."""
    try:
        from appmanager.project_setup import get_project_mode
        project_mode = get_project_mode()
        
        # PYSEED_PROJECT always uses standard structure
        if project_mode == "PYSEED_PROJECT":
            return PROJECT_ROOT / "project" / "requirements" / "requirements.txt"
        
        # EXTERNAL_REPO uses custom paths if configured, otherwise fallback to standard
        if project_mode == "EXTERNAL_REPO":
            custom_path = get_custom_path('requirements_txt')
            if custom_path:
                return PROJECT_ROOT / custom_path
            # Fallback to standard PySeed structure for EXTERNAL_REPO
            return PROJECT_ROOT / "project" / "requirements" / "requirements.txt"
    except ImportError:
        pass
    
    # Fallback to default PySeed structure
    return PROJECT_ROOT / "project" / "requirements" / "requirements.txt"

def get_requirements_in_file_path():
    """Get requirements.in path from config with fallback."""
    try:
        from appmanager.project_setup import get_project_mode
        project_mode = get_project_mode()
        
        # PYSEED_PROJECT always uses standard structure
        if project_mode == "PYSEED_PROJECT":
            return PROJECT_ROOT / "project" / "requirements" / "requirements.in"
        
        # EXTERNAL_REPO uses custom paths if configured
        if project_mode == "EXTERNAL_REPO":
            custom_path = get_custom_path('requirements_in')
            if custom_path:
                return PROJECT_ROOT / "project" / custom_path
    except ImportError:
        pass
    
    # Fallback to default PySeed structure
    return PROJECT_ROOT / "project" / "requirements" / "requirements.in"

def get_custom_path(path_key: str) -> str:
    """Get custom path from project config. Returns None if not found."""
    config_data = get_project_config()
    return config_data.get('project_paths', {}).get(path_key)

# User Interface Configuration
AUTO_PROCEED = False  # Set to True to skip "Press any key" prompts
AUTO_PROCEED_TIMEOUT = 5  # Seconds to wait before auto-proceeding when AUTO_PROCEED is True

# Chrome for Testing Configuration
# Fallback version used only if latest stable version API fails
CHROME_VERSION = "138.0.7204.168"


# =============================================================================
# INTERNAL PATHS & DIRECTORIES
# =============================================================================

# Application Data Paths (Cross-platform)
APP_DATA_DIR = get_app_data_dir()

# Version Configuration (after APP_DATA_DIR is defined)
# VERSION = _get_version_from_file()  # Project version loaded from file - now use get_version() function
PYSEED_VERSION = "PySeed Manager v1.0.0"  # PySeed framework version display

def get_version() -> str:
    """Get project version - call this instead of using VERSION constant."""
    return _get_version_from_file()
VENV_DIR = APP_DATA_DIR / "venv"
LOGS_DIR = APP_DATA_DIR / "logs"
CHROME_FOR_TESTING_DIR = APP_DATA_DIR / "ChromeForTesting"
CHROME_VERSION_FILE = APP_DATA_DIR / "chrome_for_testing_version.txt"
GITHUB_TOKEN_PATH = APP_DATA_DIR / "github_token.json"
GITHUB_CONFIG_PATH = APP_DATA_DIR / "github_config.json"

# ChromeDriver Path (Platform-specific)
if get_platform() == "Windows":
    CHROMEDRIVER_PATH = CHROME_FOR_TESTING_DIR / "chromedriver-win64" / "chromedriver.exe"
else:
    CHROMEDRIVER_PATH = CHROME_FOR_TESTING_DIR / "chromedriver-linux64" / "chromedriver"

# Project File & Directory Paths
REQUIREMENTS_IN_FILE = PROJECT_ROOT / "appmanager" / "requirements" / "requirements.in"
REQUIREMENTS_FILE = PROJECT_ROOT / "appmanager" / "requirements" / "requirements.txt"
APP_ICON = PROJECT_ROOT / "Icons" / "app_icon.ico"
MAIN_SCRIPT_PATH = PROJECT_DIR / "__main__.py"

# Dynamic project requirements paths (use functions above for project-specific files)

# Build Directories (Platform-specific)
BUILDS_ROOT = PROJECT_ROOT / "builds"
PLATFORM_BUILD_DIR = BUILDS_ROOT / get_platform().lower()
DIST_DIR = PLATFORM_BUILD_DIR / "dist"
BUILD_DIR = PLATFORM_BUILD_DIR / "build"
SPEC_DIR = PLATFORM_BUILD_DIR / "specs"


# =============================================================================
# GITHUB CONFIGURATION HELPERS
# =============================================================================

def get_github_config() -> dict:
    """Load GitHub configuration from github_config.json."""
    try:
        import json
        if GITHUB_CONFIG_PATH.exists():
            with open(GITHUB_CONFIG_PATH, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}


def get_github_repo() -> str:
    """Dynamically get GitHub repo from config or git remote origin."""
    # First try to get from config file
    config_data = get_github_config()
    if 'repo' in config_data:
        return config_data['repo']
    
    # Fallback to git remote origin
    try:
        import subprocess
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=PROJECT_DIR, capture_output=True, text=True, check=True
        )
        origin_url = result.stdout.strip()
        
        # Parse GitHub repo from various URL formats
        if "github.com" in origin_url:
            if origin_url.startswith("https://github.com/"):
                repo = origin_url.replace("https://github.com/", "").replace(".git", "")
            elif origin_url.startswith("git@github.com:"):
                repo = origin_url.replace("git@github.com:", "").replace(".git", "")
            else:
                repo = f"user/{PROJECT_NAME}"  # fallback
            return repo
    except:
        pass
    
    # Fallback to generic format
    return "Jessiebrig/PySeed_Demo_Project"


def get_github_client_id() -> str:
    """Dynamically get GitHub client ID from config."""
    config_data = get_github_config()
    return config_data.get('client_id', 'your_client_id_here')