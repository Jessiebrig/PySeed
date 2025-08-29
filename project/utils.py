"""
File read/write operations for the project.
"""

import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileHandler:
    """Handles file read/write operations."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
    
    def read_text(self, file_path: Path) -> str:
        """Read text file content."""
        full_path = self._resolve_path(file_path)
        try:
            return full_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"[ERROR] File not found: {full_path}")
            return ""
        except Exception as e:
            print(f"[ERROR] Failed to read {full_path}: {e}")
            return ""
    
    def write_text(self, file_path: Path, content: str) -> bool:
        """Write text content to file."""
        full_path = self._resolve_path(file_path)
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            print(f"[INFO] File written: {full_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write {full_path}: {e}")
            return False
    
    def read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file content."""
        full_path = self._resolve_path(file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] JSON file not found: {full_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in {full_path}: {e}")
            return {}
        except Exception as e:
            print(f"[ERROR] Failed to read JSON {full_path}: {e}")
            return {}
    
    def write_json(self, file_path: Path, data: Dict[str, Any], indent: int = 2) -> bool:
        """Write data to JSON file."""
        full_path = self._resolve_path(file_path)
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            print(f"[INFO] JSON file written: {full_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write JSON {full_path}: {e}")
            return False
    
    def read_csv(self, file_path: Path) -> List[Dict[str, str]]:
        """Read CSV file content."""
        full_path = self._resolve_path(file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            print(f"[ERROR] CSV file not found: {full_path}")
            return []
        except Exception as e:
            print(f"[ERROR] Failed to read CSV {full_path}: {e}")
            return []
    
    def write_csv(self, file_path: Path, data: List[Dict[str, str]], fieldnames: Optional[List[str]] = None) -> bool:
        """Write data to CSV file."""
        if not data:
            print("[WARNING] No data to write to CSV")
            return False
            
        full_path = self._resolve_path(file_path)
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            fieldnames = fieldnames or list(data[0].keys())
            
            with open(full_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            print(f"[INFO] CSV file written: {full_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to write CSV {full_path}: {e}")
            return False
    
    def file_exists(self, file_path: Path) -> bool:
        """Check if file exists."""
        return self._resolve_path(file_path).exists()
    
    def create_directory(self, dir_path: Path) -> bool:
        """Create directory if it doesn't exist."""
        full_path = self._resolve_path(dir_path)
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create directory {full_path}: {e}")
            return False
    
    def _resolve_path(self, file_path: Path) -> Path:
        """Resolve path relative to base path."""
        if file_path.is_absolute():
            return file_path
        return self.base_path / file_path