import importlib.metadata
import itertools
import logging
import os
import subprocess
import sys
import time
import threading

from appmanager import config


_spinner_thread = None
_spinner_stop = False

# ANSI color codes
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Extended colors for rainbow effects
    ORANGE = '\033[38;5;208m'
    PINK = '\033[38;5;198m'
    PURPLE = '\033[38;5;129m'
    TEAL = '\033[38;5;51m'
    LIME = '\033[38;5;154m'
    GOLD = '\033[38;5;220m'

def _detect_terminal_capabilities():
    """Detect terminal capabilities for spinner animation and colors."""
    # Check if we're in a modern terminal
    term = os.environ.get('TERM', '').lower()
    term_program = os.environ.get('TERM_PROGRAM', '').lower()
    
    # Modern terminals that support Unicode and colors
    modern_terms = ['xterm', 'screen', 'tmux', 'alacritty', 'kitty', 'wezterm']
    modern_programs = ['vscode', 'hyper', 'iterm', 'terminal', 'windows terminal']
    
    # Check for Windows Terminal or modern terminal emulators
    if (any(t in term for t in modern_terms) or 
        any(p in term_program for p in modern_programs) or
        os.environ.get('WT_SESSION') or
        os.environ.get('COLORTERM')):
        return 'modern'
    
    # Basic fallback for CMD and older terminals
    return 'basic'

def _supports_color():
    """Check if terminal supports ANSI colors."""
    # More strict color detection
    if os.environ.get('FORCE_COLOR'):
        return True
    
    # Check if we're in a known good terminal
    if _detect_terminal_capabilities() == 'modern':
        return True
        
    # For basic terminals, be more conservative
    # Check if ANSI is explicitly supported
    if os.environ.get('ANSICON') or os.environ.get('ConEmuANSI'):
        return True
        
    return False

def _get_spinner_frames(terminal_type):
    """Get appropriate spinner frames based on terminal capabilities."""
    if terminal_type == 'modern':
        if _supports_color():
            # Rainbow Unicode spinner - each frame gets a different color
            rainbow_colors = [Colors.RED, Colors.ORANGE, Colors.YELLOW, Colors.LIME, 
                            Colors.CYAN, Colors.BLUE, Colors.PURPLE, Colors.MAGENTA, 
                            Colors.PINK, Colors.TEAL]
            frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            return [f'{color}{frame}{Colors.RESET}' for color, frame in zip(rainbow_colors, frames)]
        else:
            # Plain Unicode for modern terminals without color support
            return ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    else:
        # Basic ASCII fallback for old terminals (CMD, etc.)
        return ['|', '/', '-', '\\']

def spin_start(message):
    """Start spinning animation in background thread."""
    global _spinner_thread, _spinner_stop
    
    _spinner_stop = False
    terminal_type = _detect_terminal_capabilities()
    frames = _get_spinner_frames(terminal_type)
    spinner = itertools.cycle(frames)
    start_time = time.time()
    
    def animate():
        while not _spinner_stop:
            elapsed = time.strftime("%M:%S", time.gmtime(time.time() - start_time))
            frame = next(spinner)
            
            # Color the elapsed time only if colors are truly supported
            if _supports_color():
                colored_elapsed = f'{Colors.DIM}{elapsed}{Colors.RESET}'
            else:
                colored_elapsed = elapsed
                
            print(f'\r{message} {frame} {colored_elapsed}', end='', flush=True)
            time.sleep(0.1 if terminal_type == 'modern' else 0.2)
    
    _spinner_thread = threading.Thread(target=animate, daemon=True)
    _spinner_thread.start()

