import logging
import shutil
import subprocess
import sys
from pathlib import Path

from appmanager import config


class GitManager:
    """Handles local Git operations and setup."""

    @staticmethod
    def is_available() -> bool:
        """Quick check if git is available and configured."""
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True, text=True)
            subprocess.run(["git", "config", "--global", "user.name"], check=True, capture_output=True, text=True)
            subprocess.run(["git", "config", "--global", "user.email"], check=True, capture_output=True, text=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def setup_if_needed(context="") -> bool:
        """Checks if git is installed and configured, offers to set it up."""
        # Check if git is installed
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"\n[SETUP OPTIONAL] Git is not installed.")
            if context:
                print(f"Git is required for {context}.")
            else:
                print("Git enables GitHub integration features (automatic updates, version sync, etc.)")
                print("PySeed will work without Git, but some features will be limited.")
            
            while True:
                choice = input("\nWould you like to install Git now? [Y/n]: ").strip().lower()
                if choice == 'n':
                    print("[INFO] Git installation skipped.")
                    return False
                elif choice in ['y', 'yes']:
                    break
                else:
                    print("[INFO] Please enter Y or n.")
                    continue
            
            if not GitManager._install_git():
                return False

        # Check if git is configured
        try:
            result = subprocess.run(["git", "config", "--global", "user.name"], 
                                  capture_output=True, text=True, check=True)
            username = result.stdout.strip()
            
            result = subprocess.run(["git", "config", "--global", "user.email"], 
                                  capture_output=True, text=True, check=True)
            email = result.stdout.strip()
            
            if not username or not email:
                raise subprocess.CalledProcessError(1, "git config")
                
        except subprocess.CalledProcessError:
            return GitManager._configure_git(context)
        
        return True

    @staticmethod
    def _install_git() -> bool:
        """Attempts to install Git based on platform."""
        platform = config.get_platform()
        try:
            if platform == "Linux":
                print("\n[INFO] Installing Git on Linux...")
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "git"], check=True)
            elif platform == "Windows":
                print("\n[INFO] Installing Git on Windows...")
                try:
                    subprocess.run(["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        subprocess.run(["choco", "install", "git", "-y"], check=True)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        print("\n[INFO] Automatic installation failed. Please install Git manually:")
                        print("Option 1: https://git-scm.com/download/windows")
                        print("Option 2: Install chocolatey, then run 'choco install git'")
                        return False
            else:
                print(f"\n[INFO] Please install Git for {platform} and restart PySeed.")
                return False
                
            print("[SUCCESS] Git installed successfully!")
            print("[INFO] You may need to restart your terminal/command prompt.")
            return True
        except subprocess.CalledProcessError:
            print("\n[ERROR] Failed to install Git automatically.")
            print("Please install Git manually and restart PySeed.")
            return False

    @staticmethod
    def _configure_git(context="") -> bool:
        """Configures Git with user credentials."""
        while True:
            print("\n[SETUP OPTIONAL] Git is not configured.")
            if context:
                print(f"Git configuration is required for {context}.")
            else:
                print("Git enables GitHub integration features (automatic updates, version sync, etc.)")
                print("PySeed will work without Git, but some features will be limited.")
            
            while True:
                choice = input("\nWould you like to configure Git now? [Y/n]: ").strip().lower()
                if choice == 'n':
                    print("[INFO] Git setup skipped.")
                    return False
                elif choice in ['y', 'yes']:
                    break
                else:
                    print("[INFO] Please enter Y or n.")
            
            # Only prompt for credentials if user chose Y
            username = input("\nEnter your Git username: ").strip()
            email = input("Enter your Git email: ").strip()
            
            if username and email:
                try:
                    subprocess.run(["git", "config", "--global", "user.name", username], check=True)
                    subprocess.run(["git", "config", "--global", "user.email", email], check=True)
                    print(f"\n[SUCCESS] Git configured with username: {username} and email: {email}")
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"\n[ERROR] Failed to configure Git: {e}")
                    return False
            else:
                print("\n[WARNING] Username and email cannot be empty.")
                # Loop back to ask again

    @staticmethod
    def _build_authenticated_url(token: str, repo: str) -> str:
        """Build authenticated GitHub HTTPS URL."""
        return f"https://token:{token}@github.com/{repo}.git"

    @staticmethod
    def pull(github_token: str = None) -> bool:
        """Performs a git pull using HTTPS with GitHub token if available. Returns True on success."""
        if not shutil.which("git"):
            print("-> Git is not installed. Please install Git and run 'git pull' manually.")
            return False
        if not (config.PROJECT_ROOT / ".git").is_dir():
            print("-> This is not a Git repository. Please update manually.")
            print("-> To set up Git for automatic updates, use Option 7 from the main menu.")
            return False

        # Check project mode to determine update strategy
        try:
            from appmanager.project_setup import get_project_mode
            project_mode = get_project_mode()
            
            if project_mode == "PYSEED_PROJECT":
                print("-> PySeed Project detected - updating project folder only (preserving appmanager)")
                return GitManager._pull_project_only(github_token)
        except ImportError:
            pass

        # For fresh Git repos (ZIP downloads), we need to reset hard to avoid conflicts
        try:
            # Check if we have any commits
            result = subprocess.run(["git", "rev-parse", "HEAD"], 
                                  check=False, cwd=config.PROJECT_ROOT, capture_output=True)
            if result.returncode != 0:
                # No commits yet, this is a fresh repo from ZIP
                return GitManager._pull_fresh_repo()
        except:
            pass

        # Try to use GitHub token for HTTPS authentication
        if github_token:
            return GitManager._pull_with_token(github_token)
        else:
            return GitManager._pull_default()



    @staticmethod
    def _pull_with_token(token: str) -> bool:
        """Pull using HTTPS with GitHub token authentication."""
        # Check project mode first
        try:
            from appmanager.project_setup import get_project_mode
            project_mode = get_project_mode()
            
            if project_mode == "PYSEED_PROJECT":
                return GitManager._pull_project_only(token)
        except ImportError:
            pass
        
        try:
            # Handle cross-platform ownership issues (NTFS/Linux)
            GitManager._handle_safe_directory()
            
            # Check if this is a fresh repo (no commits)
            result = subprocess.run(["git", "rev-parse", "HEAD"], 
                                  check=False, cwd=config.PROJECT_ROOT, capture_output=True)
            is_fresh_repo = result.returncode != 0
            
            # Get repo info from config and build authenticated URL
            repo = config.get_github_repo()
            https_url = GitManager._build_authenticated_url(token, repo)
            
            # Always use reset --hard to ensure updates are applied (overwriting local changes)
            print("-> Running authenticated reset to remote (overwriting local files)...")
            default_branch = GitManager._detect_default_branch()
            
            # First fetch latest changes
            subprocess.run(["git", "fetch", "origin"], 
                         check=True, cwd=config.PROJECT_ROOT, capture_output=True)
            
            # Then reset hard to remote branch
            subprocess.run(["git", "reset", "--hard", f"origin/{default_branch}"], 
                         check=True, cwd=config.PROJECT_ROOT, capture_output=True)
            
            print("\n[SUCCESS] Update complete!")
            print("Please restart the application to apply the changes.")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Authenticated git pull failed. Stderr:\n{e.stderr}")
            print("\n[WARNING] Authenticated pull failed, trying default method...")
            return GitManager._pull_default()

    @staticmethod
    def _detect_default_branch() -> str:
        """Detect the default branch from remote branches."""
        try:
            result = subprocess.run(["git", "branch", "-r"], 
                                  check=True, cwd=config.PROJECT_ROOT, capture_output=True, text=True)
            remote_branches = result.stdout.strip().split('\n')
            for branch in remote_branches:
                branch = branch.strip()
                if "origin/main" in branch:
                    return "main"
                elif "origin/master" in branch:
                    return "master"
            return "main"  # Default fallback
        except subprocess.CalledProcessError:
            logging.warning("Could not detect default branch from remote. Falling back to 'main'.")
            return "main"

    @staticmethod
    def _pull_fresh_repo() -> bool:
        """Handle pull for fresh repository (from ZIP download)."""
        try:
            # Handle cross-platform ownership issues (NTFS/Linux)
            GitManager._handle_safe_directory()
            
            default_branch = GitManager._detect_default_branch()
            print(f"-> Resetting to remote {default_branch} branch (overwriting local files)...")
            subprocess.run(["git", "reset", "--hard", f"origin/{default_branch}"], 
                         check=True, cwd=config.PROJECT_DIR, capture_output=True)
            
            print("\n[SUCCESS] Update complete! All files have been updated to match the remote repository.")
            print("Please restart the application to apply the changes.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Failed to update from remote repository: {e}")
            logging.error(f"Fresh repo pull failed. Stderr:\n{e.stderr}")
            return False
    
    @staticmethod
    def _pull_default() -> bool:
        """Fallback to default git pull."""
        try:
            print("-> Running 'git pull'...")
            # First try regular pull
            result = subprocess.run(["git", "pull"], check=True, cwd=config.PROJECT_DIR, capture_output=True, text=True)
            logging.info(f"git pull successful:\n{result.stdout}")
            
            # If pull says "Already up to date" but we know there's an update, force reset
            if "Already up to date" in result.stdout:
                print("-> Forcing update with reset --hard...")
                subprocess.run(["git", "fetch", "origin"], check=True, cwd=config.PROJECT_DIR, capture_output=True)
                default_branch = GitManager._detect_default_branch()
                subprocess.run(["git", "reset", "--hard", f"origin/{default_branch}"], 
                             check=True, cwd=config.PROJECT_DIR, capture_output=True)
            
            print("\n[SUCCESS] Update complete!")
            print("Please restart the application to apply the changes.")
            return True
        except subprocess.CalledProcessError as e:
            print("\n[ERROR] 'git pull' failed. You may have local changes.")
            print("Please commit or stash your changes, then try again.")
            logging.error(f"git pull failed. Stderr:\n{e.stderr}")
            return False

    @staticmethod
    def _handle_safe_directory():
        """Handle Git safe directory issues for cross-platform development."""
        try:
            # Check if we have a dubious ownership error
            result = subprocess.run(["git", "status"], 
                                  check=False, cwd=config.PROJECT_DIR, capture_output=True, text=True)
            
            if result.returncode != 0 and "dubious ownership" in result.stderr:
                print("-> Fixing cross-platform Git ownership issue...")
                subprocess.run(["git", "config", "--global", "--add", "safe.directory", str(config.PROJECT_DIR)], 
                             check=True, capture_output=True)
                logging.info(f"Added {config.PROJECT_DIR} to Git safe directories")
        except subprocess.CalledProcessError:
            # If we can't fix it, continue anyway - the error will show up later
            pass

    @staticmethod
    def _pull_project_only(github_token: str = None) -> bool:
        """Pull only the project/ folder for PySeed projects to preserve appmanager."""
        try:
            # Handle cross-platform ownership issues
            GitManager._handle_safe_directory()
            
            # Set up authenticated remote if token is available
            if github_token:
                repo = config.get_github_repo()
                https_url = GitManager._build_authenticated_url(github_token, repo)
                subprocess.run(["git", "remote", "set-url", "origin", https_url], 
                             check=True, cwd=config.PROJECT_ROOT, capture_output=True)
            
            # Fetch latest changes
            print("-> Fetching latest changes from remote...")
            subprocess.run(["git", "fetch", "origin"], 
                         check=True, cwd=config.PROJECT_ROOT, capture_output=True)
            
            # Get default branch
            default_branch = GitManager._detect_default_branch()
            
            # Use git checkout to update only project folder
            print("-> Updating project folder only using git checkout...")
            
            # Checkout only the project folder from remote
            subprocess.run([
                "git", "checkout", f"origin/{default_branch}", "--", "project/"
            ], check=True, cwd=config.PROJECT_ROOT, capture_output=True)
            

            
            print("\n[SUCCESS] Project folder updated successfully!")
            print("Your root files (appmanager/, Icons/, etc.) were preserved and not modified.")
            print("Please restart the application to apply the changes.")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Project-only pull failed: {e}")
            print("\n[ERROR] Failed to update project folder.")
            print("Falling back to full repository update...")
            
            # Fallback to full update
            if github_token:
                return GitManager._pull_with_token(github_token)
            else:
                return GitManager._pull_default()

    @staticmethod
    def get_default_branch() -> str:
        """Determines the default branch name from the local git repo."""
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                check=True, cwd=config.PROJECT_DIR, capture_output=True, text=True
            )
            return result.stdout.strip().split('/')[-1]
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            logging.warning("Could not determine default branch from git. Falling back to 'main'.")
            return "main"



# END OF FILE - GitManager class is complete with all methods implemented
# This file contains: is_available, setup_if_needed, pull, _pull_with_token, 
# _pull_fresh_repo, _pull_default, get_default_branch, _detect_default_branch, _build_authenticated_url