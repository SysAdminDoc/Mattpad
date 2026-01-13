#!/usr/bin/env python3
"""
Mattpad - Professional-grade text editor
Features: Auto-save cache, Cloud sync (GitHub/Google Drive), AI Integration, Multiple Themes
"""

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-INSTALL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════════

import subprocess
import sys

def install_dependencies():
    """Install required packages automatically on first run"""
    packages = {
        "customtkinter": "customtkinter",
        "requests": "requests",
        "chardet": "chardet",
        "google-auth": "google.auth",
        "google-auth-oauthlib": "google_auth_oauthlib",
        "google-api-python-client": "googleapiclient",
        "openai": "openai",
        "anthropic": "anthropic",
    }
    
    missing = []
    for package, import_name in packages.items():
        try:
            __import__(import_name.split(".")[0])
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Installing dependencies: {', '.join(missing)}...")
        for package in missing:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package,
                    "--quiet", "--disable-pip-version-check"
                ])
                print(f"  ✓ {package}")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ {package} failed: {e}")
        print("Dependencies installed. Starting application...\n")

install_dependencies()

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

import customtkinter as ctk
from tkinter import filedialog, messagebox, font as tkfont, simpledialog
import tkinter as tk
from tkinter import ttk
import os
import re
import json
import base64
import hashlib
import threading
import tempfile
import difflib
import time
import shutil
import ctypes
from pathlib import Path
from typing import Optional, Dict, List, Callable, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import requests

try:
    import chardet
except ImportError:
    chardet = None

# Google Drive support (auto-installed)
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    import io
    GOOGLE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google API import failed: {e}")
    GOOGLE_AVAILABLE = False

# AI libraries (auto-installed)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# WINDOWS DARK TITLE BAR
# ═══════════════════════════════════════════════════════════════════════════════

def set_dark_title_bar(window):
    """Enable dark title bar on Windows 10/11"""
    try:
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        
        # Try the newer attribute first (Windows 10 20H1+)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
        )
        
        # If that fails, try the older attribute
        if result != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
    except Exception:
        pass  # Not on Windows or API not available

