import itertools
import logging
import re
import subprocess
import sys
import time

from appmanager import config, utils
from appmanager.pip_manager import PipManager


class DependencyManager:
    """Manages all dependency-related operations including checking, installing, and validation."""

    def __init__(self):
        # Appmanager requirements (fixed path)
        self.appmanager_requirements_txt = config.REQUIREMENTS_FILE
        # Project requirements (dynamic path from config)
        self.project_requirements_txt = config.get_requirements_file_path()

    def startup_check(self):
        """Silent dependency check for startup - no console clearing or menu headers."""
        all_missing = []
        files_to_install = []
        
        # Check appmanager requirements
        if self.appmanager_requirements_txt.exists():
            missing = self._check_single_file(self.appmanager_requirements_txt, "appmanager")
            if missing:
                all_missing.extend(missing)
                files_to_install.append((self.appmanager_requirements_txt, "appmanager"))
        
        # Check project requirements (dynamic detection)
        if self.project_requirements_txt and self.project_requirements_txt.exists():
            missing = self._check_single_file(self.project_requirements_txt, "project")
            if missing:
                all_missing.extend(missing)
                files_to_install.append((self.project_requirements_txt, "project"))
        else:
            print("[INFO] No project requirements.txt found - limited functionality available")
        
        if all_missing:
            print("\n--- Missing Dependencies ---")
            for pkg in all_missing:
                print(f"  - {pkg}")
            print("----------------------------")
            choice = input("\nInstall missing dependencies? [y/N]: ").strip().lower()
            if choice == 'y':
                self._install_multiple_files(files_to_install)
            else:
                print("[WARN] Some dependencies are missing. The application may not function correctly.")
                return
        
        # Only check conflicts if we have dependencies to check
        if files_to_install:
            self._check_conflicts(files_to_install)

    def interactive_check(self):
        """Interactive dependency check for menu Option 4."""
        utils.clear_console()
        print("=== Option 4: Install Stable Dependencies ===\n")
        
        all_missing = []
        files_to_install = []
        
        # Check appmanager requirements
        if self.appmanager_requirements_txt.exists():
            missing = self._check_single_file(self.appmanager_requirements_txt, "appmanager")
            if missing:
                all_missing.extend(missing)
                files_to_install.append((self.appmanager_requirements_txt, "appmanager"))
        else:
            print("[WARN] Appmanager requirements.txt not found.")
        
        # Check project requirements (dynamic detection)
        if self.project_requirements_txt and self.project_requirements_txt.exists():
            missing = self._check_single_file(self.project_requirements_txt, "project")
            if missing:
                all_missing.extend(missing)
                files_to_install.append((self.project_requirements_txt, "project"))
        else:
            print("[INFO] No project requirements.txt found - you can configure paths via project setup")
        
        if all_missing:
            print("\n--- Missing Dependencies ---")
            for pkg in all_missing:
                print(f"  - {pkg}")
            print("----------------------------")
            choice = input("\nInstall all missing dependencies? [y/N]: ").strip().lower()
            if choice == 'y':
                self._install_multiple_files(files_to_install)
            else:
                print("Skipping installation. The application may not function correctly.")
                return
        
        # Check for dependency conflicts
        self._check_conflicts(files_to_install)

    def _check_single_file(self, req_file, context):
        """Check a single requirements file for missing packages."""
        missing_packages = []
        
        # Show path for External Repo Mode
        from appmanager.project_setup import get_project_mode
        if get_project_mode() == "EXTERNAL_REPO" and context == "project":
            # Show relative path instead of full path
            relative_path = str(req_file).replace(str(config.PROJECT_ROOT) + "/", "")
            print(f"-> Checking {context} dependencies ({relative_path})...")
        else:
            print(f"-> Checking {context} dependencies...")
        
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('-e'):
                    continue
                match = re.match(r"([a-zA-Z0-9\-_.]+)", line)
                if match:
                    package_name = match.group(1)
                    if not utils.is_package_installed(package_name):
                        missing_packages.append(f"{context}: {line}")
        
        if missing_packages:
            print(f"   ❌ {len(missing_packages)} missing packages")
        else:
            print(f"   ✅ All packages installed")
        
        return missing_packages

    def _install_multiple_files(self, files_to_install):
        """Install from multiple requirements files."""
        # Auto-update pip using centralized manager
        PipManager.check_and_upgrade_pip(force=True)
        
        for req_file, context in files_to_install:
            print(f"\n-> Installing {context} dependencies...")
            if not self.install_from_file(req_file, context):
                continue
        
        print("\n[SUCCESS] Dependency installation completed.")

    @staticmethod
    def install_from_file(requirements_file, context) -> bool:
        """Install dependencies from a single requirements file with live pip output."""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"   📦 Installing {context} packages...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    # Check if error can be auto-fixed
                    if attempt < max_retries - 1:  # Not the last attempt
                        if PipManager.handle_pip_error(result.stderr, f"{context} installation"):
                            continue  # Retry after fix
                    
                    # Final attempt failed or couldn't auto-fix
                    # Check for permission denied errors in stderr
                    if "Permission denied" in result.stderr or "PermissionError" in result.stderr or "[Errno 13]" in result.stderr:
                        print(f"   ❌ Failed to install {context} dependencies")
                        print("\n" + "="*60)
                        print("   ⚠️  PERMISSION ERROR DETECTED")
                        print("="*60)
                        print("   This error often occurs due to pip cache permissions.")
                        print("\n   💡 Try one of these solutions:")
                        print("   1. Run start.bat as Administrator (Right-click → Run as admin)")
                        print("   2. Clear pip cache: python -m pip cache purge")
                        print("   3. Use no-cache install: python -m pip install --no-cache-dir -r <file>")
                        print("="*60 + "\n")
                    else:
                        print(f"   ❌ Failed to install {context} dependencies")
                        # Show stderr for debugging
                        if result.stderr:
                            print(f"\n   Error details:\n{result.stderr}")
                    return False
                
                # Success - but check if there's a pip upgrade notice
                if result.stderr and "A new release of pip is available" in result.stderr:
                    PipManager.check_and_upgrade_pip(result.stderr)
                
                print(f"   ✅ {context.capitalize()} dependencies installed")
                return True
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Failed to install {context} dependencies: {e}")
                
                # Check if it's a permission error
                if "Permission denied" in error_msg or "PermissionError" in error_msg or "[Errno 13]" in error_msg:
                    print(f"   ❌ Failed to install {context} dependencies")
                    print("\n" + "="*60)
                    print("   ⚠️  PERMISSION ERROR DETECTED")
                    print("="*60)
                    print("   This error often occurs due to pip cache permissions.")
                    print("\n   💡 Try one of these solutions:")
                    print("   1. Run start.bat as Administrator (Right-click → Run as admin)")
                    print("   2. Clear pip cache: python -m pip cache purge")
                    print("   3. Use no-cache install: python -m pip install --no-cache-dir -r <file>")
                    print("="*60 + "\n")
                else:
                    print(f"   ❌ Failed to install {context} dependencies")
                return False
        
        return False

    @staticmethod
    def uninstall_from_file(requirements_file, context) -> bool:
        """Uninstall dependencies from a single requirements file with progress indication."""
        try:
            # Use spinning animation for clean output
            print(f"   🗑️ Uninstalling {context} packages...")
            utils.spin_start("   ✅ Uninstalling")
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "--quiet", "-y", "-r", str(requirements_file)])
            utils.spin_stop("   ✅ Uninstallation completed")
            
            print(f"   ✅ {context.capitalize()} dependencies uninstalled")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to uninstall {context} dependencies: {e}")
            print(f"   ❌ Failed to uninstall {context} dependencies")
            return False

    def _check_conflicts(self, files_to_install):
        """Check for dependency conflicts after installation."""
        try:
            subprocess.run([sys.executable, "-m", "pip", "check"], check=True, capture_output=True, text=True)
            logging.info("All dependencies are satisfied.")
        except subprocess.CalledProcessError as e:
            logging.warning(f"Dependency check failed:\n{e.stderr}")
            print("\n--- Dependency Issues ---")
            print(e.stderr.strip())
            print("-------------------------")
            choice = input("\nAttempt to fix by re-installing requirements? [y/N]: ").strip().lower()
            if choice == 'y':
                self._install_multiple_files(files_to_install)