import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from appmanager import config





class VenvManager:
    """Manages the application's virtual environment."""

    def __init__(self):
        self.venv_dir = config.VENV_DIR
        self.platform = config.get_platform()

    def is_active(self) -> bool:
        """
        Checks if the script is running in the application's specific virtual environment.
        """
        # A more robust check than `sys.prefix != sys.base_prefix` is to see
        # if sys.prefix points to our specific venv directory.
        return sys.prefix == str(self.venv_dir)

    def _get_venv_python_path(self) -> Path:
        """Determines the path to the venv's Python executable."""
        if self.platform == "Windows":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    def _check_system_dependencies(self) -> bool:
        """
        Checks for system-level dependencies required to create a venv.
        On Debian/Ubuntu, this is the python3-venv package.
        Returns True if dependencies are met or installed, False otherwise.
        """
        if importlib.util.find_spec("venv") and importlib.util.find_spec("ensurepip"):
            return True

        print("\n[SETUP] Python 'venv' module not found.")
        print("This is required to create isolated environments for the application.")
        if self.platform == "Linux":
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            package_name = f"python{py_version}-venv"
            print(f"\nOn Debian/Ubuntu-based systems, the '{package_name}' package is required.")
            choice = input(f"Would you like to attempt to install it now using 'sudo apt'? [y/N]: ").strip().lower()
            if choice == 'y':
                try:
                    print("\nAttempting to install... You may be prompted for your password.")
                    print("-> Running 'sudo apt update'...")
                    from appmanager import utils
                    utils.spin_start("-> Running 'sudo apt update'...")
                    subprocess.run(["sudo", "apt", "update"], check=True)
                    utils.spin_stop("-> apt update completed")
                    
                    utils.spin_start(f"-> Installing {package_name}...")
                    subprocess.run(["sudo", "apt", "install", "-y", package_name], check=True)
                    utils.spin_stop(f"-> {package_name} installed successfully")
                    print("\n[SUCCESS] Package installed. Relaunching the application...")
                    time.sleep(2)
                    # Relaunch the app manager to restart the whole process cleanly.
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"\n[ERROR] Failed to install the package automatically: {e}")
                    print(f"Please run the following command in your terminal manually:")
                    print(f"    sudo apt update && sudo apt install {package_name}")
                    return False
            else:
                print("Installation skipped. The application cannot continue.")
                return False
        else:
            print("\nPlease ensure your Python installation includes the standard 'venv' module.")
        return False

    def ensure_active(self):
        """
        Ensures the script runs inside the virtual environment.
        If not, it creates one and re-launches the script within it.
        """
        if self.is_active():
            # Check if dependencies are installed
            try:
                import requests
                return  # All good, dependencies are available
            except ImportError:
                # Venv exists but dependencies missing, show info then install them
                # Dependencies missing, install with spinner
                try:
                    from appmanager import utils
                    utils.spin_start("Installing core dependencies...")
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(config.REQUIREMENTS_FILE)], 
                                 check=True, capture_output=True, text=True)
                    utils.spin_stop("Core dependencies installed successfully.")
                    return
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to install dependencies: {e.stderr}")
                    print(f"[ERROR] Failed to install dependencies.\nSee details below:\n{e.stderr.strip()}")
                    input("Press Enter to exit.")
                    sys.exit(1)

        if not self._check_system_dependencies():
            input("\nPress Enter to exit.")
            sys.exit(1)

        print("\n--- Virtual Environment Setup ---")
        print("🌱 PySeed is designed to run in an isolated virtual environment to protect your system.")
        print(f"📍 Virtual environment location: {self.venv_dir}")
        
        if self.venv_dir.is_dir():
            print("✅ Virtual environment already exists")
            # If venv exists, skip to relaunch (dependencies already checked at top)
            venv_python = self._get_venv_python_path()
            if not venv_python.exists():
                logging.error(f"Could not find Python executable in venv at: {venv_python}")
                print(f"[ERROR] Could not find Python executable in venv at: {venv_python}")
                input("Press Enter to exit.")
                sys.exit(1)
            
            print("\n🚀 Launching application...")
            time.sleep(1)
            
            from appmanager import utils
            utils.clear_console()
            
            new_env = os.environ.copy()
            project_root_str = str(config.PROJECT_ROOT)
            current_python_path = new_env.get("PYTHONPATH", "")
            path_list = current_python_path.split(os.pathsep) if current_python_path else []
            if project_root_str not in path_list:
                path_list.insert(0, project_root_str)
            new_env["PYTHONPATH"] = os.pathsep.join(path_list)
            
            subprocess.run([str(venv_python)] + sys.argv, env=new_env)
            sys.exit(0)
        else:
            print("❌ Virtual environment does not exist")
            while True:
                choice = input("\nWould you like to create a virtual environment? [Y/n]: ").strip().lower()
                if choice == "":
                    print("[INFO] Please enter Y or N.")
                    continue
                elif choice == 'y':
                    break
                elif choice == 'n':
                    print("\n[INFO] Virtual environment creation cancelled. Exiting...")
                    input("Press Enter to exit.")
                    sys.exit(0)
                else:
                    print("[INFO] Invalid input. Please enter Y or N.")
            print("🔧 Creating new virtual environment...")

        # Create venv if it doesn't exist
        print("\n[STEP 1/2] Creating virtual environment...")
        try:
            from appmanager import utils
            utils.spin_start("Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], check=True, capture_output=True, text=True)
            utils.spin_stop("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create virtual environment: {e.stderr}")
            print(f"[ERROR] Failed to create virtual environment.\nSee details below:\n{e.stderr.strip()}")
            input("Press Enter to exit.")
            sys.exit(1)

        venv_python = self._get_venv_python_path()
        print("\n[STEP 2/2] Installing required dependencies...")
        try:
            from appmanager import utils
            utils.spin_start("Installing dependencies...")
            subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(config.REQUIREMENTS_FILE)], 
                         check=True, capture_output=True, text=True)
            utils.spin_stop("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install dependencies: {e.stderr}")
            print(f"[ERROR] Failed to install dependencies.\nSee details below:\n{e.stderr.strip()}")
            input("Press Enter to exit.")
            sys.exit(1)

        print("\n[STEP 3/3] Relaunching the application inside the virtual environment...")
        time.sleep(1)
        
        from appmanager import utils
        utils.clear_console()

        new_env = os.environ.copy()
        project_root_str = str(config.PROJECT_ROOT)
        current_python_path = new_env.get("PYTHONPATH", "")
        path_list = current_python_path.split(os.pathsep) if current_python_path else []
        if project_root_str not in path_list:
            path_list.insert(0, project_root_str)
        new_env["PYTHONPATH"] = os.pathsep.join(path_list)

        subprocess.run([str(venv_python)] + sys.argv, env=new_env)
        sys.exit(0)

    def delete(self):
        """Deletes the entire venv folder to force a clean setup on next launch."""
        from appmanager import utils
        utils.clear_console()
        
        if not self.venv_dir.is_dir():
            print("Virtual environment folder not found. Nothing to delete.")
            return

        print("\n=== Option 13: Delete Virtual Environment ===\n")
        print(f"This will completely remove the venv folder: {self.venv_dir}")
        confirm = input("Are you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm == 'y':
            try:
                logging.info(f"Deleting virtual environment at {self.venv_dir}")
                shutil.rmtree(self.venv_dir)
                print("\n[SUCCESS] Virtual environment deleted. Please restart the application.")
                input("Press Enter to exit.")
                sys.exit(0)
            except OSError as e:
                logging.error(f"Failed to delete venv folder: {e}")
                print(f"\n[ERROR] Could not delete the folder. It might be in use. Error: {e}")