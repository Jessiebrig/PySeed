import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass

# Cross-platform select import
try:
    import select
except ImportError:
    select = None

from appmanager import config, utils
from appmanager.build import BuildManager
from appmanager.dev_tools import DevToolsManager
from appmanager.chrome_manager import ChromeManager
from appmanager.dependency_manager import DependencyManager
from appmanager.environment import VenvManager
from appmanager.github import GitHubManager


@dataclass
class MenuOption:
    """Represents a single option in the user menu."""
    title: str
    action: callable


class AppManagerCore:
    """The main orchestrator for the application manager."""

    def __init__(self, terminal_declined=False):
        self.terminal_declined = terminal_declined
        self.venv_manager = VenvManager()
        self.github_manager = GitHubManager()
        self.build_manager = BuildManager()
        self.chrome_manager = ChromeManager()
        self.dev_tools_manager = DevToolsManager()
        self.dependency_manager = DependencyManager()
        self.remote_version = "N/A"

        self.menu_structure = {
            "--- Run & Build ---": {
                "1": MenuOption("Run Project Script", self.run_main_py),
                "2": MenuOption("Run Executable", self.run_executable),
                "3": MenuOption("Build Executable", self.build_manager.build_executable),
            },
            "--- Dependency Management ---": {
                "4": MenuOption("Install Stable Dependencies (from requirements.txt)", self.dependency_manager.interactive_check),
                "5": MenuOption("Compile requirements.txt (from .in file)", self.dev_tools_manager.compile_requirements),
                "6": MenuOption("Install Latest Dependencies (from requirements.in)", self.dev_tools_manager.install_dev_dependencies),
            },
            "--- General Management ---": {
                "7": MenuOption("Check for & Apply Updates (from GitHub)", self.check_and_apply_updates_with_refresh),
                "8": MenuOption("Install Chrome for Testing", self.chrome_manager.install),
                "9": MenuOption("Open Logs Folder", self.open_logs_folder),
            },
            "--- Destructive Actions ---": {
                "10": MenuOption("Uninstall Project Dependencies", self.dev_tools_manager.uninstall_project_dependencies),
                "11": MenuOption("Uninstall All Pip Packages (Clean Environment)", self.dev_tools_manager.clean_environment),
                "12": MenuOption("Delete Virtual Environment (Force Full Reset)", self.venv_manager.delete),
            }
        }
        self.actions = self._flatten_menu()
        # Add support option
        self.actions["0"] = self.show_support_page

    def _flatten_menu(self) -> dict:
        """Flattens the menu structure for easy action lookup."""
        flat_menu = {}
        for options in self.menu_structure.values():
            for key, menu_option in options.items():
                flat_menu[key] = menu_option.action
        return flat_menu

    def run_main_py(self):
        """Runs the project module using the venv's Python interpreter with real-time output."""
        utils.clear_console()
        print("=== Option 1: Run Project Script ===\n")
        print(f"🍎 Running your fruit...")
        print(f"Environment: {config.VENV_DIR}")
        print()  # Just a blank line
        
        try:
            # Run with real-time output streaming (unbuffered)
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
            
            process = subprocess.Popen(
                [sys.executable, "-m", "project"],
                cwd=config.PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=0,  # Unbuffered
                universal_newlines=True,
                env=env
            )
            
            # Stream output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip(), flush=True)  # Force flush
            
            # Get the return code
            return_code = process.poll()
            
            print("\n" + "="*50)
            if return_code == 0:
                print("✅ [SUCCESS] Project completed successfully!")
            else:
                print(f"❌ [ERROR] Project exited with code {return_code}")
            print("="*50)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ [INTERRUPTED] Project execution cancelled by user.")
            if 'process' in locals():
                process.terminate()
        except Exception as e:
            print(f"\n❌ [ERROR] Failed to run project: {e}")
            logging.error(f"Failed to run project module: {e}")
        
        input("\nPress Enter to return to main menu...")

    def run_executable(self):
        """Runs the built executable, if it exists."""
        # Look for executables in the project directory (where builds are moved)
        project_dir = config.PROJECT_DIR
        platform = config.get_platform()
        
        # Find executable files in project directory
        executables = []
        if project_dir.exists():
            for file in project_dir.iterdir():
                if file.is_file() and file.stat().st_mode & 0o111:  # Check if executable
                    if platform == "Windows" and file.suffix == ".exe":
                        executables.append(file)
                    elif platform != "Windows" and file.suffix == "":
                        executables.append(file)
        
        if not executables:
            print(f"\n[ERROR] No executable found in {project_dir}.")
            print("Please build the project first using option '3'.")
            logging.error(f"No executable found in {project_dir}. Build is required.")
            return
        
        if len(executables) == 1:
            exe_path = executables[0]
        else:
            # Multiple executables found, let user choose
            print("\nMultiple executables found:")
            for i, exe in enumerate(executables, 1):
                print(f"{i}. {exe.name}")
            choice = input("\nSelect executable to run (1-{}): ".format(len(executables))).strip()
            try:
                exe_path = executables[int(choice) - 1]
            except (ValueError, IndexError):
                print("Invalid choice.")
                return
        
        print(f"\nRunning executable: {exe_path.name}...")
        try:
            subprocess.run([str(exe_path)], cwd=project_dir)
        except Exception as e:
            print(f"[ERROR] Failed to run executable: {e}")
            logging.error(f"Failed to run executable {exe_path}: {e}")

    def refresh_remote_version(self):
        """Refresh the remote version from GitHub."""
        if self.git_available:
            self.remote_version = self.github_manager.fetch_remote_version()
        else:
            self.remote_version = "N/A (Git not configured)"
    
    def check_and_apply_updates_with_refresh(self):
        """Check for updates."""
        self.github_manager.check_and_apply_updates()

    def open_logs_folder(self):
        """Opens the folder where log files are stored."""
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Opening logs folder: {config.LOGS_DIR}")
        try:
            if config.get_platform() == "Windows":
                os.startfile(config.LOGS_DIR)
            else: # Linux and others
                subprocess.run(["xdg-open", str(config.LOGS_DIR)], check=True)
        except Exception as e:
            print(f"[ERROR] Could not open logs folder: {e}")
            logging.error(f"Could not open logs folder: {e}")

    def change_project_mode(self):
        """Hidden command to change project mode"""
        utils.clear_console()
        print("=== Change Project Mode ===\n")
        
        from appmanager.project_setup import get_project_mode, prompt_project_mode, save_project_mode
        current_mode = get_project_mode()
        print(f"Current mode: {current_mode}")
        print()
        
        choice = input("Change project mode? [y/N]: ").strip().lower()
        if choice == 'y':
            new_mode = prompt_project_mode()
            save_project_mode(new_mode)
            print(f"\n✅ Project mode changed to: {new_mode}")
            print("Please restart PySeed for changes to take effect.")
        else:
            print("Mode change cancelled.")
        
        input("\nPress Enter to continue...")

    def show_support_page(self):
        """Display support and about information."""
        import shutil
        utils.clear_console()
        
        # Get terminal width for proper centering
        terminal_width = shutil.get_terminal_size().columns
        separator_width = min(60, terminal_width - 4)
        separator = "=" * separator_width
        
        print(separator.center(terminal_width))
        print("🌱 PySeed - Support & About".center(terminal_width))
        print(separator.center(terminal_width))
        
        print("\n👨‍💻 Created by: Jessie")
        print("🤖 Co-developed with: Amazon Q AI Assistant")
        print("\n📖 About PySeed:")
        print("   The ultimate Python project template for hobby coders.")
        print("   Bridges the gap between beginner tutorials and enterprise tools.")
        print("   Focus on coding, not on tooling and configuration.")
        
        print("\n🔗 Links & Resources:")
        print("   📚 Documentation: https://github.com/Jessiebrig/pyseed")
        print("   🐛 Report Issues: https://github.com/Jessiebrig/pyseed/issues")
        print("   💬 Discussions: https://github.com/Jessiebrig/pyseed/discussions")
        
        print("\n💖 Support PySeed Development:")
        print("   ☕ Buy me a coffee: https://ko-fi.com/jessiebrig")
        print("   💳 PayPal: https://paypal.me/jessiebrig")
        print("   ⭐ Star on GitHub: https://github.com/Jessiebrig/pyseed")
        
        print("\n🙏 Why Support?")
        print("   • Fund new features and improvements")
        print("   • Support hobby coding community")
        print("   • Help maintain cross-platform compatibility")
        
        print("\n🚀 Recent Achievements:")
        print("   ✅ Cross-platform support (Windows/Linux)")
        print("   ✅ Smart Git integration for project management")
        print("   ✅ Automated build system with PyInstaller")
        print("   ✅ GitHub integration for releases")
        print("   ✅ Virtual environment management")
        print("   🔄 Dynamic requirements detection (in progress)")
        print("   🔄 PySeed project detection system (planned)")
        print("   🔄 Enhanced workflow options (roadmap)")
        print("   🔄 Project structure tools (development)")
        
        print("\n" + "=" * 60)
        print("\n🌟 Thank you for using PySeed!")
        print("   Every user makes the hobby coding community stronger.")
        
        choice = input("\n[1] Open GitHub [2] Support Links [3] Back to Menu: ").strip()
        
        if choice == "1":
            self._open_url("https://github.com/Jessiebrig/pyseed")
        elif choice == "2":
            print("\n🔗 Opening support links...")
            self._open_url("https://ko-fi.com/jessiebrig")
        
        input("\nPress Enter to return to main menu...")
    
    def _open_url(self, url):
        """Open URL in default browser."""
        try:
            import webbrowser
            webbrowser.open(url)
            print(f"✅ Opened: {url}")
        except Exception as e:
            print(f"❌ Could not open URL: {e}")
            print(f"Please visit manually: {url}")

    def _wait_for_input_or_timeout(self, prompt, timeout_seconds):
        """Wait for user input or auto-proceed after timeout."""
        if config.AUTO_PROCEED:
            print(f"{prompt} (auto-proceeding in {timeout_seconds}s)")
            
            # Cross-platform timeout input handling
            if select and sys.stdin.isatty() and config.get_platform() != "Windows":
                # Unix-like systems can use select
                ready, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
                if ready:
                    sys.stdin.readline()  # Consume the input
            else:
                # Windows fallback or when select is not available
                time.sleep(timeout_seconds)
        else:
            print(f"[Auto Proceed Disabled] {prompt}")
            input()

    def display_dashboard(self):
        """Displays the main menu dashboard in 2 columns with word wrapping."""
        import shutil
        import textwrap
        
        utils.clear_console()
        
        # Get terminal width for centering
        terminal_width = shutil.get_terminal_size().columns
        framework_header = config.PYSEED_VERSION
        
        # Highlight GitHub version if update available
        local_version = utils.get_version()
        github_part = self.remote_version
        
        # Clean up N/A messages for display
        if "N/A (" in github_part:
            github_part = "N/A"
        elif (self.git_available and "N/A" not in self.remote_version and 
            self.github_manager.is_update_available(local_version, self.remote_version)):
            github_part = f"🔄 {self.remote_version} (UPDATE AVAILABLE)"
        
        project_header = f"{config.PROJECT_ROOT.name} v{local_version} (GitHub: {github_part})"
        separator = "=" * min(len(project_header) + 4, terminal_width)
        
        print(separator.center(terminal_width))
        print(framework_header.center(terminal_width))
        print(project_header.center(terminal_width))
        print(separator.center(terminal_width))
        print(f"Platform: {config.get_platform()}")
        print(f"Environment: {config.VENV_DIR}")
        print()

        # Get terminal width
        terminal_width = shutil.get_terminal_size().columns
        col_width = (terminal_width - 4) // 2  # Leave 4 chars for spacing

        # Collect all menu items
        all_items = []
        for heading, options in self.menu_structure.items():
            all_items.append(("HEADER", heading))
            for key, option in options.items():
                all_items.append(("OPTION", f"{key}. {option.title}"))
        
        # Split into two columns (8 lines each for balanced layout)
        left_col = all_items[:8]
        right_col = all_items[8:]
        
        # Display in columns with word wrapping
        max_rows = max(len(left_col), len(right_col))
        for i in range(max_rows):
            left_item = left_col[i] if i < len(left_col) else ("", "")
            right_item = right_col[i] if i < len(right_col) else ("", "")
            
            left_text = left_item[1] if left_item[0] else ""
            right_text = right_item[1] if right_item[0] else ""
            
            # Wrap text if needed
            left_wrapped = textwrap.fill(left_text, width=col_width) if left_text else ""
            right_wrapped = textwrap.fill(right_text, width=col_width) if right_text else ""
            
            # Split wrapped text into lines
            left_lines = left_wrapped.split('\n') if left_wrapped else [""]
            right_lines = right_wrapped.split('\n') if right_wrapped else [""]
            
            # Print all lines for this row
            max_lines = max(len(left_lines), len(right_lines))
            for j in range(max_lines):
                left_line = left_lines[j] if j < len(left_lines) else ""
                right_line = right_lines[j] if j < len(right_lines) else ""
                print(f"{left_line:<{col_width}}  {right_line}")

        print("\n  0. Support & About")

    def check_git_setup(self):
        """Initial git setup check during startup."""
        # For startup, we don't force git setup - just offer it
        try:
            from appmanager.git_manager import GitManager
            GitManager.setup_if_needed()
        except:
            # If anything goes wrong, just continue - git setup is optional at startup
            pass

    def run(self):
        """The main application loop."""
        self.venv_manager.ensure_active()
        print(f"\n[INFO] 🌱Seed planted at: {config.PROJECT_ROOT}")
        print(f"[INFO] Using virtual environment Python")
        utils.setup_logging()
        
        # Setup project mode (detects project type and prompts if needed)
        try:
            from appmanager.project_setup import setup_project_mode
            project_mode = setup_project_mode(self.terminal_declined)
        except Exception as e:
            print(f"[ERROR] Project setup failed: {e}")
            project_mode = "TEMPLATE_MODE"
        
        self.dependency_manager.startup_check()
        self.check_git_setup()
        
        # Store git availability for menu options
        from appmanager.git_manager import GitManager
        self.git_available = GitManager.is_available()
    
        if self.git_available:
            print("\nChecking for latest version from GitHub...")
            
            # Show version file path for External Repo Mode
            from appmanager.project_setup import get_project_mode
            if get_project_mode() == "EXTERNAL_REPO":
                custom_path = config.get_custom_path('version_txt')
                if custom_path:
                    print(f"-> Looking for version file: {custom_path}")
            
            self.remote_version = self.github_manager.fetch_remote_version()
        else:
            print("\n[INFO] Skipping GitHub version check (Git not available)")
            self.remote_version = "N/A (Git not configured)"
        
        # Check for updates and prompt user (only if git is available)
        if self.git_available:
            local_version = utils.get_version()
            if not "N/A" in self.remote_version and self.github_manager.is_update_available(local_version, self.remote_version):
                print(f"\n[UPDATE AVAILABLE] Local: {local_version} -> Remote: {self.remote_version}")
                choice = input("Would you like to update now? [y/N]: ").strip().lower()
                if choice == 'y':
                    # Check if .git exists before showing overwrite warning
                    # Use dynamic git folder detection based on project mode
                    try:
                        from appmanager.project_setup import get_project_mode
                        project_mode = get_project_mode()
                        if project_mode == "PYSEED_PROJECT":
                            git_dir = config.PROJECT_ROOT / ".git"
                        else:
                            git_dir = config.PROJECT_DIR / ".git"
                    except ImportError:
                        git_dir = config.PROJECT_ROOT / ".git"
                    
                    if not git_dir.is_dir():
                        print("\n[INFO] This appears to be a downloaded ZIP copy (no .git folder found).")
                        print("To enable updates, please use Option 7 from the main menu to set up Git.")
                    else:
                        if self.github_manager._show_overwrite_warning("Continue with update?"):
                            from appmanager.git_manager import GitManager
                            github_token = self.github_manager.auth.get_token()
                            if GitManager.pull(github_token):
                                print(f"\n✅ Updated to v{self.remote_version}! Restarting...")
                                time.sleep(1)  # Brief pause to show message
                                utils.clear_console()
                                subprocess.Popen([sys.executable] + sys.argv)
                                sys.exit(0)
                        else:
                            print("[INFO] Update cancelled by user.")
            elif "N/A" not in self.remote_version:
                print(f"[UP TO DATE] You are running the latest version ({local_version}) from {self.github_manager.repo}")

        try:
            # Always pause before showing the menu. If the script is run in a truly
            # non-interactive way (e.g., piped), this input() will raise an
            # EOFError, which is caught below for a graceful exit.
            self._wait_for_input_or_timeout("Press Enter to proceed to the main dashboard...", config.AUTO_PROCEED_TIMEOUT)

            while True:
                self.display_dashboard()
                choice = input("\nEnter your choice: ").strip()

                if choice == "0":
                    self.show_support_page()
                    continue
                elif choice.lower() == "m":
                    self.change_project_mode()
                    continue

                action = self.actions.get(choice)
                if action:
                    action()
                else:
                    print("\nInvalid choice. Please try again.")

                if sys.stdin.isatty():
                    input("\nPress Enter to continue...")
        except KeyboardInterrupt:
            print("\n\nExiting due to user request (Ctrl+C).")
        except EOFError:
            # This handles cases where the script is run non-interactively.
            # It's a clean way to exit without showing an error.
            print("\n\nDetected non-interactive session or end-of-file. Exiting.")
        except Exception as e:
            logging.critical(f"An unhandled exception occurred: {e}", exc_info=True)
            print(f"\n[CRITICAL ERROR] An unexpected error occurred: {e}")
            print("Please check the log file for more details.")
            if sys.stdin.isatty():
                input("Press Enter to exit.")
            sys.exit(1)