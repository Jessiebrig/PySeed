#!/bin/bash
# ==============================================================================
# This script's only job is to launch the appmanager.py script using the system's
# Python interpreter. The Python script itself will then handle creating and
# managing its own virtual environment.
# ==============================================================================

# Get the directory where the script is located.
# Using 'readlink -f' makes it robust even if called via a symlink.
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"

# Function to install Python on different Linux distributions
install_python() {
    echo "[SETUP] Python 3 is not installed. Attempting automatic installation..."
    
    # Detect the distribution
    if command -v apt &> /dev/null; then
        echo "-> Detected Debian/Ubuntu system. Installing Python 3..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        echo "-> Detected RHEL/CentOS system. Installing Python 3..."
        sudo yum install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        echo "-> Detected Fedora system. Installing Python 3..."
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        echo "-> Detected Arch Linux system. Installing Python 3..."
        sudo pacman -S --noconfirm python python-pip
    elif command -v zypper &> /dev/null; then
        echo "-> Detected openSUSE system. Installing Python 3..."
        sudo zypper install -y python3 python3-pip
    else
        echo "[ERROR] Could not detect your Linux distribution."
        echo "Please install Python 3 manually and run this script again."
        read -p "Press Enter to exit."
        exit 1
    fi
    
    echo "[SUCCESS] Python 3 installation completed!"
}

# Check if Python 3 is installed and in the PATH.
# We'll try 'python3' first, then 'python'.
PYTHON_EXE="python3"
if ! command -v $PYTHON_EXE &> /dev/null; then
    PYTHON_EXE="python"
    if ! command -v $PYTHON_EXE &> /dev/null; then
        echo "[SETUP REQUIRED] Python 3 is not installed on your system."
        echo "PySeed requires Python 3 to run."
        read -p "Would you like to install Python 3 automatically? [Y/n]: " choice
        choice=${choice:-Y}
        if [[ $choice =~ ^[Yy]$ ]]; then
            install_python
            # Re-check for Python after installation
            PYTHON_EXE="python3"
            if ! command -v $PYTHON_EXE &> /dev/null; then
                PYTHON_EXE="python"
                if ! command -v $PYTHON_EXE &> /dev/null; then
                    echo "[ERROR] Python installation failed or Python is still not in PATH."
                    echo "Please restart your terminal and try again, or install Python manually."
                    read -p "Press Enter to exit."
                    exit 1
                fi
            fi
        else
            echo "[INFO] Python installation skipped. Please install Python 3 manually."
            read -p "Press Enter to exit."
            exit 1
        fi
    fi
fi

# Verify Python is working and is Python 3
if ! $PYTHON_EXE --version &> /dev/null; then
    echo "[ERROR] Python is installed but not working properly."
    read -p "Press Enter to exit."
    exit 1
fi

$PYTHON_EXE -c 'import sys; sys.exit(0 if sys.version_info.major == 3 else 1)'
if [ $? -ne 0 ]; then
    echo "[ERROR] Found Python, but it is not Python 3. This project requires Python 3."
    read -p "Press Enter to exit."
    exit 1
fi

# Check if venv exists and use it, otherwise use system Python
# Use the actual project folder name instead of hardcoded 'pyseed'
PROJECT_NAME=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]')
VENV_PYTHON="$HOME/.local/share/$PROJECT_NAME/venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    PYTHON_EXE="$VENV_PYTHON"
fi

# Clear screen and change to the project root
clear
cd "$PROJECT_ROOT"
$PYTHON_EXE -m appmanager
read -p "Press Enter to close this window."
exit 0