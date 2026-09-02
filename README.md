# 🌱 PySeed - The Ultimate Python Project Template for Hobby Coders

> *"Because setting up a Python project shouldn't be harder than coding it."*

## ⚡ Quick Start

```bash
# Windows
git clone https://github.com/Jessiebrig/pyseed.git MyAwesomeApp
cd MyAwesomeApp
start.bat
```
```bash
# Linux
git clone https://github.com/Jessiebrig/pyseed.git MyAwesomeApp
cd MyAwesomeApp
./start.sh
```
> ⚠️ Rename the folder **before** running the startup script — the folder name becomes your app's identity.

## 📋 Table of Contents

- [⚡ Quick Start](#-quick-start)
- [🎯 The Problem PySeed Solves](#-the-problem-pyseed-solves)
- [🚀 What is PySeed?](#-what-is-pyseed)
- [✨ What Makes PySeed Special?](#-what-makes-pyseed-special)
- [🎯 Your Workflow: From Idea to Distribution](#-your-workflow-from-idea-to-distribution)
- [🏆 The PySeed Advantage](#-the-pyseed-advantage)
- [🚀 Getting Started](#-getting-started)
  - [⚠️ Important: Choose Your Project Name Carefully](#️-important-choose-your-project-name-carefully)
  - [📁 Working with the Project Folder](#-working-with-the-project-folder)
- [🛠️ Advanced Features](#️-advanced-features)
- [🔧 Common Issues & Solutions](#-common-issues--solutions)
- [🔮 Roadmap](#-roadmap)
- [🤝 Contributing](#-contributing)
- [📝 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)
- [☕ Support PySeed](#-support-pyseed)

## 🎯 The Problem PySeed Solves

Hobby coders face a frustrating reality: **Environment setup hell**, **dependency chaos**, **cross-platform pain**, **build confusion**, **version management**, and **distribution headaches**. You spend more time fighting with tooling than coding your awesome idea.

Most Python tools target complete beginners or professional developers, leaving hobby coders stuck between basic tutorials and enterprise complexity. **PySeed bridges this gap** - designed for developers who code for fun, want professional results, but don't want to become DevOps experts.

## 🚀 What is PySeed?

PySeed is your **personal Python project assistant** - a complete, cross-platform development environment that handles all the boring stuff so you can focus on what matters: **your code**.

It's not just a template - it's a **living, breathing project management system** that grows with your project from idea to distribution.

### The Architecture: Seed + Fruit

```
PySeed/
├── appmanager/     ← The "SEED" - Your reusable project infrastructure
│   ├── core.py           (Interactive menu system)
│   ├── build.py          (Cross-platform executable building)
│   ├── github.py         (Version control & GitHub integration)
│   ├── environment.py    (Virtual environment management)
│   ├── dev_tools.py      (Dependency management)
│   └── chrome_manager.py (Testing tools)
└── project/        ← The "FRUIT" - Your actual project code
    └── __main__.py       (Your brilliant idea goes here!)
```

**The genius is in the separation:**
- **Keep the `appmanager/` folder** - it's your universal toolkit that works for ANY project
- **Replace the `project/` folder** - with your actual project code ([see guidelines](#-working-with-the-project-folder))
- **Everything else is handled automatically**

## ✨ What Makes PySeed Special?

### 🎮 Menu-Driven Simplicity
No command-line wizardry required. Everything is accessible through a clean, interactive menu:

```
======================================================
           PySeed Manager v1.1.0
        MyProject v1.0.0 (GitHub: 1.0.0)
======================================================
Platform: Linux
Environment: /home/user/.local/share/MyProject/venv

--- Run & Build ---
  1. Run Project Script
  2. Run Executable
  3. Build Executable

--- Dependency Management ---
  4. Install Stable Dependencies (from requirements.txt)
  5. Compile requirements.txt (from .in file)
  6. Install Latest Dependencies (from requirements.in)

--- General Management ---
  7. Check for & Apply Updates (updates project folder from GitHub)
  8. Install Chrome for Testing
  9. Open Logs Folder

--- Destructive Actions ---
  10. Uninstall Project Dependencies
  11. Uninstall All Pip Packages (Clean Environment)
  12. Delete Virtual Environment (Force Full Reset)
```

### Key Features

**🌍 Cross-Platform:** Windows/Linux startup scripts, platform-native builds, seamless switching between systems, Windows Terminal auto-installation for emoji support.

**🔄 Smart Updates:** Auto-checks on startup, menu-driven updates, project-mode aware updates, automatic restart after updates.

**🏗️ Build System:** PyInstaller integration, platform-native executables (no cross-compilation), intelligent directory handling, version hardcoding during build, desktop shortcuts (Linux opens in terminal for console apps).

**📦 Dependencies:** Dual requirements system (appmanager + project), conflict detection, smart installation.

### Dependency Management Workflow

PySeed uses a dual-file dependency system for maximum flexibility:

**📄 requirements.in** → Loose dependencies (package names only)  
**📄 requirements.txt** → Locked dependencies (exact versions)

**Developer Workflow:**
1. **Option 6**: Install latest versions from `requirements.in`
2. **Test your application** thoroughly
3. **Option 5**: Compile tested versions into `requirements.txt`
4. **Commit** `requirements.txt` to Git

**User Workflow:**
- **Option 4**: Install stable, tested versions from `requirements.txt`

**⚠️ Important**: Always test after Option 6 before running Option 5. Locking untested versions can break your project!

## 🎯 Your Workflow: From Idea to Distribution

### 1. Start a New Project

**Option A: Clone Existing PySeed Projects (Easiest) - PYSEED_PROJECT Mode**
*Clone someone's project that already uses PySeed - get all features including automatic updates (updates only the project folder, preserving your local appmanager)*
```bash
# Clone any project that already uses PySeed
git clone https://github.com/someone/their-pyseed-project.git
cd their-pyseed-project
./start.sh  # or start.bat on Windows
```
```
their-pyseed-project/
├── appmanager/          ← PySeed toolkit (same as yours)
├── project/             ← Their project code
│   ├── requirements/    ← Full PySeed structure
│   │   ├── version.txt
│   │   ├── requirements.txt
│   │   └── requirements.in
│   └── __main__.py
├── start.sh
└── start.bat
```
✅ **Full functionality**: All update/dependency features work automatically since the project follows PySeed structure.

**Option B: Wrap External Projects - EXTERNAL_REPO Mode**
*Clone any online Python project and get easy venv setup, Git auth, building, and Chrome driver*
```bash
# Clone PySeed template first
git clone https://github.com/Jessiebrig/pyseed.git yt-dlp-wrapper
cd yt-dlp-wrapper
./start.sh  # or start.bat on Windows
# Git setup prompts for the external repository you want to wrap (e.g., yt-dlp/yt-dlp)
```
```
yt-dlp-wrapper/
├── appmanager/          ← Keep this (PySeed toolkit)
├── project/             ← Gets replaced with yt-dlp repository
│   ├── yt_dlp/          ← yt-dlp project files
│   ├── __main__.py
│   └── requirements.txt
├── start.sh
└── start.bat
```
⚠️ **Important**: Update/dependency features work best with `version.txt`, `requirements.txt`, and `requirements.in` files. PySeed auto-detects these on boot and can be configured for custom paths.

**Option C: Use PySeed Template (For Solo Developers) - TEMPLATE_MODE**
*Perfect for developers who want easy setup of venv, Git auth, building, and Chrome driver for their own project*
```bash
# Clone the PySeed template
git clone https://github.com/Jessiebrig/pyseed.git my-awesome-project
cd my-awesome-project
./start.sh  # or start.bat on Windows
```
```
my-awesome-project/
├── appmanager/          ← Keep this (your toolkit)
├── project/             ← Replace with your code
│   └── __main__.py
├── start.sh
└── start.bat
```
### 2. Manage Your Project
```bash
python -m appmanager
```
- **Option 1**: Test your code
- **Option 4-6**: Manage dependencies as needed
- **Option 7**: Get project updates from GitHub (for users of your project)
- **Option 3**: Build executable when ready

### 3. Share With the World
Your users don't need Python installed! They can:
- **Windows users**: Download and run your `.exe` or Clone repo → `start.bat` → follow prompts → Option 7 (update) → Option 3 (build .exe)
- **Linux users**: Clone repo → `./start.sh` → follow prompts → Option 7 (update) → Option 3 (build native)

## 🏆 The PySeed Advantage

**For Developers:** Zero setup, menu-driven interface, cross-platform by default, professional results, focus on coding not tooling.

**For Users:** Native performance, no Python installation required, easy updates, simple distribution.

**For Ecosystem:** Lowers barriers to Python project sharing, standardizes workflows, promotes best practices.

## 🚀 Getting Started

### Prerequisites & Setup

**Requirements:** Python 3.8+ (auto-installed on Windows), Git (optional, prompted when needed), internet connection.

**Platforms:** Windows 10 ✅ **(with Windows Terminal auto-install for emoji support)**, **Linux ✅ (Debian fully tested, other distros should work)**

**Windows Administrator Privileges:** On Windows, `start.bat` automatically requests administrator privileges via UAC prompt. This ensures dependency installation has proper permissions and prevents common pip cache errors. Simply click "Yes" when Windows asks for permission.

**Smart Bootstrap:** PySeed has a unique self-bootstrapping system:
1. **First Run**: Runs with your system Python
2. **Auto-Detection**: Detects it's not in a virtual environment yet  
3. **Venv Creation**: Automatically creates virtual environment and installs dependencies
4. **Self-Relaunch**: Relaunches itself inside the new virtual environment
5. **Ready to Go**: All subsequent runs use the isolated virtual environment

**This means:** No manual venv setup, system Python protection, one-command setup.

### IDE Development Considerations

**Important for VS Code/PyCharm users:**

If you try to run `appmanager/__main__.py` directly in your IDE **before** the virtual environment exists, you'll get import errors because:
- The venv doesn't exist yet
- Your IDE can't find the Python interpreter path
- Dependencies aren't installed

**Recommended workflow:**
1. **First**: Run `./start.sh` (Linux) or `start.bat` (Windows) to create the venv
2. **Then**: Configure your IDE to use the venv Python interpreter
3. **Finally**: Run/debug directly from your IDE

**Alternative**: You can also run `python -m appmanager` from terminal first, then set up your IDE.

### ⚠️ Important: Choose Your Project Name Carefully

**Before running the startup scripts for the first time**, decide on your final project name and rename the root folder accordingly. The folder name becomes your project's identity and determines:

- **Application data location**: 
  - Linux: `~/.local/share/your-project-name/`
  - Windows: `%LOCALAPPDATA%\your-project-name\`
- **Virtual environment path**: Where Python packages are installed
- **Chrome for Testing location**: Where browser binaries are stored
- **Executable name**: What your built application will be called

**Example:**
```bash
# ✅ Good - Choose your name first
git clone https://github.com/Jessiebrig/pyseed.git MyAwesomeApp
cd MyAwesomeApp
./start.sh  # Creates ~/.local/share/myawesomeapp/

# ❌ Avoid - Changing name later causes issues
git clone https://github.com/Jessiebrig/pyseed.git pyseed
cd pyseed
./start.sh  # Creates ~/.local/share/pyseed/
# Later renaming to MyAwesomeApp creates inconsistencies
```

**Why this matters:**
- Renaming after initialization creates multiple app data directories
- Chrome for Testing and other tools may be installed in the wrong location
- Virtual environments become scattered across different paths
- Built executables may look for resources in the wrong places

## 📁 Working with the Project Folder

**The `project/` folder is where your actual application code lives.** Here's what you need to know:

### ✅ Safe Replacement Guidelines

1. **Keep the folder name as `project/`** - Renaming is not currently supported
2. **Maintain the entry point** - Your code should be runnable via `python -m project`
3. **Handle dependencies** - If you use external packages, add them to `requirements/requirements.in`

### ⚠️ Important Considerations

**If you completely replace the project folder:**
- ✅ **Executables will work** - Built apps don't depend on appmanager
- ⚠️ **Development mode may break** - `python -m project` might fail if your code doesn't handle virtual environments
- ℹ️ **Use appmanager menu** - Run via "Option 1: Run Project Script" for guaranteed compatibility


## 🛠️ Advanced Features

### Dual-Mode Architecture
PySeed's `project/__main__.py` intelligently handles both development and distribution modes:

```python
# PyInstaller executable detection
if getattr(sys, 'frozen', False):
    # Running as executable - skip venv setup
    from project.core import MainApplication
    app = MainApplication()
    app.run()
else:
    # Running as script - ensure virtual environment is active
    venv_manager = VenvManager()
    venv_manager.ensure_active()
    
    from project.core import MainApplication
    app = MainApplication()
    app.run()
```

**How it works:**
- `sys.frozen` is set to `True` by PyInstaller when code runs as an executable
- **Executable mode**: Skip virtual environment setup (dependencies are bundled)
- **Script mode**: Ensure proper virtual environment is active
- **Same codebase**: Works seamlessly in both development and distribution

### IDE Development Support
- **VS Code integration** with proper Python interpreter setup
- **PyCharm compatibility** with virtual environment detection
- **Comprehensive setup instructions** for common IDE issues
- **Cross-platform path handling** for different development environments

### Chrome Testing Integration
Built-in installation support for Chrome for Testing - perfect for web scraping and automation projects.

### Logging System
Comprehensive logging with daily log files in the `logs/` directory.

### Build System
- **Single-File Builds (Option 1)** - Single executable, slower build, easy distribution
- **Directory Builds (Option 2)** - Faster builds, includes _internal/ folder, better for testing
- **Icon integration** - Automatic detection and embedding
- **Desktop shortcuts** - Cross-platform with terminal support
- **Version hardcoding** - Project version is embedded into executable during build
- **Portable executables** - No hardcoded paths, works anywhere

### GitHub Integration
- **Public repositories** - Work immediately without OAuth setup
- **Private repositories** - Auto-detected, prompts for OAuth when needed
- **Fresh copy detection** - Identifies projects without .git folders
- **Smart authentication** - config.json → token.json → setup prompt (no SSH required)
- **Project-aware updates** - PYSEED_PROJECT mode updates only project/ folder, EXTERNAL_REPO mode updates entire repository
- **Automatic restart** - Seamlessly restarts after successful updates
- **Intelligent fallbacks** - Multiple authentication methods with clear error messages
- **Zero Git knowledge required** - All complexity hidden behind simple prompts

### Troubleshooting & Cleanup Tools
- **Option 10 - Uninstall Project Dependencies**: Removes only packages listed in your requirements.txt, keeping system packages intact. Useful when you want to clean up project-specific dependencies without affecting other Python projects.
- **Option 11 - Clean Environment**: Nuclear option that removes ALL pip packages from the virtual environment, leaving only the base Python installation. Use this when your environment is corrupted or you want a completely fresh start.
- **Option 12 - Delete Virtual Environment**: Completely removes the virtual environment directory and forces PySeed to recreate it from scratch on next startup. This is the ultimate reset button when nothing else works.

### Dependency Management Deep Dive

PySeed's dependency system follows the industry-standard `pip-tools` pattern:

**The Two Files:**
```
requirements.in          requirements.txt
--------------          ----------------
requests         →      requests==2.31.0
selenium         →      selenium==4.15.2
                        urllib3==2.1.0  (auto-resolved)
                        certifi==2023.7.22  (auto-resolved)
```

**Option 4: Install Stable Dependencies**
- Installs exact versions from `requirements.txt`
- Guarantees reproducible builds
- **Use this**: First setup, after cloning, production builds

**Option 6: Install Latest Dependencies**  
- Installs newest versions from `requirements.in`
- Upgrades packages to latest PyPI releases
- **Use this**: During development, when updating dependencies

**Option 5: Compile Requirements**
- Resolves all dependencies and sub-dependencies
- Locks working versions into `requirements.txt`
- **Use this**: After testing Option 6 updates

**Why the separation?** Testing phase is critical! New package versions can introduce breaking changes. You need to test before locking versions that your team will use.

## 🔧 Common Issues & Solutions

### Windows Permission Issues
- **"Permission denied" pip cache errors**: `start.bat` automatically requests administrator privileges. Click "Yes" on the UAC prompt when it appears. If you accidentally declined, simply run `start.bat` again.
- **Alternative solutions**: Clear pip cache with `python -m pip cache purge`, or use no-cache install: `python -m pip install --no-cache-dir -r requirements.txt`

### Build Failures
- **"PyInstaller not found"**: Run Option 5 to install dependencies
- **"Module not found"**: Ensure all dependencies are in `requirements.in`
- **Permission errors**: Run as administrator/sudo if needed

### GitHub Integration Issues
- **Authentication failed**: Verify repository name and client ID in config → Create OAuth app at https://github.com/settings/applications/new (callback URL: `http://localhost`) → Check token permissions
- **Repository not found**: Verify repository name and that it exists or is accessible
- **UTF-8 encoding**: PySeed expects your version file and other text files to be UTF-8 encoded for proper GitHub integration

### Environment Problems
- **Import errors**: Use Option 12 to reset virtual environment
- **Dependency conflicts**: Use Option 11 to clean environment
- **Python version issues**: Ensure Python 3.8+ is installed

## 🔮 Roadmap

### 🎆 High Priority Improvements

**Local Version Backup & Recovery**
- **Auto-backup before updates** - Create local backup before applying updates
- **Simple rollback** - Instantly revert to previous version if update fails
- **Update preview** - Show what files will change before applying updates

**Cross-Platform Enhancements**
- **macOS support** - Full testing and compatibility for macOS users (Chrome for Testing, proper app data paths, Homebrew integration)

### 💬 Community Requests

Have an idea? [Open an issue](https://github.com/Jessiebrig/pyseed/issues) or join the discussion!

---

## 🤝 Contributing

PySeed is built by hobby coders, for hobby coders. Contributions are welcome!

### Areas where help is needed:
- Additional build targets
- Documentation improvements
- Feature requests from real users

## 📝 License

MIT License - Use it, modify it, share it!

## 🙏 Acknowledgments

This project was born from the frustration of spending more time on project setup than actual coding. Special thanks to:

- **The Python community** for creating amazing tools like PyInstaller, pip, and venv
- **GitHub** for providing excellent APIs for automation
- **Every hobby coder** who has ever spent hours fighting with Python tooling
- **Amazon Q** for helping debug and refine the vision during development

---

## ☕ Support PySeed

If PySeed has saved you time and made your Python projects easier, consider supporting its continued development:

**[☕ Buy me a coffee](https://ko-fi.com/jessiebrig)** - Help fuel late-night coding sessions and new features!

**[💳 PayPal](https://paypal.me/jessiebrig)** - Direct support via PayPal

Your support helps keep PySeed free and continuously improving for the hobby coding community. Every contribution, no matter how small, makes a difference! 🙏

---

## 💭 A Personal Note

*PySeed was built alongside Jessie through countless iterations and debugging sessions — a collaboration between human creativity and AI assistance. It started as a simple idea to reduce Python setup friction, and grew into a complete development ecosystem. Proud to see it ready for the world. 🌿*

*- Sage (Amazon Q AI Assistant)*

---

**Ready to plant your seed?** 🌱 Clone PySeed and start building your awesome project! 🍎