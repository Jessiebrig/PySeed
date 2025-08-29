import logging
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from appmanager import config, utils





class ChromeManager:
    """Manages the installation of Chrome for Testing."""

    def __init__(self):
        self.platform = config.get_platform()
        self.extract_dir = config.CHROME_FOR_TESTING_DIR



    def _download_and_extract(self, url: str, zip_path: Path, desc: str = "Downloading"):
        """Downloads a zip file and extracts it to a specified directory."""
        
        print(f"-> Downloading from: {url}")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            with zip_path.open('wb') as f, tqdm(desc=f"✅ {desc}", total=total, unit='B', unit_scale=True, unit_divisor=1024, bar_format="{desc} {bar} {percentage:3.0f}% [{elapsed}<{remaining}]", colour="green") as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bar.update(len(chunk))

        self.extract_dir.mkdir(parents=True, exist_ok=True)

        logging.info(f"Extracting {desc} to {self.extract_dir} ...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.extract_dir)
        zip_path.unlink()

    def _get_latest_stable_version(self) -> str:
        """Fetches the latest stable Chrome version from Google's API."""
        try:
            # Google's Chrome for Testing API endpoint for latest stable
            api_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
            logging.info("Fetching latest stable Chrome version...")
            resp = requests.get(api_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            # Get the stable channel version
            stable_version = data.get("channels", {}).get("Stable", {}).get("version")
            if stable_version:
                logging.info(f"Latest stable Chrome version: {stable_version}")
                return stable_version
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch latest Chrome version: {e}")
        
        # Fallback to hardcoded version if API fails
        logging.info(f"Using fallback Chrome version: {config.CHROME_VERSION}")
        return config.CHROME_VERSION

    def _find_download_urls(self, chrome_version: str, platform_id: str) -> tuple[str | None, str | None, str | None]:
        """Finds download URLs for Chrome and ChromeDriver for a specific version and platform."""
        index_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        logging.info("Fetching Chrome for Testing versions index...")
        try:
            resp = requests.get(index_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for v in data.get("versions", []):
                if v["version"].startswith(chrome_version):
                    chrome_url = chromedriver_url = None
                    for d in v["downloads"]["chrome"]:
                        if d["platform"] == platform_id:
                            chrome_url = d["url"]
                    for d in v["downloads"]["chromedriver"]:
                        if d["platform"] == platform_id:
                            chromedriver_url = d["url"]
                    if chrome_url and chromedriver_url:
                        return chrome_url, chromedriver_url, v["version"]
        except requests.RequestException as e:
            logging.error(f"Failed to fetch Chrome for Testing index: {e}")
        return None, None, None

    def install(self):
        """Main method to orchestrate the installation of Chrome for Testing."""
        from appmanager import utils
        utils.clear_console()
        
        print("=== Install Chrome for Testing ===")
        print(f"[INFO] Fetching latest stable Chrome for Testing version...")
        if self.platform == "Windows":
            platform_id, chrome_rel_path = "win64", Path("chrome-win64/chrome.exe")
        elif self.platform == "Linux":
            platform_id, chrome_rel_path = "linux64", Path("chrome-linux64/chrome")
        else:
            print(f"[ERROR] Unsupported platform for this feature: {self.platform}")
            return

        chrome_version = self._get_latest_stable_version()
        print(f"[INFO] Target version: {chrome_version}")

        chrome_url, chromedriver_url, matched_version = self._find_download_urls(chrome_version, platform_id)
        if not chrome_url or not chromedriver_url or not matched_version:
            print(f"\n[ERROR] No Chrome for Testing build found for version {chrome_version}.")
            return

        chrome_path = self.extract_dir / chrome_rel_path
        if chrome_path.exists() and matched_version == chrome_version:
            print(f"\n[OK] Chrome for Testing v{matched_version} is already installed.")
            input("\nPress Enter to return to main menu...")
            return

        try:
            # Clear and recreate the directory first
            shutil.rmtree(self.extract_dir, ignore_errors=True)
            
            # Download and extract Chrome
            chrome_zip = config.PROJECT_ROOT / f"chrome-for-testing-{platform_id}.zip"
            self._download_and_extract(chrome_url, chrome_zip, "Chrome Browser")
            
            # Download and extract ChromeDriver
            chromedriver_zip = config.PROJECT_ROOT / f"chromedriver-{platform_id}.zip"
            self._download_and_extract(chromedriver_url, chromedriver_zip, "ChromeDriver")

            if self.platform != "Windows":
                # Set execute permissions for all Chrome binaries
                chrome_dir = self.extract_dir / "chrome-linux64"
                if chrome_dir.exists():
                    for file in chrome_dir.iterdir():
                        if file.is_file():
                            file.chmod(0o755)
                if config.CHROMEDRIVER_PATH.exists():
                    config.CHROMEDRIVER_PATH.chmod(0o755)

            print(f"\n[SUCCESS] Chrome for Testing v{matched_version} installed to: {chrome_path}")
            print(f"[SUCCESS] ChromeDriver v{matched_version} installed to: {config.CHROMEDRIVER_PATH}")
        except Exception as e:
            print(f"\n[ERROR] Failed to install Chrome for Testing: {e}")
            logging.error(f"Failed to install Chrome for Testing: {e}", exc_info=True)