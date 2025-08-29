#!/usr/bin/env python3
# ==============================================================================
# PySeed Manager Entry Point
# ==============================================================================
#
# This script is the main entry point for PySeed Manager. It handles virtual
# environment setup and dependency management automatically.
#
# --- HOW TO RUN PYSEED ---
#
# OPTION 1 - Startup Scripts (RECOMMENDED):
#   • Windows: Double-click 'start.bat' or run from command prompt
#   • Linux: Run './start.sh' from terminal or double-click if executable
#   • Linux Desktop: Double-click 'start.desktop' for GUI launcher
#   → These scripts automatically create venv and install dependencies
#   → Windows version also installs Python if not found
#
# OPTION 2 - Direct Module Execution:
#   • From project root: `python -m appmanager`
#   → This script will create venv automatically if it doesn't exist
#
# OPTION 3 - IDE Development:
#   • Run this file directly in your IDE
#   → Venv will be created automatically on first run
#
# --- IDE DEVELOPMENT SETUP ---
#
# PROBLEM 1: "Venv does not exist" (First-time setup)
# If you see path errors, the venv is being created automatically.
# SOLUTION: Wait for venv creation to complete, or run startup scripts for faster setup
#
# PROBLEM 2: "ImportError" or "No module named 'requests'"
# Your IDE is using system Python instead of the project's venv.
# SOLUTION: Switch your IDE's Python interpreter to the venv:
#   • VS Code: Ctrl+Shift+P → "Python: Select Interpreter" → 
#     Select '~/.local/share/PySeed/venv/bin/python' (Linux)
#     or '%USERPROFILE%\.local\share\PySeed\venv\Scripts\python.exe' (Windows)
#   • PyCharm: File → Settings → Project → Python Interpreter → 
#     Add Interpreter → Existing Environment → Browse to venv path
#
# PROBLEM 3: Cross-platform path issues
# SOLUTION: PySeed automatically detects your platform and adjusts paths.
#
# --- TESTED PLATFORMS ---
# ✅ Windows 10 - Fully supported with automatic Python installation
# ✅ Kubuntu - Fully supported (should work on other Linux distros but not tested)
# 🔄 macOS - Should work but needs community testing
#
# --- PREREQUISITES ---
# • Python 3.8+ - Automatically installed by start.bat on Windows if missing
# • Git - Required for version control features (setup prompted via appmanager)
# • Internet connection - For GitHub integration and dependency downloads
#
# ==============================================================================
import sys
from pathlib import Path

# Add project root to sys.path for module imports
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import core modules
from appmanager import config
from appmanager.environment import VenvManager

def main():
    """Initialize and run the application manager."""
    # Parse command line arguments for Windows terminal choice
    terminal_declined = False
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '--terminal-choice=declined':
                terminal_declined = True
                break
    
    # Ensure virtual environment is active
    venv_manager = VenvManager()
    venv_manager.ensure_active()
    
    # Import and run core manager
    from appmanager.core import AppManagerCore
    manager = AppManagerCore(terminal_declined=terminal_declined)
    manager.run()

if __name__ == "__main__":
    main()

#feature test