import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import tempfile
import shutil

class JSONStore:
    """Thread-safe JSON storage with atomic writes"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, filename: str) -> Path:
        return self.data_dir / filename
    
    def _write_atomic(self, file_path: Path, data: Any) -> None:
        """Atomic write using temp file"""
        try:
            # Write to temp file
            temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir)
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
                # Atomic rename
                os.replace(temp_path, file_path)
            except:
                # Clean up temp file if something goes wrong
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise
        except Exception as e:
            raise Exception(f"Failed to write {file_path}: {str(e)}")
    
    def read(self, filename: str, default: Any = None) -> Any:
        """Read JSON file, return default if not exists"""
        file_path = self._get_file_path(filename)
        
        if not file_path.exists():
            return default if default is not None else {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted, return default
            return default if default is not None else {}
        except Exception as e:
            raise Exception(f"Failed to read {filename}: {str(e)}")
    
    def write(self, filename: str, data: Any) -> None:
        """Write JSON file atomically"""
        file_path = self._get_file_path(filename)
        self._write_atomic(file_path, data)
    
    def append(self, filename: str, item: Dict) -> None:
        """Append item to JSON array"""
        data = self.read(filename, [])
        if not isinstance(data, list):
            data = []
        data.append(item)
        self.write(filename, data)
    
    def update(self, filename: str, key: str, value: Any) -> None:
        """Update key in JSON dict"""
        data = self.read(filename, {})
        if not isinstance(data, dict):
            data = {}
        data[key] = value
        self.write(filename, data)
    
    def delete(self, filename: str, key: Optional[str] = None) -> None:
        """Delete key from JSON dict or entire file"""
        if key:
            data = self.read(filename, {})
            if isinstance(data, dict) and key in data:
                del data[key]
                self.write(filename, data)
        else:
            file_path = self._get_file_path(filename)
            if file_path.exists():
                file_path.unlink()
    
    def exists(self, filename: str) -> bool:
        """Check if file exists"""
        return self._get_file_path(filename).exists()
    
    def get_all_ids(self, filename: str) -> List[str]:
        """Get all keys from JSON dict"""
        data = self.read(filename, {})
        if isinstance(data, dict):
            return list(data.keys())
        return []
    
    def backup(self, filename: str) -> str:
        """Create backup with timestamp"""
        file_path = self._get_file_path(filename)
        if not file_path.exists():
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.data_dir / f"{filename}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        return str(backup_path)


# Initialize stores
from app.core.config import settings

invoices_store = JSONStore(settings.DATA_DIR)
anomalies_store = JSONStore(settings.DATA_DIR)
vendors_store = JSONStore(settings.DATA_DIR)
processing_jobs_store = JSONStore(settings.DATA_DIR)
