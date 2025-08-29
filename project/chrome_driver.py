"""
Chrome WebDriver management for the project.
"""

import sys
import time
from contextlib import contextmanager
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService

from .config import Config


class ChromeDriverManager:
    """Manages Chrome WebDriver setup and configuration."""
    
    def __init__(self):
        self.config = Config()
        self.platform = self._get_platform()
        
    def _get_platform(self):
        """Get the current platform."""
        try:
            sys.path.insert(0, str(self.config.PROJECT_ROOT))
            from appmanager import config as app_config
            return app_config.get_platform()
        except ImportError:
            import platform
            return platform.system()
    
    def _get_chrome_paths(self):
        """Get Chrome binary and driver paths."""
        try:
            sys.path.insert(0, str(self.config.PROJECT_ROOT))
            from appmanager import config as app_config
            
            if self.platform == "Windows":
                chrome_binary = app_config.CHROME_FOR_TESTING_DIR / "chrome-win64/chrome.exe"
                driver_path = app_config.CHROMEDRIVER_PATH
            else:
                chrome_binary = app_config.CHROME_FOR_TESTING_DIR / "chrome-linux64/chrome"
                driver_path = app_config.CHROMEDRIVER_PATH
                
            return chrome_binary, driver_path
        except ImportError:
            # Fallback for built executables - use same logic as appmanager
            import os
            
            if self.platform == "Windows":
                app_data = os.environ.get("LOCALAPPDATA")
                if not app_data:
                    raise RuntimeError("LOCALAPPDATA environment variable not found.")
                base_path = Path(app_data)
            elif self.platform == "Linux":
                xdg_data_home = os.environ.get("XDG_DATA_HOME")
                base_path = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
            else:
                base_path = Path.home()
                project_name = self.config.PROJECT_ROOT.name.lower()
                chrome_dir = base_path / f".{project_name}" / "ChromeForTesting"
                if self.platform == "Windows":
                    return chrome_dir / "chrome-win64/chrome.exe", chrome_dir / "chromedriver-win64/chromedriver.exe"
                else:
                    return chrome_dir / "chrome-linux64/chrome", chrome_dir / "chromedriver-linux64/chromedriver"
            
            project_name = self.config.PROJECT_ROOT.name.lower()
            chrome_dir = base_path / project_name / "ChromeForTesting"
            
            if self.platform == "Windows":
                chrome_binary = chrome_dir / "chrome-win64/chrome.exe"
                driver_path = chrome_dir / "chromedriver-win64/chromedriver.exe"
            else:
                chrome_binary = chrome_dir / "chrome-linux64/chrome"
                driver_path = chrome_dir / "chromedriver-linux64/chromedriver"
                
            return chrome_binary, driver_path
    
    def create_driver(self, profile_name=None, detach=False):
        """Create and configure Chrome WebDriver."""
        if profile_name is None:
            profile_name = self.config.DEFAULT_PROFILE_NAME
            
        chrome_binary, driver_path = self._get_chrome_paths()
        
        if not chrome_binary.exists():
            raise FileNotFoundError(f"Chrome binary not found at: {chrome_binary}")
        if not driver_path.exists():
            raise FileNotFoundError(f"ChromeDriver not found at: {driver_path}")
        
        # Create unique profile path
        timestamp = int(time.time())
        profile_path = self.config.get_chrome_profile_path() / f"{profile_name}_{timestamp}"
        
        # Configure Chrome options
        options = Options()
        options.binary_location = str(chrome_binary)
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        
        if detach:
            options.add_experimental_option("detach", True)
        
        if self.platform == "Linux":
            options.add_argument("--no-sandbox")
            
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Create service
        service = ChromeService(executable_path=str(driver_path))
        
        return webdriver.Chrome(service=service, options=options)
    
    @contextmanager
    def managed_driver(self, profile_name=None, keep_open=False):
        """Context manager for Chrome WebDriver."""
        driver = None
        self._keep_open = keep_open
        try:
            print(f"[INFO] Launching Chrome with profile: {profile_name or self.config.DEFAULT_PROFILE_NAME}...")
            driver = self.create_driver(profile_name)
            yield driver
        except FileNotFoundError as e:
            print(f"\n[ERROR] Required file not found: {e}")
            print("[INFO] Please run 'Install Chrome for Testing' in PySeed Manager.")
        except Exception as e:
            print(f"\n[ERROR] Chrome setup failed: {e}")
        finally:
            if driver and not getattr(self, '_keep_open', False):
                driver.quit()
                print("[INFO] Chrome closed.")
            elif driver and getattr(self, '_keep_open', False):
                print("[INFO] Chrome left open for manual inspection.")