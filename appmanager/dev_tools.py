import importlib.metadata
import logging
import subprocess
import sys

from appmanager import config, utils
from appmanager.dependency_manager import DependencyManager


class DevToolsManager:
    """Manages developer-centric tools like dependency compilation."""

    def __init__(self):
        # Appmanager requirements
        self.appmanager_requirements_in = config.REQUIREMENTS_IN_FILE
        self.appmanager_requirements_txt = config.REQUIREMENTS_FILE
        
        # Project requirements (dynamic paths based on project mode)
        self.project_requirements_in = config.get_requirements_in_file_path()
        self.project_requirements_txt = config.get_requirements_file_path()

    def _create_template_requirements_in(self):
        """Creates a template requirements.in file with helpful comments."""
        content = """\
#
# This file is for specifying the project's direct dependencies.
# Add your top-level packages here, one per line.
#
# Example:
# requests
# selenium
# packaging
#
# After adding packages, run the 'Compile requirements.txt' option
# in the app manager to generate the full requirements.txt file.
"""
        self.appmanager_requirements_in.write_text(content)
        logging.info(f"Template file created at: {self.appmanager_requirements_in}")

    def compile_requirements(self) -> bool:
        """
        Compiles requirements.in to requirements.txt using pip-compile.
        Offers choice between compiling all requirements or just project requirements.
        """
        utils.clear_console()
        print("=== Option 5: Compile Requirements ===\n")
        
        if not utils.is_package_installed("pip-tools"):
            print("-> pip-tools not found. Installing...")
            utils.install_packages(["pip-tools"])
        
        print("Choose compilation scope:")
        print("  1. Compile all requirements (appmanager + project)")
        print("  2. Compile project requirements only")
        choice = input("\nEnter your choice [1-2]: ").strip()
        
        if choice == "1":
            return self._compile_all_requirements()
        elif choice == "2":
            return self._compile_project_requirements()
        else:
            print("[INFO] Invalid choice. Operation cancelled.")
            return False
    
    def _compile_all_requirements(self) -> bool:
        """Compile both appmanager and project requirements."""
        print("\n-> Compiling all requirements...")
        success = True
        
        # Compile appmanager requirements
        if self.appmanager_requirements_in.exists():
            print(f"-> Compiling appmanager requirements...")
            if not self._compile_single_file(self.appmanager_requirements_in, self.appmanager_requirements_txt):
                success = False
        else:
            print(f"[WARN] Appmanager requirements.in not found, skipping.")
        
        # Compile project requirements
        if self.project_requirements_in.exists():
            print(f"-> Compiling project requirements...")
            if not self._compile_single_file(self.project_requirements_in, self.project_requirements_txt):
                success = False
        else:
            print(f"[WARN] Project requirements.in not found, skipping.")
        
        if success:
            print("\n[SUCCESS] All requirements compiled successfully.")
        return success
    
    def _compile_project_requirements(self) -> bool:
        """Compile only project requirements."""
        if not self.project_requirements_in.exists():
            print(f"[ERROR] Project requirements.in not found at {self.project_requirements_in}")
            return False
        
        print(f"\n-> Compiling project requirements...")
        return self._compile_single_file(self.project_requirements_in, self.project_requirements_txt)
    
    def _compile_single_file(self, in_file, out_file) -> bool:
        """Compile a single requirements.in file to requirements.txt."""
        try:
            command = [
                sys.executable, "-m", "piptools", "compile",
                "--output-file", str(out_file),
                "--quiet",  # Suppress verbose output
                str(in_file)
            ]
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logging.info(f"pip-compile completed for {in_file.name}")
            print(f"   ✅ {out_file.name} updated")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to compile {in_file.name}")
            if e.stderr:
                print(f"   Error: {e.stderr.strip()}")
            return False

    def install_dev_dependencies(self):
        """Installs latest dependencies from both appmanager and project requirements.in files."""
        utils.clear_console()
        print("=== Option 6: Install Latest Dependencies ===\n")
        
        success = True
        
        # Install appmanager dependencies first
        if self.appmanager_requirements_in.exists():
            print("-> Installing appmanager dependencies...")
            if not DependencyManager.install_from_file(self.appmanager_requirements_in, "appmanager"):
                success = False
        else:
            print("[WARN] Appmanager requirements.in not found, skipping.")
        
        # Install project dependencies
        if self.project_requirements_in.exists():
            print("\n-> Installing project dependencies...")
            if not DependencyManager.install_from_file(self.project_requirements_in, "project"):
                success = False
        else:
            print("\n[WARN] Project requirements.in not found, skipping.")
        
        if success:
            print("\n✅ [SUCCESS] All latest dependencies installed.")
        else:
            print("\n⚠️ [PARTIAL] Some dependencies failed to install. Check logs for details.")
    


    def uninstall_project_dependencies(self):
        """Uninstalls only the packages listed in project requirements.txt."""
        utils.clear_console()
        print("=== Option 10: Uninstall Project Dependencies ===\n")
        
        # Only check project requirements file
        if not self.project_requirements_txt.exists():
            print(f"No project requirements.txt found at {self.project_requirements_txt}")
            print("Cannot uninstall project dependencies.")
            return
        
        print("\nThis will uninstall packages from:")
        print(f"  - project: {self.project_requirements_txt.name}")
        print("\n⚠️  Note: Appmanager dependencies will NOT be touched.")
        confirm = input("\nProceed? [y/N]: ").strip().lower()
        if confirm == 'y':
            print(f"\n-> Uninstalling project dependencies...")
            if DependencyManager.uninstall_from_file(self.project_requirements_txt, "project"):
                print("\n✅ [OK] Project dependencies uninstalled successfully.")
            else:
                print("\n⚠️ [PARTIAL] Some project dependencies failed to uninstall. Check logs for details.")

    def clean_environment(self):
        """Uninstalls all packages except for pip, setuptools, and wheel."""
        utils.clear_console()
        print("=== Option 12: Clean Environment ===\n")
        installed_packages = [dist.metadata["name"] for dist in importlib.metadata.distributions()]
        exclude = {"pip", "setuptools", "wheel"}
        to_uninstall = [pkg for pkg in installed_packages if pkg.lower() not in exclude]

        prompt = "The following packages will be uninstalled from your environment:"
        utils.uninstall_packages(to_uninstall, prompt)