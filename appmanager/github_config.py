import json
import logging
from pathlib import Path

from appmanager import config


class GitHubConfig:
    """Manages dynamic GitHub configuration stored safely in user data directory."""

    def __init__(self):
        self.config_path = config.GITHUB_CONFIG_PATH
        self._config = None

    def get_repo(self) -> str:
        """Get GitHub repository (user/repo format)."""
        cfg = self._load_config()
        return cfg.get("repo", config.get_github_repo())

    def get_client_id(self) -> str:
        """Get GitHub OAuth client ID."""
        cfg = self._load_config()
        return cfg.get("client_id", config.get_github_client_id())

    def set_repo(self, repo: str):
        """Set GitHub repository."""
        cfg = self._load_config()
        cfg["repo"] = repo
        self._save_config(cfg)

    def set_client_id(self, client_id: str):
        """Set GitHub OAuth client ID."""
        cfg = self._load_config()
        cfg["client_id"] = client_id
        self._save_config(cfg)

    def is_configured(self) -> bool:
        """Check if GitHub is properly configured."""
        cfg = self._load_config()
        repo = cfg.get("repo", config.get_github_repo())
        client_id = cfg.get("client_id", config.get_github_client_id())
        
        return (
            repo and not repo.startswith("user/") and
            client_id and (client_id == "public_repo" or not client_id.startswith("your_"))
        )

    def _load_config(self) -> dict:
        """Load configuration from file, creating defaults if needed."""
        if self._config is not None:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                    logging.info(f"Loaded GitHub config from {self.config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Failed to load GitHub config: {e}. Using defaults.")
                self._config = self._create_default_config()
        else:
            self._config = self._create_default_config()
            self._save_config(self._config)

        return self._config

    def _create_default_config(self) -> dict:
        """Create default configuration with auto-detected values."""
        return {
            "repo": "Jessiebrig/PySeed_Demo_Project",
            "client_id": config.get_github_client_id(),
            "_comment": "GitHub configuration - Edit repo and client_id as needed"
        }

    def _save_config(self, cfg: dict):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            self._config = cfg
        except IOError as e:
            logging.error(f"Failed to save GitHub config: {e}")

    def setup_interactive(self) -> bool:
        """Interactive setup for GitHub configuration."""
        
        current_repo = self.get_repo()
        current_client_id = self.get_client_id()
        
        # Auto-fill removed - let user enter repository manually
        
        print(f"\nCurrent repository: {current_repo}")
        new_repo = input(f"Enter GitHub repository (user/repo format) [{current_repo}]: ").strip()
        repo_to_check = new_repo if new_repo else current_repo
        
        if new_repo:
            self.set_repo(new_repo)
        
        # Check repo visibility
        print(f"\nChecking repository visibility...")
        from appmanager.github import GitHubManager
        github_manager = GitHubManager()
        is_public = github_manager._check_repo_visibility(repo_to_check)
        
        if is_public:
            print(f"Repository '{repo_to_check}' is: public")
            print(f"✅ OAuth Client ID not required for public repository")
            self.set_client_id("public_repo")
        else:
            print(f"Repository '{repo_to_check}' is: private or not found")
            print(f"\nCurrent OAuth Client ID: {current_client_id}")
            print("💡 Create your OAuth app at: https://github.com/settings/applications/new")
            new_client_id = input(f"Enter OAuth Client ID [{current_client_id}]: ").strip()
            if new_client_id:
                self.set_client_id(new_client_id)
        
        # Auto-relaunch after GitHub setup
        print("GitHub setup completed! Restarting PySeed...")
        
        # Clear console before restarting
        from appmanager import utils
        utils.clear_console()
        
        import sys
        import os
        
        # Restart the application
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
        return True
    
