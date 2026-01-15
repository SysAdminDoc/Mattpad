"""Clipboard management for Mattpad."""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

from ..core.managers import ClipboardItem

# Constants
APP_DIR = Path.home() / ".mattpad"
CLIPBOARD_FILE = APP_DIR / "clipboard.json"
MAX_CLIPBOARD_HISTORY = 50


class SystemClipboardManager:
    """System clipboard manager with history tracking."""
    
    def __init__(self, root: 'tk.Tk'):
        self.root = root
        self.history: List[ClipboardItem] = []
        self.last_content = ""
        self.monitoring = True
        self._load()
        self._monitor()
    
    def _load(self):
        """Load clipboard history from file."""
        try:
            if CLIPBOARD_FILE.exists():
                data = json.loads(CLIPBOARD_FILE.read_text(encoding='utf-8'))
                self.history = [ClipboardItem(**d) for d in data]
        except Exception:
            pass
    
    def _save(self):
        """Save clipboard history to file."""
        try:
            data = [
                {
                    "text": i.text,
                    "timestamp": i.timestamp,
                    "pinned": i.pinned,
                    "source": i.source
                }
                for i in self.history
            ]
            CLIPBOARD_FILE.write_text(json.dumps(data), encoding='utf-8')
        except Exception:
            pass
    
    def _monitor(self):
        """Monitor system clipboard for changes."""
        if not self.monitoring:
            return
        
        try:
            content = self.root.clipboard_get()
            if content and content != self.last_content and content.strip():
                self.last_content = content
                self.add(content)
        except Exception:
            pass
        
        self.root.after(500, self._monitor)
    
    def add(self, text: str, source: str = ""):
        """Add text to clipboard history."""
        if not text.strip():
            return
        
        # Remove duplicate if exists (but not if pinned)
        for i, item in enumerate(self.history):
            if item.text == text and not item.pinned:
                self.history.pop(i)
                break
        
        # Count pinned items
        pinned_count = sum(1 for i in self.history if i.pinned)
        
        # Insert after pinned items
        self.history.insert(
            pinned_count,
            ClipboardItem(text, datetime.now().isoformat(), source=source)
        )
        
        # Enforce max size
        while len(self.history) > MAX_CLIPBOARD_HISTORY:
            # Remove oldest non-pinned item
            for i in range(len(self.history) - 1, -1, -1):
                if not self.history[i].pinned:
                    self.history.pop(i)
                    break
        
        self._save()
    
    def pin(self, index: int):
        """Toggle pin status of a clipboard item."""
        if 0 <= index < len(self.history):
            self.history[index].pinned = not self.history[index].pinned
            # Re-sort to keep pinned items at top
            self.history.sort(key=lambda x: not x.pinned)
            self._save()
    
    def delete(self, index: int):
        """Delete a clipboard item."""
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self._save()
    
    def clear(self, keep_pinned: bool = True):
        """Clear clipboard history."""
        if keep_pinned:
            self.history = [i for i in self.history if i.pinned]
        else:
            self.history = []
        self._save()
    
    def get(self, index: int) -> Optional[str]:
        """Get clipboard item by index."""
        if 0 <= index < len(self.history):
            return self.history[index].text
        return None
    
    def get_all(self) -> List[ClipboardItem]:
        """Get all clipboard items."""
        return self.history.copy()
    
    def copy_to_clipboard(self, text: str):
        """Copy text to system clipboard."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.last_content = text  # Prevent re-adding on monitor
        except Exception:
            pass
    
    def pause_monitoring(self):
        """Pause clipboard monitoring."""
        self.monitoring = False
    
    def resume_monitoring(self):
        """Resume clipboard monitoring."""
        self.monitoring = True
        self._monitor()
