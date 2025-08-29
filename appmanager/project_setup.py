"""
Project Setup and Mode Detection for PySeed

Handles the three workflow options:
- Option 1: PySeed Project (original structure, full features)
- Option 2: External Repo Mode (replace with online repo, dynamic requirements)
- Option 3: Template Mode (keep current project/)
"""

import os
import json
from pathlib import Path

PROJECT_MODES = {
    1: "PYSEED_PROJECT",
    2: "EXTERNAL_REPO", 
    3: "TEMPLATE_MODE"
}

def detect_project_type():
    """Auto-detect project type to minimize user prompting"""
    project_path = Path("project")
    
    # 1. Check if project/requirements/version.txt exists (PySeed structure)
    if (project_path / "requirements" / "version.txt").exists():
        return "PYSEED_PROJECT"
    
    # 2. Check if it has requirements folder but version.txt in wrong location (Structure issues)
    if (project_path / "requirements").exists() and (project_path / "version.txt").exists():
        print("[INFO] Not a PySeed structure - requirements files not in original location")
        return "NEEDS_CHOICE"
    
    # 3. Check if project has existing code (External repo candidate)
    if project_path.exists() and not is_empty_template():
        return "EXTERNAL_REPO"
    
    # 4. Check if project folder is essentially empty (Template mode)
    if not project_path.exists() or is_empty_template():
        return "TEMPLATE_MODE"
    
    # Fallback
    return "NEEDS_CHOICE"

def is_empty_template():
    """Check if project folder contains only template files"""
    project_path = Path("project")
    if not project_path.exists():
        return True
    
    files = list(project_path.rglob("*"))
    # Consider empty if only __main__.py or very few template files
    return len(files) <= 2

def prompt_project_mode():
    """Prompt user to choose project mode"""
    print("=" * 54)
    print("           PySeed Setup - Project Type Selection")
    print("=" * 54)
    print()
    print("How would you like to use this project?")
    print()
    print("1. This is a PySeed project (Original Structure)")
    print("   └─ Full PySeed features + auto-checks for updates,")
    print("   └─ uses default project/requirements/ location.")
    print()
    print("2. Replace with online repository (External Repo Mode)")
    print("   └─ All Template features + clone Python project into project/ folder,")
    print("   └─ appmanager handles updates/builds. Requires manual requirements setup.")
    print()
    print("3. Keep current project/ folder (Template Mode)")
    print("   └─ Use project template and implement your own, basic PySeed features (venv, dependencies, build, Chrome driver)")
    print()
    
    while True:
        try:
            choice = int(input("Choice (1-3): ").strip())
            if choice in PROJECT_MODES:
                mode = PROJECT_MODES[choice]
                
                # If External Repo Mode, prompt for file paths
                if mode == "EXTERNAL_REPO":
                    setup_integration_paths()
                
                return mode
            else:
                print("Please enter 1, 2, or 3")
        except ValueError:
            print("Please enter a valid number (1-3)")

def setup_integration_paths():
    """Setup custom file paths for Integration Mode"""
    print("\n=== External Repo Mode - File Path Setup ===")
    print("Please provide paths to your project files (press Enter to skip):")
    print()
    
    paths = {}
    
    # Version file
    print("📄 Version file:")
    print("   This tracks the online repository version for version checking")
    print("   Currently supports .txt files only")
    print("   Enter path from repository root (not including username/repo)")
    version_path = input("   Path (e.g., version.txt or docs/version.txt): ").strip()
    if version_path:
        paths['version_txt'] = version_path
    
    # Requirements.txt
    print("\n📦 Production requirements (requirements.txt):")
    req_path = input("   Path (e.g., project/requirements/requirements.txt): ").strip()
    if req_path:
        paths['requirements_txt'] = req_path
    
    # Requirements.in
    print("\n🔧 Source requirements (requirements.in):")
    req_in_path = input("   Path (e.g., project/requirements/requirements.in): ").strip()
    if req_in_path:
        paths['requirements_in'] = req_in_path
    
    if paths:
        save_project_paths(paths)
        print(f"\n✅ Saved {len(paths)} custom file paths")
        
        # Clear console after saving
        from appmanager import utils
        utils.clear_console()
    else:
        print("\n📁 No custom paths provided - will use auto-detection")

def save_project_paths(paths):
    """Save custom project file paths to config"""
    config = load_config()
    if 'project_paths' not in config:
        config['project_paths'] = {}
    config['project_paths'].update(paths)
    save_config(config)

def get_project_mode():
    """Get current project mode from config"""
    config = load_config()
    return config.get('project_mode', 'TEMPLATE_MODE')

def save_project_mode(mode, terminal_declined=False):
    """Save project mode to config"""
    config = load_config()
    config['project_mode'] = mode
    
    # Set terminal preference based on Windows batch script choice or default
    if 'skip_terminal_install' not in config:
        config['skip_terminal_install'] = terminal_declined  # Use passed choice or False
    
    save_config(config)

def load_config():
    """Load existing config or return empty dict"""
    from appmanager.config import APP_DATA_DIR
    config_path = APP_DATA_DIR / "project_config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}

def save_config(config):
    """Save config to file"""
    from appmanager.config import APP_DATA_DIR
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config_path = APP_DATA_DIR / "project_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def setup_project_mode(terminal_declined=False):
    """Main setup function - detect or prompt for project mode"""
    # Check if mode already configured
    current_mode = get_project_mode()
    if current_mode != 'TEMPLATE_MODE':  # Already configured
        if current_mode == "PYSEED_PROJECT":
            print("[INFO] PySeed structure detected")
        print(f"[INFO] Project mode: {current_mode}")
        print("[INFO] To change mode, delete project_config.json and relaunch or press 'm' in main menu")
        return current_mode
    
    # Auto-detect project type
    detected_type = detect_project_type()
    
    if detected_type == "NEEDS_CHOICE":
        # Prompt user for choice
        chosen_mode = prompt_project_mode()
        save_project_mode(chosen_mode, terminal_declined)
        return chosen_mode
    else:
        # Auto-detected, show what was detected then save
        if detected_type == "PYSEED_PROJECT":
            print("[INFO] PySeed structure detected")
        elif detected_type == "TEMPLATE_MODE":
            print("[INFO] Template structure detected")
        
        save_project_mode(detected_type, terminal_declined)
        print(f"[INFO] Project mode: {detected_type}")
        print("[INFO] To change mode, delete project_config.json and relaunch or press 'm' in main menu")
        return detected_type

def has_full_features():
    """Check if current mode supports full PySeed features"""
    return get_project_mode() == "PYSEED_PROJECT"

def requires_dynamic_requirements():
    """Check if current mode needs dynamic requirements detection"""
    return get_project_mode() == "EXTERNAL_REPO"

def get_project_paths():
    """Get custom project file paths from config"""
    config = load_config()
    return config.get('project_paths', {})