def get_icon_path():
    """Get the icon path for the application"""
    # Check multiple possible locations
    possible_paths = [
        Path(__file__).parent / "mattpad.ico",
        Path.cwd() / "mattpad.ico",
        Path(sys.executable).parent / "mattpad.ico",
        Path.home() / ".mattpad" / "mattpad.ico",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# THEME SYSTEM - Multiple Themes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ThemeColors:
    """Theme color configuration"""
    name: str = "GitHub Dark"
    bg_darkest: str = "#0a0e14"
    bg_dark: str = "#0d1117"
    bg_medium: str = "#161b22"
    bg_light: str = "#21262d"
    bg_hover: str = "#30363d"
    bg_active: str = "#388bfd20"
    accent_primary: str = "#58a6ff"
    accent_green: str = "#3fb950"
    accent_orange: str = "#d29922"
    accent_red: str = "#f85149"
    accent_purple: str = "#a371f7"
    accent_cyan: str = "#39c5cf"
    accent_pink: str = "#db61a2"
    text_primary: str = "#f0f6fc"
    text_secondary: str = "#8b949e"
    text_muted: str = "#6e7681"
    text_disabled: str = "#484f58"
    syntax_keyword: str = "#ff7b72"
    syntax_string: str = "#a5d6ff"
    syntax_comment: str = "#8b949e"
    syntax_number: str = "#79c0ff"
    syntax_function: str = "#d2a8ff"
    syntax_class: str = "#ffa657"
    syntax_operator: str = "#ff7b72"
    syntax_decorator: str = "#ffa657"
    syntax_builtin: str = "#79c0ff"
    syntax_constant: str = "#79c0ff"
    selection_bg: str = "#264f78"
    current_line: str = "#161b22"
    bracket_match: str = "#ffa657"
    search_highlight: str = "#533d00"
    tab_active: str = "#0d1117"
    tab_inactive: str = "#010409"
    tab_border: str = "#30363d"
    tab_modified: str = "#d29922"
    minimap_bg: str = "#0d1117"
    minimap_viewport: str = "#58a6ff20"
    status_synced: str = "#3fb950"
    status_syncing: str = "#58a6ff"
    status_error: str = "#f85149"
    status_modified: str = "#d29922"

# Theme Presets
THEMES = {
    "GitHub Dark": ThemeColors(name="GitHub Dark"),
    "Monokai": ThemeColors(
        name="Monokai", bg_darkest="#272822", bg_dark="#2d2e27", bg_medium="#3e3d32",
        bg_light="#49483e", bg_hover="#5a5a50", accent_primary="#a6e22e", accent_green="#a6e22e",
        accent_orange="#fd971f", accent_red="#f92672", accent_purple="#ae81ff",
        text_primary="#f8f8f2", text_secondary="#cfcfc2", text_muted="#75715e",
        syntax_keyword="#f92672", syntax_string="#e6db74", syntax_comment="#75715e",
        syntax_number="#ae81ff", syntax_function="#a6e22e", syntax_class="#66d9ef",
        selection_bg="#49483e", current_line="#3e3d32", tab_active="#3e3d32", tab_inactive="#272822",
    ),
    "Dracula": ThemeColors(
        name="Dracula", bg_darkest="#21222c", bg_dark="#282a36", bg_medium="#343746",
        bg_light="#44475a", bg_hover="#4d5066", accent_primary="#bd93f9", accent_green="#50fa7b",
        accent_orange="#ffb86c", accent_red="#ff5555", accent_purple="#bd93f9", accent_cyan="#8be9fd",
        text_primary="#f8f8f2", text_secondary="#bfbfbf", text_muted="#6272a4",
        syntax_keyword="#ff79c6", syntax_string="#f1fa8c", syntax_comment="#6272a4",
        syntax_number="#bd93f9", syntax_function="#50fa7b", syntax_class="#8be9fd",
        selection_bg="#44475a", current_line="#343746", tab_active="#343746", tab_inactive="#21222c",
    ),
    "Nord": ThemeColors(
        name="Nord", bg_darkest="#2e3440", bg_dark="#3b4252", bg_medium="#434c5e",
        bg_light="#4c566a", bg_hover="#5e6779", accent_primary="#88c0d0", accent_green="#a3be8c",
        accent_orange="#d08770", accent_red="#bf616a", accent_purple="#b48ead",
        text_primary="#eceff4", text_secondary="#d8dee9", text_muted="#7b88a1",
        syntax_keyword="#81a1c1", syntax_string="#a3be8c", syntax_comment="#616e88",
        syntax_number="#b48ead", syntax_function="#88c0d0", syntax_class="#8fbcbb",
        selection_bg="#434c5e", current_line="#3b4252", tab_active="#434c5e", tab_inactive="#2e3440",
    ),
    "One Dark": ThemeColors(
        name="One Dark", bg_darkest="#1e2127", bg_dark="#282c34", bg_medium="#2c323c",
        bg_light="#3e4451", bg_hover="#4b5363", accent_primary="#61afef", accent_green="#98c379",
        accent_orange="#d19a66", accent_red="#e06c75", accent_purple="#c678dd", accent_cyan="#56b6c2",
        text_primary="#abb2bf", text_secondary="#9da5b4", text_muted="#5c6370",
        syntax_keyword="#c678dd", syntax_string="#98c379", syntax_comment="#5c6370",
        syntax_number="#d19a66", syntax_function="#61afef", syntax_class="#e5c07b",
        selection_bg="#3e4451", current_line="#2c323c", tab_active="#2c323c", tab_inactive="#1e2127",
    ),
    "Solarized Dark": ThemeColors(
        name="Solarized Dark", bg_darkest="#002b36", bg_dark="#073642", bg_medium="#0a4351",
        bg_light="#124d5c", bg_hover="#1a5a6b", accent_primary="#268bd2", accent_green="#859900",
        accent_orange="#cb4b16", accent_red="#dc322f", accent_purple="#6c71c4", accent_cyan="#2aa198",
        text_primary="#fdf6e3", text_secondary="#93a1a1", text_muted="#657b83",
        syntax_keyword="#859900", syntax_string="#2aa198", syntax_comment="#586e75",
        syntax_number="#d33682", syntax_function="#268bd2", syntax_class="#b58900",
        selection_bg="#073642", current_line="#073642", tab_active="#073642", tab_inactive="#002b36",
    ),
    "Light": ThemeColors(
        name="Light", bg_darkest="#ffffff", bg_dark="#f6f8fa", bg_medium="#eaeef2",
        bg_light="#d0d7de", bg_hover="#c8d1da", accent_primary="#0969da", accent_green="#1a7f37",
        accent_orange="#9a6700", accent_red="#cf222e", accent_purple="#8250df",
        text_primary="#1f2328", text_secondary="#57606a", text_muted="#8c959f",
        syntax_keyword="#cf222e", syntax_string="#0a3069", syntax_comment="#6e7781",
        syntax_number="#0550ae", syntax_function="#8250df", syntax_class="#953800",
        selection_bg="#ddf4ff", current_line="#f6f8fa", tab_active="#ffffff", tab_inactive="#f6f8fa",
    ),
}

THEME = THEMES["GitHub Dark"]

# ═══════════════════════════════════════════════════════════════════════════════
# CACHE AND SYNC CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

CACHE_DIR = Path.home() / ".mattpad/cache"
SETTINGS_FILE = Path.home() / ".mattpad/settings.json"
SYNC_INTERVAL = 300  # 5 minutes in seconds
LOCAL_SAVE_INTERVAL = 10  # Auto-save to cache every 10 seconds
MAX_CLIPBOARD_HISTORY = 50
MAX_RECENT_FILES = 20

# ═══════════════════════════════════════════════════════════════════════════════
# FILE EXTENSIONS
# ═══════════════════════════════════════════════════════════════════════════════

FILE_EXTENSIONS = {
    ".py": "Python", ".pyw": "Python", ".pyx": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".html": "HTML", ".htm": "HTML", ".xhtml": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "SASS", ".less": "LESS",
    ".json": "JSON", ".json5": "JSON",
    ".xml": "XML", ".svg": "XML", ".xsl": "XML",
    ".md": "Markdown", ".markdown": "Markdown", ".mdx": "Markdown",
    ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI", ".cfg": "INI", ".conf": "INI",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell", ".psm1": "PowerShell", ".psd1": "PowerShell",
    ".bat": "Batch", ".cmd": "Batch",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++", ".hxx": "C++",
    ".cs": "C#",
    ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".swift": "Swift",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby", ".erb": "Ruby",
    ".php": "PHP",
    ".sql": "SQL",
    ".r": "R", ".R": "R",
    ".lua": "Lua",
    ".pl": "Perl", ".pm": "Perl",
    ".scala": "Scala",
    ".dart": "Dart",
    ".ex": "Elixir", ".exs": "Elixir",
    ".erl": "Erlang", ".hrl": "Erlang",
    ".hs": "Haskell",
    ".clj": "Clojure", ".cljs": "Clojure",
    ".vim": "VimL",
    ".dockerfile": "Dockerfile",
    ".tf": "Terraform", ".tfvars": "Terraform",
    ".proto": "Protocol Buffers",
    ".graphql": "GraphQL", ".gql": "GraphQL",
    ".txt": "Plain Text", ".log": "Plain Text", ".text": "Plain Text",
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TabData:
    """Data for a single editor tab"""
    tab_id: str = ""
    filepath: Optional[str] = None
    modified: bool = False
    content_hash: str = ""
    encoding: str = "utf-8"
    line_ending: str = "\n"
    language: str = "Plain Text"
    cursor_pos: tuple = (1, 0)
    scroll_pos: tuple = (0, 0)
    bookmarks: List[int] = field(default_factory=list)
    tab_frame: Any = None
    remote_path: Optional[str] = None
    remote_type: Optional[str] = None
    last_synced: Optional[str] = None
    sync_status: str = "local"  # local, synced, syncing, error
    cache_file: Optional[str] = None

@dataclass
class SearchState:
    """State for find/replace operations"""
    find_text: str = ""
    replace_text: str = ""
    match_case: bool = False
    whole_word: bool = False
    use_regex: bool = False
    search_up: bool = False

@dataclass
class EditorSettings:
    """Editor configuration"""
    font_family: str = "JetBrains Mono"
    font_size: int = 13
    tab_size: int = 4
    use_spaces: bool = True
    word_wrap: bool = False
    show_line_numbers: bool = True
    highlight_current_line: bool = True
    auto_indent: bool = True
    show_minimap: bool = True
    minimap_width: int = 120
    bracket_matching: bool = True
    auto_close_brackets: bool = True
    sidebar_visible: bool = True
    sidebar_width: int = 280
    window_geometry: str = "1600x1000"
    recent_files: List[str] = field(default_factory=list)
    
    # UI Scale (1.0 = normal, 1.25 = 125%, 1.5 = 150%)
    ui_scale: float = 1.0
    
    # Default file extension for new files
    default_extension: str = ".ps1"
    
    # Theme
    theme_name: str = "GitHub Dark"
    
    # Cloud sync settings
    cloud_sync_enabled: bool = False
    sync_provider: str = ""  # "github" or "gdrive"
    github_token: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    github_path: str = "mattpad_sync"
    gdrive_folder_id: str = ""
    gdrive_credentials: str = ""
    sync_interval: int = 300  # seconds
    
    # AI settings
    ai_provider: str = ""  # "openai", "anthropic", "ollama"
    ai_api_key: str = ""
    ai_model: str = ""
    ai_custom_prompts: List[Dict] = field(default_factory=list)
    
    # Clipboard history
    clipboard_history: List[str] = field(default_factory=list)
    
    # Session
    session_tabs: List[Dict] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════════════════════
# CLOUD SYNC MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class CloudSyncManager:
    """Manages cloud synchronization to GitHub or Google Drive"""
    
    def __init__(self, settings: EditorSettings):
        self.settings = settings
        self.is_syncing = False
        self.last_sync = None
        self.sync_errors = []
        
    def configure_github(self, token: str, repo: str, branch: str = "main", path: str = "mattpad_sync"):
        """Configure GitHub sync"""
        self.settings.github_token = token
        self.settings.github_repo = repo
        self.settings.github_branch = branch
        self.settings.github_path = path
        self.settings.sync_provider = "github"
        self.settings.cloud_sync_enabled = True
        
    def configure_gdrive(self, credentials: str, folder_id: str = ""):
        """Configure Google Drive sync"""
        self.settings.gdrive_credentials = credentials
        self.settings.gdrive_folder_id = folder_id
        self.settings.sync_provider = "gdrive"
        self.settings.cloud_sync_enabled = True
        
    def sync_file(self, tab_data: TabData, content: str) -> Tuple[bool, str]:
        """Sync a single file to cloud"""
        if not self.settings.cloud_sync_enabled:
            return False, "Cloud sync not configured"
            
        if self.settings.sync_provider == "github":
            return self._sync_to_github(tab_data, content)
        elif self.settings.sync_provider == "gdrive":
            return self._sync_to_gdrive(tab_data, content)
        return False, "Unknown sync provider"
        
    def _sync_to_github(self, tab_data: TabData, content: str) -> Tuple[bool, str]:
        """Sync file to GitHub"""
        try:
            token = self.settings.github_token
            repo = self.settings.github_repo
            branch = self.settings.github_branch
            base_path = self.settings.github_path
            
            if not token or not repo:
                return False, "GitHub not configured"
                
            # Generate filename
            if tab_data.filepath:
                filename = os.path.basename(tab_data.filepath)
            else:
                filename = f"untitled_{tab_data.tab_id[:8]}.txt"
                
            file_path = f"{base_path}/{filename}"
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Check if file exists to get SHA
            url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
            params = {"ref": branch}
            
            r = requests.get(url, headers=headers, params=params, timeout=10)
            sha = r.json().get("sha") if r.status_code == 200 else None
            
            # Create/update file
            data = {
                "message": f"Auto-sync: {filename} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
                "branch": branch
            }
            if sha:
                data["sha"] = sha
                
            r = requests.put(url, headers=headers, json=data, timeout=30)
            
            if r.status_code in (200, 201):
                tab_data.last_synced = datetime.now().isoformat()
                tab_data.sync_status = "synced"
                tab_data.remote_path = file_path
                return True, "Synced to GitHub"
            else:
                tab_data.sync_status = "error"
                return False, f"GitHub error: {r.status_code}"
                
        except Exception as e:
            tab_data.sync_status = "error"
            return False, str(e)
            
    def _sync_to_gdrive(self, tab_data: TabData, content: str) -> Tuple[bool, str]:
        """Sync file to Google Drive"""
        if not GOOGLE_AVAILABLE:
            return False, "Google API not available"
            
        try:
            # Load credentials
            token_path = Path.home() / ".mattpad/gdrive_token.json"
            if not token_path.exists():
                return False, "Google Drive not authenticated"
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, 'w') as f:
                    f.write(creds.to_json())
                    
            service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            
            # Generate filename
            if tab_data.filepath:
                filename = os.path.basename(tab_data.filepath)
            else:
                filename = f"untitled_{tab_data.tab_id[:8]}.txt"
                
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_file = f.name
                
            try:
                media = MediaFileUpload(temp_file, mimetype='text/plain')
                
                if tab_data.remote_path:
                    # Update existing
                    file = service.files().update(
                        fileId=tab_data.remote_path,
                        media_body=media
                    ).execute()
                else:
                    # Create new
                    file_metadata = {'name': filename}
                    if self.settings.gdrive_folder_id:
                        file_metadata['parents'] = [self.settings.gdrive_folder_id]
                        
                    file = service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()
                    tab_data.remote_path = file.get('id')
                    
                tab_data.last_synced = datetime.now().isoformat()
                tab_data.sync_status = "synced"
                return True, "Synced to Google Drive"
                
            finally:
                os.unlink(temp_file)
                
        except Exception as e:
            tab_data.sync_status = "error"
            return False, str(e)
            
    def test_github_connection(self) -> Tuple[bool, str]:
        """Test GitHub connection"""
        try:
            headers = {
                "Authorization": f"token {self.settings.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            if r.status_code == 200:
                return True, f"Connected as {r.json().get('login')}"
            return False, f"Error: {r.status_code}"
        except Exception as e:
            return False, str(e)

# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL CACHE MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class CacheManager:
    """Manages local file cache for auto-save"""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.cache_dir / "session.json"
        
    def save_to_cache(self, tab_id: str, content: str, metadata: Dict) -> str:
        """Save content to cache, returns cache file path"""
        cache_file = self.cache_dir / f"{tab_id}.txt"
        meta_file = self.cache_dir / f"{tab_id}.meta.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        return str(cache_file)
        
    def load_from_cache(self, tab_id: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Load content from cache"""
        cache_file = self.cache_dir / f"{tab_id}.txt"
        meta_file = self.cache_dir / f"{tab_id}.meta.json"
        
        content = None
        metadata = None
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
        return content, metadata
        
    def delete_from_cache(self, tab_id: str):
        """Delete cached file"""
        cache_file = self.cache_dir / f"{tab_id}.txt"
        meta_file = self.cache_dir / f"{tab_id}.meta.json"
        
        if cache_file.exists():
            cache_file.unlink()
        if meta_file.exists():
            meta_file.unlink()
            
    def save_session(self, tabs: List[Dict]):
        """Save session data"""
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "tabs": tabs
            }, f, indent=2)
            
    def load_session(self) -> List[Dict]:
        """Load session data"""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("tabs", [])
            except:
                pass
        return []
        
    def get_cached_tabs(self) -> List[str]:
        """Get list of cached tab IDs"""
        return [f.stem for f in self.cache_dir.glob("*.txt") if not f.stem.endswith('.meta')]
        
    def cleanup_old_cache(self, active_tabs: List[str]):
        """Remove cache files for tabs that are no longer active"""
        for cache_file in self.cache_dir.glob("*.txt"):
            tab_id = cache_file.stem
            if tab_id not in active_tabs and not cache_file.stem.endswith('.meta'):
                self.delete_from_cache(tab_id)

# ═══════════════════════════════════════════════════════════════════════════════
# CLIPBOARD MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ClipboardManager:
    """Manages clipboard history"""
    
    def __init__(self, max_items: int = MAX_CLIPBOARD_HISTORY):
        self.history: List[str] = []
        self.max_items = max_items
        
    def add(self, text: str):
        if not text or text.isspace():
            return
        if text in self.history:
            self.history.remove(text)
        self.history.insert(0, text)
        self.history = self.history[:self.max_items]
        
    def get_history(self) -> List[str]:
        return self.history.copy()
        
    def clear(self):
        self.history.clear()
        
    def load(self, history: List[str]):
        self.history = history[:self.max_items]

# ═══════════════════════════════════════════════════════════════════════════════
# AI MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class AIManager:
    """Manages AI API calls"""
    
    DEFAULT_PROMPTS = [
        {"name": "Summarize", "prompt": "Summarize the following text concisely:\n\n{text}"},
        {"name": "Improve for Email", "prompt": "Rewrite the following text to sound more professional and suitable for an email:\n\n{text}"},
        {"name": "Organize/Format", "prompt": "Organize and format the following text for better readability:\n\n{text}"},
        {"name": "Fix Grammar", "prompt": "Fix any grammar, spelling, and punctuation errors in the following text:\n\n{text}"},
        {"name": "Simplify", "prompt": "Simplify the following text to make it easier to understand:\n\n{text}"},
        {"name": "Make Formal", "prompt": "Rewrite the following text in a more formal tone:\n\n{text}"},
        {"name": "Make Casual", "prompt": "Rewrite the following text in a more casual, friendly tone:\n\n{text}"},
        {"name": "Expand", "prompt": "Expand on the following text with more detail:\n\n{text}"},
        {"name": "Create Bullet Points", "prompt": "Convert the following text into bullet points:\n\n{text}"},
        {"name": "Explain Code", "prompt": "Explain what the following code does in simple terms:\n\n{text}"},
        {"name": "Add Comments", "prompt": "Add helpful comments to the following code:\n\n{text}"},
    ]
    
    def __init__(self, settings: EditorSettings):
        self.settings = settings
        self.prompts = self.DEFAULT_PROMPTS.copy()
        if settings.ai_custom_prompts:
            self.prompts.extend(settings.ai_custom_prompts)
            
    def add_custom_prompt(self, name: str, prompt: str):
        self.prompts.append({"name": name, "prompt": prompt})
        self.settings.ai_custom_prompts.append({"name": name, "prompt": prompt})
        
    def process_text(self, text: str, prompt_name: str, callback: Callable[[str, str], None]):
        """Process text with AI (runs in background thread)"""
        prompt_template = None
        for p in self.prompts:
            if p["name"] == prompt_name:
                prompt_template = p["prompt"]
                break
        if not prompt_template:
            callback("", f"Prompt '{prompt_name}' not found")
            return
        full_prompt = prompt_template.replace("{text}", text)
        
        def run_ai():
            try:
                result = self._call_api(full_prompt)
                callback(result, "")
            except Exception as e:
                callback("", str(e))
        threading.Thread(target=run_ai, daemon=True).start()
        
    def process_custom(self, text: str, custom_prompt: str, callback: Callable[[str, str], None]):
        """Process text with custom prompt"""
        full_prompt = f"{custom_prompt}\n\n{text}"
        def run_ai():
            try:
                result = self._call_api(full_prompt)
                callback(result, "")
            except Exception as e:
                callback("", str(e))
        threading.Thread(target=run_ai, daemon=True).start()
        
    def _call_api(self, prompt: str) -> str:
        provider = self.settings.ai_provider
        api_key = self.settings.ai_api_key
        model = self.settings.ai_model
        if not provider or not api_key:
            raise ValueError("AI not configured. Go to AI > AI Settings")
        if provider == "openai":
            return self._call_openai(prompt, api_key, model or "gpt-4o-mini")
        elif provider == "anthropic":
            return self._call_anthropic(prompt, api_key, model or "claude-sonnet-4-20250514")
        elif provider == "ollama":
            return self._call_ollama(prompt, model or "llama3.2")
        else:
            raise ValueError(f"Unknown AI provider: {provider}")
            
    def _call_openai(self, prompt: str, api_key: str, model: str) -> str:
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}], max_tokens=2000
        )
        return response.choices[0].message.content
        
    def _call_anthropic(self, prompt: str, api_key: str, model: str) -> str:
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model, max_tokens=2000, messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
        
    def _call_ollama(self, prompt: str, model: str) -> str:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}, timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "")

# ═══════════════════════════════════════════════════════════════════════════════
# UI WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════

class LineNumberCanvas(tk.Canvas):
    """Professional line number display"""
    
    def __init__(self, master, text_widget=None, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.text_font = None
        self.bookmarks = set()
        self.configure(
            bg=THEME.bg_dark,
            highlightthickness=0,
            width=55,
            bd=0
        )
        
    def set_bookmarks(self, bookmarks: List[int]):
        self.bookmarks = set(bookmarks)
        self.redraw()
        
    def toggle_bookmark(self, line: int) -> List[int]:
        if line in self.bookmarks:
            self.bookmarks.discard(line)
        else:
            self.bookmarks.add(line)
        self.redraw()
        return list(self.bookmarks)
        
    def redraw(self):
        self.delete("all")
        if not self.text_widget:
            return
            
        # Get visible lines
        try:
            first_visible = self.text_widget.index("@0,0")
            last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
        except:
            return
            
        first_line = int(first_visible.split(".")[0])
        last_line = int(last_visible.split(".")[0])
        
        font = self.text_font or tkfont.Font(family="JetBrains Mono", size=13)
        line_height = font.metrics("linespace")
        
        for line_num in range(first_line, last_line + 1):
            try:
                bbox = self.text_widget.bbox(f"{line_num}.0")
                if bbox:
                    y = bbox[1]
                    
                    # Bookmark indicator
                    if line_num in self.bookmarks:
                        self.create_oval(
                            4, y + 4, 12, y + 12,
                            fill=THEME.accent_primary,
                            outline=""
                        )
                        
                    # Line number
                    self.create_text(
                        45, y,
                        text=str(line_num),
                        fill=THEME.text_muted,
                        font=font,
                        anchor="ne"
                    )
            except:
                pass
                
        # Right border
        self.create_line(
            self.winfo_width() - 1, 0,
            self.winfo_width() - 1, self.winfo_height(),
            fill=THEME.bg_light
        )


class Minimap(tk.Canvas):
    """Code minimap with viewport indicator"""
    
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.configure(
            bg=THEME.minimap_bg,
            highlightthickness=0,
            width=120
        )
        self.dragging = False
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", lambda e: setattr(self, 'dragging', False))
        
    def _on_click(self, event):
        self.dragging = True
        self._scroll_to_y(event.y)
        
    def _on_drag(self, event):
        if self.dragging:
            self._scroll_to_y(event.y)
            
    def _scroll_to_y(self, y):
        total_lines = int(self.text_widget.index("end-1c").split(".")[0])
        if total_lines <= 1:
            return
        height = self.winfo_height()
        line_ratio = y / height
        target_line = max(1, min(total_lines, int(line_ratio * total_lines)))
        self.text_widget.see(f"{target_line}.0")
        
    def redraw(self):
        self.delete("all")
        
        content = self.text_widget.get("1.0", "end-1c")
        lines = content.split("\n")
        total_lines = len(lines)
        
        if total_lines == 0:
            return
            
        height = self.winfo_height()
        width = self.winfo_width()
        line_height = max(1, height / max(total_lines, 1))
        
        # Draw content preview
        for i, line in enumerate(lines[:500]):  # Limit for performance
            y = i * line_height
            if y > height:
                break
                
            stripped = line.strip()
            if not stripped:
                continue
                
            indent = len(line) - len(line.lstrip())
            text_len = min(len(stripped), 80)
            
            x1 = min(indent * 0.5 + 4, width - 4)
            x2 = min(x1 + text_len * 0.5, width - 4)
            
            # Color based on content
            color = THEME.text_disabled
            if stripped.startswith(("#", "//", "--", "/*", "*")):
                color = THEME.syntax_comment
            elif stripped.startswith(("def ", "function ", "class ", "func ", "fn ")):
                color = THEME.syntax_function
            elif stripped.startswith(("import ", "from ", "require", "use ", "#include")):
                color = THEME.syntax_keyword
                
            self.create_line(x1, y, x2, y, fill=color, width=max(1, line_height * 0.6))
            
        # Viewport indicator
        try:
            first_visible = self.text_widget.index("@0,0")
            last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
            
            first_line = int(first_visible.split(".")[0])
            last_line = int(last_visible.split(".")[0])
            
            y1 = (first_line - 1) * line_height
            y2 = last_line * line_height
            
            self.create_rectangle(
                0, y1, width, y2,
                fill=THEME.minimap_viewport,
                outline=THEME.accent_primary,
                width=1
            )
        except:
            pass


class SyntaxHighlighter:
    """Syntax highlighting engine"""
    
    PATTERNS = {
        "Python": {
            "keyword": r"\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|break|continue|pass|raise|and|or|not|in|is|lambda|global|nonlocal|assert|async|await|True|False|None)\b",
            "string": r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"#.*$",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()",
            "decorator": r"@[a-zA-Z_][a-zA-Z0-9_]*",
            "builtin": r"\b(print|len|range|str|int|float|list|dict|set|tuple|open|file|input|type|isinstance|hasattr|getattr|setattr)\b",
        },
        "JavaScript": {
            "keyword": r"\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|try|catch|finally|throw|new|delete|typeof|instanceof|class|extends|import|export|default|from|async|await|yield|static|get|set|true|false|null|undefined)\b",
            "string": r'(`[\s\S]*?`|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?=\()",
        },
        "HTML": {
            "tags": r"</?[a-zA-Z][a-zA-Z0-9]*",
            "attributes": r'\s([a-zA-Z-]+)(?==)',
            "string": r'"[^"]*"|\'[^\']*\'',
            "comment": r"<!--[\s\S]*?-->",
        },
        "CSS": {
            "selectors": r"[.#]?[a-zA-Z_-][a-zA-Z0-9_-]*(?=\s*[{,])",
            "properties": r"[a-zA-Z-]+(?=\s*:)",
            "values": r":\s*([^;{}]+)",
            "comment": r"/\*[\s\S]*?\*/",
        },
        "JSON": {
            "keys": r'"[^"]+"\s*(?=:)',
            "string": r'"[^"]*"(?!\s*:)',
            "number": r"\b-?\d+\.?\d*\b",
            "keyword": r"\b(true|false|null)\b",
        },
    }
    
    def __init__(self, text_widget: tk.Text, language_ext: str = ".txt"):
        self.text_widget = text_widget
        self.language_ext = language_ext
        self._setup_tags()
        
    def _setup_tags(self):
        """Setup text tags for highlighting"""
        tag_configs = {
            "keyword": THEME.syntax_keyword,
            "string": THEME.syntax_string,
            "comment": THEME.syntax_comment,
            "number": THEME.syntax_number,
            "function": THEME.syntax_function,
            "class": THEME.syntax_class,
            "decorator": THEME.syntax_decorator,
            "builtin": THEME.syntax_builtin,
            "tags": THEME.syntax_function,
            "attributes": THEME.syntax_decorator,
            "selectors": THEME.syntax_function,
            "properties": THEME.syntax_keyword,
            "values": THEME.syntax_string,
            "keys": THEME.syntax_function,
        }
        
        for tag, color in tag_configs.items():
            self.text_widget.tag_configure(tag, foreground=color)
            
    def set_language(self, ext: str):
        self.language_ext = ext
        
    def get_language_name(self) -> str:
        return FILE_EXTENSIONS.get(self.language_ext, "Plain Text")
        
    def highlight_all(self):
        """Highlight entire document"""
        lang_name = self.get_language_name()
        patterns = self.PATTERNS.get(lang_name, {})
        
        # Remove existing tags
        for tag in self.PATTERNS.get(lang_name, {}).keys():
            self.text_widget.tag_remove(tag, "1.0", "end")
            
        if not patterns:
            return
            
        content = self.text_widget.get("1.0", "end-1c")
        
        for tag, pattern in patterns.items():
            try:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    start_idx = f"1.0+{match.start()}c"
                    end_idx = f"1.0+{match.end()}c"
                    self.text_widget.tag_add(tag, start_idx, end_idx)
            except:
                pass


class FileTreeView(ctk.CTkFrame):
    """File explorer sidebar"""
    
    def __init__(self, master, on_file_select: Callable, **kwargs):
        super().__init__(master, fg_color=THEME.bg_dark, **kwargs)
        
        self.on_file_select = on_file_select
        self.current_path: Optional[Path] = None
        self._create_widgets()
        
    def _create_widgets(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=THEME.bg_medium, height=40, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="  EXPLORER",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=THEME.text_secondary,
            anchor="w"
        ).pack(side="left", padx=8, pady=8)
        
        ctk.CTkButton(
            header,
            text="📁",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            command=self._open_folder,
            font=ctk.CTkFont(size=14)
        ).pack(side="right", padx=4)
        
        # Tree container
        tree_container = ctk.CTkFrame(self, fg_color=THEME.bg_dark)
        tree_container.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Pro.Treeview",
            background=THEME.bg_dark,
            foreground=THEME.text_secondary,
            fieldbackground=THEME.bg_dark,
            borderwidth=0,
            rowheight=26,
            font=("Segoe UI", 10)
        )
        style.map(
            "Pro.Treeview",
            background=[("selected", THEME.bg_active)],
            foreground=[("selected", THEME.text_primary)]
        )
        style.layout("Pro.Treeview", [("Pro.Treeview.treearea", {"sticky": "nswe"})])
        
        self.tree = ttk.Treeview(tree_container, style="Pro.Treeview", show="tree", selectmode="browse")
        
        scrollbar = ctk.CTkScrollbar(tree_container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
        
    def _open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.set_root(folder)
            
    def set_root(self, path: str):
        self.current_path = Path(path)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        root_id = self.tree.insert(
            "", "end",
            text=f"📁 {self.current_path.name}",
            values=(str(self.current_path), "folder"),
            open=True
        )
        
        self._populate_directory(root_id, self.current_path)
        
    def _populate_directory(self, parent_id: str, path: Path):
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.name.startswith('.'):
                    continue
                    
                if item.is_dir():
                    folder_id = self.tree.insert(
                        parent_id, "end",
                        text=f"📁 {item.name}",
                        values=(str(item), "folder")
                    )
                    self.tree.insert(folder_id, "end", text="Loading...")
                else:
                    icon = self._get_icon(item.suffix.lower())
                    self.tree.insert(
                        parent_id, "end",
                        text=f"{icon} {item.name}",
                        values=(str(item), "file")
                    )
        except PermissionError:
            pass
            
    def _get_icon(self, ext: str) -> str:
        icons = {
            ".py": "🐍", ".js": "📜", ".ts": "📘", ".html": "🌐",
            ".css": "🎨", ".json": "📋", ".md": "📝", ".txt": "📄",
            ".xml": "📰", ".yaml": "⚙️", ".yml": "⚙️",
            ".png": "🖼️", ".jpg": "🖼️", ".gif": "🖼️", ".svg": "🖼️",
            ".pdf": "📕", ".zip": "📦", ".exe": "⚡",
        }
        return icons.get(ext, "📄")
        
    def _on_expand(self, event):
        item_id = self.tree.focus()
        values = self.tree.item(item_id, "values")
        
        if values and values[1] == "folder":
            children = self.tree.get_children(item_id)
            if children and self.tree.item(children[0], "text") == "Loading...":
                self.tree.delete(children[0])
                self._populate_directory(item_id, Path(values[0]))
                
    def _on_double_click(self, event):
        item_id = self.tree.focus()
        values = self.tree.item(item_id, "values")
        
        if values and values[1] == "file":
            self.on_file_select(values[0])


class FindReplaceBar(ctk.CTkFrame):
    """Professional find/replace bar"""
    
    def __init__(self, master, on_find, on_replace, on_replace_all, on_close, **kwargs):
        super().__init__(master, fg_color=THEME.bg_medium, height=88, corner_radius=0, **kwargs)
        
        self.on_find = on_find
        self.on_replace = on_replace
        self.on_replace_all = on_replace_all
        self.on_close = on_close
        self.state = SearchState()
        
        self.pack_propagate(False)
        self._create_widgets()
        
    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=12, pady=8)
        
        # Find row
        find_frame = ctk.CTkFrame(container, fg_color="transparent")
        find_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            find_frame,
            text="Find:",
            width=70,
            anchor="w",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.find_entry = ctk.CTkEntry(
            find_frame,
            width=350,
            height=32,
            fg_color=THEME.bg_dark,
            border_color=THEME.bg_light,
            border_width=1,
            text_color=THEME.text_primary,
            placeholder_text="Search...",
            font=ctk.CTkFont(size=12)
        )
        self.find_entry.pack(side="left", padx=4)
        self.find_entry.bind("<Return>", lambda e: self._do_find())
        self.find_entry.bind("<Escape>", lambda e: self.on_close())
        
        # Navigation buttons
        btn_style = {
            "width": 32,
            "height": 32,
            "fg_color": THEME.bg_dark,
            "hover_color": THEME.bg_hover,
            "border_width": 1,
            "border_color": THEME.bg_light,
            "font": ctk.CTkFont(size=12)
        }
        
        ctk.CTkButton(find_frame, text="↑", command=lambda: self._do_find(up=True), **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(find_frame, text="↓", command=lambda: self._do_find(up=False), **btn_style).pack(side="left", padx=2)
        
        # Options
        opt_style = {
            "width": 90,
            "height": 28,
            "fg_color": THEME.accent_primary,
            "hover_color": THEME.accent_primary,
            "text_color": THEME.text_primary,
            "font": ctk.CTkFont(size=11)
        }
        
        self.case_var = ctk.BooleanVar()
        ctk.CTkCheckBox(find_frame, text="Aa", variable=self.case_var, **opt_style).pack(side="left", padx=6)
        
        self.word_var = ctk.BooleanVar()
        ctk.CTkCheckBox(find_frame, text="Word", variable=self.word_var, **opt_style).pack(side="left", padx=2)
        
        self.regex_var = ctk.BooleanVar()
        ctk.CTkCheckBox(find_frame, text=".*", variable=self.regex_var, **opt_style).pack(side="left", padx=2)
        
        self.results_label = ctk.CTkLabel(
            find_frame,
            text="",
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=11)
        )
        self.results_label.pack(side="left", padx=12)
        
        ctk.CTkButton(
            find_frame,
            text="✕",
            width=32,
            height=32,
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            text_color=THEME.text_secondary,
            command=self.on_close
        ).pack(side="right")
        
        # Replace row
        replace_frame = ctk.CTkFrame(container, fg_color="transparent")
        replace_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            replace_frame,
            text="Replace:",
            width=70,
            anchor="w",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=12)
        ).pack(side="left")
        
        self.replace_entry = ctk.CTkEntry(
            replace_frame,
            width=350,
            height=32,
            fg_color=THEME.bg_dark,
            border_color=THEME.bg_light,
            border_width=1,
            text_color=THEME.text_primary,
            placeholder_text="Replace with...",
            font=ctk.CTkFont(size=12)
        )
        self.replace_entry.pack(side="left", padx=4)
        
        replace_btn_style = {
            "height": 32,
            "fg_color": THEME.bg_dark,
            "hover_color": THEME.bg_hover,
            "border_width": 1,
            "border_color": THEME.bg_light,
            "font": ctk.CTkFont(size=11)
        }
        
        ctk.CTkButton(replace_frame, text="Replace", width=80, command=self._do_replace, **replace_btn_style).pack(side="left", padx=2)
        ctk.CTkButton(replace_frame, text="Replace All", width=100, command=self._do_replace_all, **replace_btn_style).pack(side="left", padx=2)
        
    def _do_find(self, up=False):
        self.state.find_text = self.find_entry.get()
        self.state.match_case = self.case_var.get()
        self.state.whole_word = self.word_var.get()
        self.state.use_regex = self.regex_var.get()
        self.state.search_up = up
        
        result = self.on_find(self.state)
        if result:
            self.results_label.configure(text=result)
            
    def _do_replace(self):
        self.state.replace_text = self.replace_entry.get()
        self._do_find()
        self.on_replace(self.state)
        
    def _do_replace_all(self):
        self.state.find_text = self.find_entry.get()
        self.state.replace_text = self.replace_entry.get()
        self.state.match_case = self.case_var.get()
        self.state.whole_word = self.word_var.get()
        self.state.use_regex = self.regex_var.get()
        
        result = self.on_replace_all(self.state)
        if result:
            self.results_label.configure(text=result)
            
    def focus_find(self):
        self.find_entry.focus_set()
        self.find_entry.select_range(0, "end")
        
    def set_find_text(self, text: str):
        self.find_entry.delete(0, "end")
        self.find_entry.insert(0, text)


class SyncStatusIndicator(ctk.CTkFrame):
    """Cloud sync status indicator"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.status_icon = ctk.CTkLabel(
            self,
            text="○",
            font=ctk.CTkFont(size=10),
            text_color=THEME.text_muted,
            width=16
        )
        self.status_icon.pack(side="left")
        
        self.status_label = ctk.CTkLabel(
            self,
            text="Local",
            font=ctk.CTkFont(size=10),
            text_color=THEME.text_muted
        )
        self.status_label.pack(side="left", padx=2)
        
    def set_status(self, status: str, message: str = ""):
        """Update sync status indicator"""
        if status == "synced":
            self.status_icon.configure(text="●", text_color=THEME.status_synced)
            self.status_label.configure(text="Synced", text_color=THEME.status_synced)
        elif status == "syncing":
            self.status_icon.configure(text="◐", text_color=THEME.status_syncing)
            self.status_label.configure(text="Syncing...", text_color=THEME.status_syncing)
        elif status == "error":
            self.status_icon.configure(text="●", text_color=THEME.status_error)
            self.status_label.configure(text="Sync Error", text_color=THEME.status_error)
        elif status == "modified":
            self.status_icon.configure(text="●", text_color=THEME.status_modified)
            self.status_label.configure(text="Modified", text_color=THEME.status_modified)
        else:
            self.status_icon.configure(text="○", text_color=THEME.text_muted)
            self.status_label.configure(text="Local", text_color=THEME.text_muted)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class Mattpad(ctk.CTk):
    """Professional-grade text editor with auto-save and cloud sync"""
    
    AUTO_CLOSE_PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'", "`": "`"}
    BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}", "<": ">"}
    CLOSE_BRACKETS = {")": "(", "]": "[", "}": "{", ">": "<"}
    
    def __init__(self):
        super().__init__()
        
        # Core state
        self.settings = EditorSettings()
        self.tabs: Dict[str, TabData] = {}
        self.current_tab: Optional[str] = None
        self.text_widgets: Dict[str, tk.Text] = {}
        self.line_numbers: Dict[str, LineNumberCanvas] = {}
        self.minimaps: Dict[str, Minimap] = {}
        self.highlighters: Dict[str, SyntaxHighlighter] = {}
        self.editor_frames: Dict[str, ctk.CTkFrame] = {}
        self.find_bar_visible = False
        
        # Drag state for tabs
        self.drag_data = {"tab_id": None, "start_x": 0}
        
        # Auto-scroll (middle mouse button) state
        self.auto_scroll_data = {
            "active": False,
            "start_y": 0,
            "current_y": 0,
            "widget": None,
            "job": None
        }
        
        # File change tracking
        self.file_mtimes: Dict[str, float] = {}
        
        # Load settings first
        self._load_settings()
        
        # Apply theme from settings
        global THEME
        THEME = THEMES.get(self.settings.theme_name, THEMES["GitHub Dark"])
        
        # Managers
        self.cache_manager = CacheManager()
        self.cloud_sync = CloudSyncManager(self.settings)
        self.clipboard_manager = ClipboardManager()
        self.clipboard_manager.load(self.settings.clipboard_history)
        self.ai_manager = AIManager(self.settings)
        
        # Timers
        self.auto_save_job = None
        self.cloud_sync_job = None
        self.file_check_job = None
        
        # Configure window
        self.title("Mattpad")
        self.configure(fg_color=THEME.bg_darkest)
        
        # Set window icon
        icon_path = get_icon_path()
        if icon_path:
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        # Start maximized (full screen)
        try:
            self.state('zoomed')  # Windows
        except:
            try:
                self.attributes('-zoomed', True)  # Linux
            except:
                self.geometry(self.settings.window_geometry)
        
        # Enable dark title bar on Windows
        self.after(100, lambda: set_dark_title_bar(self))
        
        # Build UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_statusbar()
        self._bind_shortcuts()
        
        # Restore session or create new tab
        self._restore_session()
        
        # Start timers
        self._start_auto_save()
        self._start_cloud_sync()
        self._start_file_check()
        
        # Handle close without prompts
        self.protocol("WM_DELETE_WINDOW", self._on_close_no_prompt)
        
    # ═══════════════════════════════════════════════════════════════════════════
    # SETTINGS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _load_settings(self):
        """Load settings from file"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                for key, value in data.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
                        
                # Apply cloud settings
                if self.settings.github_token:
                    self.cloud_sync.configure_github(
                        self.settings.github_token,
                        self.settings.github_repo,
                        self.settings.github_branch,
                        self.settings.github_path
                    )
            except:
                pass
                
    def _save_settings(self):
        """Save settings to file"""
        try:
            self.settings.clipboard_history = self.clipboard_manager.get_history()[:20]
            data = {
                "font_family": self.settings.font_family,
                "font_size": self.settings.font_size,
                "tab_size": self.settings.tab_size,
                "use_spaces": self.settings.use_spaces,
                "word_wrap": self.settings.word_wrap,
                "show_line_numbers": self.settings.show_line_numbers,
                "show_minimap": self.settings.show_minimap,
                "sidebar_visible": self.settings.sidebar_visible,
                "window_geometry": self.geometry(),
                "theme_name": self.settings.theme_name,
                "ui_scale": self.settings.ui_scale,
                "default_extension": self.settings.default_extension,
                "cloud_sync_enabled": self.settings.cloud_sync_enabled,
                "sync_provider": self.settings.sync_provider,
                "github_token": self.settings.github_token,
                "github_repo": self.settings.github_repo,
                "github_branch": self.settings.github_branch,
                "github_path": self.settings.github_path,
                "gdrive_folder_id": self.settings.gdrive_folder_id,
                "ai_provider": self.settings.ai_provider,
                "ai_api_key": self.settings.ai_api_key,
                "ai_model": self.settings.ai_model,
                "ai_custom_prompts": self.settings.ai_custom_prompts,
                "recent_files": self.settings.recent_files[:MAX_RECENT_FILES],
                "clipboard_history": self.settings.clipboard_history,
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
            
    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _restore_session(self):
        """Restore previous session from cache"""
        session_tabs = self.cache_manager.load_session()
        
        if session_tabs:
            for tab_info in session_tabs:
                tab_id = tab_info.get("tab_id")
                if tab_id:
                    content, metadata = self.cache_manager.load_from_cache(tab_id)
                    if content is not None:
                        self._create_tab(
                            filepath=tab_info.get("filepath"),
                            content=content,
                            tab_id=tab_id
                        )
        
        if not self.tabs:
            self._new_file()
            
    def _save_session(self):
        """Save current session to cache"""
        session_tabs = []
        
        for tab_id, tab_data in self.tabs.items():
            # Save content to cache
            if tab_id in self.text_widgets:
                content = self.text_widgets[tab_id].get("1.0", "end-1c")
                metadata = {
                    "filepath": tab_data.filepath,
                    "language": tab_data.language,
                    "cursor_pos": tab_data.cursor_pos,
                    "remote_path": tab_data.remote_path,
                    "remote_type": tab_data.remote_type,
                }
                self.cache_manager.save_to_cache(tab_id, content, metadata)
                
            session_tabs.append({
                "tab_id": tab_id,
                "filepath": tab_data.filepath,
            })
            
        self.cache_manager.save_session(session_tabs)
        
    # ═══════════════════════════════════════════════════════════════════════════
    # AUTO-SAVE AND CLOUD SYNC
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _start_auto_save(self):
        """Start auto-save timer"""
        self._do_auto_save()
        
    def _do_auto_save(self):
        """Auto-save all tabs to local cache"""
        self._save_session()
        self.auto_save_job = self.after(LOCAL_SAVE_INTERVAL * 1000, self._do_auto_save)
        
    def _start_cloud_sync(self):
        """Start cloud sync timer"""
        if self.settings.cloud_sync_enabled:
            self._do_cloud_sync()
        else:
            self.cloud_sync_job = self.after(SYNC_INTERVAL * 1000, self._start_cloud_sync)
            
    def _do_cloud_sync(self):
        """Sync all tabs to cloud"""
        if not self.settings.cloud_sync_enabled:
            self.cloud_sync_job = self.after(SYNC_INTERVAL * 1000, self._do_cloud_sync)
            return
            
        # Update status
        self.sync_indicator.set_status("syncing")
        
        def sync_all():
            success_count = 0
            error_count = 0
            
            for tab_id, tab_data in self.tabs.items():
                if tab_id in self.text_widgets:
                    content = self.text_widgets[tab_id].get("1.0", "end-1c")
                    tab_data.sync_status = "syncing"
                    
                    success, msg = self.cloud_sync.sync_file(tab_data, content)
                    
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        
            # Update UI on main thread
            self.after(0, lambda: self._sync_complete(success_count, error_count))
            
        # Run sync in background thread
        threading.Thread(target=sync_all, daemon=True).start()
        
        # Schedule next sync
        self.cloud_sync_job = self.after(SYNC_INTERVAL * 1000, self._do_cloud_sync)
        
    def _sync_complete(self, success: int, errors: int):
        """Handle sync completion"""
        if errors > 0:
            self.sync_indicator.set_status("error")
            self.status_label.configure(text=f"Sync completed with {errors} error(s)")
        elif success > 0:
            self.sync_indicator.set_status("synced")
            self.status_label.configure(text=f"Synced {success} file(s)")
        else:
            self.sync_indicator.set_status("local")
            
    def _sync_now(self):
        """Trigger immediate sync"""
        if self.cloud_sync_job:
            self.after_cancel(self.cloud_sync_job)
        self._do_cloud_sync()
        
    def _start_file_check(self):
        """Start file change detection timer"""
        self._check_file_changes()
        
    def _check_file_changes(self):
        """Check for external file changes"""
        for tab_id, tab_data in list(self.tabs.items()):
            if tab_data.filepath and os.path.exists(tab_data.filepath):
                current_mtime = os.path.getmtime(tab_data.filepath)
                stored_mtime = self.file_mtimes.get(tab_data.filepath, 0)
                if stored_mtime > 0 and current_mtime > stored_mtime:
                    self._prompt_reload(tab_id, tab_data.filepath)
                self.file_mtimes[tab_data.filepath] = current_mtime
        self.file_check_job = self.after(2000, self._check_file_changes)
        
    def _prompt_reload(self, tab_id: str, filepath: str):
        """Prompt user to reload changed file"""
        filename = os.path.basename(filepath)
        result = messagebox.askyesno(
            "File Changed",
            f"'{filename}' has been modified outside the editor.\n\nReload?",
            icon="question"
        )
        if result:
            self._reload_file(tab_id)
            
    def _reload_file(self, tab_id: str):
        """Reload file content"""
        if tab_id not in self.tabs:
            return
        tab_data = self.tabs[tab_id]
        if not tab_data.filepath or not os.path.exists(tab_data.filepath):
            return
        try:
            with open(tab_data.filepath, 'r', encoding=tab_data.encoding) as f:
                content = f.read()
            text_widget = self.text_widgets[tab_id]
            cursor_pos = text_widget.index("insert")
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", content)
            try:
                text_widget.mark_set("insert", cursor_pos)
            except:
                pass
            tab_data.content_hash = hashlib.md5(content.encode()).hexdigest()
            tab_data.modified = False
            self.file_mtimes[tab_data.filepath] = os.path.getmtime(tab_data.filepath)
            if tab_data.tab_frame:
                tab_data.tab_frame.modified_label.configure(text="")
            self._highlight_all(tab_id)
            self.status_label.configure(text=f"Reloaded: {os.path.basename(tab_data.filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload: {e}")
            
    def _update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.delete(0, "end")
        for filepath in self.settings.recent_files[:MAX_RECENT_FILES]:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                self.recent_menu.add_command(label=filename, command=lambda f=filepath: self._open_file(f))
        if self.settings.recent_files:
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Clear Recent Files", command=self._clear_recent_files)
            
    def _clear_recent_files(self):
        """Clear recent files list"""
        self.settings.recent_files.clear()
        self._update_recent_menu()
        self._save_settings()
        
    def _open_folder(self):
        """Open folder in sidebar"""
        folder = filedialog.askdirectory()
        if folder:
            self.sidebar.set_root(folder)
            if not self.settings.sidebar_visible:
                self._toggle_sidebar()
        
    # ═══════════════════════════════════════════════════════════════════════════
    # UI CREATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _create_menu(self):
        """Create menu bar"""
        self.menu_bar = tk.Menu(self, bg=THEME.bg_dark, fg=THEME.text_primary,
                                 activebackground=THEME.bg_hover, activeforeground=THEME.text_primary,
                                 borderwidth=0, relief="flat")
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                            activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        file_menu.add_command(label="New                    Ctrl+N", command=self._new_file)
        file_menu.add_command(label="Open                   Ctrl+O", command=self._open_file)
        file_menu.add_command(label="Open Folder...", command=self._open_folder)
        file_menu.add_separator()
        
        # Recent Files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                                   activebackground=THEME.bg_hover)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Save                   Ctrl+S", command=self._save_file)
        file_menu.add_command(label="Save As          Ctrl+Shift+S", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab              Ctrl+W", command=self._close_current_tab)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                            activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        edit_menu.add_command(label="Undo                   Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo                   Ctrl+Y", command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut                    Ctrl+X", command=self._cut)
        edit_menu.add_command(label="Copy                   Ctrl+C", command=self._copy)
        edit_menu.add_command(label="Paste                  Ctrl+V", command=self._paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find                   Ctrl+F", command=self._show_find_bar)
        edit_menu.add_command(label="Find in Files    Ctrl+Shift+F", command=self._show_find_in_files)
        edit_menu.add_command(label="Go to Line             Ctrl+G", command=self._goto_line)
        edit_menu.add_separator()
        edit_menu.add_command(label="Clipboard History Ctrl+Shift+V", command=self._show_clipboard_history)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                            activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        
        # Themes submenu
        themes_menu = tk.Menu(view_menu, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                              activebackground=THEME.bg_hover)
        for theme_name in THEMES.keys():
            themes_menu.add_command(label=theme_name, command=lambda t=theme_name: self._change_theme(t))
        view_menu.add_cascade(label="Theme", menu=themes_menu)
        view_menu.add_separator()
        
        self.word_wrap_var = tk.BooleanVar(value=self.settings.word_wrap)
        view_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap_var, command=self._toggle_word_wrap)
        
        self.line_numbers_var = tk.BooleanVar(value=self.settings.show_line_numbers)
        view_menu.add_checkbutton(label="Line Numbers", variable=self.line_numbers_var, command=self._toggle_line_numbers)
        
        self.minimap_var = tk.BooleanVar(value=self.settings.show_minimap)
        view_menu.add_checkbutton(label="Minimap", variable=self.minimap_var, command=self._toggle_minimap)
        
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In               Ctrl++", command=self._zoom_in)
        view_menu.add_command(label="Zoom Out              Ctrl+-", command=self._zoom_out)
        view_menu.add_command(label="Reset Zoom            Ctrl+0", command=self._zoom_reset)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Sidebar         Ctrl+B", command=self._toggle_sidebar)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # AI menu
        ai_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                          activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        ai_menu.add_command(label="AI Settings...", command=self._show_ai_settings)
        ai_menu.add_separator()
        for prompt in AIManager.DEFAULT_PROMPTS[:8]:
            ai_menu.add_command(label=prompt["name"], command=lambda p=prompt["name"]: self._ai_action(p))
        ai_menu.add_separator()
        ai_menu.add_command(label="Custom Prompt...", command=self._ai_custom_prompt)
        self.menu_bar.add_cascade(label="AI", menu=ai_menu)
        
        # Cloud menu
        cloud_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                             activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        cloud_menu.add_command(label="Configure GitHub...", command=self._configure_github)
        cloud_menu.add_command(label="Configure Google Drive...", command=self._configure_gdrive)
        cloud_menu.add_separator()
        cloud_menu.add_command(label="Sync Now", command=self._sync_now)
        cloud_menu.add_command(label="Sync Status...", command=self._show_sync_status)
        self.menu_bar.add_cascade(label="Cloud", menu=cloud_menu)
        
        # Options menu
        options_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                               activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        
        # UI Scale submenu
        scale_menu = tk.Menu(options_menu, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                             activebackground=THEME.bg_hover)
        for scale_val, scale_name in [(1.0, "100% (Normal)"), (1.25, "125%"), (1.5, "150%"), (1.75, "175%"), (2.0, "200%")]:
            scale_menu.add_command(label=scale_name, command=lambda s=scale_val: self._set_ui_scale(s))
        options_menu.add_cascade(label="UI Scale", menu=scale_menu)
        
        # Default Extension submenu
        ext_menu = tk.Menu(options_menu, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                           activebackground=THEME.bg_hover)
        for ext in [".ps1", ".bat", ".py", ".js", ".txt", ".md", ".json", ".html", ".css"]:
            ext_menu.add_command(label=ext, command=lambda e=ext: self._set_default_extension(e))
        options_menu.add_cascade(label="Default Save Extension", menu=ext_menu)
        
        options_menu.add_separator()
        options_menu.add_command(label="Preferences...", command=self._show_preferences)
        self.menu_bar.add_cascade(label="Options", menu=options_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                            activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.configure(menu=self.menu_bar)
        
    def _create_toolbar(self):
        """Create toolbar"""
        scale = self.settings.ui_scale
        self.toolbar = ctk.CTkFrame(self, fg_color=THEME.bg_medium, height=int(44 * scale), corner_radius=0)
        self.toolbar.pack(fill="x")
        self.toolbar.pack_propagate(False)
        
        # Left toolbar buttons
        left_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        left_frame.pack(side="left", padx=int(8 * scale), pady=int(6 * scale))
        
        btn_style = {
            "width": int(32 * scale),
            "height": int(32 * scale),
            "fg_color": "transparent",
            "hover_color": THEME.bg_hover,
            "font": ctk.CTkFont(size=int(14 * scale))
        }
        
        buttons = [
            ("📄", "New (Ctrl+N)", self._new_file),
            ("📂", "Open (Ctrl+O)", self._open_file),
            ("💾", "Save (Ctrl+S)", self._save_file),
            (None, None, None),  # Separator
            ("↩️", "Undo (Ctrl+Z)", self._undo),
            ("↪️", "Redo (Ctrl+Y)", self._redo),
            (None, None, None),
            ("🔍", "Find (Ctrl+F)", self._show_find_bar),
        ]
        
        for icon, tooltip, command in buttons:
            if icon is None:
                sep = ctk.CTkFrame(left_frame, width=1, height=int(24 * scale), fg_color=THEME.bg_light)
                sep.pack(side="left", padx=int(8 * scale))
            else:
                btn = ctk.CTkButton(left_frame, text=icon, command=command, **btn_style)
                btn.pack(side="left", padx=2)
                
        # Right toolbar - sync status
        right_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        right_frame.pack(side="right", padx=int(12 * scale), pady=int(6 * scale))
        
        self.sync_indicator = SyncStatusIndicator(right_frame)
        self.sync_indicator.pack(side="right")
        
        ctk.CTkButton(
            right_frame,
            text="☁️",
            width=int(32 * scale),
            height=int(32 * scale),
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            command=self._sync_now,
            font=ctk.CTkFont(size=int(14 * scale))
        ).pack(side="right", padx=4)
        
    def _create_main_layout(self):
        """Create main layout"""
        self.main_container = ctk.CTkFrame(self, fg_color=THEME.bg_darkest, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar = FileTreeView(
            self.main_container,
            on_file_select=self._open_file,
            width=self.settings.sidebar_width
        )
        if self.settings.sidebar_visible:
            self.sidebar.pack(side="left", fill="y")
            
        # Editor container
        self.editor_container = ctk.CTkFrame(self.main_container, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_container.pack(side="left", fill="both", expand=True)
        
        # Tab bar
        self.tab_bar = ctk.CTkFrame(self.editor_container, fg_color=THEME.tab_inactive, height=int(38 * self.settings.ui_scale), corner_radius=0)
        self.tab_bar.pack(fill="x")
        self.tab_bar.pack_propagate(False)
        
        self.tab_container = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.tab_container.pack(side="left", fill="both", expand=True)
        
        # Click on empty tab bar area to create new tab
        self.tab_container.bind("<Button-1>", lambda e: self._new_file())
        self.tab_bar.bind("<Button-1>", lambda e: self._new_file())
        
        ctk.CTkButton(
            self.tab_bar,
            text="+",
            width=int(32 * self.settings.ui_scale),
            height=int(28 * self.settings.ui_scale),
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            text_color=THEME.text_secondary,
            command=self._new_file,
            font=ctk.CTkFont(size=int(16 * self.settings.ui_scale))
        ).pack(side="right", padx=4, pady=4)
        
        # Find bar (hidden)
        self.find_bar = FindReplaceBar(
            self.editor_container,
            on_find=self._do_find,
            on_replace=self._do_replace,
            on_replace_all=self._do_replace_all,
            on_close=self._hide_find_bar
        )
        
        # Editor frame
        self.editor_frame = ctk.CTkFrame(self.editor_container, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_frame.pack(fill="both", expand=True)
        
    def _create_statusbar(self):
        """Create status bar"""
        scale = self.settings.ui_scale
        self.statusbar = ctk.CTkFrame(self, fg_color=THEME.bg_medium, height=int(26 * scale), corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        # Left - status message
        left_frame = ctk.CTkFrame(self.statusbar, fg_color="transparent")
        left_frame.pack(side="left", fill="y")
        
        self.status_label = ctk.CTkLabel(
            left_frame,
            text="Ready",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(11 * scale)),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=int(12 * scale), pady=int(4 * scale))
        
        # Right - position info
        right_frame = ctk.CTkFrame(self.statusbar, fg_color="transparent")
        right_frame.pack(side="right", fill="y")
        
        self.language_label = ctk.CTkLabel(
            right_frame,
            text="Plain Text",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(11 * scale))
        )
        self.language_label.pack(side="right", padx=int(12 * scale), pady=int(4 * scale))
        
        ctk.CTkFrame(right_frame, width=1, height=int(16 * scale), fg_color=THEME.bg_light).pack(side="right", padx=int(4 * scale))
        
        self.encoding_label = ctk.CTkLabel(
            right_frame,
            text="UTF-8",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(11 * scale))
        )
        self.encoding_label.pack(side="right", padx=int(8 * scale), pady=int(4 * scale))
        
        ctk.CTkFrame(right_frame, width=1, height=int(16 * scale), fg_color=THEME.bg_light).pack(side="right", padx=int(4 * scale))
        
        self.position_label = ctk.CTkLabel(
            right_frame,
            text="Ln 1, Col 1",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(11 * scale)),
            width=int(100 * scale)
        )
        self.position_label.pack(side="right", pady=int(4 * scale))
        
        ctk.CTkFrame(right_frame, width=1, height=int(16 * scale), fg_color=THEME.bg_light).pack(side="right", padx=int(4 * scale))
        
        self.zoom_label = ctk.CTkLabel(
            right_frame,
            text="100%",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=11),
            width=50
        )
        self.zoom_label.pack(side="right", pady=4)
        
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.bind("<Control-n>", lambda e: self._new_file())
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-s>", lambda e: self._save_file())
        self.bind("<Control-Shift-S>", lambda e: self._save_file_as())
        self.bind("<Control-w>", lambda e: self._close_current_tab())
        self.bind("<Control-f>", lambda e: self._show_find_bar())
        self.bind("<Control-Shift-F>", lambda e: self._show_find_in_files())
        self.bind("<Control-h>", lambda e: self._show_find_bar())
        self.bind("<Control-g>", lambda e: self._goto_line())
        self.bind("<Control-Shift-V>", lambda e: self._show_clipboard_history())
        self.bind("<F3>", lambda e: self._find_next())
        self.bind("<Shift-F3>", lambda e: self._find_prev())
        self.bind("<Control-plus>", lambda e: self._zoom_in())
        self.bind("<Control-equal>", lambda e: self._zoom_in())
        self.bind("<Control-minus>", lambda e: self._zoom_out())
        self.bind("<Control-0>", lambda e: self._zoom_reset())
        self.bind("<Control-b>", lambda e: self._toggle_sidebar())
        self.bind("<Escape>", lambda e: self._hide_find_bar())
        self.bind("<Control-d>", lambda e: self._duplicate_line())
        self.bind("<Control-slash>", lambda e: self._toggle_comment())
        
    # ═══════════════════════════════════════════════════════════════════════════
    # TAB MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _create_tab(self, filepath: Optional[str] = None, content: str = "", tab_id: Optional[str] = None) -> str:
        """Create a new editor tab"""
        import uuid
        tab_id = tab_id or str(uuid.uuid4())
        
        # Determine language
        if filepath:
            ext = Path(filepath).suffix.lower()
            language = FILE_EXTENSIONS.get(ext, "Plain Text")
        else:
            ext = ".txt"
            language = "Plain Text"
            
        # Create tab data
        self.tabs[tab_id] = TabData(
            tab_id=tab_id,
            filepath=filepath,
            language=language,
            content_hash=hashlib.md5(content.encode()).hexdigest()
        )
        
        # Create editor frame
        editor_frame = ctk.CTkFrame(self.editor_frame, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_frames[tab_id] = editor_frame
        
        # Text container
        text_container = ctk.CTkFrame(editor_frame, fg_color=THEME.bg_darkest, corner_radius=0)
        text_container.pack(fill="both", expand=True)
        
        # Line numbers
        line_canvas = LineNumberCanvas(text_container)
        if self.settings.show_line_numbers:
            line_canvas.pack(side="left", fill="y")
            
        # Text widget
        text_widget = tk.Text(
            text_container,
            bg=THEME.bg_darkest,
            fg=THEME.text_primary,
            insertbackground=THEME.accent_primary,
            insertwidth=2,
            selectbackground=THEME.selection_bg,
            selectforeground=THEME.text_primary,
            font=(self.settings.font_family, self.settings.font_size),
            wrap="none" if not self.settings.word_wrap else "word",
            undo=True,
            maxundo=-1,
            autoseparators=True,
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=8,
            tabs=(f"{self.settings.tab_size * 8}p",)
        )
        text_widget.pack(side="left", fill="both", expand=True)
        
        # Link line numbers
        line_canvas.text_widget = text_widget
        line_canvas.text_font = tkfont.Font(family=self.settings.font_family, size=self.settings.font_size)
        
        # Minimap
        minimap = Minimap(text_container, text_widget, width=self.settings.minimap_width)
        if self.settings.show_minimap:
            minimap.pack(side="right", fill="y")
            
        # Scrollbars
        v_scrollbar = ctk.CTkScrollbar(text_container, command=text_widget.yview)
        v_scrollbar.pack(side="right", fill="y")
        
        h_scrollbar = ctk.CTkScrollbar(editor_frame, command=text_widget.xview, orientation="horizontal")
        if not self.settings.word_wrap:
            h_scrollbar.pack(side="bottom", fill="x")
            
        text_widget.configure(
            yscrollcommand=lambda *args: self._on_scroll(v_scrollbar, line_canvas, minimap, *args),
            xscrollcommand=h_scrollbar.set
        )
        
        text_widget.tag_configure("current_line", background=THEME.current_line)
        text_widget.tag_configure("bracket_match", background=THEME.bracket_match)
        text_widget.tag_configure("search_highlight", background=THEME.search_highlight)
        text_widget.tag_configure("search_current", background=THEME.accent_primary)
        
        highlighter = SyntaxHighlighter(text_widget, ext)
        
        if content:
            text_widget.insert("1.0", content)
            text_widget.edit_reset()
            text_widget.edit_modified(False)
            
        # Bind events
        text_widget.bind("<KeyRelease>", lambda e: self._on_text_changed(tab_id))
        text_widget.bind("<ButtonRelease-1>", lambda e: self._update_cursor_position(tab_id))
        text_widget.bind("<KeyRelease>", lambda e: self._update_cursor_position(tab_id), add=True)
        text_widget.bind("<Tab>", lambda e: self._handle_tab(tab_id, e))
        text_widget.bind("<Return>", lambda e: self._handle_return(tab_id, e))
        text_widget.bind("<Key>", lambda e: self._handle_key(tab_id, e))
        
        # Update line numbers on any key press for instant feedback
        text_widget.bind("<KeyPress>", lambda e: self.after(1, lambda: self._update_line_numbers(tab_id)), add=True)
        text_widget.bind("<Configure>", lambda e: self._update_line_numbers(tab_id), add=True)
        
        # Middle mouse button auto-scroll (like browser)
        text_widget.bind("<Button-2>", lambda e: self._start_auto_scroll(e, text_widget))
        text_widget.bind("<ButtonRelease-2>", lambda e: self._stop_auto_scroll())
        text_widget.bind("<Motion>", lambda e: self._update_auto_scroll(e), add=True)
        
        # Right-click context menu with AI
        self._create_context_menu(text_widget, tab_id)
        
        # Store references
        self.text_widgets[tab_id] = text_widget
        self.line_numbers[tab_id] = line_canvas
        self.minimaps[tab_id] = minimap
        self.highlighters[tab_id] = highlighter
        editor_frame.h_scrollbar = h_scrollbar
        editor_frame.v_scrollbar = v_scrollbar
        
        self._create_tab_button(tab_id)
        self.after(100, lambda: self._highlight_all(tab_id))
        self._switch_to_tab(tab_id)
        
        return tab_id
        
    def _create_tab_button(self, tab_id: str):
        """Create tab button with drag-and-drop support"""
        tab_data = self.tabs[tab_id]
        scale = self.settings.ui_scale
        
        if tab_data.filepath:
            display_name = os.path.basename(tab_data.filepath)
        else:
            display_name = "Untitled"
            
        tab_frame = ctk.CTkFrame(self.tab_container, fg_color=THEME.tab_inactive, corner_radius=0, height=int(32 * scale))
        tab_frame.pack(side="left", padx=0, pady=int(4 * scale))
        tab_frame.pack_propagate(False)
        
        # Modified indicator
        modified_label = ctk.CTkLabel(
            tab_frame,
            text="",
            width=int(10 * scale),
            text_color=THEME.tab_modified,
            font=ctk.CTkFont(size=int(10 * scale))
        )
        modified_label.pack(side="left", padx=(int(8 * scale), 0))
        tab_frame.modified_label = modified_label
        
        # Tab label
        tab_label = ctk.CTkLabel(
            tab_frame,
            text=display_name,
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(11 * scale)),
            cursor="hand2"
        )
        tab_label.pack(side="left", padx=int(4 * scale), pady=int(4 * scale))
        tab_frame.label = tab_label
        
        # Close button
        close_btn = ctk.CTkButton(
            tab_frame,
            text="×",
            width=int(22 * scale),
            height=int(22 * scale),
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            text_color=THEME.text_muted,
            command=lambda: self._close_tab(tab_id),
            font=ctk.CTkFont(size=int(12 * scale))
        )
        close_btn.pack(side="right", padx=(0, int(4 * scale)))
        
        # Drag and drop handlers
        tab_label.bind("<Button-1>", lambda e: self._start_tab_drag(tab_id, e))
        tab_frame.bind("<Button-1>", lambda e: self._start_tab_drag(tab_id, e))
        tab_label.bind("<B1-Motion>", lambda e: self._on_tab_drag(tab_id, e))
        tab_frame.bind("<B1-Motion>", lambda e: self._on_tab_drag(tab_id, e))
        tab_label.bind("<ButtonRelease-1>", lambda e: self._end_tab_drag(tab_id, e))
        tab_frame.bind("<ButtonRelease-1>", lambda e: self._end_tab_drag(tab_id, e))
        
        # Middle-click to close
        tab_label.bind("<Button-2>", lambda e: self._close_tab_no_prompt(tab_id))
        tab_frame.bind("<Button-2>", lambda e: self._close_tab_no_prompt(tab_id))
        
        self.tabs[tab_id].tab_frame = tab_frame
        
    def _start_tab_drag(self, tab_id: str, event):
        """Start tab drag"""
        self.drag_data["tab_id"] = tab_id
        self.drag_data["start_x"] = event.x_root
        self._switch_to_tab(tab_id)
        
    def _on_tab_drag(self, tab_id: str, event):
        """Handle tab dragging"""
        if self.drag_data["tab_id"] != tab_id:
            return
        tab_frame = self.tabs[tab_id].tab_frame
        if not tab_frame:
            return
            
        # Get all tab frames in order
        tab_frames = [(tid, self.tabs[tid].tab_frame) for tid in self.tabs if self.tabs[tid].tab_frame]
        tab_frames.sort(key=lambda x: x[1].winfo_x())
        current_index = next((i for i, (tid, _) in enumerate(tab_frames) if tid == tab_id), 0)
        
        # Check if we should swap with another tab
        for i, (other_id, other_frame) in enumerate(tab_frames):
            if other_id == tab_id:
                continue
            other_x = other_frame.winfo_x()
            other_width = other_frame.winfo_width()
            mouse_x = event.x_root - self.tab_container.winfo_rootx()
            
            if other_x < mouse_x < other_x + other_width:
                if i < current_index:
                    tab_frame.pack_forget()
                    tab_frame.pack(side="left", before=other_frame, padx=0, pady=4)
                elif i > current_index:
                    tab_frame.pack_forget()
                    tab_frame.pack(side="left", after=other_frame, padx=0, pady=4)
                break
                
    def _end_tab_drag(self, tab_id: str, event):
        """End tab drag"""
        self.drag_data["tab_id"] = None
        
    def _create_context_menu(self, text_widget: tk.Text, tab_id: str):
        """Create right-click context menu with AI options"""
        context_menu = tk.Menu(text_widget, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                               activebackground=THEME.bg_hover, activeforeground=THEME.text_primary)
        
        context_menu.add_command(label="Cut", command=self._cut)
        context_menu.add_command(label="Copy", command=self._copy)
        context_menu.add_command(label="Paste", command=self._paste)
        context_menu.add_separator()
        
        # AI submenu
        ai_menu = tk.Menu(context_menu, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary,
                          activebackground=THEME.bg_hover)
        for prompt in AIManager.DEFAULT_PROMPTS:
            ai_menu.add_command(label=prompt["name"], command=lambda p=prompt["name"]: self._ai_action(p))
        ai_menu.add_separator()
        ai_menu.add_command(label="Custom Prompt...", command=self._ai_custom_prompt)
        context_menu.add_cascade(label="🤖 AI", menu=ai_menu)
        
        context_menu.add_separator()
        context_menu.add_command(label="Select All", command=lambda: text_widget.tag_add("sel", "1.0", "end"))
        
        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
                
        text_widget.bind("<Button-3>", show_context_menu)
        
    def _switch_to_tab(self, tab_id: str):
        """Switch to a tab"""
        if tab_id not in self.tabs:
            return
            
        # Hide current tab
        if self.current_tab and self.current_tab in self.editor_frames:
            self.editor_frames[self.current_tab].pack_forget()
            if self.tabs[self.current_tab].tab_frame:
                self.tabs[self.current_tab].tab_frame.configure(fg_color=THEME.tab_inactive)
                self.tabs[self.current_tab].tab_frame.label.configure(text_color=THEME.text_secondary)
                
        # Show new tab
        if tab_id in self.editor_frames:
            self.editor_frames[tab_id].pack(fill="both", expand=True)
            
        if self.tabs[tab_id].tab_frame:
            self.tabs[tab_id].tab_frame.configure(fg_color=THEME.tab_active)
            self.tabs[tab_id].tab_frame.label.configure(text_color=THEME.text_primary)
            
        self.current_tab = tab_id
        self._update_statusbar()
        
        if tab_id in self.text_widgets:
            self.text_widgets[tab_id].focus_set()
            self._update_line_numbers(tab_id)
            self._update_minimap(tab_id)
            
    def _close_tab(self, tab_id: str):
        """Close a tab (saves to cache first)"""
        self._close_tab_no_prompt(tab_id)
        
    def _close_tab_no_prompt(self, tab_id: str):
        """Close tab without prompt (content already in cache)"""
        if tab_id not in self.tabs:
            return
            
        tab_data = self.tabs[tab_id]
        
        # Save to cache before closing
        if tab_id in self.text_widgets:
            content = self.text_widgets[tab_id].get("1.0", "end-1c")
            self.cache_manager.save_to_cache(tab_id, content, {
                "filepath": tab_data.filepath,
                "language": tab_data.language,
            })
            
        # Clean up
        if tab_data.tab_frame:
            tab_data.tab_frame.destroy()
            
        if tab_id in self.editor_frames:
            self.editor_frames[tab_id].destroy()
            del self.editor_frames[tab_id]
            
        del self.tabs[tab_id]
        if tab_id in self.text_widgets:
            del self.text_widgets[tab_id]
        if tab_id in self.line_numbers:
            del self.line_numbers[tab_id]
        if tab_id in self.minimaps:
            del self.minimaps[tab_id]
        if tab_id in self.highlighters:
            del self.highlighters[tab_id]
            
        # Switch to another tab or create new
        if self.current_tab == tab_id:
            if self.tabs:
                self._switch_to_tab(list(self.tabs.keys())[-1])
            else:
                self._new_file()
                
    def _close_current_tab(self):
        """Close current tab"""
        if self.current_tab:
            self._close_tab(self.current_tab)
            
    # ═══════════════════════════════════════════════════════════════════════════
    # TEXT EDITING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _on_scroll(self, scrollbar, line_canvas, minimap, *args):
        scrollbar.set(*args)
        line_canvas.redraw()
        minimap.redraw()
        
    def _start_auto_scroll(self, event, widget):
        """Start auto-scroll mode (middle mouse button)"""
        self.auto_scroll_data["active"] = True
        self.auto_scroll_data["start_y"] = event.y_root
        self.auto_scroll_data["current_y"] = event.y_root
        self.auto_scroll_data["widget"] = widget
        widget.config(cursor="sb_v_double_arrow")
        # Start continuous scroll loop
        self._do_auto_scroll()
        return "break"  # Prevent default middle-click paste
        
    def _stop_auto_scroll(self):
        """Stop auto-scroll mode"""
        if self.auto_scroll_data.get("job"):
            self.after_cancel(self.auto_scroll_data["job"])
        if self.auto_scroll_data.get("widget"):
            self.auto_scroll_data["widget"].config(cursor="xterm")
        self.auto_scroll_data = {
            "active": False,
            "start_y": 0,
            "current_y": 0,
            "widget": None,
            "job": None
        }
        
    def _update_auto_scroll(self, event):
        """Track mouse position for auto-scroll"""
        if self.auto_scroll_data["active"]:
            self.auto_scroll_data["current_y"] = event.y_root
            
    def _do_auto_scroll(self):
        """Continuously scroll based on distance from start point"""
        if not self.auto_scroll_data["active"]:
            return
            
        widget = self.auto_scroll_data.get("widget")
        if not widget:
            return
            
        # Calculate distance from start point
        delta_y = self.auto_scroll_data["current_y"] - self.auto_scroll_data["start_y"]
        
        # Dead zone - no scrolling if within 15 pixels of start
        if abs(delta_y) > 15:
            # Scroll speed increases exponentially with distance
            # Positive delta = scroll down, negative = scroll up
            speed = (delta_y / 30.0)
            
            # Clamp speed for smoother experience
            if speed > 0:
                speed = min(speed, 20)
            else:
                speed = max(speed, -20)
            
            # Scroll
            widget.yview_scroll(int(speed), "units")
            
            # Update line numbers and minimap
            if self.current_tab:
                self._update_line_numbers(self.current_tab)
                self._update_minimap(self.current_tab)
        
        # Schedule next scroll (30ms = ~33 fps)
        self.auto_scroll_data["job"] = self.after(30, self._do_auto_scroll)
        
    def _on_text_changed(self, tab_id: str):
        if tab_id not in self.tabs:
            return
            
        text_widget = self.text_widgets[tab_id]
        tab_data = self.tabs[tab_id]
        
        content = text_widget.get("1.0", "end-1c")
        new_hash = hashlib.md5(content.encode()).hexdigest()
        
        was_modified = tab_data.modified
        tab_data.modified = new_hash != tab_data.content_hash
        
        if tab_data.tab_frame and was_modified != tab_data.modified:
            tab_data.tab_frame.modified_label.configure(text="●" if tab_data.modified else "")
            
        if tab_data.modified:
            self.sync_indicator.set_status("modified")
            
        self._update_line_numbers(tab_id)
        self._highlight_current_line(tab_id)
        self._update_minimap(tab_id)
        
    def _update_line_numbers(self, tab_id: str):
        if tab_id in self.line_numbers and tab_id in self.text_widgets:
            # Force geometry update before redrawing
            self.text_widgets[tab_id].update_idletasks()
            self.line_numbers[tab_id].redraw()
            
    def _update_minimap(self, tab_id: str):
        if tab_id in self.minimaps and self.settings.show_minimap:
            self.minimaps[tab_id].redraw()
            
    def _highlight_current_line(self, tab_id: str):
        if not self.settings.highlight_current_line or tab_id not in self.text_widgets:
            return
        text_widget = self.text_widgets[tab_id]
        text_widget.tag_remove("current_line", "1.0", "end")
        line = text_widget.index("insert").split(".")[0]
        text_widget.tag_add("current_line", f"{line}.0", f"{line}.end+1c")
        text_widget.tag_lower("current_line")
        
    def _update_cursor_position(self, tab_id: str):
        if tab_id not in self.text_widgets:
            return
        text_widget = self.text_widgets[tab_id]
        pos = text_widget.index("insert")
        line, col = pos.split(".")
        self.position_label.configure(text=f"Ln {line}, Col {int(col) + 1}")
        self._highlight_current_line(tab_id)
        self._update_line_numbers(tab_id)
        
    def _update_statusbar(self):
        if not self.current_tab or self.current_tab not in self.tabs:
            return
        tab_data = self.tabs[self.current_tab]
        self.language_label.configure(text=tab_data.language)
        self.encoding_label.configure(text=tab_data.encoding.upper())
        self._update_cursor_position(self.current_tab)
        
    def _handle_tab(self, tab_id: str, event) -> str:
        text_widget = self.text_widgets[tab_id]
        if self.settings.use_spaces:
            text_widget.insert("insert", " " * self.settings.tab_size)
            return "break"
        return None
        
    def _handle_return(self, tab_id: str, event) -> str:
        if not self.settings.auto_indent:
            return None
        text_widget = self.text_widgets[tab_id]
        line = text_widget.get("insert linestart", "insert")
        indent = ""
        for char in line:
            if char in " \t":
                indent += char
            else:
                break
        stripped = line.rstrip()
        if stripped.endswith((":", "{", "[", "(")):
            indent += " " * self.settings.tab_size if self.settings.use_spaces else "\t"
        text_widget.insert("insert", "\n" + indent)
        
        # Scroll to keep cursor visible
        text_widget.see("insert")
        
        # Update line numbers immediately
        self.after(1, lambda: self._update_line_numbers(tab_id))
        
        return "break"
        
    def _handle_key(self, tab_id: str, event):
        if not self.settings.auto_close_brackets:
            return
            
        char = event.char
        if char in self.AUTO_CLOSE_PAIRS:
            text_widget = self.text_widgets[tab_id]
            closing = self.AUTO_CLOSE_PAIRS[char]
            try:
                next_char = text_widget.get("insert", "insert+1c")
                if next_char == closing:
                    text_widget.mark_set("insert", "insert+1c")
                    return "break"
            except:
                pass
            text_widget.insert("insert", closing)
            text_widget.mark_set("insert", "insert-1c")
            
    def _highlight_all(self, tab_id: str):
        if tab_id in self.highlighters:
            self.highlighters[tab_id].highlight_all()
            self._update_line_numbers(tab_id)
            self._update_minimap(tab_id)
            
    # ═══════════════════════════════════════════════════════════════════════════
    # FILE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _new_file(self):
        self._create_tab()
        
    def _open_file(self, filepath: Optional[str] = None):
        if filepath is None:
            filetypes = [
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("Python", "*.py"),
                ("JavaScript", "*.js"),
                ("HTML", "*.html"),
                ("CSS", "*.css"),
                ("JSON", "*.json"),
                ("Markdown", "*.md"),
            ]
            filepath = filedialog.askopenfilename(filetypes=filetypes)
        if not filepath:
            return
            
        # Check if already open
        for tab_id, tab_data in self.tabs.items():
            if tab_data.filepath == filepath:
                self._switch_to_tab(tab_id)
                return
                
        try:
            with open(filepath, 'rb') as f:
                raw = f.read()
            if chardet:
                detected = chardet.detect(raw)
                encoding = detected.get('encoding', 'utf-8') or 'utf-8'
            else:
                encoding = 'utf-8'
            content = raw.decode(encoding)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return
            
        tab_id = self._create_tab(filepath, content)
        self.tabs[tab_id].encoding = encoding
        
        # Update recent files
        if filepath not in self.settings.recent_files:
            self.settings.recent_files.insert(0, filepath)
            self.settings.recent_files = self.settings.recent_files[:MAX_RECENT_FILES]
        else:
            # Move to front if already in list
            self.settings.recent_files.remove(filepath)
            self.settings.recent_files.insert(0, filepath)
        self._update_recent_menu()
        self._save_settings()
        
        # Track file mtime for change detection
        self.file_mtimes[filepath] = os.path.getmtime(filepath)
        
        # Set folder in sidebar
        folder = os.path.dirname(filepath)
        if folder and not self.sidebar.current_path:
            self.sidebar.set_root(folder)
            
        self.status_label.configure(text=f"Opened: {os.path.basename(filepath)}")
        
    def _save_file(self) -> bool:
        if not self.current_tab:
            return False
            
        tab_data = self.tabs[self.current_tab]
        
        if tab_data.filepath is None:
            return self._save_file_as()
            
        return self._save_to_path(tab_data.filepath)
        
    def _save_file_as(self) -> bool:
        if not self.current_tab:
            return False
            
        filetypes = [
            ("PowerShell", "*.ps1"),
            ("Batch File", "*.bat"),
            ("Python", "*.py"),
            ("JavaScript", "*.js"),
            ("Text Files", "*.txt"),
            ("Markdown", "*.md"),
            ("JSON", "*.json"),
            ("HTML", "*.html"),
            ("CSS", "*.css"),
            ("All Files", "*.*"),
        ]
        filepath = filedialog.asksaveasfilename(
            defaultextension=self.settings.default_extension,
            filetypes=filetypes
        )
        if not filepath:
            return False
            
        return self._save_to_path(filepath)
        
    def _save_to_path(self, filepath: str) -> bool:
        if not self.current_tab:
            return False
            
        text_widget = self.text_widgets[self.current_tab]
        tab_data = self.tabs[self.current_tab]
        
        try:
            content = text_widget.get("1.0", "end-1c")
            
            with open(filepath, 'w', encoding=tab_data.encoding) as f:
                f.write(content)
                
            tab_data.filepath = filepath
            tab_data.content_hash = hashlib.md5(content.encode()).hexdigest()
            tab_data.modified = False
            
            # Update mtime tracking
            self.file_mtimes[filepath] = os.path.getmtime(filepath)
            
            ext = Path(filepath).suffix.lower()
            tab_data.language = FILE_EXTENSIONS.get(ext, "Plain Text")
            
            if self.current_tab in self.highlighters:
                self.highlighters[self.current_tab].set_language(ext)
                self._highlight_all(self.current_tab)
                
            if tab_data.tab_frame:
                tab_data.tab_frame.label.configure(text=os.path.basename(filepath))
                tab_data.tab_frame.modified_label.configure(text="")
                
            self._update_statusbar()
            self._save_settings()
            self.status_label.configure(text=f"Saved: {os.path.basename(filepath)}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
            return False
            
    # ═══════════════════════════════════════════════════════════════════════════
    # EDIT OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _undo(self):
        if self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_undo()
            except:
                pass
                
    def _redo(self):
        if self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_redo()
            except:
                pass
                
    def _cut(self):
        if self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            try:
                selected = text_widget.get("sel.first", "sel.last")
                self.clipboard_manager.add(selected)
            except:
                pass
            text_widget.event_generate("<<Cut>>")
            
    def _copy(self):
        if self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            try:
                selected = text_widget.get("sel.first", "sel.last")
                self.clipboard_manager.add(selected)
            except:
                pass
            text_widget.event_generate("<<Copy>>")
            
    def _paste(self):
        if self.current_tab in self.text_widgets:
            self.text_widgets[self.current_tab].event_generate("<<Paste>>")
            
    def _duplicate_line(self):
        if not self.current_tab:
            return
        text_widget = self.text_widgets[self.current_tab]
        line = text_widget.get("insert linestart", "insert lineend")
        text_widget.insert("insert lineend", "\n" + line)
        
    def _toggle_comment(self):
        """Toggle line comment"""
        if not self.current_tab:
            return
            
        text_widget = self.text_widgets[self.current_tab]
        tab_data = self.tabs[self.current_tab]
        
        comment_chars = {
            "Python": "#", "JavaScript": "//", "TypeScript": "//",
            "HTML": "<!--", "CSS": "/*", "JSON": "//",
            "Shell": "#", "PowerShell": "#", "Bash": "#",
            "C": "//", "C++": "//", "Java": "//", "Go": "//", "Rust": "//",
            "Ruby": "#", "PHP": "//",
        }
        
        comment = comment_chars.get(tab_data.language, "#")
        
        try:
            sel_start = text_widget.index("sel.first linestart")
            sel_end = text_widget.index("sel.last lineend")
        except:
            sel_start = text_widget.index("insert linestart")
            sel_end = text_widget.index("insert lineend")
            
        start_line = int(sel_start.split(".")[0])
        end_line = int(sel_end.split(".")[0])
        
        # Check if all commented
        all_commented = True
        for line_num in range(start_line, end_line + 1):
            line = text_widget.get(f"{line_num}.0", f"{line_num}.end").lstrip()
            if line and not line.startswith(comment):
                all_commented = False
                break
                
        # Toggle
        for line_num in range(start_line, end_line + 1):
            line = text_widget.get(f"{line_num}.0", f"{line_num}.end")
            if all_commented:
                stripped = line.lstrip()
                indent = line[:len(line) - len(stripped)]
                if stripped.startswith(comment + " "):
                    new_line = indent + stripped[len(comment) + 1:]
                elif stripped.startswith(comment):
                    new_line = indent + stripped[len(comment):]
                else:
                    new_line = line
            else:
                stripped = line.lstrip()
                indent = line[:len(line) - len(stripped)]
                new_line = indent + comment + " " + stripped
                
            text_widget.delete(f"{line_num}.0", f"{line_num}.end")
            text_widget.insert(f"{line_num}.0", new_line)
            
    # ═══════════════════════════════════════════════════════════════════════════
    # FIND/REPLACE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _show_find_bar(self):
        if not self.find_bar_visible:
            self.find_bar.pack(fill="x", before=self.editor_frame)
            self.find_bar_visible = True
        if self.current_tab in self.text_widgets:
            try:
                selected = self.text_widgets[self.current_tab].get("sel.first", "sel.last")
                if selected:
                    self.find_bar.set_find_text(selected)
            except:
                pass
        self.find_bar.focus_find()
        
    def _hide_find_bar(self):
        if self.find_bar_visible:
            self.find_bar.pack_forget()
            self.find_bar_visible = False
            if self.current_tab in self.text_widgets:
                self.text_widgets[self.current_tab].focus_set()
                
    def _find_next(self):
        if self.find_bar_visible:
            self.find_bar._do_find(up=False)
        else:
            self._show_find_bar()
            
    def _find_prev(self):
        if self.find_bar_visible:
            self.find_bar._do_find(up=True)
        else:
            self._show_find_bar()
            
    def _do_find(self, state: SearchState) -> str:
        if not self.current_tab or not state.find_text:
            return ""
            
        text_widget = self.text_widgets[self.current_tab]
        text_widget.tag_remove("search_highlight", "1.0", "end")
        text_widget.tag_remove("search_current", "1.0", "end")
        
        pattern = state.find_text
        if not state.use_regex:
            pattern = re.escape(pattern)
        if state.whole_word:
            pattern = r'\b' + pattern + r'\b'
            
        flags = re.MULTILINE
        if not state.match_case:
            flags |= re.IGNORECASE
            
        content = text_widget.get("1.0", "end-1c")
        try:
            matches = list(re.finditer(pattern, content, flags))
        except re.error:
            return "Invalid regex"
            
        if not matches:
            return "No results"
            
        for match in matches:
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            text_widget.tag_add("search_highlight", start_idx, end_idx)
            
        cursor_pos = text_widget.index("insert")
        cursor_offset = len(text_widget.get("1.0", cursor_pos))
        
        current_idx = 0
        if state.search_up:
            for i, match in enumerate(matches):
                if match.start() < cursor_offset:
                    current_idx = i
        else:
            for i, match in enumerate(matches):
                if match.start() >= cursor_offset:
                    current_idx = i
                    break
            else:
                current_idx = 0
                
        match = matches[current_idx]
        start_idx = f"1.0+{match.start()}c"
        end_idx = f"1.0+{match.end()}c"
        text_widget.tag_remove("search_highlight", start_idx, end_idx)
        text_widget.tag_add("search_current", start_idx, end_idx)
        text_widget.mark_set("insert", start_idx)
        text_widget.see(start_idx)
        
        return f"{current_idx + 1} of {len(matches)}"
        
    def _do_replace(self, state: SearchState):
        if not self.current_tab or not state.find_text:
            return
            
        text_widget = self.text_widgets[self.current_tab]
        try:
            sel_start = text_widget.index("sel.first")
            sel_end = text_widget.index("sel.last")
            selected = text_widget.get(sel_start, sel_end)
            
            pattern = state.find_text
            if not state.use_regex:
                pattern = re.escape(pattern)
            if state.whole_word:
                pattern = r'\b' + pattern + r'\b'
                
            flags = 0 if state.match_case else re.IGNORECASE
            if re.fullmatch(pattern, selected, flags):
                text_widget.delete(sel_start, sel_end)
                text_widget.insert(sel_start, state.replace_text)
        except:
            pass
        self._do_find(state)
        
    def _do_replace_all(self, state: SearchState) -> str:
        if not self.current_tab or not state.find_text:
            return ""
            
        text_widget = self.text_widgets[self.current_tab]
        
        pattern = state.find_text
        if not state.use_regex:
            pattern = re.escape(pattern)
        if state.whole_word:
            pattern = r'\b' + pattern + r'\b'
            
        flags = re.MULTILINE
        if not state.match_case:
            flags |= re.IGNORECASE
            
        content = text_widget.get("1.0", "end-1c")
        try:
            new_content, count = re.subn(pattern, state.replace_text, content, flags=flags)
        except re.error:
            return "Invalid regex"
            
        if count > 0:
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", new_content)
            self._highlight_all(self.current_tab)
            
        return f"Replaced {count}"
        
    def _goto_line(self):
        if not self.current_tab:
            return
        dialog = ctk.CTkInputDialog(text="Line number:", title="Go to Line")
        result = dialog.get_input()
        if result:
            try:
                line_num = int(result)
                text_widget = self.text_widgets[self.current_tab]
                text_widget.mark_set("insert", f"{line_num}.0")
                text_widget.see(f"{line_num}.0")
                self._update_cursor_position(self.current_tab)
            except:
                pass
                
    # ═══════════════════════════════════════════════════════════════════════════
    # VIEW OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _toggle_word_wrap(self):
        self.settings.word_wrap = self.word_wrap_var.get()
        for tab_id, text_widget in self.text_widgets.items():
            text_widget.configure(wrap="word" if self.settings.word_wrap else "none")
            if tab_id in self.editor_frames:
                if self.settings.word_wrap:
                    self.editor_frames[tab_id].h_scrollbar.pack_forget()
                else:
                    self.editor_frames[tab_id].h_scrollbar.pack(side="bottom", fill="x")
        self._save_settings()
        
    def _toggle_line_numbers(self):
        self.settings.show_line_numbers = self.line_numbers_var.get()
        for tab_id, line_canvas in self.line_numbers.items():
            if self.settings.show_line_numbers:
                line_canvas.pack(side="left", fill="y", before=self.text_widgets[tab_id])
            else:
                line_canvas.pack_forget()
        self._save_settings()
        
    def _toggle_minimap(self):
        self.settings.show_minimap = self.minimap_var.get()
        for tab_id, minimap in self.minimaps.items():
            if self.settings.show_minimap:
                minimap.pack(side="right", fill="y")
                minimap.redraw()
            else:
                minimap.pack_forget()
        self._save_settings()
        
    def _toggle_sidebar(self):
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
            self.settings.sidebar_visible = False
        else:
            self.sidebar.pack(side="left", fill="y", before=self.editor_container)
            self.settings.sidebar_visible = True
        self._save_settings()
        
    def _zoom_in(self):
        self.settings.font_size = min(self.settings.font_size + 2, 48)
        self._apply_font_size()
        
    def _zoom_out(self):
        self.settings.font_size = max(self.settings.font_size - 2, 8)
        self._apply_font_size()
        
    def _zoom_reset(self):
        self.settings.font_size = 13
        self._apply_font_size()
        
    def _apply_font_size(self):
        font = (self.settings.font_family, self.settings.font_size)
        for text_widget in self.text_widgets.values():
            text_widget.configure(font=font)
        for line_canvas in self.line_numbers.values():
            line_canvas.text_font = tkfont.Font(family=self.settings.font_family, size=self.settings.font_size)
            line_canvas.redraw()
        zoom_percent = int((self.settings.font_size / 13) * 100)
        self.zoom_label.configure(text=f"{zoom_percent}%")
        self._save_settings()
        
    def _change_theme(self, theme_name: str):
        """Change the editor theme"""
        global THEME
        if theme_name not in THEMES:
            return
        THEME = THEMES[theme_name]
        self.settings.theme_name = theme_name
        
        # Update main window
        self.configure(fg_color=THEME.bg_darkest)
        self.toolbar.configure(fg_color=THEME.bg_medium)
        self.tab_bar.configure(fg_color=THEME.tab_inactive)
        self.statusbar.configure(fg_color=THEME.bg_medium)
        
        # Update editor widgets
        for tab_id in self.tabs:
            if tab_id in self.editor_frames:
                self.editor_frames[tab_id].configure(fg_color=THEME.bg_darkest)
            if tab_id in self.text_widgets:
                text_widget = self.text_widgets[tab_id]
                text_widget.configure(bg=THEME.bg_darkest, fg=THEME.text_primary,
                                     insertbackground=THEME.accent_primary, selectbackground=THEME.selection_bg)
                text_widget.tag_configure("current_line", background=THEME.current_line)
                text_widget.tag_configure("search_highlight", background=THEME.search_highlight)
            if tab_id in self.highlighters:
                self.highlighters[tab_id]._setup_tags()
                self._highlight_all(tab_id)
            if tab_id in self.line_numbers:
                self.line_numbers[tab_id].configure(bg=THEME.bg_dark)
                self.line_numbers[tab_id].redraw()
            if tab_id in self.minimaps:
                self.minimaps[tab_id].configure(bg=THEME.minimap_bg)
                self.minimaps[tab_id].redraw()
            # Update tab button
            tab_data = self.tabs[tab_id]
            if tab_data.tab_frame:
                if tab_id == self.current_tab:
                    tab_data.tab_frame.configure(fg_color=THEME.tab_active)
                    tab_data.tab_frame.label.configure(text_color=THEME.text_primary)
                else:
                    tab_data.tab_frame.configure(fg_color=THEME.tab_inactive)
                    tab_data.tab_frame.label.configure(text_color=THEME.text_secondary)
        
        self.sidebar.configure(fg_color=THEME.bg_dark)
        self.main_container.configure(fg_color=THEME.bg_darkest)
        self.editor_container.configure(fg_color=THEME.bg_darkest)
        self.editor_frame.configure(fg_color=THEME.bg_darkest)
        
        self._save_settings()
        self.status_label.configure(text=f"Theme: {theme_name}")
        
    def _set_ui_scale(self, scale: float):
        """Set UI scale - requires restart"""
        self.settings.ui_scale = scale
        self._save_settings()
        messagebox.showinfo("UI Scale", f"UI Scale set to {int(scale * 100)}%\n\nRestart the application for changes to take effect.")
        
    def _set_default_extension(self, ext: str):
        """Set default file extension for new files"""
        self.settings.default_extension = ext
        self._save_settings()
        self.status_label.configure(text=f"Default extension: {ext}")
        
    def _show_preferences(self):
        """Show preferences dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Preferences")
        dialog.geometry("500x550")
        dialog.configure(fg_color=THEME.bg_dark)
        dialog.transient(self)
        dialog.grab_set()
        dialog.after(100, lambda: set_dark_title_bar(dialog))
        
        ctk.CTkLabel(dialog, text="Preferences", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=THEME.text_primary).pack(pady=15)
        
        # UI Scale
        scale_frame = ctk.CTkFrame(dialog, fg_color=THEME.bg_medium)
        scale_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(scale_frame, text="UI Scale:", text_color=THEME.text_secondary).pack(anchor="w", padx=15, pady=(10, 5))
        scale_var = ctk.StringVar(value=f"{int(self.settings.ui_scale * 100)}%")
        scale_combo = ctk.CTkComboBox(scale_frame, values=["100%", "125%", "150%", "175%", "200%"],
                                      variable=scale_var, width=150, fg_color=THEME.bg_dark)
        scale_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Default Extension
        ext_frame = ctk.CTkFrame(dialog, fg_color=THEME.bg_medium)
        ext_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(ext_frame, text="Default Save Extension:", text_color=THEME.text_secondary).pack(anchor="w", padx=15, pady=(10, 5))
        ext_var = ctk.StringVar(value=self.settings.default_extension)
        ext_combo = ctk.CTkComboBox(ext_frame, values=[".ps1", ".bat", ".py", ".js", ".txt", ".md", ".json", ".html", ".css"],
                                    variable=ext_var, width=150, fg_color=THEME.bg_dark)
        ext_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Font Size
        font_frame = ctk.CTkFrame(dialog, fg_color=THEME.bg_medium)
        font_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(font_frame, text="Font Size:", text_color=THEME.text_secondary).pack(anchor="w", padx=15, pady=(10, 5))
        font_var = ctk.StringVar(value=str(self.settings.font_size))
        font_combo = ctk.CTkComboBox(font_frame, values=["10", "11", "12", "13", "14", "16", "18", "20", "24"],
                                     variable=font_var, width=150, fg_color=THEME.bg_dark)
        font_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Tab Size
        tab_frame = ctk.CTkFrame(dialog, fg_color=THEME.bg_medium)
        tab_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(tab_frame, text="Tab Size:", text_color=THEME.text_secondary).pack(anchor="w", padx=15, pady=(10, 5))
        tab_var = ctk.StringVar(value=str(self.settings.tab_size))
        tab_combo = ctk.CTkComboBox(tab_frame, values=["2", "4", "8"],
                                    variable=tab_var, width=150, fg_color=THEME.bg_dark)
        tab_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        def save_prefs():
            scale_str = scale_var.get().replace("%", "")
            new_scale = int(scale_str) / 100.0
            if new_scale != self.settings.ui_scale:
                self.settings.ui_scale = new_scale
                messagebox.showinfo("UI Scale", "Restart required for UI scale changes")
            self.settings.default_extension = ext_var.get()
            self.settings.font_size = int(font_var.get())
            self.settings.tab_size = int(tab_var.get())
            self._apply_font_size()
            self._save_settings()
            dialog.destroy()
            
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color=THEME.bg_medium,
                      hover_color=THEME.bg_hover, command=dialog.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Save", fg_color=THEME.accent_primary,
                      hover_color=THEME.accent_green, command=save_prefs).pack(side="right", padx=5)
        
    def _show_clipboard_history(self):
        """Show clipboard history dialog"""
        def on_select(text: str):
            if self.current_tab in self.text_widgets:
                self.text_widgets[self.current_tab].insert("insert", text)
        history = self.clipboard_manager.get_history()
        if not history:
            messagebox.showinfo("Clipboard History", "Clipboard history is empty")
            return
        ClipboardHistoryDialog(self, history, on_select)
        
    def _show_find_in_files(self):
        """Show find in files dialog"""
        def on_result_click(filepath: str, line_num: int):
            self._open_file(filepath)
            if self.current_tab in self.text_widgets:
                text_widget = self.text_widgets[self.current_tab]
                text_widget.mark_set("insert", f"{line_num}.0")
                text_widget.see(f"{line_num}.0")
                self._update_cursor_position(self.current_tab)
        dialog = FindInFilesDialog(self, on_result_click)
        if self.sidebar.current_path:
            dialog.folder_entry.insert(0, str(self.sidebar.current_path))
            
    def _show_ai_settings(self):
        """Show AI settings dialog"""
        dialog = AISettingsDialog(self, self.settings)
        self.wait_window(dialog)
        if dialog.result:
            self._save_settings()
            self.status_label.configure(text="AI settings saved")
            
    def _ai_action(self, prompt_name: str):
        """Run AI action on selected text"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return
        text_widget = self.text_widgets[self.current_tab]
        try:
            selected_text = text_widget.get("sel.first", "sel.last")
        except:
            messagebox.showwarning("AI", "Please select some text first")
            return
        if not selected_text.strip():
            messagebox.showwarning("AI", "Please select some text first")
            return
            
        self.status_label.configure(text=f"AI: Processing...")
        
        def on_complete(result: str, error: str):
            if error:
                self.status_label.configure(text=f"AI Error: {error[:50]}")
                messagebox.showerror("AI Error", error)
            else:
                # Show result in a dialog
                self._show_ai_result(result, selected_text)
                self.status_label.configure(text="AI: Complete")
                
        self.ai_manager.process_text(selected_text, prompt_name, on_complete)
        
    def _show_ai_result(self, result: str, original: str):
        """Show AI result dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("AI Result")
        dialog.geometry("700x600")
        dialog.configure(fg_color=THEME.bg_dark)
        dialog.after(100, lambda: set_dark_title_bar(dialog))
        
        ctk.CTkLabel(dialog, text="AI Result:", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=THEME.text_primary).pack(anchor="w", padx=15, pady=(15, 5))
        
        result_text = ctk.CTkTextbox(dialog, width=650, height=350, fg_color=THEME.bg_darkest,
                                     text_color=THEME.text_primary)
        result_text.pack(padx=15, pady=5)
        result_text.insert("1.0", result)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=15)
        
        def replace_selection():
            if self.current_tab in self.text_widgets:
                text_widget = self.text_widgets[self.current_tab]
                try:
                    text_widget.delete("sel.first", "sel.last")
                    text_widget.insert("insert", result)
                except:
                    text_widget.insert("insert", result)
            dialog.destroy()
            
        def copy_result():
            self.clipboard_clear()
            self.clipboard_append(result)
            self.clipboard_manager.add(result)
            dialog.destroy()
            
        ctk.CTkButton(btn_frame, text="Replace Selection", fg_color=THEME.accent_primary,
                      hover_color=THEME.accent_green, command=replace_selection).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Copy to Clipboard", fg_color=THEME.bg_light,
                      hover_color=THEME.bg_hover, command=copy_result).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Close", fg_color=THEME.bg_medium,
                      hover_color=THEME.bg_hover, command=dialog.destroy).pack(side="right", padx=5)
        
        dialog.transient(self)
        dialog.grab_set()
        
    def _ai_custom_prompt(self):
        """Run custom AI prompt on selected text"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return
        text_widget = self.text_widgets[self.current_tab]
        try:
            selected_text = text_widget.get("sel.first", "sel.last")
        except:
            messagebox.showwarning("AI", "Please select some text first")
            return
        if not selected_text.strip():
            messagebox.showwarning("AI", "Please select some text first")
            return
            
        # Show custom prompt dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Custom AI Prompt")
        dialog.geometry("600x400")
        dialog.configure(fg_color=THEME.bg_dark)
        dialog.after(100, lambda: set_dark_title_bar(dialog))
        
        ctk.CTkLabel(dialog, text="Enter your prompt:", text_color=THEME.text_secondary).pack(anchor="w", padx=20, pady=(20, 5))
        prompt_entry = ctk.CTkTextbox(dialog, width=550, height=150, fg_color=THEME.bg_darkest,
                                      text_color=THEME.text_primary)
        prompt_entry.pack(padx=20, pady=5)
        
        def run_prompt():
            prompt = prompt_entry.get("1.0", "end-1c").strip()
            if not prompt:
                return
            dialog.destroy()
            self.status_label.configure(text="AI: Processing...")
            
            def on_complete(result: str, error: str):
                if error:
                    self.status_label.configure(text=f"AI Error")
                    messagebox.showerror("AI Error", error)
                else:
                    self._show_ai_result(result, selected_text)
                    self.status_label.configure(text="AI: Complete")
                    
            self.ai_manager.process_custom(selected_text, prompt, on_complete)
            
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color=THEME.bg_medium,
                      hover_color=THEME.bg_hover, command=dialog.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Run", fg_color=THEME.accent_primary,
                      hover_color=THEME.accent_green, command=run_prompt).pack(side="right", padx=5)
        
        dialog.transient(self)
        dialog.grab_set()
        
    # ═══════════════════════════════════════════════════════════════════════════
    # CLOUD CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _configure_github(self):
        """Configure GitHub sync"""
        dialog = GitHubConfigDialog(self, self.settings)
        self.wait_window(dialog)
        
        if dialog.result:
            token, repo, branch, path = dialog.result
            self.cloud_sync.configure_github(token, repo, branch, path)
            self._save_settings()
            
            # Test connection
            success, msg = self.cloud_sync.test_github_connection()
            if success:
                self.sync_indicator.set_status("synced")
                self.status_label.configure(text=f"GitHub: {msg}")
            else:
                self.sync_indicator.set_status("error")
                messagebox.showerror("GitHub Error", msg)
                
    def _configure_gdrive(self):
        """Configure Google Drive sync"""
        if not GOOGLE_AVAILABLE:
            messagebox.showerror(
                "Google Drive Error",
                "Google API libraries failed to load.\n\n"
                "Try restarting the application or manually install:\n"
                "pip install google-auth google-auth-oauthlib google-api-python-client"
            )
            return
            
        dialog = GDriveConfigDialog(self, self.settings)
        self.wait_window(dialog)
        
        if dialog.result:
            folder_id = dialog.result
            self.settings.gdrive_folder_id = folder_id
            self.settings.sync_provider = "gdrive"
            self.settings.cloud_sync_enabled = True
            self._save_settings()
            self.sync_indicator.set_status("synced")
            self.status_label.configure(text="Google Drive configured successfully")
        
    def _show_sync_status(self):
        """Show sync status dialog"""
        status_lines = ["Cloud Sync Status\n"]
        
        if self.settings.cloud_sync_enabled:
            status_lines.append(f"Provider: {self.settings.sync_provider.upper()}")
            if self.settings.sync_provider == "github":
                status_lines.append(f"Repository: {self.settings.github_repo}")
                status_lines.append(f"Branch: {self.settings.github_branch}")
                status_lines.append(f"Path: {self.settings.github_path}")
            elif self.settings.sync_provider == "gdrive":
                status_lines.append(f"Folder ID: {self.settings.gdrive_folder_id or 'Root'}")
                token_path = Path.home() / ".mattpad/gdrive_token.json"
                if token_path.exists():
                    status_lines.append("Authentication: ✓ Valid")
                else:
                    status_lines.append("Authentication: ✗ Not authenticated")
            status_lines.append(f"\nSync Interval: {self.settings.sync_interval} seconds")
            status_lines.append(f"Auto-save Interval: {LOCAL_SAVE_INTERVAL} seconds")
            
            status_lines.append("\nTab Status:")
            for tab_id, tab_data in self.tabs.items():
                name = os.path.basename(tab_data.filepath) if tab_data.filepath else "Untitled"
                status_lines.append(f"  {name}: {tab_data.sync_status}")
        else:
            status_lines.append("Cloud sync is not configured.")
            status_lines.append("\nGo to Cloud menu to set up sync:")
            status_lines.append("  • Configure GitHub - sync to a GitHub repo")
            status_lines.append("  • Configure Google Drive - sync to Drive")
            
        messagebox.showinfo("Sync Status", "\n".join(status_lines))
        
    # ═══════════════════════════════════════════════════════════════════════════
    # DIALOGS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _show_shortcuts(self):
        shortcuts = """Keyboard Shortcuts

