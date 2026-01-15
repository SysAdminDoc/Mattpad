"""Various manager classes for Mattpad."""
import os
import json
import time
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import EditorSettings

logger = logging.getLogger(__name__)

# Directories
APP_DIR = Path.home() / ".mattpad"
CACHE_DIR = APP_DIR / "cache"
BACKUP_DIR = APP_DIR / "backups"
HOT_EXIT_DIR = APP_DIR / "hot_exit"
SNIPPETS_DIR = APP_DIR / "snippets"
MACROS_DIR = APP_DIR / "macros"
SESSION_FILE = APP_DIR / "session.json"
CLIPBOARD_FILE = APP_DIR / "clipboard.json"

# Ensure directories exist
for d in [APP_DIR, CACHE_DIR, BACKUP_DIR, HOT_EXIT_DIR, SNIPPETS_DIR, MACROS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Constants
MAX_CLIPBOARD_HISTORY = 50


class SecretStorage:
    """Simple secret storage using keyring if available, file fallback."""
    
    _keyring_available = False
    _secrets_file = APP_DIR / "secrets.json"
    _cache: Dict[str, str] = {}
    
    @classmethod
    def _init_keyring(cls):
        """Initialize keyring if available."""
        try:
            import keyring
            cls._keyring_available = True
        except ImportError:
            cls._keyring_available = False
    
    @classmethod
    def store(cls, key: str, value: str):
        """Store a secret."""
        cls._init_keyring()
        cls._cache[key] = value
        
        if cls._keyring_available:
            try:
                import keyring
                keyring.set_password("mattpad", key, value)
                return
            except Exception:
                pass
        
        # Fallback to file (not secure but functional)
        try:
            secrets = {}
            if cls._secrets_file.exists():
                secrets = json.loads(cls._secrets_file.read_text())
            secrets[key] = value
            cls._secrets_file.write_text(json.dumps(secrets))
        except Exception:
            pass
    
    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """Retrieve a secret."""
        cls._init_keyring()
        
        if key in cls._cache:
            return cls._cache[key]
        
        if cls._keyring_available:
            try:
                import keyring
                value = keyring.get_password("mattpad", key)
                if value:
                    cls._cache[key] = value
                    return value
            except Exception:
                pass
        
        # Fallback to file
        try:
            if cls._secrets_file.exists():
                secrets = json.loads(cls._secrets_file.read_text())
                value = secrets.get(key, default)
                cls._cache[key] = value
                return value
        except Exception:
            pass
        
        return default


@dataclass
class ClipboardItem:
    """Clipboard history item."""
    text: str
    timestamp: str = ""
    pinned: bool = False
    source: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CacheManager:
    """Manages file content caching for faster access."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        """Load cache index from disk."""
        index_file = CACHE_DIR / "index.json"
        if index_file.exists():
            try:
                self._cache = json.loads(index_file.read_text())
            except Exception:
                pass
    
    def _save(self):
        """Save cache index to disk."""
        try:
            index_file = CACHE_DIR / "index.json"
            index_file.write_text(json.dumps(self._cache))
        except Exception:
            pass
    
    def get(self, filepath: str) -> Optional[str]:
        """Get cached content if still valid."""
        if filepath not in self._cache:
            return None
        
        entry = self._cache[filepath]
        try:
            mtime = os.path.getmtime(filepath)
            if mtime == entry.get("mtime"):
                cache_file = CACHE_DIR / entry.get("hash", "")
                if cache_file.exists():
                    return cache_file.read_text(encoding='utf-8')
        except Exception:
            pass
        
        return None
    
    def put(self, filepath: str, content: str):
        """Cache file content."""
        try:
            content_hash = hashlib.md5(filepath.encode()).hexdigest()
            mtime = os.path.getmtime(filepath)
            
            cache_file = CACHE_DIR / content_hash
            cache_file.write_text(content, encoding='utf-8')
            
            self._cache[filepath] = {
                "hash": content_hash,
                "mtime": mtime,
                "size": len(content),
            }
            
            # Enforce max size
            while len(self._cache) > self.max_size:
                oldest = min(self._cache.keys(), key=lambda k: self._cache[k].get("mtime", 0))
                del self._cache[oldest]
            
            self._save()
        except Exception:
            pass
    
    def invalidate(self, filepath: str):
        """Invalidate cache entry."""
        if filepath in self._cache:
            del self._cache[filepath]
            self._save()


class BackupManager:
    """Manages file backups."""
    
    def __init__(self, settings: 'EditorSettings'):
        self.settings = settings
    
    def create_backup(self, filepath: str, content: str) -> Optional[str]:
        """Create a backup of the file."""
        if not self.settings.create_backup or not filepath:
            return None
        
        try:
            basename = os.path.basename(filepath)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{basename}.{timestamp}.bak"
            backup_path = BACKUP_DIR / backup_name
            
            backup_path.write_text(content, encoding='utf-8')
            
            # Clean old backups
            self._cleanup_old_backups(basename)
            
            return str(backup_path)
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None
    
    def _cleanup_old_backups(self, basename: str):
        """Remove old backups beyond the limit."""
        pattern = f"{basename}.*.bak"
        backups = sorted(BACKUP_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        
        for old_backup in backups[self.settings.backup_count:]:
            try:
                old_backup.unlink()
            except Exception:
                pass
    
    def list_backups(self, filepath: str) -> List[Dict]:
        """List backups for a file."""
        if not filepath:
            return []
        
        basename = os.path.basename(filepath)
        pattern = f"{basename}.*.bak"
        
        backups = []
        for backup in sorted(BACKUP_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                stat = backup.stat()
                backups.append({
                    "path": str(backup),
                    "name": backup.name,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception:
                pass
        
        return backups
    
    def restore_backup(self, backup_path: str) -> Optional[str]:
        """Read backup content."""
        try:
            return Path(backup_path).read_text(encoding='utf-8')
        except Exception:
            return None


class SessionManager:
    """Manages session persistence."""
    
    def __init__(self):
        self.session_file = SESSION_FILE
    
    def save_session(self, tabs: List[Dict], current_tab: Optional[str] = None):
        """Save session to file."""
        try:
            session = {
                "timestamp": datetime.now().isoformat(),
                "current_tab": current_tab,
                "tabs": tabs,
            }
            self.session_file.write_text(json.dumps(session, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Session save error: {e}")
    
    def load_session(self) -> List[Dict]:
        """Load session from file."""
        if self.session_file.exists():
            try:
                data = json.loads(self.session_file.read_text(encoding='utf-8'))
                return data.get("tabs", [])
            except Exception:
                pass
        return []


class HotExitManager:
    """Saves complete session state on exit, restores on startup."""
    
    SNAPSHOT_FILE = HOT_EXIT_DIR / "snapshot.json"
    
    def __init__(self):
        self.enabled = True
    
    def save_snapshot(self, tabs: Dict, text_widgets: Dict,
                     current_tab: Optional[str], active_order: List[str],
                     version: str = "1.0") -> bool:
        """Save complete session snapshot including unsaved content."""
        if not self.enabled:
            return False
        
        try:
            import tkinter as tk
            
            snapshot = {
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "current_tab": current_tab,
                "active_order": active_order,
                "tabs": []
            }
            
            for tab_id in active_order:
                if tab_id not in tabs or tab_id not in text_widgets:
                    continue
                
                tab_data = tabs[tab_id]
                text_widget = text_widgets[tab_id]
                
                try:
                    content = text_widget.get("1.0", "end-1c")
                    cursor_pos = text_widget.index(tk.INSERT)
                    scroll_pos = (text_widget.xview()[0], text_widget.yview()[0])
                except Exception:
                    content = ""
                    cursor_pos = "1.0"
                    scroll_pos = (0.0, 0.0)
                
                # Save content to separate file
                content_file = HOT_EXIT_DIR / f"{tab_id}.content"
                content_file.write_text(content, encoding='utf-8')
                
                tab_snapshot = {
                    "tab_id": tab_id,
                    "filepath": tab_data.filepath,
                    "modified": tab_data.modified,
                    "encoding": tab_data.encoding,
                    "language": tab_data.language,
                    "cursor_position": cursor_pos,
                    "scroll_position": scroll_pos,
                    "bookmarks": list(tab_data.bookmarks) if hasattr(tab_data, 'bookmarks') else [],
                    "folds": list(tab_data.folds) if hasattr(tab_data, 'folds') else [],
                }
                snapshot["tabs"].append(tab_snapshot)
            
            self.SNAPSHOT_FILE.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
            logger.info(f"Hot exit snapshot saved: {len(snapshot['tabs'])} tabs")
            return True
            
        except Exception as e:
            logger.error(f"Hot exit save failed: {e}")
            return False
    
    def load_snapshot(self) -> Optional[Dict]:
        """Load session snapshot if exists."""
        if not self.enabled or not self.SNAPSHOT_FILE.exists():
            return None
        
        try:
            snapshot = json.loads(self.SNAPSHOT_FILE.read_text(encoding='utf-8'))
            
            for tab in snapshot.get("tabs", []):
                content_file = HOT_EXIT_DIR / f"{tab['tab_id']}.content"
                if content_file.exists():
                    tab["content"] = content_file.read_text(encoding='utf-8')
                else:
                    tab["content"] = ""
            
            logger.info(f"Hot exit snapshot loaded: {len(snapshot.get('tabs', []))} tabs")
            return snapshot
            
        except Exception as e:
            logger.error(f"Hot exit load failed: {e}")
            return None
    
    def clear_snapshot(self):
        """Clear snapshot after successful restore."""
        try:
            if self.SNAPSHOT_FILE.exists():
                self.SNAPSHOT_FILE.unlink()
            for f in HOT_EXIT_DIR.glob("*.content"):
                f.unlink()
            logger.info("Hot exit snapshot cleared")
        except OSError as e:
            logger.error(f"Hot exit clear failed: {e}")
    
    def has_snapshot(self) -> bool:
        """Check if a snapshot exists."""
        return self.SNAPSHOT_FILE.exists()


class ClosedTabsManager:
    """Manages recently closed tabs for reopening."""
    
    def __init__(self, max_items: int = 20):
        self.max_items = max_items
        self.closed_tabs: List[Dict] = []
    
    def add(self, filepath: str, content: str, cursor_pos: str = "1.0"):
        """Add a closed tab to history."""
        if not filepath and not content.strip():
            return
        
        self.closed_tabs.insert(0, {
            "filepath": filepath,
            "content": content,
            "cursor_pos": cursor_pos,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Enforce limit
        self.closed_tabs = self.closed_tabs[:self.max_items]
    
    def pop(self) -> Optional[Dict]:
        """Get and remove the most recently closed tab."""
        if self.closed_tabs:
            return self.closed_tabs.pop(0)
        return None
    
    def peek(self) -> Optional[Dict]:
        """Get the most recently closed tab without removing it."""
        if self.closed_tabs:
            return self.closed_tabs[0]
        return None
    
    def clear(self):
        """Clear all closed tabs."""
        self.closed_tabs = []
    
    def list_all(self) -> List[Dict]:
        """Get all closed tabs."""
        return self.closed_tabs.copy()
