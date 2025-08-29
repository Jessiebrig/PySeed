import base64
import logging
import sys

from appmanager import config, utils
from appmanager.git_manager import GitManager
from appmanager.github_auth import GitHubAuth
from appmanager.github_config import GitHubConfig


class GitHubManager:
    """Manages GitHub API interactions and update workflows."""

    def __init__(self):
        self.config = GitHubConfig()
        self.auth = GitHubAuth(self.config)
        self.git = GitManager()

    @property
    def repo(self) -> str:
        """Get current GitHub repository."""
        return self.config.get_repo()

    def _check_repo_visibility(self, repo: str) -> bool:
        """Check if a GitHub repository is public. Returns True if public, False otherwise."""
        try:
            import requests
            url = f"https://api.github.com/repos/{repo}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                repo_data = response.json()
                return not repo_data.get("private", True)
            elif response.status_code == 403:
                return True  # Rate limited - assume public
            elif response.status_code == 404:
                return False  # Private or doesn't exist
            return False
        except:
            return True  # Assume public on network errors



    def _is_valid_github_client_id(self, client_id: str) -> bool:
        """Validate GitHub client_id format."""
        if not client_id or len(client_id) != 20:
            return False
        return client_id.startswith("Ov23li") or client_id.startswith("Iv1.")

    def _print_github_features(self):
        """Print GitHub integration features."""
        print("🔗 GitHub integration enables:")
        print("   ✅ Version checking - Compare local vs remote versions")
        print("   🔔 Update notifications - Get notified via appmanager startup")
        print("   🚀 Releases - Create and manage project releases")

    def _try_api_call_with_token(self, token: str, warning_msg: str = None) -> str:
        """Helper method to try API call with a given token."""
        try:
            import requests
            headers = {"Authorization": f"token {token}"}
            branches_to_try = ["main", "master"]
            
            for branch in branches_to_try:
                # Get version file path based on project mode
                try:
                    from appmanager.project_setup import get_project_mode
                    project_mode = get_project_mode()
                    
                    if project_mode == "PYSEED_PROJECT":
                        version_paths = ["project/requirements/version.txt"]
                    elif project_mode == "EXTERNAL_REPO":
                        custom_path = config.get_custom_path('version_txt')
                        version_paths = [custom_path] if custom_path else ["project/requirements/version.txt"]
                    else:
                        version_paths = ["project/requirements/version.txt"]
                except ImportError:
                    version_paths = ["project/requirements/version.txt"]
                
                for version_path in version_paths:
                    api_url = f"https://api.github.com/repos/{self.repo}/contents/{version_path}?ref={branch}"
                    logging.info(f"Attempting to fetch from branch '{branch}' path '{version_path}'...")
                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        content_b64 = response.json()["content"]
                        version = base64.b64decode(content_b64).decode("utf-8").strip()
                        if warning_msg:
                            print(warning_msg)
                        print("[SUCCESS] GitHub API key validated - version fetched successfully")
                        return version
                    elif response.status_code == 401:
                        return None  # Invalid token
        except:
            pass
        return None

    def fetch_remote_version(self) -> str:
        """Fetches the version string from version.txt in the GitHub repo."""
        # Priority 1: Check if config.json exists and try to use it
        if config.GITHUB_CONFIG_PATH.exists() and self.config.is_configured():
            client_id = self.auth.client_id
            
            # Handle public repos - try without authentication first
            if client_id == "public_repo":
                try:
                    import requests
                    branches_to_try = ["main", "master"]
                    
                    for branch in branches_to_try:
                        # Get version file path based on project mode
                        try:
                            from appmanager.project_setup import get_project_mode
                            project_mode = get_project_mode()
                            
                            if project_mode == "PYSEED_PROJECT":
                                version_paths = ["project/requirements/version.txt"]
                            elif project_mode == "EXTERNAL_REPO":
                                custom_path = config.get_custom_path('version_txt')
                                version_paths = [custom_path] if custom_path else ["project/requirements/version.txt"]
                            else:
                                version_paths = ["project/requirements/version.txt"]
                        except ImportError:
                            version_paths = ["project/requirements/version.txt"]
                        
                        for version_path in version_paths:
                            api_url = f"https://api.github.com/repos/{self.repo}/contents/{version_path}?ref={branch}"
                            response = requests.get(api_url, timeout=10)
                            if response.status_code == 200:
                                content_b64 = response.json()["content"]
                                version = base64.b64decode(content_b64).decode("utf-8").strip()
                                return version
                except:
                    pass
            elif client_id and not client_id.startswith("your_") and self._is_valid_github_client_id(client_id):
                # Try to get token using config
                try:
                    access_token = self.auth.get_token()
                    if access_token:
                        result = self._try_api_call_with_token(access_token)
                        if result:
                            return result
                except:
                    pass
        
        # Priority 2: No config.json or config invalid - check for token.json
        if not config.GITHUB_CONFIG_PATH.exists():
            existing_token = self.auth._load_token()
            if existing_token and existing_token.get("access_token"):
                print("[INFO] Found existing GitHub token, attempting to use it...")
                result = self._try_api_call_with_token(
                    existing_token["access_token"],
                    "[WARNING] Using cached token - default config.json created"
                )
                if result:
                    return result
            
            # No working token, prompt for setup
            print("[INFO] GitHub config file not found - creating default config")
            self._print_github_features()
            choice = input("\nWould you like to set up GitHub integration now? [y/N]: ").strip().lower()
            if choice == 'y':
                if self.setup_github_config():
                    print("GitHub setup completed! Please restart to use new configuration.")
                    return "N/A (Setup Completed - Restart Required)"
            return "N/A (Config Not Found)"
        
        # Priority 3: Config exists but not properly configured
        if not self.config.is_configured():
            self._print_github_features()
            choice = input("\nGitHub not configured. Set up now? [y/N]: ").strip().lower()
            if choice == 'y':
                if self.setup_github_config():
                    print("GitHub setup completed! Please restart to use new configuration.")
                    return "N/A (Setup Completed - Restart Required)"
            return "N/A (Not Configured)"
        
        # If we reach here, config exists but has invalid client_id
        client_id = self.auth.client_id
        repo = self.repo
        print(f"[INFO] Config: repo='{repo}', client_id='{client_id}'")
        
        # Special case: repo was public but now private
        if client_id == "public_repo":
            print("[INFO] Repository was previously public but may now be private")
            print("Re-checking repository visibility...")
            if not self._check_repo_visibility(repo):
                print("[INFO] Repository is now private - OAuth Client ID required")
                choice = input("\nSet up OAuth authentication for private repository? [y/N]: ").strip().lower()
                if choice == 'y':
                    if self.setup_github_config():
                        print("GitHub setup completed! Please restart to use new configuration.")
                        return "N/A (Setup Completed - Restart Required)"
                return "N/A (Repository Now Private)"
        
        print("[WARNING] GitHub API key from config.json is invalid")
        
        # Try to use existing token as fallback
        existing_token = self.auth._load_token()
        if existing_token and existing_token.get("access_token"):
            print("[INFO] Found existing GitHub token, attempting to use it...")
            result = self._try_api_call_with_token(existing_token["access_token"])
            if result:
                return result
            print("[WARNING] Cached token also failed - repository does not exist or is not accessible")
        
        # No working fallback, prompt for setup
        self._print_github_features()
        print(f"\n❌ Repository '{repo}' not accessible with client_id '{client_id}'")
        print("This could be due to:")
        print("  • Incorrect repository name or URL")
        print("  • Repository doesn't exist or is private")
        print("  • Client_id doesn't have access to this repository")
        print("  • Project mode was recently switched (old GitHub config uses wrong file paths)")
        
        # Show actual version file path being searched
        custom_path = config.get_custom_path('version_txt')
        if custom_path:
            print(f"  • version file not found at: {repo}/{custom_path}")
        else:
            print("  • version.txt file not found in project/requirements/ folder of the repository")
        print("\n💡 If you recently switched project modes, you should update GitHub config")
        print("   Different modes use different file structures and version file locations")
        choice = input("\nSet up GitHub configuration? [y/N]: ").strip().lower()
        if choice == 'y':
            if self.setup_github_config():
                print("GitHub setup completed! Please restart to use new configuration.")
                return "N/A (Setup Completed - Restart Required)"
        return "N/A (Invalid Client ID)"


    @staticmethod
    def is_update_available(local_v: str, remote_v: str) -> bool:
        """Compares two version strings. Returns True if remote is newer."""
        if "N/A" in remote_v or "(Cached)" in remote_v:
            return False
        try:
            from packaging.version import Version
            # Clean version strings by removing any suffixes
            clean_remote = remote_v.split()[0]  # Remove anything after first space
            clean_local = local_v.split()[0]
            return Version(clean_remote) > Version(clean_local)
        except (ImportError, TypeError):
            logging.warning("'packaging' library not found or versions invalid.")
            return False



    def setup_github_config(self) -> bool:
        """Interactive GitHub configuration setup."""
        return self.config.setup_interactive()
    
    def _show_overwrite_warning(self, context: str) -> bool:
        """Show warning about overwriting local changes and get user confirmation."""
        # Check project mode to show appropriate warning
        try:
            from appmanager.project_setup import get_project_mode
            project_mode = get_project_mode()
            
            if project_mode == "PYSEED_PROJECT":
                print(f"\n⚠️  [WARNING] This will overwrite changes in the PROJECT folder only!")
                print("Any modifications you've made to project/ will be PERMANENTLY LOST.")
                print("\n✅ Your appmanager/ folder will be PRESERVED (not updated).")
                print("⚙️  Technical: Executes 'git checkout origin/main -- project/' (project-only update)")
            else:
                print(f"\n⚠️  [WARNING] This will overwrite ALL local changes!")
                print("Any modifications you've made will be PERMANENTLY LOST.")
                print("\n⚙️  Technical: Executes 'git reset --hard origin/main' (destructive!)")
        except ImportError:
            print(f"\n⚠️  [WARNING] This will overwrite ALL local changes!")
            print("Any modifications you've made will be PERMANENTLY LOST.")
            print("\n⚙️  Technical: Executes 'git reset --hard origin/main' (destructive!)")
        
        print("💾 Automatic backup will be available soon!")
        
        while True:
            choice = input(f"\n-> {context} [y/n]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def _initialize_git_repo(self) -> bool:
        """Initialize Git repository and set up remote for ZIP downloads."""
        import subprocess
        
        try:
            # Check project mode to determine where to initialize git
            try:
                from appmanager.project_setup import get_project_mode
                project_mode = get_project_mode()
                if project_mode == "PYSEED_PROJECT":
                    git_cwd = config.PROJECT_ROOT  # Initialize in root for PySeed projects
                else:
                    git_cwd = config.PROJECT_DIR   # Initialize in project for external repos
            except ImportError:
                git_cwd = config.PROJECT_ROOT
            
            print("\n-> Initializing Git repository...")
            subprocess.run(["git", "init"], check=True, cwd=git_cwd, capture_output=True)
            
            # Handle cross-platform ownership issues immediately after init
            print("-> Configuring Git for cross-platform compatibility...")
            subprocess.run(["git", "config", "--global", "--add", "safe.directory", str(git_cwd)], 
                         check=True, capture_output=True)
            
            # Check if GitHub is already configured
            if self.config.is_configured():
                # Special case: check if repo was public but is now private
                client_id = self.auth.client_id
                if client_id == "public_repo" and not self._check_repo_visibility(self.repo):
                    print(f"\n-> Repository '{self.repo}' is now private - reconfiguration needed")
                    if not self.config.setup_interactive():
                        print("[ERROR] GitHub configuration cancelled.")
                        return False
                else:
                    print(f"\n-> Using existing GitHub configuration: {self.repo}")
            else:
                print("\n=== GitHub Configuration Required ===")
                if not self.config.setup_interactive():
                    print("[ERROR] GitHub configuration cancelled.")
                    return False
            
            # Get repository URL from config (updated if changed)
            repo = self.repo
            if not repo or repo.startswith("your_"):
                print("[ERROR] Repository not configured. Please set up GitHub configuration first.")
                return False
            
            # Try to get GitHub token for authenticated operations
            github_token = self.auth.get_token()
            if github_token:
                # Use authenticated URL
                repo_url = GitManager._build_authenticated_url(github_token, repo)
                print(f"-> Adding authenticated remote origin...")
            else:
                # Fallback to public URL (may fail for private repos)
                repo_url = f"https://github.com/{repo}.git"
                print(f"-> Adding remote origin: {repo_url}")
                
            subprocess.run(["git", "remote", "add", "origin", repo_url], check=True, cwd=git_cwd, capture_output=True)
            
            print("-> Fetching from remote...")
            subprocess.run(["git", "fetch", "origin"], check=True, cwd=git_cwd, capture_output=True)
            
            # Determine default branch using consolidated method
            default_branch = GitManager._detect_default_branch()
                
            print(f"-> Setting up tracking branch: {default_branch}")
            subprocess.run(["git", "checkout", "-b", default_branch], check=True, cwd=git_cwd, capture_output=True)
            print(f"-> ⚠️  Running 'git reset --hard origin/{default_branch}' (overwriting files)...")
            subprocess.run(["git", "reset", "--hard", f"origin/{default_branch}"], check=True, cwd=git_cwd, capture_output=True)
            subprocess.run(["git", "branch", "--set-upstream-to", f"origin/{default_branch}"], check=True, cwd=git_cwd, capture_output=True)
            
            print("[SUCCESS] Git repository initialized and connected to remote.")
            print("You can now use the update functionality.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Failed to initialize Git repository: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"Details: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
            return False

    def check_and_apply_updates(self):
        """Checks for updates and prompts the user to apply them."""
        from appmanager import utils
        utils.clear_console()
        print("=== Option 7: Check for & Apply Updates ===\n")
        
        if not GitManager.setup_if_needed("update functionality"):
            return
            
        # Check for .git folder in the correct location based on project mode
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
            print("To enable updates, we need to initialize Git and connect to the repository.")
            
            if not self._show_overwrite_warning("Do you want to continue and overwrite your project?"):
                print("[INFO] Update cancelled to protect your project files.")
                return
                
            # Clear console before starting Git initialization
            from appmanager import utils
            utils.clear_console()
            print("=== Initializing Git Repository ===\n")
            
            if not self._initialize_git_repo():
                return
            
            # After Git initialization, project is already at latest version
            local_version = utils.get_version()
            print(f"\n[SUCCESS] Project updated to latest version ({local_version}) from {self.repo}")
            print("Your project is now up to date!")
            
            # Update remote version for dashboard display
            self.remote_version = local_version
            return
            
        print("\nChecking for updates from GitHub...")
        
        # Show version file path for External Repo Mode
        from appmanager.project_setup import get_project_mode
        if get_project_mode() == "EXTERNAL_REPO":
            custom_path = config.get_custom_path('version_txt')
            if custom_path:
                print(f"-> Looking for version file: {custom_path}")
        elif get_project_mode() == "PYSEED_PROJECT":
            print("-> Using standard PySeed structure: project/requirements/version.txt")
        
        remote_version = self.fetch_remote_version()
        local_version = utils.get_version()

        print(f"-> Your local version: {local_version}")
        print(f"-> Latest version on GitHub: {remote_version}")

        if "N/A" in remote_version:
            print(f"\nStatus: Could not check for updates ({remote_version}).")
            if "Invalid Token" in remote_version:
                print("Your token was invalid and has been cleared. Please try again.")
            elif "Setup Completed - Restart Required" in remote_version:
                input("\nPress Enter to restart and apply new configuration...")
                sys.exit(0)
            return

        if self.is_update_available(local_version, remote_version):
            print("\nStatus: An update is available!")
            
            # Show what will be updated based on project mode
            try:
                from appmanager.project_setup import get_project_mode
                project_mode = get_project_mode()
                if project_mode == "PYSEED_PROJECT":
                    update_context = "Apply update to project folder only?"
                else:
                    update_context = "Apply update and overwrite local changes?"
            except ImportError:
                update_context = "Apply update and overwrite local changes?"
            
            if self._show_overwrite_warning(update_context):
                github_token = self.auth.get_token()
                if GitManager.pull(github_token):
                    input("\nPress Enter to exit.")
                    sys.exit(0)
            else:
                print("[INFO] Update cancelled by user.")
                input("\nPress Enter to continue...")
                return
        else:
            print(f"\n[UP TO DATE] You are running the latest version ({local_version}) from {self.repo}")