File:
  Ctrl+N          New file
  Ctrl+O          Open file
  Ctrl+S          Save file
  Ctrl+Shift+S    Save as
  Ctrl+W          Close tab

Edit:
  Ctrl+Z          Undo
  Ctrl+Y          Redo
  Ctrl+X/C/V      Cut/Copy/Paste
  Ctrl+D          Duplicate line
  Ctrl+/          Toggle comment

Find:
  Ctrl+F          Find/Replace
  F3              Find next
  Shift+F3        Find previous
  Ctrl+G          Go to line

View:
  Ctrl++/-/0      Zoom in/out/reset
  Ctrl+B          Toggle sidebar

Cloud:
  Auto-saves to local cache every 10 seconds
  Syncs to cloud every 5 minutes (when configured)
  Close without saving - work is always preserved!"""
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
        
    def _show_about(self):
        about = """Mattpad v2.0

A professional-grade text editor

Features:
• Auto-save to local cache (never lose work!)
• Cloud sync to GitHub or Google Drive
• Syntax highlighting for 50+ languages
• Find and replace with regex
• Code minimap
• Multi-tab editing
• No save prompts - just close!

Your work is automatically saved locally and
synced to the cloud every 5 minutes."""

        messagebox.showinfo("About", about)
        
    # ═══════════════════════════════════════════════════════════════════════════
    # CLOSE HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _on_close_no_prompt(self):
        """Close without prompting - everything is auto-saved"""
        # Final save to cache
        self._save_session()
        
        # Cancel timers
        if self.auto_save_job:
            self.after_cancel(self.auto_save_job)
        if self.cloud_sync_job:
            self.after_cancel(self.cloud_sync_job)
            
        # Save settings
        self._save_settings()
        
        # Close
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# DIALOGS
# ═══════════════════════════════════════════════════════════════════════════════

class GitHubConfigDialog(ctk.CTkToplevel):
    """GitHub configuration dialog"""
    
    def __init__(self, parent, settings: EditorSettings):
        super().__init__(parent)
        self.title("Configure GitHub Sync")
        self.geometry("500x450")
        self.configure(fg_color=THEME.bg_dark)
        self.result = None
        self.after(100, lambda: set_dark_title_bar(self))
        
        # Token
        ctk.CTkLabel(self, text="Personal Access Token:", text_color=THEME.text_secondary).pack(anchor="w", padx=20, pady=(20, 5))
        self.token_entry = ctk.CTkEntry(
            self, width=400, height=36,
            fg_color=THEME.bg_darkest,
            border_color=THEME.bg_light,
            text_color=THEME.text_primary,
            show="•"
        )
        self.token_entry.pack(padx=20)
        if settings.github_token:
            self.token_entry.insert(0, settings.github_token)
            
        # Repo
        ctk.CTkLabel(self, text="Repository (owner/repo):", text_color=THEME.text_secondary).pack(anchor="w", padx=20, pady=(15, 5))
        self.repo_entry = ctk.CTkEntry(
            self, width=400, height=36,
            fg_color=THEME.bg_darkest,
            border_color=THEME.bg_light,
            text_color=THEME.text_primary,
            placeholder_text="username/my-notes"
        )
        self.repo_entry.pack(padx=20)
        if settings.github_repo:
            self.repo_entry.insert(0, settings.github_repo)
            
        # Branch
        ctk.CTkLabel(self, text="Branch:", text_color=THEME.text_secondary).pack(anchor="w", padx=20, pady=(15, 5))
        self.branch_entry = ctk.CTkEntry(
            self, width=400, height=36,
            fg_color=THEME.bg_darkest,
            border_color=THEME.bg_light,
            text_color=THEME.text_primary
        )
        self.branch_entry.pack(padx=20)
        self.branch_entry.insert(0, settings.github_branch or "main")
        
        # Path
        ctk.CTkLabel(self, text="Sync Path:", text_color=THEME.text_secondary).pack(anchor="w", padx=20, pady=(15, 5))
        self.path_entry = ctk.CTkEntry(
            self, width=400, height=36,
            fg_color=THEME.bg_darkest,
            border_color=THEME.bg_light,
            text_color=THEME.text_primary
        )
        self.path_entry.pack(padx=20)
        self.path_entry.insert(0, settings.github_path or "mattpad_sync")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame, text="Cancel",
            fg_color=THEME.bg_medium,
            hover_color=THEME.bg_hover,
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="Save",
            fg_color=THEME.accent_primary,
            hover_color=THEME.accent_green,
            command=self._save
        ).pack(side="right", padx=5)
        
        self.transient(parent)
        self.grab_set()
        
    def _save(self):
        self.result = (
            self.token_entry.get(),
            self.repo_entry.get(),
            self.branch_entry.get(),
            self.path_entry.get()
        )
        self.destroy()


class GDriveConfigDialog(ctk.CTkToplevel):
    """Google Drive configuration dialog with OAuth flow"""
    
    # Google Drive API scopes
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, parent, settings: EditorSettings):
        super().__init__(parent)
        self.title("Configure Google Drive Sync")
        self.geometry("550x600")
        self.configure(fg_color=THEME.bg_dark)
        self.settings = settings
        self.result = None
        self.credentials = None
        self.after(100, lambda: set_dark_title_bar(self))
        
        self._create_widgets()
        self._check_existing_auth()
        
        self.transient(parent)
        self.grab_set()
        
    def _create_widgets(self):
        # Title
        ctk.CTkLabel(
            self,
            text="Google Drive Sync Setup",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=THEME.text_primary
        ).pack(pady=(20, 10))
        
        # Instructions
        instructions = ctk.CTkFrame(self, fg_color=THEME.bg_medium, corner_radius=8)
        instructions.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            instructions,
            text="Setup Instructions:",
            font=ctk.CTkFont(weight="bold"),
            text_color=THEME.accent_primary,
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        steps = [
            "1. Go to Google Cloud Console (console.cloud.google.com)",
            "2. Create a new project or select existing one",
            "3. Enable the Google Drive API",
            "4. Create OAuth 2.0 credentials (Desktop app)",
            "5. Download the credentials JSON file",
            "6. Click 'Load Credentials' below and select the file",
        ]
        
        for step in steps:
            ctk.CTkLabel(
                instructions,
                text=step,
                text_color=THEME.text_secondary,
                font=ctk.CTkFont(size=11),
                anchor="w"
            ).pack(anchor="w", padx=15, pady=1)
            
        ctk.CTkLabel(instructions, text="").pack(pady=5)  # Spacer
        
        # Status
        self.status_frame = ctk.CTkFrame(self, fg_color=THEME.bg_medium, corner_radius=8)
        self.status_frame.pack(fill="x", padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status: Not authenticated",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=15)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="📁 Load Credentials JSON",
            fg_color=THEME.accent_primary,
            hover_color=THEME.accent_green,
            height=40,
            command=self._load_credentials
        ).pack(fill="x", pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔑 Authenticate with Google",
            fg_color=THEME.bg_light,
            hover_color=THEME.bg_hover,
            height=40,
            command=self._authenticate,
            state="disabled"
        ).pack(fill="x", pady=5)
        self.auth_btn = btn_frame.winfo_children()[-1]
        
        # Folder ID (optional)
        ctk.CTkLabel(
            self,
            text="Sync Folder ID (optional - leave empty for root):",
            text_color=THEME.text_secondary
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.folder_entry = ctk.CTkEntry(
            self,
            width=400,
            height=36,
            fg_color=THEME.bg_darkest,
            border_color=THEME.bg_light,
            text_color=THEME.text_primary,
            placeholder_text="Folder ID from Google Drive URL"
        )
        self.folder_entry.pack(padx=20)
        if self.settings.gdrive_folder_id:
            self.folder_entry.insert(0, self.settings.gdrive_folder_id)
        
        # Bottom buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        
        ctk.CTkButton(
            bottom_frame,
            text="Cancel",
            fg_color=THEME.bg_medium,
            hover_color=THEME.bg_hover,
            command=self.destroy
        ).pack(side="right", padx=5)
        
        self.save_btn = ctk.CTkButton(
            bottom_frame,
            text="Save & Enable Sync",
            fg_color=THEME.accent_green,
            hover_color=THEME.accent_primary,
            command=self._save,
            state="disabled"
        )
        self.save_btn.pack(side="right", padx=5)
        
    def _check_existing_auth(self):
        """Check if already authenticated"""
        token_path = Path.home() / ".mattpad/gdrive_token.json"
        if token_path.exists():
            try:
                self.credentials = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)
                if self.credentials and self.credentials.valid:
                    self.status_label.configure(
                        text="Status: ✓ Authenticated",
                        text_color=THEME.status_synced
                    )
                    self.save_btn.configure(state="normal")
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    self._save_token()
                    self.status_label.configure(
                        text="Status: ✓ Authenticated (refreshed)",
                        text_color=THEME.status_synced
                    )
                    self.save_btn.configure(state="normal")
            except Exception as e:
                self.status_label.configure(
                    text=f"Status: Token expired - re-authenticate",
                    text_color=THEME.status_modified
                )
                
    def _load_credentials(self):
        """Load OAuth credentials JSON file"""
        filepath = filedialog.askopenfilename(
            title="Select Google OAuth Credentials JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                # Copy to app directory
                creds_path = Path.home() / ".mattpad/gdrive_credentials.json"
                shutil.copy(filepath, creds_path)
                
                self.status_label.configure(
                    text="Status: Credentials loaded - click Authenticate",
                    text_color=THEME.accent_primary
                )
                self.auth_btn.configure(state="normal")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load credentials: {e}")
                
    def _authenticate(self):
        """Run OAuth flow"""
        creds_path = Path.home() / ".mattpad/gdrive_credentials.json"
        
        if not creds_path.exists():
            messagebox.showerror("Error", "Please load credentials JSON first")
            return
            
        try:
            self.status_label.configure(
                text="Status: Opening browser for authentication...",
                text_color=THEME.status_syncing
            )
            self.update()
            
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), self.SCOPES)
            self.credentials = flow.run_local_server(port=0)
            
            self._save_token()
            
            self.status_label.configure(
                text="Status: ✓ Successfully authenticated!",
                text_color=THEME.status_synced
            )
            self.save_btn.configure(state="normal")
            
        except Exception as e:
            self.status_label.configure(
                text=f"Status: Authentication failed",
                text_color=THEME.status_error
            )
            messagebox.showerror("Authentication Error", str(e))
            
    def _save_token(self):
        """Save OAuth token"""
        token_path = Path.home() / ".mattpad/gdrive_token.json"
        with open(token_path, 'w') as f:
            f.write(self.credentials.to_json())
            
    def _save(self):
        """Save configuration"""
        self.result = self.folder_entry.get()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# FIND IN FILES DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class FindInFilesDialog(ctk.CTkToplevel):
    """Find text across files in a folder"""
    
    def __init__(self, parent, on_result_click: Callable[[str, int], None]):
        super().__init__(parent)
        self.title("Find in Files")
        self.geometry("800x700")
        self.configure(fg_color=THEME.bg_dark)
        self.on_result_click = on_result_click
        self.stop_search = False
        self.after(100, lambda: set_dark_title_bar(self))
        self._create_widgets()
        self.transient(parent)
        
    def _create_widgets(self):
        options_frame = ctk.CTkFrame(self, fg_color=THEME.bg_medium)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        row1 = ctk.CTkFrame(options_frame, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row1, text="Search:", width=70, text_color=THEME.text_secondary).pack(side="left")
        self.search_entry = ctk.CTkEntry(row1, width=400, height=32, fg_color=THEME.bg_dark,
                                         border_color=THEME.bg_light, text_color=THEME.text_primary)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self._search())
        self.case_var = ctk.BooleanVar()
        self.regex_var = ctk.BooleanVar()
        ctk.CTkCheckBox(row1, text="Case", variable=self.case_var, width=70,
                       fg_color=THEME.accent_primary, text_color=THEME.text_secondary).pack(side="left", padx=5)
        ctk.CTkCheckBox(row1, text="Regex", variable=self.regex_var, width=70,
                       fg_color=THEME.accent_primary, text_color=THEME.text_secondary).pack(side="left", padx=5)
        
        row2 = ctk.CTkFrame(options_frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row2, text="Folder:", width=70, text_color=THEME.text_secondary).pack(side="left")
        self.folder_entry = ctk.CTkEntry(row2, width=350, height=32, fg_color=THEME.bg_dark,
                                         border_color=THEME.bg_light, text_color=THEME.text_primary)
        self.folder_entry.pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Browse...", width=80, height=32, fg_color=THEME.bg_light,
                      hover_color=THEME.bg_hover, command=self._browse_folder).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="🔍 Search", width=100, height=32, fg_color=THEME.accent_primary,
                      hover_color=THEME.accent_green, command=self._search).pack(side="right", padx=5)
        
        row3 = ctk.CTkFrame(options_frame, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row3, text="Filter:", width=70, text_color=THEME.text_secondary).pack(side="left")
        self.filter_entry = ctk.CTkEntry(row3, width=300, height=32, fg_color=THEME.bg_dark,
                                         border_color=THEME.bg_light, text_color=THEME.text_primary)
        self.filter_entry.pack(side="left", padx=5)
        self.filter_entry.insert(0, "*.py,*.js,*.txt,*.md,*.json,*.html,*.css")
        
        results_frame = ctk.CTkFrame(self, fg_color=THEME.bg_darkest)
        results_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.status_label = ctk.CTkLabel(results_frame, text="Ready", text_color=THEME.text_muted, anchor="w")
        self.status_label.pack(fill="x", padx=5, pady=5)
        
        style = ttk.Style()
        style.configure("Results.Treeview", background=THEME.bg_darkest, foreground=THEME.text_primary,
                       fieldbackground=THEME.bg_darkest, rowheight=24)
        self.results_tree = ttk.Treeview(results_frame, style="Results.Treeview",
                                         columns=("line", "text"), show="tree headings")
        self.results_tree.heading("#0", text="File", anchor="w")
        self.results_tree.heading("line", text="Line", anchor="w")
        self.results_tree.heading("text", text="Match", anchor="w")
        self.results_tree.column("#0", width=300)
        self.results_tree.column("line", width=60)
        self.results_tree.column("text", width=400)
        scrollbar = ctk.CTkScrollbar(results_frame, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.results_tree.bind("<Double-1>", self._on_result_double_click)
        
    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            
    def _search(self):
        search_text = self.search_entry.get()
        folder = self.folder_entry.get()
        if not search_text or not folder or not os.path.isdir(folder):
            return
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.stop_search = False
        filters = [f.strip() for f in self.filter_entry.get().split(",")]
        
        def search_worker():
            match_count, file_count = 0, 0
            try:
                pattern = search_text if self.regex_var.get() else re.escape(search_text)
                flags = 0 if self.case_var.get() else re.IGNORECASE
                regex = re.compile(pattern, flags)
                for root, dirs, files in os.walk(folder):
                    if self.stop_search:
                        break
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for filename in files:
                        if self.stop_search:
                            break
                        if not any(filename.endswith(f[1:]) if f.startswith("*") else filename == f for f in filters):
                            continue
                        filepath = os.path.join(root, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                                lines = file.readlines()
                            file_matches = [(ln, line.strip()[:200]) for ln, line in enumerate(lines, 1) if regex.search(line)]
                            if file_matches:
                                file_count += 1
                                match_count += len(file_matches)
                                rel_path = os.path.relpath(filepath, folder)
                                self.after(0, lambda p=rel_path, m=file_matches, fp=filepath: self._add_file_results(p, m, fp))
                        except:
                            pass
                    self.after(0, lambda mc=match_count, fc=file_count: self.status_label.configure(text=f"Found {mc} matches in {fc} files..."))
            except re.error:
                pass
            self.after(0, lambda: self.status_label.configure(text=f"Complete: {match_count} matches in {file_count} files"))
        threading.Thread(target=search_worker, daemon=True).start()
        
    def _add_file_results(self, rel_path: str, matches: List[Tuple[int, str]], filepath: str):
        file_id = self.results_tree.insert("", "end", text=f"📄 {rel_path}", values=("", ""), tags=(filepath,))
        for line_num, text in matches:
            self.results_tree.insert(file_id, "end", text="", values=(str(line_num), text), tags=(filepath, str(line_num)))
            
    def _on_result_double_click(self, event):
        item = self.results_tree.selection()
        if not item:
            return
        tags = self.results_tree.item(item[0], "tags")
        if tags and len(tags) >= 1:
            filepath = tags[0]
            line_num = int(tags[1]) if len(tags) > 1 and tags[1].isdigit() else 1
            self.on_result_click(filepath, line_num)


# ═══════════════════════════════════════════════════════════════════════════════
# CLIPBOARD HISTORY DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class ClipboardHistoryDialog(ctk.CTkToplevel):
    """Clipboard history viewer"""
    
    def __init__(self, parent, history: List[str], on_select: Callable[[str], None]):
        super().__init__(parent)
        self.title("Clipboard History")
        self.geometry("600x600")
        self.configure(fg_color=THEME.bg_dark)
        self.on_select = on_select
        self.history = history
        self.after(100, lambda: set_dark_title_bar(self))
        self._create_widgets()
        self.transient(parent)
        self.grab_set()
        
    def _create_widgets(self):
        ctk.CTkLabel(self, text="Clipboard History", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=THEME.text_primary).pack(pady=15)
        list_frame = ctk.CTkFrame(self, fg_color=THEME.bg_darkest)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.listbox = tk.Listbox(list_frame, bg=THEME.bg_darkest, fg=THEME.text_primary,
                                  selectbackground=THEME.selection_bg, selectforeground=THEME.text_primary,
                                  font=("Consolas", 11), borderwidth=0, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for i, text in enumerate(self.history):
            preview = text.replace("\n", "↵ ")[:100] + ("..." if len(text) > 100 else "")
            self.listbox.insert("end", f"{i+1}. {preview}")
        self.listbox.bind("<Double-1>", self._on_select)
        self.listbox.bind("<Return>", self._on_select)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(btn_frame, text="Paste Selected", fg_color=THEME.accent_primary,
                      hover_color=THEME.accent_green, command=self._paste_selected).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Close", fg_color=THEME.bg_medium,
                      hover_color=THEME.bg_hover, command=self.destroy).pack(side="right", padx=5)
                      
    def _on_select(self, event=None):
        self._paste_selected()
        
    def _paste_selected(self):
        selection = self.listbox.curselection()
        if selection and 0 <= selection[0] < len(self.history):
            self.on_select(self.history[selection[0]])
            self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# AI SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class AISettingsDialog(ctk.CTkToplevel):
    """AI configuration dialog"""
    
    def __init__(self, parent, settings: EditorSettings):
        super().__init__(parent)
        self.title("AI Settings")
        self.geometry("550x550")
        self.configure(fg_color=THEME.bg_dark)
        self.settings = settings
        self.result = None
        self.after(100, lambda: set_dark_title_bar(self))
        self._create_widgets()
        self.transient(parent)
        self.grab_set()
        
    def _create_widgets(self):
        ctk.CTkLabel(self, text="AI Integration Settings", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=THEME.text_primary).pack(pady=15)
        
        provider_frame = ctk.CTkFrame(self, fg_color=THEME.bg_medium)
        provider_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(provider_frame, text="AI Provider:", text_color=THEME.text_secondary).pack(anchor="w", padx=15, pady=(10, 5))
        self.provider_var = ctk.StringVar(value=self.settings.ai_provider or "openai")
        providers_row = ctk.CTkFrame(provider_frame, fg_color="transparent")
        providers_row.pack(fill="x", padx=15, pady=5)
        ctk.CTkRadioButton(providers_row, text="OpenAI", variable=self.provider_var, value="openai",
                          fg_color=THEME.accent_primary, text_color=THEME.text_secondary).pack(side="left", padx=10)
        ctk.CTkRadioButton(providers_row, text="Anthropic", variable=self.provider_var, value="anthropic",
                          fg_color=THEME.accent_primary, text_color=THEME.text_secondary).pack(side="left", padx=10)
        ctk.CTkRadioButton(providers_row, text="Ollama", variable=self.provider_var, value="ollama",
                          fg_color=THEME.accent_primary, text_color=THEME.text_secondary).pack(side="left", padx=10)
        ctk.CTkLabel(provider_frame, text="").pack(pady=3)
        
        ctk.CTkLabel(self, text="API Key:", text_color=THEME.text_secondary).pack(anchor="w", padx=20, pady=(10, 5))
        self.api_key_entry = ctk.CTkEntry(self, width=450, height=36, fg_color=THEME.bg_darkest,
                                          border_color=THEME.bg_light, text_color=THEME.text_primary, show="•")
        self.api_key_entry.pack(padx=20)
        if self.settings.ai_api_key:
            self.api_key_entry.insert(0, self.settings.ai_api_key)
            
        ctk.CTkLabel(self, text="Model (optional):", text_color=THEME.text_secondary).pack(anchor="w", padx=20, pady=(15, 5))
        self.model_entry = ctk.CTkEntry(self, width=450, height=36, fg_color=THEME.bg_darkest,
                                        border_color=THEME.bg_light, text_color=THEME.text_primary,
                                        placeholder_text="gpt-4o-mini, claude-sonnet-4-20250514, llama3.2")
        self.model_entry.pack(padx=20)
        if self.settings.ai_model:
            self.model_entry.insert(0, self.settings.ai_model)
            
        info_frame = ctk.CTkFrame(self, fg_color=THEME.bg_medium)
        info_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(info_frame, text="Usage: Select text, right-click → AI menu\nOr use the AI menu in the menu bar",
                     text_color=THEME.text_muted, justify="left").pack(padx=15, pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btn_frame, text="Cancel", fg_color=THEME.bg_medium,
                      hover_color=THEME.bg_hover, command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Save", fg_color=THEME.accent_primary,
                      hover_color=THEME.accent_green, command=self._save).pack(side="right", padx=5)
                      
    def _save(self):
        self.settings.ai_provider = self.provider_var.get()
        self.settings.ai_api_key = self.api_key_entry.get()
        self.settings.ai_model = self.model_entry.get()
        self.result = True
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = Mattpad()
    app.mainloop()


if __name__ == "__main__":
    main()