def hammer_start(message):
    """Start hammering animation in background thread."""
    global _spinner_thread, _spinner_stop
    
    _spinner_stop = False
    terminal_type = _detect_terminal_capabilities()
    
    # Get appropriate hammer frames based on terminal capabilities
    if terminal_type == 'modern':
        hammer_frames = ['🔨', '🔧', '⚒️', '🔨', '🔧', '⚒️']
    else:
        # Fallback to basic ASCII animation
        hammer_frames = ['|', '/', '-', '\\']
    
    spinner = itertools.cycle(hammer_frames)
    start_time = time.time()
    
    def animate():
        while not _spinner_stop:
            elapsed = time.strftime("%M:%S", time.gmtime(time.time() - start_time))
            frame = next(spinner)
            
            # Color the elapsed time if supported
            if _supports_color():
                colored_elapsed = f'{Colors.DIM}{elapsed}{Colors.RESET}'
            else:
                colored_elapsed = elapsed
            
            print(f'\r{message} {frame} {colored_elapsed}', end='', flush=True)
            time.sleep(0.3)
    
    _spinner_thread = threading.Thread(target=animate, daemon=True)
    _spinner_thread.start()

def spin_stop(success_message=None):
    """Stop spinning animation and show completion message."""
    global _spinner_thread, _spinner_stop
    
    if _spinner_thread and _spinner_thread.is_alive():
        _spinner_stop = True
        _spinner_thread.join()
        if success_message:
            print(f'\r{success_message}')
        else:
            print()  # Just clear the line

def hammer_stop(success_message=None):
    """Stop hammering animation and show completion message."""
    global _spinner_thread, _spinner_stop
    
    if _spinner_thread and _spinner_thread.is_alive():
        _spinner_stop = True
        _spinner_thread.join()
        if success_message:
            print(f'\r{success_message}')
        else:
            print()  # Just clear the line


class UserCancelledError(Exception):
    """Raised when the user cancels an operation like authentication."""
    pass


def clear_console():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_version() -> str:
    """
    Returns the project version by reading directly from version file.
    This ensures we get the current version even if it was updated after startup.
    """
    version_file = config.get_version_file_path()
    if version_file and version_file.exists():
        try:
            version = version_file.read_text().strip()
            if version:
                return version
        except:
            pass
    return "0.0.0"


