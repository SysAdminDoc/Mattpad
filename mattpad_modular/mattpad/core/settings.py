"""Editor settings management."""
from dataclasses import dataclass, field
from typing import List, Optional
import json
from pathlib import Path

# App directories
APP_NAME = "Mattpad"
APP_DIR = Path.home() / ".mattpad"
SETTINGS_FILE = APP_DIR / "settings.json"


@dataclass
class EditorSettings:
    """Editor settings with defaults."""
    
    # Appearance
    theme_name: str = "Professional Dark"
    font_family: str = "Consolas"
    font_size: int = 12
    ui_scale: float = 1.0
    
    # Editor behavior
    tab_size: int = 4
    use_spaces: bool = True
    word_wrap: bool = False
    auto_indent: bool = True
    auto_close_brackets: bool = True
    highlight_current_line: bool = True
    show_whitespace: bool = False
    
    # Line numbers & minimap
    show_line_numbers: bool = True
    show_minimap: bool = True
    minimap_width: int = 100
    
    # Status bar
    show_status_bar: bool = True
    
    # File handling
    encoding: str = "utf-8"
    line_ending: str = "CRLF"
    auto_detect_encoding: bool = True
    create_backup: bool = True
    backup_count: int = 5
    
    # Auto-save
    auto_save_enabled: bool = False
    auto_save_interval: int = 60
    
    # Session
    restore_session: bool = True
    hot_exit_enabled: bool = True
    show_welcome_screen: bool = True
    remember_window_state: bool = True
    
    # Recent files
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 20
    
    # Sidebar
    sidebar_visible: bool = True
    sidebar_width: int = 250
    last_folder: str = ""
    
    # Clipboard panel
    clipboard_panel_visible: bool = False
    clipboard_panel_width: int = 280
    
    # Spellcheck
    spellcheck_enabled: bool = False
    spellcheck_language: str = "en"
    custom_dictionary: List[str] = field(default_factory=list)
    
    # Terminal
    terminal_enabled: bool = True
    terminal_font_size: int = 11
    
    # AI integration
    ai_provider: str = "openai"
    ai_model: str = ""
    ai_api_key: str = ""
    
    # Cloud sync
    cloud_sync_enabled: bool = False
    sync_provider: str = ""
    github_token: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    github_path: str = "mattpad_sync"
    
    # Ribbon
    ribbon_collapsed: bool = True
    ribbon_pinned: bool = False
    show_toolbar: bool = True
    
    # Window state
    window_geometry: str = "1400x800"
    window_maximized: bool = False
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        result = {}
        for key in self.__dataclass_fields__:
            value = getattr(self, key)
            # Skip sensitive fields
            if key not in ('github_token', 'ai_api_key'):
                result[key] = value
        return result
    
    def from_dict(self, data: dict):
        """Load settings from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def save(self):
        """Save settings to file."""
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(
                json.dumps(self.to_dict(), indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def load(self):
        """Load settings from file."""
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding='utf-8'))
                self.from_dict(data)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def add_recent_file(self, filepath: str):
        """Add file to recent files list."""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.recent_files = self.recent_files[:self.max_recent_files]
