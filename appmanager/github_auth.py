import json
import logging
import time
import webbrowser

from appmanager import config, utils


class GitHubAuth:
    """Handles GitHub OAuth authentication."""

    def __init__(self, github_config=None):
        self.github_config = github_config
        self.token_path = config.GITHUB_TOKEN_PATH

    @property
    def client_id(self) -> str:
        """Get current client ID dynamically."""
        if self.github_config:
            return self.github_config.get_client_id()
        return config.GITHUB_CLIENT_ID

    def get_token(self) -> str | None:
        """Gets a GitHub access token, from cache or by performing device login."""
        # Skip token generation for public repos
        if self.client_id == "public_repo":
            return None
            
        token_data = self._load_token()
        if not token_data:
            try:
                token_data = self._perform_device_login()
            except utils.UserCancelledError:
                return None
        return token_data.get("access_token") if token_data else None

    def clear_token(self):
        """Deletes the stored GitHub token file."""
        if self.token_path.exists():
            self.token_path.unlink()
            logging.info("Invalid or old GitHub token has been cleared.")

    def _load_token(self) -> dict | None:
        """Loads the GitHub token data from the JSON file."""
        if self.token_path.exists():
            with open(self.token_path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logging.warning(f"Could not decode token file at {self.token_path}")
                    return None
        return None

    def _save_token(self, token_data: dict):
        """Saves the GitHub token data to a JSON file."""
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f)
        logging.info(f"GitHub token saved to {self.token_path}")

    def _perform_device_login(self) -> dict | None:
        """Handles the OAuth device flow to get a new token from the user."""
        if not self.client_id or self.client_id.startswith("your_"):
            print("\n[SETUP REQUIRED] GitHub OAuth App not configured.")
            print("To use GitHub features, create an OAuth App at:")
            print("https://github.com/settings/applications/new")
            print("Then update GITHUB_CLIENT_ID in appmanager/config.py")
            logging.error("GitHub Client ID is not configured in config.py.")
            return None

        import requests

        try:
            response = requests.post(
                "https://github.com/login/device/code",
                data={"client_id": self.client_id, "scope": "repo"},
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if response.status_code == 422:
                # Invalid client_id
                print(f"\n[ERROR] Invalid GitHub client_id: '{self.client_id}'")
                print("This client_id does not exist or is not configured properly.")
                print("\n💡 To fix this:")
                print("1. Create a new OAuth App at: https://github.com/settings/applications/new")
                print("2. Copy the Client ID from your OAuth App")
                print("3. Update your config using Option 9 in the main menu")
                return None
            response.raise_for_status()
            device_data = response.json()
        except requests.RequestException as e:
            logging.error(f"Failed to initiate device login: {e}")
            return None

        try:
            verification_uri = device_data["verification_uri"]
            user_code = device_data["user_code"]
            print("\n[INFO] GitHub token not found - authentication required")
            print("Config is valid, but you need to authenticate this app with GitHub")
            print("\n--- GitHub Authentication Required ---")
            print(f"1. Your browser will now open to: {verification_uri}")
            print(f"2. Please enter this code there: {user_code}")
            
            try:
                import pyperclip
                pyperclip.copy(user_code)
                print("   (Code has been copied to your clipboard!)")
            except (ImportError, pyperclip.PyperclipException) as e:
                logging.warning(f"Could not copy to clipboard: {e}")
            
            print("\n💡 Need your own OAuth app? Create one at:")
            print("   https://github.com/settings/applications/new")

            input("\nPress Enter to open the browser...")
            webbrowser.open(verification_uri)

            interval = device_data.get("interval", 5)
            device_code = device_data["device_code"]
            while True:
                time.sleep(interval)
                try:
                    token_response = requests.post(
                        "https://github.com/login/oauth/access_token",
                        data={
                            "client_id": self.client_id,
                            "device_code": device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        },
                        headers={"Accept": "application/json"},
                        timeout=10,
                    )
                    token_data = token_response.json()
                    if "error" in token_data:
                        error = token_data["error"]
                        if error == "authorization_pending":
                            continue
                        elif error == "slow_down":
                            interval += 5
                            continue
                        else:
                            logging.error(f"Device login error: {token_data.get('error_description', 'Unknown error')}")
                            return None
                    elif "access_token" in token_data:
                        print("\n[SUCCESS] GitHub authentication successful!")
                        self._save_token(token_data)
                        
                        # Refresh remote version in core if available
                        try:
                            import sys
                            for obj in sys.modules.values():
                                if hasattr(obj, 'refresh_remote_version'):
                                    obj.refresh_remote_version()
                                    break
                        except:
                            pass
                        
                        return token_data
                except requests.RequestException as e:
                    logging.error(f"Error while polling for token: {e}")
                    return None
        except (KeyboardInterrupt, EOFError):
            print("\n\n[INFO] GitHub authentication cancelled by user.")
            raise utils.UserCancelledError()