def is_package_installed(package_name: str) -> bool:
    """
    Checks if a package is installed using its distribution name.
    This is the most reliable way to check against requirements.txt.
    """
    try:
        importlib.metadata.distribution(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def install_packages(packages: list[str]):
    """Installs a list of packages using pip."""
    if not packages:
        return
    logging.info(f"Installing: {', '.join(packages)}")
    
    if _supports_color():
        spin_start(f"{Colors.BLUE}[INFO]{Colors.RESET} Installing packages")
        success_msg = f"{Colors.GREEN}[INFO]{Colors.RESET} Packages installed successfully"
        error_msg = f"{Colors.RED}[ERROR]{Colors.RESET} Package installation failed"
    else:
        spin_start("[INFO] Installing packages")
        success_msg = "[INFO] Packages installed successfully"
        error_msg = "[ERROR] Package installation failed"
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        spin_stop(success_msg)
    except subprocess.CalledProcessError as e:
        spin_stop(error_msg)
        raise


def uninstall_packages(packages_to_uninstall: list[str], prompt_message: str):
    """
    Uninstalls a list of packages after user confirmation.
    """
    if not packages_to_uninstall:
        print("No packages to uninstall.")
        return

    print(f"\n{prompt_message} ({len(packages_to_uninstall)} packages)")
    # Print in columns for better readability
    for i in range(0, len(packages_to_uninstall), 4):
        print("  " + "  ".join(f"{p:<25}" for p in packages_to_uninstall[i:i+4]))

    confirm = input("Proceed? [y/N]: ").strip().lower()
    if confirm == 'y':
        command = [sys.executable, "-m", "pip", "uninstall", "-y"] + packages_to_uninstall
        try:
            logging.info(f"Uninstalling {len(packages_to_uninstall)} packages...")
            
            # Use enhanced spinning animation for package uninstallation
            terminal_type = _detect_terminal_capabilities()
            supports_color = _supports_color()
            
            if terminal_type == 'modern':
                if supports_color:
                    spinner_frames = [f'{Colors.MAGENTA}⠋{Colors.RESET}', f'{Colors.MAGENTA}⠙{Colors.RESET}', 
                                    f'{Colors.MAGENTA}⠹{Colors.RESET}', f'{Colors.MAGENTA}⠸{Colors.RESET}', 
                                    f'{Colors.MAGENTA}⠼{Colors.RESET}', f'{Colors.MAGENTA}⠴{Colors.RESET}', 
                                    f'{Colors.MAGENTA}⠦{Colors.RESET}', f'{Colors.MAGENTA}⠧{Colors.RESET}', 
                                    f'{Colors.MAGENTA}⠇{Colors.RESET}', f'{Colors.MAGENTA}⠏{Colors.RESET}']
                    success_char = f'{Colors.GREEN}✓{Colors.RESET}'
                    error_char = f'{Colors.RED}✗{Colors.RESET}'
                else:
                    spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                    success_char = '✓'
                    error_char = '✗'
            else:
                if supports_color:
                    spinner_frames = [f'{Colors.MAGENTA}|{Colors.RESET}', f'{Colors.MAGENTA}/{Colors.RESET}', 
                                    f'{Colors.MAGENTA}-{Colors.RESET}', f'{Colors.MAGENTA}\\{Colors.RESET}']
                    success_char = f'{Colors.GREEN}OK{Colors.RESET}'
                    error_char = f'{Colors.RED}ERR{Colors.RESET}'
                else:
                    spinner_frames = ['|', '/', '-', '\\']
                    success_char = 'OK'
                    error_char = 'ERR'
            
            spinner = itertools.cycle(spinner_frames)
            start_time = time.time()
            
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while process.poll() is None:
                elapsed = time.strftime("%M:%S", time.gmtime(time.time() - start_time))
                if supports_color:
                    colored_elapsed = f'{Colors.DIM}{elapsed}{Colors.RESET}'
                    info_label = f'{Colors.BLUE}[INFO]{Colors.RESET}'
                else:
                    colored_elapsed = elapsed
                    info_label = '[INFO]'
                print(f'\r{info_label} Uninstalling {next(spinner)} {colored_elapsed}', end='', flush=True)
                time.sleep(0.1 if terminal_type == 'modern' else 0.3)
            
            stdout, stderr = process.communicate()
            elapsed = time.strftime("%M:%S", time.gmtime(time.time() - start_time))
            
            if process.returncode == 0:
                if supports_color:
                    colored_elapsed = f'{Colors.DIM}{elapsed}{Colors.RESET}'
                    info_label = f'{Colors.BLUE}[INFO]{Colors.RESET}'
                    ok_label = f'{Colors.GREEN}[OK]{Colors.RESET}'
                else:
                    colored_elapsed = elapsed
                    info_label = '[INFO]'
                    ok_label = '[OK]'
                print(f'\r{info_label} Uninstalling {success_char} {colored_elapsed}')
                logging.info(stdout)
                print(f"\n{ok_label} Packages uninstalled successfully.")
            else:
                if supports_color:
                    colored_elapsed = f'{Colors.DIM}{elapsed}{Colors.RESET}'
                    info_label = f'{Colors.BLUE}[INFO]{Colors.RESET}'
                else:
                    colored_elapsed = elapsed
                    info_label = '[INFO]'
                print(f'\r{info_label} Uninstalling {error_char} {colored_elapsed}')
                raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to uninstall packages: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            if _supports_color():
                error_label = f'{Colors.RED}[ERROR]{Colors.RESET}'
            else:
                error_label = '[ERROR]'
            print(f"{error_label} The uninstall command failed.\n{e.stderr if hasattr(e, 'stderr') else str(e)}")


def setup_logging():
    """Configures logging to output to both console and a dated file."""
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = config.LOGS_DIR / f"pyseed_{time.strftime('%Y-%m-%d')}.log"

    # Get the root logger
    root_logger = logging.getLogger()
    # Avoid adding handlers multiple times if this function is called again
    if root_logger.hasHandlers():
        return

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(log_file)

    # Set formatters
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)