#!/usr/bin/env python3
"""
Mattpad v5.0 - Professional Text Editor
Production Quality Edition with Thread Safety, Hot Exit, and Performance Optimizations
"""

# =============================================================================
# DPI AWARENESS (must be before any GUI imports)
# =============================================================================

import ctypes
import sys

def enable_dpi_awareness():
    """Enable DPI awareness on Windows for crisp rendering"""
    if sys.platform == "win32":
        try:
            # Windows 10 1703+ Per-Monitor DPI Awareness v2
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Windows 8.1+ Per-Monitor DPI Awareness
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                try:
                    # Windows Vista+ System DPI Awareness
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

enable_dpi_awareness()

# =============================================================================
# DEPENDENCY HANDLING
# =============================================================================

import subprocess
import sys
import importlib.util

def check_and_install_dependencies():
    packages = {
        "customtkinter": "customtkinter", "requests": "requests", "chardet": "chardet",
        "pyspellchecker": "spellchecker", "keyring": "keyring",
        "openai": "openai", "anthropic": "anthropic", "Pillow": "PIL",
    }
    missing = [p for p, i in packages.items() if importlib.util.find_spec(i.split(".")[0]) is None]
    if missing:
        print(f"Installing: {', '.join(missing)}...")
        for pkg in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg,
                                      "--quiet", "--disable-pip-version-check"], stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                pass

check_and_install_dependencies()

# =============================================================================
# IMPORTS
# =============================================================================

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
import queue
import time
import ctypes
import logging
import logging.handlers
import xml.etree.ElementTree as ET
import shutil
import difflib
import webbrowser
from pathlib import Path
from typing import Optional, Dict, List, Callable, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import requests

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

try:
    from spellchecker import SpellChecker
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

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

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# =============================================================================
# LOGGING
# =============================================================================

LOG_DIR = Path.home() / ".mattpad" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "mattpad.log"

logger = logging.getLogger("mattpad")
logger.setLevel(logging.DEBUG)
file_handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.info("=" * 60)
logger.info("Mattpad v4.0 starting")

# =============================================================================
# CONFIGURATION
# =============================================================================

VERSION = "5.0"
CONFIG_DIR = Path.home() / ".mattpad"
CACHE_DIR = CONFIG_DIR / "cache"
CLOSED_TABS_DIR = CONFIG_DIR / "closed_tabs"
BACKUPS_DIR = CONFIG_DIR / "backups"
SNIPPETS_DIR = CONFIG_DIR / "snippets"
THEMES_DIR = CONFIG_DIR / "themes"
MACROS_DIR = CONFIG_DIR / "macros"
SESSIONS_DIR = CONFIG_DIR / "sessions"
HOT_EXIT_DIR = CONFIG_DIR / "hot_exit"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
CLIPBOARD_FILE = CONFIG_DIR / "clipboard_history.json"
CUSTOM_DICT_FILE = CONFIG_DIR / "custom_dictionary.txt"

for d in [CONFIG_DIR, CACHE_DIR, CLOSED_TABS_DIR, BACKUPS_DIR, SNIPPETS_DIR, THEMES_DIR, MACROS_DIR, SESSIONS_DIR, HOT_EXIT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MAX_CLIPBOARD_HISTORY = 500
MAX_RECENT_FILES = 50
LARGE_FILE_THRESHOLD = 1024 * 1024  # 1MB - files larger disable syntax highlighting
VIEWPORT_HIGHLIGHT_BUFFER = 50  # Lines above/below viewport to highlight

# Minimum window dimensions
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# =============================================================================
# THREAD-SAFE DISPATCHER (Critical: All UI updates from threads go through this)
# =============================================================================

class ThreadSafeDispatcher:
    """Marshals callbacks from worker threads to the main Tkinter thread"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._queue: queue.Queue = queue.Queue()
        self._poll()
    
    def _poll(self):
        """Poll queue and execute callbacks on main thread"""
        try:
            while True:
                callback, args, kwargs = self._queue.get_nowait()
                try:
                    callback(*args, **kwargs)
                except tk.TclError as e:
                    logger.error(f"TclError in dispatcher: {e}")
                except Exception as e:
                    logger.error(f"Dispatcher callback error: {e}")
        except queue.Empty:
            pass
        finally:
            self.root.after(10, self._poll)  # Poll every 10ms
    
    def dispatch(self, callback: Callable, *args, **kwargs):
        """Queue a callback to run on the main thread"""
        if threading.current_thread() is threading.main_thread():
            callback(*args, **kwargs)
        else:
            self._queue.put((callback, args, kwargs))

# Global dispatcher - initialized when app starts
_dispatcher: Optional[ThreadSafeDispatcher] = None

def get_dispatcher() -> Optional[ThreadSafeDispatcher]:
    return _dispatcher

# =============================================================================
# SPACING CONSTANTS (Consistent UI tokens)
# =============================================================================

class Spacing:
    """Consistent spacing tokens for the entire application"""
    XS = 4   # Extra small - tight spacing
    SM = 6   # Small - compact elements
    MD = 10  # Medium - standard padding
    LG = 14  # Large - section spacing
    XL = 20  # Extra large - major sections
    XXL = 28 # Double extra large - dialogs

# File type icons (Unicode symbols that scale well)
FILE_ICONS = {
    ".py": "🐍", ".pyw": "🐍", ".js": "📜", ".jsx": "⚛", ".ts": "📘", ".tsx": "⚛",
    ".html": "🌐", ".htm": "🌐", ".css": "🎨", ".scss": "🎨", ".json": "📋",
    ".xml": "📄", ".md": "📝", ".yaml": "⚙", ".yml": "⚙", ".ps1": "⚡", ".psm1": "⚡",
    ".bat": "📦", ".cmd": "📦", ".sh": "🐚", ".c": "©", ".h": "©", ".cpp": "➕",
    ".cs": "♯", ".java": "☕", ".go": "🔵", ".rs": "🦀", ".rb": "💎", ".php": "🐘",
    ".sql": "🗃", ".txt": "📄", ".log": "📋", ".ini": "⚙", ".cfg": "⚙", ".env": "🔐",
    ".gitignore": "📛", ".dockerfile": "🐳", "folder": "📁", "default": "📄",
}

FILE_EXTENSIONS = {
    ".py": "Python", ".pyw": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".json": "JSON", ".xml": "XML",
    ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML",
    ".ps1": "PowerShell", ".psm1": "PowerShell", ".bat": "Batch", ".cmd": "Batch",
    ".c": "C", ".h": "C", ".cpp": "C++", ".cs": "C#", ".java": "Java",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".sql": "SQL",
    ".txt": "Plain Text", ".log": "Plain Text", ".sh": "Shell",
}

# Bracket pairs for matching
BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}", "<": ">"}
CLOSE_BRACKETS = {v: k for k, v in BRACKET_PAIRS.items()}
ALL_BRACKETS = set(BRACKET_PAIRS.keys()) | set(BRACKET_PAIRS.values())

# =============================================================================
# THEME SYSTEM
# =============================================================================

@dataclass
class Theme:
    name: str = "Professional Dark"
    # Ribbon
    ribbon_bg: str = "#1e1e1e"
    ribbon_tab_bg: str = "#2d2d2d"
    ribbon_tab_active: str = "#3c3c3c"
    ribbon_tab_hover: str = "#404040"
    ribbon_group_bg: str = "#252526"
    ribbon_separator: str = "#404040"
    # Editor
    bg_darkest: str = "#0d1117"
    bg_dark: str = "#161b22"
    bg_medium: str = "#21262d"
    bg_light: str = "#30363d"
    bg_hover: str = "#3c4450"
    # Text
    text_primary: str = "#e6edf3"
    text_secondary: str = "#8b949e"
    text_muted: str = "#6e7681"
    text_disabled: str = "#484f58"
    # Accents
    accent_primary: str = "#58a6ff"
    accent_green: str = "#3fb950"
    accent_orange: str = "#d29922"
    accent_red: str = "#f85149"
    accent_purple: str = "#a371f7"
    # Syntax
    syntax_keyword: str = "#ff7b72"
    syntax_string: str = "#a5d6ff"
    syntax_comment: str = "#8b949e"
    syntax_number: str = "#79c0ff"
    syntax_function: str = "#d2a8ff"
    # Editor specific
    selection_bg: str = "#264f78"
    current_line: str = "#1c2128"
    search_highlight: str = "#533d00"
    misspelled: str = "#f85149"
    bracket_match: str = "#444444"
    git_added: str = "#3fb950"
    git_modified: str = "#d29922"
    git_deleted: str = "#f85149"
    # Tabs
    tab_active: str = "#161b22"
    tab_inactive: str = "#0d1117"
    tab_modified: str = "#d29922"
    minimap_viewport: str = "#ffffff15"
    fold_gutter: str = "#6e7681"

THEMES = {
    "Professional Dark": Theme(),
    "Light": Theme(
        name="Light", ribbon_bg="#f3f3f3", ribbon_tab_bg="#e5e5e5", ribbon_tab_active="#ffffff",
        ribbon_tab_hover="#d0d0d0", ribbon_group_bg="#fafafa", ribbon_separator="#d0d0d0",
        bg_darkest="#ffffff", bg_dark="#f5f5f5", bg_medium="#eeeeee", bg_light="#e0e0e0",
        bg_hover="#d5d5d5", text_primary="#24292f", text_secondary="#57606a", text_muted="#6e7781",
        text_disabled="#8c959f", accent_primary="#0969da", accent_green="#1a7f37",
        accent_orange="#9a6700", accent_red="#cf222e", accent_purple="#8250df",
        syntax_keyword="#cf222e", syntax_string="#0a3069", syntax_comment="#6e7781",
        syntax_number="#0550ae", syntax_function="#8250df", selection_bg="#b6d7ff",
        current_line="#f6f8fa", search_highlight="#fff8c5", misspelled="#cf222e",
        bracket_match="#d0d0d0", tab_active="#ffffff", tab_inactive="#f5f5f5",
    ),
    "Monokai": Theme(
        name="Monokai", ribbon_bg="#272822", ribbon_tab_bg="#1e1f1c", ribbon_tab_active="#3e3d32",
        ribbon_tab_hover="#49483e", ribbon_group_bg="#2d2e27", ribbon_separator="#49483e",
        bg_darkest="#272822", bg_dark="#2d2e27", bg_medium="#3e3d32", bg_light="#49483e",
        bg_hover="#75715e", text_primary="#f8f8f2", text_secondary="#a6a69c", text_muted="#75715e",
        accent_primary="#66d9ef", accent_green="#a6e22e", accent_orange="#fd971f",
        accent_red="#f92672", accent_purple="#ae81ff", syntax_keyword="#f92672",
        syntax_string="#e6db74", syntax_comment="#75715e", syntax_number="#ae81ff",
        syntax_function="#a6e22e", selection_bg="#49483e", current_line="#3e3d32",
        tab_active="#3e3d32", tab_inactive="#272822",
    ),
    "Solarized Dark": Theme(
        name="Solarized Dark", ribbon_bg="#002b36", ribbon_tab_bg="#073642", ribbon_tab_active="#094656",
        ribbon_tab_hover="#094656", ribbon_group_bg="#073642", ribbon_separator="#094656",
        bg_darkest="#002b36", bg_dark="#073642", bg_medium="#094656", bg_light="#586e75",
        bg_hover="#657b83", text_primary="#839496", text_secondary="#657b83", text_muted="#586e75",
        text_disabled="#073642", accent_primary="#268bd2", accent_green="#859900",
        accent_orange="#cb4b16", accent_red="#dc322f", accent_purple="#6c71c4",
        syntax_keyword="#859900", syntax_string="#2aa198", syntax_comment="#586e75",
        syntax_number="#d33682", syntax_function="#268bd2", selection_bg="#094656",
        current_line="#073642", search_highlight="#b58900", misspelled="#dc322f",
        bracket_match="#586e75", tab_active="#073642", tab_inactive="#002b36",
    ),
    "Solarized Light": Theme(
        name="Solarized Light", ribbon_bg="#eee8d5", ribbon_tab_bg="#fdf6e3", ribbon_tab_active="#ffffff",
        ribbon_tab_hover="#93a1a1", ribbon_group_bg="#fdf6e3", ribbon_separator="#93a1a1",
        bg_darkest="#fdf6e3", bg_dark="#eee8d5", bg_medium="#93a1a1", bg_light="#839496",
        bg_hover="#657b83", text_primary="#657b83", text_secondary="#839496", text_muted="#93a1a1",
        accent_primary="#268bd2", accent_green="#859900", accent_orange="#cb4b16", accent_red="#dc322f",
        syntax_keyword="#859900", syntax_string="#2aa198", syntax_comment="#93a1a1",
        syntax_number="#d33682", syntax_function="#268bd2", selection_bg="#eee8d5",
        current_line="#eee8d5", tab_active="#fdf6e3", tab_inactive="#eee8d5",
    ),
    "Dracula": Theme(
        name="Dracula", ribbon_bg="#282a36", ribbon_tab_bg="#21222c", ribbon_tab_active="#44475a",
        ribbon_tab_hover="#44475a", ribbon_group_bg="#282a36", ribbon_separator="#44475a",
        bg_darkest="#282a36", bg_dark="#21222c", bg_medium="#343746", bg_light="#44475a",
        bg_hover="#6272a4", text_primary="#f8f8f2", text_secondary="#6272a4", text_muted="#44475a",
        accent_primary="#bd93f9", accent_green="#50fa7b", accent_orange="#ffb86c", accent_red="#ff5555",
        accent_purple="#bd93f9", syntax_keyword="#ff79c6", syntax_string="#f1fa8c",
        syntax_comment="#6272a4", syntax_number="#bd93f9", syntax_function="#50fa7b",
        selection_bg="#44475a", current_line="#343746", search_highlight="#ffb86c",
        misspelled="#ff5555", bracket_match="#6272a4", tab_active="#44475a", tab_inactive="#282a36",
    ),
    "Nord": Theme(
        name="Nord", ribbon_bg="#2e3440", ribbon_tab_bg="#3b4252", ribbon_tab_active="#434c5e",
        ribbon_tab_hover="#4c566a", ribbon_group_bg="#3b4252", ribbon_separator="#4c566a",
        bg_darkest="#2e3440", bg_dark="#3b4252", bg_medium="#434c5e", bg_light="#4c566a",
        bg_hover="#5e81ac", text_primary="#eceff4", text_secondary="#d8dee9", text_muted="#4c566a",
        accent_primary="#88c0d0", accent_green="#a3be8c", accent_orange="#d08770", accent_red="#bf616a",
        accent_purple="#b48ead", syntax_keyword="#81a1c1", syntax_string="#a3be8c",
        syntax_comment="#616e88", syntax_number="#b48ead", syntax_function="#88c0d0",
        selection_bg="#434c5e", current_line="#3b4252", search_highlight="#ebcb8b",
        misspelled="#bf616a", bracket_match="#4c566a", tab_active="#434c5e", tab_inactive="#2e3440",
    ),
    "One Dark": Theme(
        name="One Dark", ribbon_bg="#21252b", ribbon_tab_bg="#282c34", ribbon_tab_active="#2c313a",
        ribbon_tab_hover="#3e4451", ribbon_group_bg="#282c34", ribbon_separator="#3e4451",
        bg_darkest="#282c34", bg_dark="#21252b", bg_medium="#2c313a", bg_light="#3e4451",
        bg_hover="#4b5263", text_primary="#abb2bf", text_secondary="#5c6370", text_muted="#4b5263",
        accent_primary="#61afef", accent_green="#98c379", accent_orange="#d19a66", accent_red="#e06c75",
        accent_purple="#c678dd", syntax_keyword="#c678dd", syntax_string="#98c379",
        syntax_comment="#5c6370", syntax_number="#d19a66", syntax_function="#61afef",
        selection_bg="#3e4451", current_line="#2c313a", search_highlight="#d19a66",
        misspelled="#e06c75", bracket_match="#4b5263", tab_active="#2c313a", tab_inactive="#21252b",
    ),
    "Gruvbox Dark": Theme(
        name="Gruvbox Dark", ribbon_bg="#282828", ribbon_tab_bg="#1d2021", ribbon_tab_active="#3c3836",
        ribbon_tab_hover="#504945", ribbon_group_bg="#282828", ribbon_separator="#504945",
        bg_darkest="#1d2021", bg_dark="#282828", bg_medium="#3c3836", bg_light="#504945",
        bg_hover="#665c54", text_primary="#ebdbb2", text_secondary="#a89984", text_muted="#665c54",
        accent_primary="#83a598", accent_green="#b8bb26", accent_orange="#fe8019", accent_red="#fb4934",
        accent_purple="#d3869b", syntax_keyword="#fb4934", syntax_string="#b8bb26",
        syntax_comment="#928374", syntax_number="#d3869b", syntax_function="#fabd2f",
        selection_bg="#504945", current_line="#3c3836", search_highlight="#fabd2f",
        misspelled="#fb4934", bracket_match="#665c54", tab_active="#3c3836", tab_inactive="#282828",
    ),
    "Gruvbox Light": Theme(
        name="Gruvbox Light", ribbon_bg="#fbf1c7", ribbon_tab_bg="#f9f5d7", ribbon_tab_active="#ebdbb2",
        ribbon_tab_hover="#d5c4a1", ribbon_group_bg="#fbf1c7", ribbon_separator="#d5c4a1",
        bg_darkest="#fbf1c7", bg_dark="#f9f5d7", bg_medium="#ebdbb2", bg_light="#d5c4a1",
        bg_hover="#bdae93", text_primary="#3c3836", text_secondary="#504945", text_muted="#7c6f64",
        accent_primary="#076678", accent_green="#79740e", accent_orange="#af3a03", accent_red="#9d0006",
        accent_purple="#8f3f71", syntax_keyword="#9d0006", syntax_string="#79740e",
        syntax_comment="#928374", syntax_number="#8f3f71", syntax_function="#b57614",
        selection_bg="#d5c4a1", current_line="#ebdbb2", tab_active="#ebdbb2", tab_inactive="#fbf1c7",
    ),
    "Catppuccin Mocha": Theme(
        name="Catppuccin Mocha", ribbon_bg="#1e1e2e", ribbon_tab_bg="#181825", ribbon_tab_active="#313244",
        ribbon_tab_hover="#45475a", ribbon_group_bg="#1e1e2e", ribbon_separator="#45475a",
        bg_darkest="#11111b", bg_dark="#1e1e2e", bg_medium="#313244", bg_light="#45475a",
        bg_hover="#585b70", text_primary="#cdd6f4", text_secondary="#a6adc8", text_muted="#6c7086",
        accent_primary="#89b4fa", accent_green="#a6e3a1", accent_orange="#fab387", accent_red="#f38ba8",
        accent_purple="#cba6f7", syntax_keyword="#cba6f7", syntax_string="#a6e3a1",
        syntax_comment="#6c7086", syntax_number="#fab387", syntax_function="#89b4fa",
        selection_bg="#45475a", current_line="#313244", search_highlight="#f9e2af",
        misspelled="#f38ba8", bracket_match="#585b70", tab_active="#313244", tab_inactive="#1e1e2e",
    ),
    "Catppuccin Latte": Theme(
        name="Catppuccin Latte", ribbon_bg="#eff1f5", ribbon_tab_bg="#e6e9ef", ribbon_tab_active="#ccd0da",
        ribbon_tab_hover="#bcc0cc", ribbon_group_bg="#eff1f5", ribbon_separator="#bcc0cc",
        bg_darkest="#eff1f5", bg_dark="#e6e9ef", bg_medium="#ccd0da", bg_light="#bcc0cc",
        bg_hover="#acb0be", text_primary="#4c4f69", text_secondary="#5c5f77", text_muted="#6c6f85",
        accent_primary="#1e66f5", accent_green="#40a02b", accent_orange="#fe640b", accent_red="#d20f39",
        accent_purple="#8839ef", syntax_keyword="#8839ef", syntax_string="#40a02b",
        syntax_comment="#9ca0b0", syntax_number="#fe640b", syntax_function="#1e66f5",
        selection_bg="#ccd0da", current_line="#e6e9ef", tab_active="#ccd0da", tab_inactive="#eff1f5",
    ),
    "Tokyo Night": Theme(
        name="Tokyo Night", ribbon_bg="#1a1b26", ribbon_tab_bg="#16161e", ribbon_tab_active="#24283b",
        ribbon_tab_hover="#414868", ribbon_group_bg="#1a1b26", ribbon_separator="#414868",
        bg_darkest="#16161e", bg_dark="#1a1b26", bg_medium="#24283b", bg_light="#414868",
        bg_hover="#565f89", text_primary="#c0caf5", text_secondary="#a9b1d6", text_muted="#565f89",
        accent_primary="#7aa2f7", accent_green="#9ece6a", accent_orange="#ff9e64", accent_red="#f7768e",
        accent_purple="#bb9af7", syntax_keyword="#bb9af7", syntax_string="#9ece6a",
        syntax_comment="#565f89", syntax_number="#ff9e64", syntax_function="#7aa2f7",
        selection_bg="#414868", current_line="#24283b", search_highlight="#e0af68",
        misspelled="#f7768e", bracket_match="#565f89", tab_active="#24283b", tab_inactive="#1a1b26",
    ),
    "Cobalt2": Theme(
        name="Cobalt2", ribbon_bg="#193549", ribbon_tab_bg="#122738", ribbon_tab_active="#1f4662",
        ribbon_tab_hover="#234e6d", ribbon_group_bg="#193549", ribbon_separator="#234e6d",
        bg_darkest="#122738", bg_dark="#193549", bg_medium="#1f4662", bg_light="#234e6d",
        bg_hover="#305a78", text_primary="#ffffff", text_secondary="#afc4db", text_muted="#6688aa",
        accent_primary="#ffc600", accent_green="#3ad900", accent_orange="#ff9d00", accent_red="#ff628c",
        accent_purple="#ff9d00", syntax_keyword="#ff9d00", syntax_string="#3ad900",
        syntax_comment="#0088ff", syntax_number="#ff628c", syntax_function="#ffc600",
        selection_bg="#1f4662", current_line="#1f4662", search_highlight="#ffc600",
        misspelled="#ff628c", bracket_match="#305a78", tab_active="#1f4662", tab_inactive="#193549",
    ),
    "High Contrast": Theme(
        name="High Contrast", ribbon_bg="#000000", ribbon_tab_bg="#000000", ribbon_tab_active="#1a1a1a",
        ribbon_tab_hover="#333333", ribbon_group_bg="#0a0a0a", ribbon_separator="#333333",
        bg_darkest="#000000", bg_dark="#0a0a0a", bg_medium="#1a1a1a", bg_light="#2a2a2a",
        bg_hover="#333333", text_primary="#ffffff", text_secondary="#cccccc", text_muted="#888888",
        text_disabled="#555555", accent_primary="#00ff00", accent_green="#00ff00",
        accent_orange="#ffff00", accent_red="#ff0000", accent_purple="#ff00ff",
        syntax_keyword="#ff6600", syntax_string="#00ffff", syntax_comment="#888888",
        syntax_number="#ffff00", syntax_function="#00ff00", selection_bg="#0000ff",
        current_line="#1a1a1a", search_highlight="#ffff00", misspelled="#ff0000",
        bracket_match="#444444", tab_active="#1a1a1a", tab_inactive="#000000",
    ),
}

THEME = THEMES["Professional Dark"]

def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["Professional Dark"])

# =============================================================================
# SETTINGS DATA CLASS (Comprehensive)
# =============================================================================

@dataclass
class EditorSettings:
    # === Editor Basics ===
    font_family: str = "Consolas"
    font_size: int = 12
    tab_size: int = 4
    use_spaces: bool = True
    word_wrap: bool = False
    default_extension: str = ".txt"
    encoding: str = "utf-8"
    
    # === Display ===
    show_line_numbers: bool = True
    show_minimap: bool = True
    show_status_bar: bool = True
    highlight_current_line: bool = True
    show_whitespace: bool = False
    show_indent_guides: bool = True
    
    # === UI ===
    theme_name: str = "Professional Dark"
    ui_scale: float = 1.0
    sidebar_visible: bool = True
    sidebar_width: int = 250
    clipboard_panel_visible: bool = False
    clipboard_panel_width: int = 280
    show_welcome_screen: bool = True
    ribbon_collapsed: bool = True  # Start collapsed, show on hover
    ribbon_pinned: bool = False  # When pinned, ribbon stays visible
    show_toolbar: bool = True
    
    # === Behavior ===
    auto_indent: bool = True
    auto_close_brackets: bool = False  # Disabled by default per user request
    auto_close_quotes: bool = False
    auto_close_tags: bool = False
    smart_backspace: bool = True
    
    # === Saving ===
    auto_save_enabled: bool = True
    auto_save_interval: int = 120  # seconds
    auto_save_to_disk: bool = True  # Actually save files, not just cache
    create_backups: bool = True
    backup_count: int = 5
    prompt_save_on_close: bool = False  # Disabled per user request
    hot_exit_enabled: bool = True  # Save all tabs on exit without prompting (Notepad++ style)
    
    # === Features (all toggleable) ===
    spellcheck_enabled: bool = True
    multi_cursor_enabled: bool = True
    code_folding_enabled: bool = True
    bracket_matching_enabled: bool = True
    bracket_highlight_enabled: bool = True
    git_integration_enabled: bool = False
    terminal_enabled: bool = True
    markdown_preview_enabled: bool = True
    snippets_enabled: bool = True
    macros_enabled: bool = True
    
    # === Search ===
    search_highlight_all: bool = True
    search_case_sensitive: bool = False
    search_regex: bool = False
    search_whole_word: bool = False
    
    # === Notifications ===
    toast_notifications: bool = True
    toast_duration: int = 3000  # ms
    sound_enabled: bool = False
    
    # === Command Palette ===
    command_palette_enabled: bool = True
    fuzzy_search: bool = True
    
    # === Split View ===
    split_view_enabled: bool = True
    split_orientation: str = "horizontal"  # or "vertical"
    
    # === Terminal ===
    terminal_shell: str = ""  # Empty = auto-detect
    terminal_font_size: int = 11
    
    # === Cloud ===
    cloud_sync_enabled: bool = False
    sync_provider: str = ""
    github_token: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    github_path: str = "mattpad_sync"
    sync_interval: int = 300
    
    # === AI ===
    ai_provider: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    
    # === Session ===
    restore_session: bool = True
    recent_files: List[str] = field(default_factory=list)
    recent_folders: List[str] = field(default_factory=list)
    window_geometry: str = "1400x800"
    window_maximized: bool = True
    last_session: str = ""
    
    # === Accessibility ===
    high_contrast: bool = False
    reduced_motion: bool = False
    cursor_blink_rate: int = 530  # ms, 0 = no blink
    keyboard_only_mode: bool = False

# =============================================================================
# TAB DATA
# =============================================================================

@dataclass
class TabData:
    tab_id: str = ""
    filepath: Optional[str] = None
    modified: bool = False
    content_hash: str = ""
    encoding: str = "utf-8"
    line_ending: str = "CRLF"  # Track line ending style (CRLF or LF)
    language: str = "Plain Text"
    is_large_file: bool = False
    tab_frame: Any = None
    cursors: List[str] = field(default_factory=list)  # Multi-cursor positions
    folds: Set[int] = field(default_factory=set)  # Folded line numbers
    bookmarks: Set[int] = field(default_factory=set)
    last_saved: Optional[datetime] = None
    backup_path: Optional[str] = None
    scroll_position: Tuple[float, float] = (0.0, 0.0)  # For hot exit restoration
    cursor_position: str = "1.0"  # For hot exit restoration

@dataclass
class ClipboardItem:
    text: str
    timestamp: str
    pinned: bool = False
    source: str = ""  # Which app it came from

@dataclass
class Snippet:
    name: str
    trigger: str
    content: str
    language: str = ""  # Empty = all languages
    description: str = ""

@dataclass
class Macro:
    name: str
    actions: List[Dict]
    shortcut: str = ""

# =============================================================================
# SECURE STORAGE
# =============================================================================

class SecretStorage:
    SERVICE_NAME = "Mattpad"
    
    @classmethod
    def store(cls, key: str, value: str) -> bool:
        if not value or not KEYRING_AVAILABLE:
            return False
        try:
            keyring.set_password(cls.SERVICE_NAME, key, value)
            return True
        except Exception:
            return False
    
    @classmethod
    def get(cls, key: str, fallback: str = "") -> str:
        if KEYRING_AVAILABLE:
            try:
                v = keyring.get_password(cls.SERVICE_NAME, key)
                if v:
                    return v
            except Exception:
                pass
        return fallback

# =============================================================================
# UTILITIES
# =============================================================================

class Debouncer:
    def __init__(self, widget, delay_ms: int = 200):
        self.widget = widget
        self.delay_ms = delay_ms
        self._jobs: Dict[str, str] = {}
    
    def debounce(self, key: str, callback: Callable):
        if key in self._jobs:
            try:
                self.widget.after_cancel(self._jobs[key])
            except Exception:
                pass
        self._jobs[key] = self.widget.after(self.delay_ms, lambda: self._run(key, callback))
    
    def _run(self, key: str, callback: Callable):
        self._jobs.pop(key, None)
        try:
            callback()
        except Exception as e:
            logger.error(f"Debounce error: {e}")
    
    def cancel_all(self):
        for job in self._jobs.values():
            try:
                self.widget.after_cancel(job)
            except Exception:
                pass
        self._jobs.clear()

def set_dark_title_bar(window):
    try:
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
    except Exception:
        pass

def get_file_icon(filepath: str) -> str:
    if not filepath:
        return FILE_ICONS["default"]
    ext = os.path.splitext(filepath)[1].lower()
    return FILE_ICONS.get(ext, FILE_ICONS["default"])

def detect_line_ending(content: str) -> str:
    """Detect whether content uses CRLF or LF line endings"""
    crlf_count = content.count('\r\n')
    lf_count = content.count('\n') - crlf_count
    return "CRLF" if crlf_count >= lf_count else "LF"

def normalize_line_endings(content: str, target: str = "CRLF") -> str:
    """Convert content to specified line ending style"""
    # First normalize to LF
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    if target == "CRLF":
        return content.replace('\n', '\r\n')
    return content

def convert_line_endings(content: str, from_ending: str, to_ending: str) -> str:
    """Convert between line ending styles"""
    if from_ending == to_ending:
        return content
    return normalize_line_endings(content, to_ending)

def detect_shell() -> str:
    if sys.platform == 'win32':
        if shutil.which('pwsh'):
            return 'pwsh'
        return 'powershell'
    return os.environ.get('SHELL', '/bin/bash')

# =============================================================================
# SPELLCHECK MANAGER
# =============================================================================

class SpellCheckManager:
    def __init__(self):
        self.enabled = SPELLCHECK_AVAILABLE
        self.spell = SpellChecker() if SPELLCHECK_AVAILABLE else None
        self.custom_words: Set[str] = set()
        self._load_custom_dictionary()
        
    def _load_custom_dictionary(self):
        try:
            if CUSTOM_DICT_FILE.exists():
                words = CUSTOM_DICT_FILE.read_text(encoding='utf-8').strip().split('\n')
                self.custom_words = set(w.strip().lower() for w in words if w.strip())
                if self.spell:
                    self.spell.word_frequency.load_words(list(self.custom_words))
        except Exception as e:
            logger.error(f"Failed to load dictionary: {e}")
            
    def _save_custom_dictionary(self):
        try:
            CUSTOM_DICT_FILE.write_text('\n'.join(sorted(self.custom_words)), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save dictionary: {e}")
            
    def add_word(self, word: str):
        word = word.strip().lower()
        if word:
            self.custom_words.add(word)
            if self.spell:
                self.spell.word_frequency.load_words([word])
            self._save_custom_dictionary()
            
    def remove_word(self, word: str):
        self.custom_words.discard(word.strip().lower())
        self._save_custom_dictionary()
            
    def is_misspelled(self, word: str) -> bool:
        if not self.enabled or not self.spell:
            return False
        word = word.strip().lower()
        if not word or len(word) < 2 or not word.isalpha():
            return False
        if word in self.custom_words:
            return False
        return word not in self.spell
        
    def get_suggestions(self, word: str) -> List[str]:
        if not self.enabled or not self.spell:
            return []
        return list(self.spell.candidates(word.lower()) or [])[:5]

# =============================================================================
# BACKUP MANAGER
# =============================================================================

class BackupManager:
    def __init__(self, settings: EditorSettings):
        self.settings = settings
        
    def create_backup(self, filepath: str, content: str) -> Optional[str]:
        if not self.settings.create_backups or not filepath:
            return None
        try:
            filename = os.path.basename(filepath)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filename}.{timestamp}.bak"
            backup_path = BACKUPS_DIR / backup_name
            backup_path.write_text(content, encoding='utf-8')
            self._cleanup_old_backups(filename)
            return str(backup_path)
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
            
    def _cleanup_old_backups(self, filename: str):
        try:
            backups = sorted(BACKUPS_DIR.glob(f"{filename}.*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in backups[self.settings.backup_count:]:
                old.unlink()
        except Exception:
            pass
            
    def get_backups(self, filepath: str) -> List[Tuple[Path, datetime]]:
        if not filepath:
            return []
        filename = os.path.basename(filepath)
        backups = []
        try:
            for p in BACKUPS_DIR.glob(f"{filename}.*.bak"):
                backups.append((p, datetime.fromtimestamp(p.stat().st_mtime)))
        except Exception:
            pass
        return sorted(backups, key=lambda x: x[1], reverse=True)
        
    def restore_backup(self, backup_path: Path) -> Optional[str]:
        try:
            return backup_path.read_text(encoding='utf-8')
        except Exception:
            return None

# =============================================================================
# CLOSED TABS MANAGER (Unlimited)
# =============================================================================

class ClosedTabsManager:
    def __init__(self):
        self.dir = CLOSED_TABS_DIR
        self.index_file = self.dir / "index.json"
        self.tabs: List[Dict] = []
        self._load()
        
    def _load(self):
        try:
            if self.index_file.exists():
                self.tabs = json.loads(self.index_file.read_text(encoding='utf-8'))
        except Exception:
            self.tabs = []
            
    def _save_index(self):
        try:
            self.index_file.write_text(json.dumps(self.tabs, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Index save error: {e}")
            
    def save_tab(self, tab_id: str, filepath: Optional[str], content: str, language: str):
        if not content.strip():
            return
        try:
            (self.dir / f"{tab_id}.txt").write_text(content, encoding='utf-8')
            self.tabs.insert(0, {
                "tab_id": tab_id, "filepath": filepath, "language": language,
                "timestamp": datetime.now().isoformat(),
                "preview": content[:100].replace("\n", " "), "size": len(content)
            })
            self._save_index()
        except Exception as e:
            logger.error(f"Save closed tab error: {e}")
            
    def get_tab(self, index: int) -> Optional[Tuple[str, Optional[str], str]]:
        if index >= len(self.tabs):
            return None
        info = self.tabs[index]
        path = self.dir / f"{info['tab_id']}.txt"
        if not path.exists():
            return None
        try:
            content = path.read_text(encoding='utf-8')
            return content, info.get("filepath"), info.get("language", "Plain Text")
        except Exception:
            return None
            
    def remove_tab(self, index: int):
        if index < len(self.tabs):
            info = self.tabs.pop(index)
            path = self.dir / f"{info['tab_id']}.txt"
            if path.exists():
                path.unlink()
            self._save_index()
            
    def get_list(self) -> List[Dict]:
        return self.tabs.copy()
        
    def clear_all(self):
        for tab in self.tabs:
            path = self.dir / f"{tab['tab_id']}.txt"
            if path.exists():
                path.unlink()
        self.tabs = []
        self._save_index()

# =============================================================================
# CACHE MANAGER
# =============================================================================

class CacheManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.session_file = self.cache_dir / "session.json"
        
    def save_tab(self, tab_id: str, content: str, metadata: Dict) -> bool:
        if not content.strip():
            return False
        try:
            (self.cache_dir / f"{tab_id}.txt").write_text(content, encoding='utf-8')
            (self.cache_dir / f"{tab_id}.meta.json").write_text(json.dumps(metadata), encoding='utf-8')
            return True
        except Exception as e:
            logger.error(f"Cache save error: {e}")
            return False
            
    def load_tab(self, tab_id: str) -> Tuple[Optional[str], Optional[Dict]]:
        try:
            content = (self.cache_dir / f"{tab_id}.txt").read_text(encoding='utf-8')
            meta = json.loads((self.cache_dir / f"{tab_id}.meta.json").read_text(encoding='utf-8'))
            return content, meta
        except Exception:
            return None, None
            
    def delete_tab(self, tab_id: str):
        for f in [self.cache_dir / f"{tab_id}.txt", self.cache_dir / f"{tab_id}.meta.json"]:
            if f.exists():
                f.unlink()
                
    def save_session(self, tabs: List[Dict]):
        try:
            self.session_file.write_text(json.dumps({"tabs": tabs, "timestamp": datetime.now().isoformat()}, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Session save error: {e}")
            
    def load_session(self) -> List[Dict]:
        if self.session_file.exists():
            try:
                return json.loads(self.session_file.read_text(encoding='utf-8')).get("tabs", [])
            except Exception:
                pass
        return []

# =============================================================================
# HOT EXIT MANAGER (Notepad++ Style Session Persistence)
# =============================================================================

class HotExitManager:
    """Saves complete session state on exit, restores on startup - never prompts for unsaved files"""
    
    SNAPSHOT_FILE = HOT_EXIT_DIR / "snapshot.json"
    
    def __init__(self):
        self.enabled = True
    
    def save_snapshot(self, tabs: Dict, text_widgets: Dict, 
                      current_tab: Optional[str], active_order: List[str]) -> bool:
        """Save complete session snapshot including unsaved content"""
        if not self.enabled:
            return False
            
        try:
            snapshot = {
                "version": VERSION,
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
                except tk.TclError:
                    content = ""
                    cursor_pos = "1.0"
                    scroll_pos = (0.0, 0.0)
                
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
        """Load session snapshot if exists"""
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
        """Clear snapshot after successful restore"""
        try:
            if self.SNAPSHOT_FILE.exists():
                self.SNAPSHOT_FILE.unlink()
            for f in HOT_EXIT_DIR.glob("*.content"):
                f.unlink()
            logger.info("Hot exit snapshot cleared")
        except OSError as e:
            logger.error(f"Hot exit clear failed: {e}")
    
    def has_snapshot(self) -> bool:
        """Check if a snapshot exists"""
        return self.SNAPSHOT_FILE.exists()

# =============================================================================
# CLIPBOARD MANAGER
# =============================================================================

class SystemClipboardManager:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.history: List[ClipboardItem] = []
        self.last_content = ""
        self.monitoring = True
        self._load()
        self._monitor()
        
    def _load(self):
        try:
            if CLIPBOARD_FILE.exists():
                data = json.loads(CLIPBOARD_FILE.read_text(encoding='utf-8'))
                self.history = [ClipboardItem(**d) for d in data]
        except Exception:
            pass
            
    def _save(self):
        try:
            data = [{"text": i.text, "timestamp": i.timestamp, "pinned": i.pinned, "source": i.source} for i in self.history]
            CLIPBOARD_FILE.write_text(json.dumps(data), encoding='utf-8')
        except Exception:
            pass
            
    def _monitor(self):
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
        if not text.strip():
            return
        for i, item in enumerate(self.history):
            if item.text == text and not item.pinned:
                self.history.pop(i)
                break
        pinned_count = sum(1 for i in self.history if i.pinned)
        self.history.insert(pinned_count, ClipboardItem(text, datetime.now().isoformat(), source=source))
        while len(self.history) > MAX_CLIPBOARD_HISTORY:
            for i in range(len(self.history) - 1, -1, -1):
                if not self.history[i].pinned:
                    self.history.pop(i)
                    break
        self._save()
        
    def pin(self, index: int):
        if 0 <= index < len(self.history):
            self.history[index].pinned = not self.history[index].pinned
            self.history.sort(key=lambda x: not x.pinned)
            self._save()
            
    def delete(self, index: int):
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self._save()
            
    def clear(self, keep_pinned: bool = True):
        self.history = [i for i in self.history if i.pinned] if keep_pinned else []
        self._save()
        
    def get(self, index: int) -> Optional[str]:
        if 0 <= index < len(self.history):
            return self.history[index].text
        return None

# =============================================================================
# SNIPPETS MANAGER
# =============================================================================

class SnippetsManager:
    DEFAULT_SNIPPETS = [
        Snippet("if statement", "if", "if ${1:condition}:\n    ${2:pass}", "Python"),
        Snippet("for loop", "for", "for ${1:item} in ${2:items}:\n    ${3:pass}", "Python"),
        Snippet("function", "def", "def ${1:name}(${2:args}):\n    ${3:pass}", "Python"),
        Snippet("class", "class", "class ${1:Name}:\n    def __init__(self${2:, args}):\n        ${3:pass}", "Python"),
        Snippet("try/except", "try", "try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:pass}", "Python"),
        Snippet("function", "func", "function ${1:name}(${2:args}) {\n    ${3}\n}", "JavaScript"),
        Snippet("arrow function", "arrow", "const ${1:name} = (${2:args}) => {\n    ${3}\n};", "JavaScript"),
        Snippet("console.log", "log", "console.log(${1});", "JavaScript"),
        Snippet("foreach", "foreach", "ForEach-Object { ${1} }", "PowerShell"),
        Snippet("function", "func", "function ${1:Name} {\n    param(\n        ${2}\n    )\n    ${3}\n}", "PowerShell"),
    ]
    
    def __init__(self):
        self.snippets: List[Snippet] = []
        self._load()
        
    def _load(self):
        self.snippets = self.DEFAULT_SNIPPETS.copy()
        snippets_file = SNIPPETS_DIR / "snippets.json"
        if snippets_file.exists():
            try:
                data = json.loads(snippets_file.read_text(encoding='utf-8'))
                for s in data:
                    self.snippets.append(Snippet(**s))
            except Exception:
                pass
                
    def save(self):
        snippets_file = SNIPPETS_DIR / "snippets.json"
        custom = [s for s in self.snippets if s not in self.DEFAULT_SNIPPETS]
        data = [{"name": s.name, "trigger": s.trigger, "content": s.content, 
                "language": s.language, "description": s.description} for s in custom]
        snippets_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        
    def get_for_language(self, language: str) -> List[Snippet]:
        return [s for s in self.snippets if not s.language or s.language == language]
        
    def find_by_trigger(self, trigger: str, language: str) -> Optional[Snippet]:
        for s in self.snippets:
            if s.trigger == trigger and (not s.language or s.language == language):
                return s
        return None
        
    def add(self, snippet: Snippet):
        self.snippets.append(snippet)
        self.save()
        
    def remove(self, snippet: Snippet):
        if snippet in self.snippets and snippet not in self.DEFAULT_SNIPPETS:
            self.snippets.remove(snippet)
            self.save()

# =============================================================================
# MACRO MANAGER
# =============================================================================

class MacroManager:
    def __init__(self):
        self.macros: List[Macro] = []
        self.recording = False
        self.current_actions: List[Dict] = []
        self._load()
        
    def _load(self):
        macros_file = MACROS_DIR / "macros.json"
        if macros_file.exists():
            try:
                data = json.loads(macros_file.read_text(encoding='utf-8'))
                self.macros = [Macro(**m) for m in data]
            except Exception:
                pass
                
    def save(self):
        macros_file = MACROS_DIR / "macros.json"
        data = [{"name": m.name, "actions": m.actions, "shortcut": m.shortcut} for m in self.macros]
        macros_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        
    def start_recording(self):
        self.recording = True
        self.current_actions = []
        
    def stop_recording(self, name: str) -> Macro:
        self.recording = False
        macro = Macro(name=name, actions=self.current_actions.copy())
        self.macros.append(macro)
        self.save()
        return macro
        
    def record_action(self, action_type: str, data: Any):
        if self.recording:
            self.current_actions.append({"type": action_type, "data": data, "time": time.time()})
            
    def cancel_recording(self):
        self.recording = False
        self.current_actions = []

# =============================================================================
# AI MANAGER
# =============================================================================

class AIManager:
    """AI integration with thread-safe callback dispatch"""
    
    PROMPTS = [
        ("Summarize", "Summarize this text concisely:\n\n{text}"),
        ("Fix Grammar", "Fix grammar and spelling errors:\n\n{text}"),
        ("Professional Email", "Rewrite as a professional email:\n\n{text}"),
        ("Simplify", "Simplify this text for clarity:\n\n{text}"),
        ("Expand", "Expand with more detail:\n\n{text}"),
        ("Explain Code", "Explain what this code does:\n\n{text}"),
        ("Refactor Code", "Refactor this code for clarity and efficiency:\n\n{text}"),
        ("Add Comments", "Add helpful comments to this code:\n\n{text}"),
        ("Convert to Bullet Points", "Convert to bullet points:\n\n{text}"),
        ("Translate to Python", "Convert this code to Python:\n\n{text}"),
    ]
    
    def __init__(self, settings: EditorSettings):
        self.settings = settings
    
    def _safe_callback(self, callback: Callable, result: str, error: str):
        """Dispatch callback to main thread safely"""
        dispatcher = get_dispatcher()
        if dispatcher:
            dispatcher.dispatch(callback, result, error)
        else:
            callback(result, error)
        
    def process(self, text: str, prompt_name: str, callback: Callable):
        template = next((p[1] for p in self.PROMPTS if p[0] == prompt_name), None)
        if not template:
            self._safe_callback(callback, "", "Unknown prompt")
            return
        threading.Thread(target=lambda: self._call_api(template.format(text=text), callback), daemon=True).start()
        
    def process_custom(self, text: str, prompt: str, callback: Callable):
        full_prompt = f"{prompt}\n\n{text}" if text else prompt
        threading.Thread(target=lambda: self._call_api(full_prompt, callback), daemon=True).start()
        
    def _call_api(self, prompt: str, callback: Callable):
        try:
            key = SecretStorage.get("ai_api_key", self.settings.ai_api_key)
            if not key and self.settings.ai_provider != "ollama":
                self._safe_callback(callback, "", "API key not configured")
                return
            if self.settings.ai_provider == "openai" and OPENAI_AVAILABLE:
                client = openai.OpenAI(api_key=key)
                r = client.chat.completions.create(
                    model=self.settings.ai_model or "gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                self._safe_callback(callback, r.choices[0].message.content, "")
            elif self.settings.ai_provider == "anthropic" and ANTHROPIC_AVAILABLE:
                client = anthropic.Anthropic(api_key=key)
                r = client.messages.create(
                    model=self.settings.ai_model or "claude-sonnet-4-20250514",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                self._safe_callback(callback, r.content[0].text, "")
            elif self.settings.ai_provider == "ollama":
                r = requests.post("http://localhost:11434/api/generate",
                                json={"model": self.settings.ai_model or "llama3.2", "prompt": prompt, "stream": False},
                                timeout=120)
                self._safe_callback(callback, r.json().get("response", ""), "")
            else:
                self._safe_callback(callback, "", "Provider not configured")
        except Exception as e:
            logger.error(f"AI API error: {e}")
            self._safe_callback(callback, "", str(e))

# =============================================================================
# CLOUD SYNC MANAGER
# =============================================================================

class CloudSyncManager:
    def __init__(self, settings: EditorSettings):
        self.settings = settings
        
    def configure_github(self, token: str, repo: str, branch: str = "main", path: str = "mattpad_sync"):
        SecretStorage.store("github_token", token)
        self.settings.github_token = token
        self.settings.github_repo = repo
        self.settings.github_branch = branch
        self.settings.github_path = path
        self.settings.sync_provider = "github"
        self.settings.cloud_sync_enabled = True
        
    def sync_file(self, filepath: str, content: str) -> Tuple[bool, str]:
        if not self.settings.cloud_sync_enabled:
            return False, "Not configured"
        if self.settings.sync_provider == "github":
            return self._sync_github(filepath, content)
        return False, "Unknown provider"
        
    def _sync_github(self, filepath: str, content: str) -> Tuple[bool, str]:
        try:
            token = SecretStorage.get("github_token", self.settings.github_token)
            if not token or not self.settings.github_repo:
                return False, "Not configured"
            filename = os.path.basename(filepath) if filepath else f"untitled_{int(time.time())}.txt"
            file_path = f"{self.settings.github_path}/{filename}"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            url = f"https://api.github.com/repos/{self.settings.github_repo}/contents/{file_path}"
            r = requests.get(url, headers=headers, params={"ref": self.settings.github_branch}, timeout=10)
            sha = r.json().get("sha") if r.status_code == 200 else None
            data = {"message": f"Mattpad: {filename}", "content": base64.b64encode(content.encode()).decode(), "branch": self.settings.github_branch}
            if sha:
                data["sha"] = sha
            r = requests.put(url, headers=headers, json=data, timeout=30)
            return r.status_code in (200, 201), r.json().get("message", "OK") if r.status_code not in (200, 201) else "Synced"
        except Exception as e:
            return False, str(e)
            
    def test_connection(self) -> Tuple[bool, str]:
        try:
            token = SecretStorage.get("github_token", self.settings.github_token)
            r = requests.get("https://api.github.com/user", headers={"Authorization": f"token {token}"}, timeout=10)
            return (True, f"Connected: {r.json().get('login')}") if r.status_code == 200 else (False, f"Error {r.status_code}")
        except Exception as e:
            return False, str(e)

# =============================================================================
# NOTEPAD++ IMPORTER
# =============================================================================

class NotepadPlusPlusImporter:
    @staticmethod
    def get_session_paths() -> List[Path]:
        paths = []
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(Path(appdata) / "Notepad++" / "session.xml")
        for pf in [os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", "")]:
            if pf:
                paths.append(Path(pf) / "Notepad++" / "session.xml")
        return [p for p in paths if p.exists()]
    
    @staticmethod
    def parse_session(path: Path) -> List[str]:
        files = []
        try:
            tree = ET.parse(path)
            for elem in tree.getroot().iter("File"):
                fp = elem.get("filename")
                if fp and os.path.exists(fp):
                    files.append(fp)
        except Exception:
            pass
        return files
    
    @classmethod
    def import_tabs(cls) -> List[str]:
        all_files = []
        for path in cls.get_session_paths():
            for f in cls.parse_session(path):
                if f not in all_files:
                    all_files.append(f)
        return all_files

# =============================================================================
# DIFF ENGINE
# =============================================================================

class DiffEngine:
    @staticmethod
    def compare(text1: str, text2: str) -> List[Tuple[str, str, int, int]]:
        """Returns list of (tag, content, start, end) for differences"""
        lines1, lines2 = text1.splitlines(keepends=True), text2.splitlines(keepends=True)
        differ = difflib.unified_diff(lines1, lines2, lineterm='')
        return list(differ)
    
    @staticmethod
    def get_line_diff(text1: str, text2: str) -> Dict[int, str]:
        """Returns dict of line_number -> change_type ('added', 'removed', 'modified')"""
        lines1, lines2 = text1.splitlines(), text2.splitlines()
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        changes = {}
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                for i in range(i1, i2):
                    changes[i + 1] = 'modified'
            elif tag == 'delete':
                for i in range(i1, i2):
                    changes[i + 1] = 'removed'
            elif tag == 'insert':
                for j in range(j1, j2):
                    changes[j + 1] = 'added'
        return changes

# =============================================================================
# TOAST NOTIFICATION SYSTEM
# =============================================================================

class ToastManager:
    def __init__(self, root, settings: EditorSettings):
        self.root = root
        self.settings = settings
        self.toasts: List[ctk.CTkFrame] = []
        self.max_toasts = 5
        
    def show(self, message: str, type_: str = "info", duration: int = None):
        if not self.settings.toast_notifications:
            return
        duration = duration or self.settings.toast_duration
        
        colors = {
            "info": (THEME.accent_primary, THEME.bg_medium),
            "success": (THEME.accent_green, THEME.bg_medium),
            "warning": (THEME.accent_orange, THEME.bg_medium),
            "error": (THEME.accent_red, THEME.bg_medium),
        }
        accent, bg = colors.get(type_, colors["info"])
        s = self.settings.ui_scale
        
        toast = ctk.CTkFrame(self.root, fg_color=bg, corner_radius=int(8*s), border_width=1, border_color=accent)
        
        icon_map = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✕"}
        ctk.CTkLabel(toast, text=icon_map.get(type_, "ℹ"), font=ctk.CTkFont(size=int(16*s)),
                    text_color=accent, width=int(24*s)).pack(side="left", padx=int(10*s))
        ctk.CTkLabel(toast, text=message, font=ctk.CTkFont(size=int(11*s)),
                    text_color=THEME.text_primary).pack(side="left", padx=(0, int(10*s)), pady=int(10*s))
        
        close_btn = ctk.CTkButton(toast, text="×", width=int(24*s), height=int(24*s),
                                 fg_color="transparent", hover_color=THEME.bg_hover,
                                 command=lambda: self._dismiss(toast))
        close_btn.pack(side="right", padx=int(5*s))
        
        # Position toast
        y_offset = int(80*s) + sum(t.winfo_height() + 10 for t in self.toasts if t.winfo_exists())
        toast.place(relx=1.0, y=y_offset, anchor="ne", x=-int(20*s))
        self.toasts.append(toast)
        
        # Remove old toasts
        while len(self.toasts) > self.max_toasts:
            old = self.toasts.pop(0)
            if old.winfo_exists():
                old.destroy()
                
        # Auto-dismiss
        self.root.after(duration, lambda: self._dismiss(toast))
        
    def _dismiss(self, toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
        if toast.winfo_exists():
            toast.destroy()
        self._reposition()
        
    def _reposition(self):
        s = self.settings.ui_scale
        y = int(80*s)
        for toast in self.toasts:
            if toast.winfo_exists():
                toast.place(relx=1.0, y=y, anchor="ne", x=-int(20*s))
                y += toast.winfo_height() + 10

# =============================================================================
# LINE NUMBER CANVAS
# =============================================================================

class LineNumberCanvas(tk.Canvas):
    def __init__(self, master, settings: EditorSettings, **kwargs):
        self.settings = settings
        s = settings.ui_scale
        super().__init__(master, width=int(60*s), bg=THEME.bg_dark, highlightthickness=0, **kwargs)
        self.text_widget: Optional[tk.Text] = None
        self.text_font = None
        self.bookmarks: Set[int] = set()
        self.folds: Set[int] = set()
        self.git_changes: Dict[int, str] = {}
        self.bind("<Button-1>", lambda e: self._on_click(e))
        
    def _on_click(self, event):
        if not self.text_widget:
            return
        try:
            index = self.text_widget.index(f"@0,{event.y}")
            line = int(index.split(".")[0])
            if event.x < 20 * self.settings.ui_scale:  # Fold gutter
                if line in self.folds:
                    self.folds.remove(line)
                else:
                    self.folds.add(line)
            else:  # Bookmark
                if line in self.bookmarks:
                    self.bookmarks.remove(line)
                else:
                    self.bookmarks.add(line)
            self.redraw()
        except Exception:
            pass
            
    def redraw(self):
        self.delete("all")
        if not self.text_widget:
            return
        s = self.settings.ui_scale
        try:
            first = self.text_widget.index("@0,0")
            last = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
        except Exception:
            return
        first_line = int(first.split(".")[0])
        last_line = int(last.split(".")[0])
        
        total = int(self.text_widget.index("end-1c").split(".")[0])
        digits = max(3, len(str(total)))
        width = int((digits * 10 + 30) * s)
        if self.winfo_reqwidth() != width:
            self.configure(width=width)
            
        font = self.text_font or tkfont.Font(family=self.settings.font_family, size=int(self.settings.font_size * s))
        
        for line in range(first_line, last_line + 1):
            try:
                bbox = self.text_widget.bbox(f"{line}.0")
                if not bbox:
                    continue
                y = bbox[1]
                
                # Git indicator
                if self.settings.git_integration_enabled and line in self.git_changes:
                    color = {"added": THEME.git_added, "modified": THEME.git_modified, "removed": THEME.git_deleted}.get(self.git_changes[line], THEME.text_muted)
                    self.create_rectangle(0, y, int(3*s), y + int(16*s), fill=color, outline="")
                    
                # Fold indicator
                if self.settings.code_folding_enabled:
                    if line in self.folds:
                        self.create_text(int(12*s), y + int(8*s), text="▶", fill=THEME.fold_gutter, font=("", int(8*s)))
                    
                # Bookmark
                if line in self.bookmarks:
                    self.create_oval(int(16*s), y + int(2*s), int(24*s), y + int(14*s), fill=THEME.accent_primary, outline="")
                    
                # Line number
                self.create_text(width - int(10*s), y, text=str(line), fill=THEME.text_muted, font=font, anchor="ne")
            except Exception:
                pass

# =============================================================================
# MINIMAP
# =============================================================================

class Minimap(tk.Canvas):
    def __init__(self, master, text_widget: tk.Text, settings: EditorSettings, **kwargs):
        s = settings.ui_scale
        super().__init__(master, width=int(100*s), bg=THEME.bg_dark, highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        self.settings = settings
        self.bind("<Button-1>", lambda e: self._on_click(e))
        self.bind("<B1-Motion>", lambda e: self._on_click(e))
        
    def _on_click(self, event):
        if not self.text_widget:
            return
        try:
            height = self.winfo_height()
            total = int(self.text_widget.index("end-1c").split(".")[0])
            if total > 0 and height > 0:
                target = max(1, int((event.y / height) * total))
                self.text_widget.see(f"{target}.0")
        except Exception:
            pass
            
    def redraw(self):
        self.delete("all")
        if not self.text_widget:
            return
        try:
            content = self.text_widget.get("1.0", "end-1c")
        except Exception:
            return
        lines = content.split("\n")
        total = len(lines)
        if total == 0:
            return
        height = self.winfo_height()
        width = self.winfo_width()
        if height <= 0:
            return
        line_h = max(1, height / max(total, 1))
        
        for i, line in enumerate(lines[:3000]):
            y = i * line_h
            if y > height:
                break
            stripped = line.strip()
            if not stripped:
                continue
            length = min(len(stripped), 100)
            x2 = min(4 + length * 0.4, width - 4)
            self.create_line(4, y, x2, y, fill=THEME.text_disabled, width=max(1, line_h * 0.4))
            
        try:
            first = int(self.text_widget.index("@0,0").split(".")[0])
            last = int(self.text_widget.index(f"@0,{self.text_widget.winfo_height()}").split(".")[0])
            y1 = (first - 1) * line_h
            y2 = last * line_h
            self.create_rectangle(0, y1, width, y2, fill=THEME.minimap_viewport, outline=THEME.accent_primary, width=1)
        except Exception:
            pass

# =============================================================================
# SYNTAX HIGHLIGHTER
# =============================================================================

class SyntaxHighlighter:
    """Syntax highlighting with viewport-only processing for large files"""
    
    PATTERNS = {
        "Python": {
            "keyword": r"\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|break|continue|pass|raise|and|or|not|in|is|lambda|global|nonlocal|async|await|True|False|None|self)\b",
            "string": r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|f"[^"\\]*(?:\\.[^"\\]*)*"|f\'[^\'\\]*(?:\\.[^\'\\]*)*\'|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"#.*$",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_]\w*)\s*(?=\()",
            "decorator": r"@\w+",
        },
        "JavaScript": {
            "keyword": r"\b(const|let|var|function|return|if|else|for|while|switch|case|break|continue|try|catch|finally|throw|new|class|extends|import|export|default|from|async|await|true|false|null|undefined|this|typeof|instanceof)\b",
            "string": r'(`[\s\S]*?`|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_$]\w*)\s*(?=\()",
        },
        "TypeScript": {
            "keyword": r"\b(const|let|var|function|return|if|else|for|while|switch|case|break|continue|try|catch|finally|throw|new|class|extends|implements|interface|type|enum|import|export|default|from|async|await|true|false|null|undefined|this|typeof|instanceof|public|private|protected|readonly|static|abstract)\b",
            "string": r'(`[\s\S]*?`|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_$]\w*)\s*(?=\()",
            "type": r":\s*([A-Z]\w*)",
        },
        "PowerShell": {
            "keyword": r"\b(function|param|if|else|elseif|switch|for|foreach|while|do|try|catch|finally|throw|return|break|continue|begin|process|end)\b",
            "string": r'(".*?"|\'.*?\')',
            "comment": r"#.*$|<#[\s\S]*?#>",
            "number": r"\b\d+\.?\d*\b",
            "variable": r"\$\w+",
            "cmdlet": r"\b[A-Z][a-z]+-[A-Z]\w+",
        },
        "JSON": {
            "keys": r'"[^"]+"\s*(?=:)',
            "string": r'"[^"]*"(?!\s*:)',
            "number": r"\b-?\d+\.?\d*\b",
            "keyword": r"\b(true|false|null)\b",
        },
        "HTML": {
            "tag": r"</?[a-zA-Z][a-zA-Z0-9]*",
            "attribute": r'\b[a-zA-Z-]+(?==)',
            "string": r'"[^"]*"|\'[^\']*\'',
            "comment": r"<!--[\s\S]*?-->",
        },
        "CSS": {
            "selector": r"[.#]?[a-zA-Z][a-zA-Z0-9_-]*(?=\s*\{)",
            "property": r"[a-zA-Z-]+(?=\s*:)",
            "value": r":\s*([^;{}]+)",
            "comment": r"/\*[\s\S]*?\*/",
        },
        "Markdown": {
            "heading": r"^#{1,6}\s.*$",
            "bold": r"\*\*[^*]+\*\*|__[^_]+__",
            "italic": r"\*[^*]+\*|_[^_]+_",
            "code": r"`[^`]+`",
            "link": r"\[[^\]]+\]\([^)]+\)",
        },
    }
    
    def __init__(self, text_widget: tk.Text, ext: str = ".txt"):
        self.text_widget = text_widget
        self.ext = ext
        self.is_large_file = False
        self._last_highlighted_range: Optional[Tuple[int, int]] = None
        self._setup_tags()
        
    def _setup_tags(self):
        tags = {
            "keyword": THEME.syntax_keyword, "string": THEME.syntax_string,
            "comment": THEME.syntax_comment, "number": THEME.syntax_number,
            "function": THEME.syntax_function, "keys": THEME.syntax_function,
            "variable": THEME.accent_orange, "cmdlet": THEME.accent_purple,
            "decorator": THEME.accent_orange, "type": THEME.accent_purple,
            "tag": THEME.syntax_keyword, "attribute": THEME.syntax_function,
            "selector": THEME.syntax_keyword, "property": THEME.syntax_function,
            "heading": THEME.accent_primary, "bold": THEME.text_primary,
            "italic": THEME.text_secondary, "code": THEME.syntax_string,
            "link": THEME.accent_primary, "value": THEME.syntax_string,
        }
        for tag, color in tags.items():
            self.text_widget.tag_configure(tag, foreground=color)
        self.text_widget.tag_configure("bold", font=(THEME.name, 12, "bold"))
        
    def set_language(self, ext: str):
        self.ext = ext
        self._last_highlighted_range = None
    
    def set_large_file_mode(self, is_large: bool):
        """Enable/disable large file mode (disables highlighting)"""
        self.is_large_file = is_large
        if is_large:
            self._clear_all_tags()
    
    def _clear_all_tags(self):
        """Remove all syntax highlighting tags"""
        for lang_patterns in self.PATTERNS.values():
            for tag in lang_patterns.keys():
                try:
                    self.text_widget.tag_remove(tag, "1.0", "end")
                except tk.TclError:
                    pass
        
    def highlight_all(self):
        if self.is_large_file:
            return
        lang = FILE_EXTENSIONS.get(self.ext, "Plain Text")
        patterns = self.PATTERNS.get(lang, {})
        for tag in list(self.PATTERNS.get(lang, {}).keys()) + ["keyword", "string", "comment", "number", "function"]:
            self.text_widget.tag_remove(tag, "1.0", "end")
        if not patterns:
            return
        try:
            content = self.text_widget.get("1.0", "end-1c")
            for tag, pattern in patterns.items():
                for match in re.finditer(pattern, content, re.MULTILINE):
                    start = f"1.0+{match.start()}c"
                    end = f"1.0+{match.end()}c"
                    self.text_widget.tag_add(tag, start, end)
        except Exception:
            pass
            
    def highlight_visible(self):
        """Highlight only visible viewport plus buffer - optimized for large files"""
        if self.is_large_file:
            return
        lang = FILE_EXTENSIONS.get(self.ext, "Plain Text")
        patterns = self.PATTERNS.get(lang, {})
        if not patterns:
            return
        try:
            # Get visible range
            first_visible = self.text_widget.index("@0,0")
            last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
            
            first_line = max(1, int(first_visible.split(".")[0]) - VIEWPORT_HIGHLIGHT_BUFFER)
            last_line = int(last_visible.split(".")[0]) + VIEWPORT_HIGHLIGHT_BUFFER
            
            # Check if we need to re-highlight
            current_range = (first_line, last_line)
            if self._last_highlighted_range == current_range:
                return
            self._last_highlighted_range = current_range
            
            start_idx = f"{first_line}.0"
            end_idx = f"{last_line}.end"
            
            content = self.text_widget.get(start_idx, end_idx)
            offset = len(self.text_widget.get("1.0", start_idx))
            
            for tag in patterns.keys():
                self.text_widget.tag_remove(tag, start_idx, end_idx)
            for tag, pattern in patterns.items():
                for match in re.finditer(pattern, content, re.MULTILINE):
                    self.text_widget.tag_add(tag, f"1.0+{offset+match.start()}c", f"1.0+{offset+match.end()}c")
        except Exception:
            pass
    
    def invalidate_cache(self):
        """Force re-highlight on next call"""
        self._last_highlighted_range = None

# =============================================================================
# FILE TREE VIEW
# =============================================================================

class FileTreeView(ctk.CTkFrame):
    def __init__(self, master, on_file_select: Callable, settings: EditorSettings, **kwargs):
        super().__init__(master, fg_color=THEME.bg_dark, **kwargs)
        self.on_file_select = on_file_select
        self.settings = settings
        self.current_path: Optional[Path] = None
        self._create()
        
    def _create(self):
        s = self.settings.ui_scale
        header = ctk.CTkFrame(self, fg_color=THEME.ribbon_group_bg, height=int(36*s), corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="  EXPLORER", font=ctk.CTkFont(size=int(11*s), weight="bold"),
                     text_color=THEME.text_secondary).pack(side="left", padx=int(8*s))
        ctk.CTkButton(header, text="📁", width=int(28*s), height=int(28*s), fg_color="transparent",
                      hover_color=THEME.bg_hover, font=ctk.CTkFont(size=int(14*s)),
                      command=self._open_folder).pack(side="right", padx=int(4*s))
        ctk.CTkButton(header, text="⟳", width=int(28*s), height=int(28*s), fg_color="transparent",
                      hover_color=THEME.bg_hover, font=ctk.CTkFont(size=int(14*s)),
                      command=self._refresh).pack(side="right", padx=int(2*s))
        
        tree_frame = ctk.CTkFrame(self, fg_color=THEME.bg_dark)
        tree_frame.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("File.Treeview", background=THEME.bg_dark, foreground=THEME.text_secondary,
                       fieldbackground=THEME.bg_dark, borderwidth=0, rowheight=int(26*s),
                       font=("Segoe UI", int(10*s)))
        style.map("File.Treeview", background=[("selected", THEME.selection_bg)])
        
        self.tree = ttk.Treeview(tree_frame, style="File.Treeview", show="tree", selectmode="browse")
        scroll = ctk.CTkScrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._on_double_click(e))
        self.tree.bind("<<TreeviewOpen>>", lambda e: self._on_expand(e))
        
    def _open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.set_root(folder)
            
    def _refresh(self):
        if self.current_path:
            self.set_root(str(self.current_path))
            
    def set_root(self, path: str):
        self.current_path = Path(path)
        for item in self.tree.get_children():
            self.tree.delete(item)
        icon = FILE_ICONS.get("folder", "📁")
        root_id = self.tree.insert("", "end", text=f"{icon} {self.current_path.name}", values=(str(self.current_path), "folder"), open=True)
        self._populate(root_id, self.current_path)
        
    def _populate(self, parent: str, path: Path):
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if item.name.startswith('.') or item.name == '__pycache__' or item.name == 'node_modules':
                    continue
                if item.is_dir():
                    icon = FILE_ICONS.get("folder", "📁")
                    fid = self.tree.insert(parent, "end", text=f"{icon} {item.name}", values=(str(item), "folder"))
                    self.tree.insert(fid, "end", text="...")
                else:
                    icon = get_file_icon(str(item))
                    self.tree.insert(parent, "end", text=f"{icon} {item.name}", values=(str(item), "file"))
        except PermissionError:
            pass
            
    def _on_expand(self, event):
        item = self.tree.focus()
        children = self.tree.get_children(item)
        if children and self.tree.item(children[0], "text") == "...":
            self.tree.delete(children[0])
            vals = self.tree.item(item, "values")
            if vals and vals[1] == "folder":
                self._populate(item, Path(vals[0]))
                
    def _on_double_click(self, event):
        item = self.tree.focus()
        if item:
            vals = self.tree.item(item, "values")
            if vals and vals[1] == "file":
                self.on_file_select(vals[0])

# =============================================================================
# FIND/REPLACE BAR
# =============================================================================

class FindReplaceBar(ctk.CTkFrame):
    def __init__(self, master, on_find, on_replace, on_replace_all, on_close, on_find_in_files, settings: EditorSettings, **kwargs):
        s = settings.ui_scale
        super().__init__(master, fg_color=THEME.ribbon_group_bg, height=int(44*s), corner_radius=0, **kwargs)
        self.settings = settings
        self.on_find = on_find
        self.on_replace = on_replace
        self.on_replace_all = on_replace_all
        self.on_close = on_close
        self.on_find_in_files = on_find_in_files
        self._create()
        
    def _create(self):
        s = self.settings.ui_scale
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=int(10*s), pady=int(6*s))
        
        self.find_entry = ctk.CTkEntry(container, width=int(200*s), height=int(28*s),
                                       placeholder_text="Find...", fg_color=THEME.bg_darkest,
                                       font=ctk.CTkFont(size=int(11*s)))
        self.find_entry.pack(side="left", padx=(0, int(6*s)))
        self.find_entry.bind("<Return>", lambda e: self.on_find(self.find_entry.get(), 1))
        
        self.replace_entry = ctk.CTkEntry(container, width=int(200*s), height=int(28*s),
                                          placeholder_text="Replace...", fg_color=THEME.bg_darkest,
                                          font=ctk.CTkFont(size=int(11*s)))
        self.replace_entry.pack(side="left", padx=(0, int(10*s)))
        
        btn_cfg = {"height": int(26*s), "fg_color": THEME.bg_light, "hover_color": THEME.bg_hover, "font": ctk.CTkFont(size=int(10*s)), "corner_radius": int(4*s)}
        ctk.CTkButton(container, text="◀", width=int(30*s), command=lambda: self.on_find(self.find_entry.get(), -1), **btn_cfg).pack(side="left", padx=int(1*s))
        ctk.CTkButton(container, text="▶", width=int(30*s), command=lambda: self.on_find(self.find_entry.get(), 1), **btn_cfg).pack(side="left", padx=int(1*s))
        ctk.CTkButton(container, text="Replace", width=int(65*s), command=lambda: self.on_replace(self.find_entry.get(), self.replace_entry.get()), **btn_cfg).pack(side="left", padx=int(4*s))
        ctk.CTkButton(container, text="All", width=int(40*s), command=lambda: self.on_replace_all(self.find_entry.get(), self.replace_entry.get()), **btn_cfg).pack(side="left", padx=int(1*s))
        ctk.CTkButton(container, text="📁 Files", width=int(55*s), command=self.on_find_in_files, **btn_cfg).pack(side="left", padx=int(4*s))
        
        opts = ctk.CTkFrame(container, fg_color="transparent")
        opts.pack(side="left", padx=int(10*s))
        self.case_var = ctk.BooleanVar(value=self.settings.search_case_sensitive)
        self.regex_var = ctk.BooleanVar(value=self.settings.search_regex)
        self.word_var = ctk.BooleanVar(value=self.settings.search_whole_word)
        ctk.CTkCheckBox(opts, text="Aa", variable=self.case_var, width=int(40*s), font=ctk.CTkFont(size=int(9*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(side="left", padx=int(2*s))
        ctk.CTkCheckBox(opts, text=".*", variable=self.regex_var, width=int(40*s), font=ctk.CTkFont(size=int(9*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(side="left", padx=int(2*s))
        ctk.CTkCheckBox(opts, text="\\b", variable=self.word_var, width=int(40*s), font=ctk.CTkFont(size=int(9*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(side="left", padx=int(2*s))
        
        ctk.CTkButton(container, text="✕", width=int(28*s), height=int(28*s), fg_color="transparent",
                      hover_color=THEME.bg_hover, font=ctk.CTkFont(size=int(14*s)), command=self.on_close).pack(side="right")
        self.result_label = ctk.CTkLabel(container, text="", text_color=THEME.text_secondary, font=ctk.CTkFont(size=int(10*s)))
        self.result_label.pack(side="right", padx=int(10*s))

# =============================================================================
# CLIPBOARD PANEL
# =============================================================================

class ClipboardPanel(ctk.CTkFrame):
    def __init__(self, master, clipboard_mgr: SystemClipboardManager, on_paste: Callable, settings: EditorSettings, **kwargs):
        super().__init__(master, fg_color=THEME.bg_dark, **kwargs)
        self.clipboard_mgr = clipboard_mgr
        self.on_paste = on_paste
        self.settings = settings
        self._create()
        self._refresh_loop()
        
    def _create(self):
        s = self.settings.ui_scale
        header = ctk.CTkFrame(self, fg_color=THEME.ribbon_group_bg, height=int(36*s), corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="  CLIPBOARD", font=ctk.CTkFont(size=int(11*s), weight="bold"),
                     text_color=THEME.text_secondary).pack(side="left", padx=int(8*s))
        ctk.CTkButton(header, text="🗑", width=int(28*s), height=int(28*s), fg_color="transparent",
                      hover_color=THEME.bg_hover, font=ctk.CTkFont(size=int(14*s)),
                      command=self._clear_all).pack(side="right", padx=int(4*s))
        
        list_frame = ctk.CTkFrame(self, fg_color=THEME.bg_darkest)
        list_frame.pack(fill="both", expand=True, padx=int(4*s), pady=int(4*s))
        
        self.listbox = tk.Listbox(list_frame, bg=THEME.bg_darkest, fg=THEME.text_primary,
                                  selectbackground=THEME.selection_bg, font=("Consolas", int(10*s)),
                                  borderwidth=0, highlightthickness=0, activestyle='none')
        scroll = ctk.CTkScrollbar(list_frame, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-1>", lambda e: self._paste())
        self.listbox.bind("<Button-3>", lambda e: self._context_menu(e))
        
        btn_bar = ctk.CTkFrame(self, fg_color=THEME.ribbon_group_bg, height=int(32*s))
        btn_bar.pack(fill="x")
        btn_bar.pack_propagate(False)
        btn_cfg = {"height": int(24*s), "fg_color": THEME.bg_light, "hover_color": THEME.bg_hover, "font": ctk.CTkFont(size=int(9*s))}
        ctk.CTkButton(btn_bar, text="📋 Paste", width=int(60*s), command=self._paste, **btn_cfg).pack(side="left", padx=int(3*s), pady=int(4*s))
        ctk.CTkButton(btn_bar, text="📌 Pin", width=int(50*s), command=self._pin, **btn_cfg).pack(side="left", padx=int(3*s), pady=int(4*s))
        ctk.CTkButton(btn_bar, text="🗑 Del", width=int(50*s), command=self._delete, **btn_cfg).pack(side="left", padx=int(3*s), pady=int(4*s))
        
        self.ctx_menu = tk.Menu(self.listbox, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        self.ctx_menu.add_command(label="Paste to Editor", command=self._paste)
        self.ctx_menu.add_command(label="Copy", command=self._copy)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="Pin/Unpin", command=self._pin)
        self.ctx_menu.add_command(label="Delete", command=self._delete)
        
    def _refresh_loop(self):
        self._refresh()
        self.after(1000, self._refresh_loop)
        
    def _refresh(self):
        sel = self.listbox.curselection()
        old_idx = sel[0] if sel else -1
        yview = self.listbox.yview()
        self.listbox.delete(0, "end")
        for i, item in enumerate(self.clipboard_mgr.history):
            prefix = "📌 " if item.pinned else "   "
            preview = item.text.replace("\n", "↵ ")[:60]
            self.listbox.insert("end", f"{prefix}{preview}")
            if item.pinned:
                self.listbox.itemconfig(i, fg=THEME.accent_primary)
        if 0 <= old_idx < self.listbox.size():
            self.listbox.selection_set(old_idx)
        self.listbox.yview_moveto(yview[0])
        
    def _context_menu(self, event):
        idx = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx)
        self.ctx_menu.tk_popup(event.x_root, event.y_root)
        
    def _copy(self):
        sel = self.listbox.curselection()
        if sel:
            text = self.clipboard_mgr.get(sel[0])
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
                
    def _paste(self):
        sel = self.listbox.curselection()
        if sel:
            text = self.clipboard_mgr.get(sel[0])
            if text:
                self.on_paste(text)
                
    def _pin(self):
        sel = self.listbox.curselection()
        if sel:
            self.clipboard_mgr.pin(sel[0])
            self._refresh()
            
    def _delete(self):
        sel = self.listbox.curselection()
        if sel:
            self.clipboard_mgr.delete(sel[0])
            self._refresh()
            
    def _clear_all(self):
        if messagebox.askyesno("Clear All", "Clear all clipboard history? (Pinned items kept)"):
            self.clipboard_mgr.clear()
            self._refresh()

# =============================================================================
# COMMAND PALETTE
# =============================================================================

class CommandPalette(ctk.CTkToplevel):
    def __init__(self, master, commands: List[Tuple[str, str, Callable]], settings: EditorSettings):
        super().__init__(master)
        self.settings = settings
        self.commands = commands
        self.filtered = commands.copy()
        
        s = settings.ui_scale
        self.title("")
        self.geometry(f"{int(600*s)}x{int(400*s)}")
        self.configure(fg_color=THEME.bg_dark)
        self.transient(master)
        self.grab_set()
        self.overrideredirect(True)
        
        # Center on parent
        self.update_idletasks()
        px = master.winfo_x() + (master.winfo_width() - int(600*s)) // 2
        py = master.winfo_y() + int(100*s)
        self.geometry(f"+{px}+{py}")
        
        # Search entry
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self._on_search)
        
        self.entry = ctk.CTkEntry(self, textvariable=self.search_var, width=int(580*s), height=int(40*s),
                                  placeholder_text="Type a command...", fg_color=THEME.bg_darkest,
                                  font=ctk.CTkFont(size=int(14*s)), corner_radius=0)
        self.entry.pack(fill="x", padx=int(10*s), pady=int(10*s))
        self.entry.focus_set()
        
        # Results list
        self.listbox = tk.Listbox(self, bg=THEME.bg_darkest, fg=THEME.text_primary,
                                 selectbackground=THEME.selection_bg, font=("Segoe UI", int(11*s)),
                                 borderwidth=0, highlightthickness=0, activestyle='none')
        self.listbox.pack(fill="both", expand=True, padx=int(10*s), pady=(0, int(10*s)))
        
        self._populate()
        if self.listbox.size() > 0:
            self.listbox.selection_set(0)
            
        self.entry.bind("<Return>", lambda e: self._execute(e))
        self.entry.bind("<Escape>", lambda e: self.destroy())
        self.entry.bind("<Up>", lambda e: self._move_selection(e))
        self.entry.bind("<Down>", lambda e: self._move_selection(e))
        self.listbox.bind("<Double-1>", lambda e: self._execute(e))
        self.bind("<FocusOut>", lambda e: self.after(100, self._check_focus))
        
    def _check_focus(self):
        if not self.focus_get():
            self.destroy()
            
    def _populate(self):
        self.listbox.delete(0, "end")
        for name, shortcut, _ in self.filtered:
            display = f"{name}  ({shortcut})" if shortcut else name
            self.listbox.insert("end", display)
            
    def _on_search(self, *args):
        query = self.search_var.get().lower()
        if self.settings.fuzzy_search:
            self.filtered = [c for c in self.commands if all(ch in c[0].lower() for ch in query)]
        else:
            self.filtered = [c for c in self.commands if query in c[0].lower()]
        self._populate()
        if self.listbox.size() > 0:
            self.listbox.selection_set(0)
            
    def _move_selection(self, event):
        if self.listbox.size() == 0:
            return
        sel = self.listbox.curselection()
        idx = sel[0] if sel else 0
        if event.keysym == "Up":
            idx = max(0, idx - 1)
        else:
            idx = min(self.listbox.size() - 1, idx + 1)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx)
        self.listbox.see(idx)
        return "break"
        
    def _execute(self, event=None):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.filtered):
            _, _, callback = self.filtered[sel[0]]
            self.destroy()
            callback()

# =============================================================================
# RIBBON INTERFACE
# =============================================================================

class RibbonButton(ctk.CTkFrame):
    def __init__(self, master, icon: str, text: str, command: Callable, settings: EditorSettings, large: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        s = settings.ui_scale
        self.command = command
        
        if large:
            self.configure(width=int(58*s), height=int(66*s))
            self.btn = ctk.CTkButton(self, text=icon, width=int(40*s), height=int(36*s),
                                    fg_color="transparent", hover_color=THEME.ribbon_tab_hover,
                                    font=ctk.CTkFont(size=int(18*s)), command=command, corner_radius=int(4*s))
            self.btn.pack(pady=(int(4*s), 0))
            self.lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=int(9*s)), text_color=THEME.text_secondary)
            self.lbl.pack()
        else:
            self.configure(height=int(26*s))
            self.btn = ctk.CTkButton(self, text=f"{icon} {text}", height=int(24*s),
                                    fg_color="transparent", hover_color=THEME.ribbon_tab_hover,
                                    font=ctk.CTkFont(size=int(10*s)), command=command,
                                    corner_radius=int(3*s), anchor="w")
            self.btn.pack(fill="x", padx=int(2*s))

class RibbonGroup(ctk.CTkFrame):
    def __init__(self, master, title: str, settings: EditorSettings, **kwargs):
        super().__init__(master, fg_color=THEME.ribbon_group_bg, corner_radius=int(4*settings.ui_scale), **kwargs)
        s = settings.ui_scale
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=int(6*s), pady=(int(4*s), 0))
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=int(9*s)), text_color=THEME.text_muted, height=int(16*s)).pack(side="bottom", pady=(0, int(2*s)))

class RibbonTab(ctk.CTkFrame):
    def __init__(self, master, settings: EditorSettings, **kwargs):
        super().__init__(master, fg_color=THEME.ribbon_bg, height=int(90*settings.ui_scale), corner_radius=0, **kwargs)
        self.settings = settings
        self.pack_propagate(False)
        self.groups: List[RibbonGroup] = []
        
    def add_group(self, title: str) -> RibbonGroup:
        s = self.settings.ui_scale
        if self.groups:
            sep = ctk.CTkFrame(self, width=int(1*s), fg_color=THEME.ribbon_separator)
            sep.pack(side="left", fill="y", padx=int(4*s), pady=int(6*s))
        group = RibbonGroup(self, title, self.settings)
        group.pack(side="left", fill="y", padx=int(4*s), pady=int(4*s))
        self.groups.append(group)
        return group

class Ribbon(ctk.CTkFrame):
    def __init__(self, master, settings: EditorSettings, **kwargs):
        super().__init__(master, fg_color=THEME.ribbon_bg, corner_radius=0, **kwargs)
        self.settings = settings
        self.tabs: Dict[str, RibbonTab] = {}
        self.tab_buttons: Dict[str, ctk.CTkButton] = {}
        self.active_tab = None
        self.pinned = settings.ribbon_pinned
        self.collapsed = not self.pinned  # If not pinned, start collapsed
        self._hover_active = False
        self._hide_timer = None
        self._create()
        
    def _create(self):
        s = self.settings.ui_scale
        self.tab_bar = ctk.CTkFrame(self, fg_color=THEME.ribbon_tab_bg, height=int(30*s), corner_radius=0)
        self.tab_bar.pack(fill="x")
        self.tab_bar.pack_propagate(False)
        
        # Logo
        ctk.CTkLabel(self.tab_bar, text="  Mattpad", font=ctk.CTkFont(size=int(12*s), weight="bold"),
                     text_color=THEME.accent_primary).pack(side="left", padx=int(8*s))
                     
        self.tab_btn_frame = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.tab_btn_frame.pack(side="left", fill="y", padx=int(10*s))
        
        # Pin button (keeps ribbon open)
        self.pin_btn = ctk.CTkButton(self.tab_bar, text="📌" if self.pinned else "📍", 
                                    width=int(28*s), height=int(24*s),
                                    fg_color=THEME.ribbon_tab_active if self.pinned else "transparent",
                                    hover_color=THEME.ribbon_tab_hover,
                                    font=ctk.CTkFont(size=int(12*s)), command=self._toggle_pin)
        self.pin_btn.pack(side="right", padx=int(4*s))
        
        self.content_frame = ctk.CTkFrame(self, fg_color=THEME.ribbon_bg, corner_radius=0)
        if not self.collapsed:
            self.content_frame.pack(fill="x")
        
        # Bind hover events to tab_bar (always visible)
        self.tab_bar.bind("<Enter>", lambda e: self._on_enter(e))
        self.tab_bar.bind("<Leave>", lambda e: self._on_leave(e))
        self.content_frame.bind("<Enter>", lambda e: self._on_enter(e))
        self.content_frame.bind("<Leave>", lambda e: self._on_leave(e))
        
        # Bind to self as well
        self.bind("<Enter>", lambda e: self._on_enter(e))
        self.bind("<Leave>", lambda e: self._on_leave(e))
        
    def _bind_hover_recursive(self, widget):
        """Bind hover events to widget and all children"""
        try:
            widget.bind("<Enter>", lambda e: self._on_enter(e), add=True)
            widget.bind("<Leave>", lambda e: self._on_leave(e), add=True)
            for child in widget.winfo_children():
                self._bind_hover_recursive(child)
        except Exception:
            pass
        
    def add_tab(self, name: str) -> RibbonTab:
        s = self.settings.ui_scale
        btn = ctk.CTkButton(self.tab_btn_frame, text=name, width=int(70*s), height=int(26*s),
                           fg_color="transparent", hover_color=THEME.ribbon_tab_hover,
                           font=ctk.CTkFont(size=int(11*s)), corner_radius=0,
                           command=lambda n=name: self._on_tab_click(n))
        btn.pack(side="left", padx=int(1*s), pady=int(2*s))
        btn.bind("<Double-1>", lambda e: self._toggle_pin())
        btn.bind("<Enter>", lambda e: self._on_enter(e), add=True)
        btn.bind("<Leave>", lambda e: self._on_leave(e), add=True)
        self.tab_buttons[name] = btn
        
        tab = RibbonTab(self.content_frame, self.settings)
        self.tabs[name] = tab
        
        # Bind hover to tab content
        self._bind_hover_recursive(tab)
        
        if self.active_tab is None:
            self.show_tab(name)
        return tab
    
    def _on_enter(self, event=None):
        """Mouse entered ribbon area - show if not pinned"""
        self._hover_active = True
        # Cancel any pending hide
        if self._hide_timer:
            self.after_cancel(self._hide_timer)
            self._hide_timer = None
        
        # Expand ribbon if collapsed
        if self.collapsed:
            self._expand()
    
    def _on_leave(self, event=None):
        """Mouse left ribbon area - schedule hide if not pinned"""
        # Check if mouse is still within ribbon bounds
        try:
            x, y = self.winfo_pointerxy()
            rx, ry = self.winfo_rootx(), self.winfo_rooty()
            rw, rh = self.winfo_width(), self.winfo_height()
            
            # If mouse is still inside ribbon, don't hide
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                return
        except Exception:
            pass
        
        self._hover_active = False
        
        # Only auto-hide if not pinned
        if not self.pinned:
            # Quick hide - 100ms delay to prevent flicker but feel responsive
            if self._hide_timer:
                self.after_cancel(self._hide_timer)
            self._hide_timer = self.after(100, self._check_and_hide)
    
    def _check_and_hide(self):
        """Check if we should hide after delay"""
        self._hide_timer = None
        if not self._hover_active and not self.pinned and not self.collapsed:
            self._collapse()
        
    def _on_tab_click(self, name: str):
        """Handle tab click - show tab and expand if collapsed"""
        if self.collapsed:
            self._expand()
        self.show_tab(name)
        
    def show_tab(self, name: str):
        if name not in self.tabs:
            return
        for n, tab in self.tabs.items():
            tab.pack_forget()
            self.tab_buttons[n].configure(fg_color="transparent")
        self.tabs[name].pack(fill="x")
        self.tab_buttons[name].configure(fg_color=THEME.ribbon_tab_active)
        self.active_tab = name
    
    def _expand(self):
        """Expand the ribbon content"""
        if not self.collapsed:
            return
        self.collapsed = False
        self.content_frame.pack(fill="x")
        if self.active_tab:
            self.show_tab(self.active_tab)
    
    def _collapse(self):
        """Collapse the ribbon content"""
        if self.collapsed:
            return
        self.collapsed = True
        self.content_frame.pack_forget()
                
    def _toggle_pin(self):
        """Toggle pin state - when pinned, ribbon stays open"""
        self.pinned = not self.pinned
        self.settings.ribbon_pinned = self.pinned
        
        if self.pinned:
            self.pin_btn.configure(text="📌", fg_color=THEME.ribbon_tab_active)
            # Expand if collapsed
            if self.collapsed:
                self._expand()
        else:
            self.pin_btn.configure(text="📍", fg_color="transparent")
            # Will auto-collapse on mouse leave
            
    def auto_hide(self):
        """Called when focus leaves ribbon - collapse if not pinned"""
        if not self.pinned and not self.collapsed:
            self._collapse()

# =============================================================================
# WELCOME SCREEN
# =============================================================================

class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, master, settings: EditorSettings, on_new: Callable, on_open: Callable, 
                 on_recent: Callable, recent_files: List[str], **kwargs):
        super().__init__(master, fg_color=THEME.bg_darkest, **kwargs)
        self.settings = settings
        self.on_new = on_new
        self.on_open = on_open
        self.on_recent = on_recent
        self._create(recent_files)
        
    def _create(self, recent_files: List[str]):
        s = self.settings.ui_scale
        
        # Center container
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")
        
        # Logo and title
        ctk.CTkLabel(center, text="📝", font=ctk.CTkFont(size=int(64*s))).pack(pady=(0, int(10*s)))
        ctk.CTkLabel(center, text="Mattpad", font=ctk.CTkFont(size=int(36*s), weight="bold"),
                    text_color=THEME.accent_primary).pack()
        ctk.CTkLabel(center, text=f"v{VERSION} - Professional Text Editor", 
                    font=ctk.CTkFont(size=int(12*s)), text_color=THEME.text_secondary).pack(pady=(0, int(30*s)))
        
        # Action buttons
        btn_frame = ctk.CTkFrame(center, fg_color="transparent")
        btn_frame.pack(pady=int(20*s))
        
        btn_cfg = {"width": int(180*s), "height": int(40*s), "corner_radius": int(8*s), "font": ctk.CTkFont(size=int(12*s))}
        ctk.CTkButton(btn_frame, text="📄  New File", fg_color=THEME.accent_primary, 
                     command=self.on_new, **btn_cfg).pack(pady=int(5*s))
        ctk.CTkButton(btn_frame, text="📂  Open File", fg_color=THEME.bg_medium,
                     hover_color=THEME.bg_hover, command=self.on_open, **btn_cfg).pack(pady=int(5*s))
        ctk.CTkButton(btn_frame, text="📁  Open Folder", fg_color=THEME.bg_medium,
                     hover_color=THEME.bg_hover, command=lambda: self._open_folder(), **btn_cfg).pack(pady=int(5*s))
        
        # Recent files
        if recent_files:
            ctk.CTkLabel(center, text="Recent Files", font=ctk.CTkFont(size=int(14*s), weight="bold"),
                        text_color=THEME.text_secondary).pack(pady=(int(30*s), int(10*s)))
            
            recent_frame = ctk.CTkFrame(center, fg_color=THEME.bg_dark, corner_radius=int(8*s))
            recent_frame.pack()
            
            for i, filepath in enumerate(recent_files[:8]):
                if os.path.exists(filepath):
                    icon = get_file_icon(filepath)
                    name = os.path.basename(filepath)
                    folder = os.path.dirname(filepath)
                    
                    item = ctk.CTkFrame(recent_frame, fg_color="transparent", cursor="hand2")
                    item.pack(fill="x", padx=int(8*s), pady=int(4*s))
                    item.bind("<Button-1>", lambda e, f=filepath: self.on_recent(f))
                    
                    ctk.CTkLabel(item, text=f"{icon} {name}", font=ctk.CTkFont(size=int(11*s)),
                                text_color=THEME.text_primary, anchor="w").pack(side="left")
                    ctk.CTkLabel(item, text=f"  {folder[:50]}", font=ctk.CTkFont(size=int(9*s)),
                                text_color=THEME.text_muted, anchor="w").pack(side="left")
                    
                    for child in item.winfo_children():
                        child.bind("<Button-1>", lambda e, f=filepath: self.on_recent(f))
                        
        # Tips
        tips = [
            "Ctrl+Shift+P - Command Palette",
            "Ctrl+Scroll - Zoom In/Out",
            "Ctrl+B - Toggle Sidebar",
            "Ctrl+Shift+T - Reopen Closed Tab",
        ]
        tip = tips[int(time.time()) % len(tips)]
        ctk.CTkLabel(center, text=f"💡 {tip}", font=ctk.CTkFont(size=int(10*s)),
                    text_color=THEME.text_muted).pack(pady=(int(30*s), 0))
                    
    def _open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.on_open(folder)

# =============================================================================
# SETTINGS DIALOG
# =============================================================================

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, settings: EditorSettings, on_save: Callable):
        super().__init__(master)
        self.settings = settings
        self.on_save = on_save
        
        s = settings.ui_scale
        w, h = int(700*s), int(550*s)
        self.title("Settings")
        self.configure(fg_color=THEME.bg_dark)
        self.transient(master)
        self.grab_set()
        self.resizable(True, True)
        
        # Center on parent
        self.update_idletasks()
        px = master.winfo_x() + (master.winfo_width() - w) // 2
        py = master.winfo_y() + (master.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")
        
        self.after(100, lambda: set_dark_title_bar(self))
        
        self._create()
        
    def _create(self):
        s = self.settings.ui_scale
        
        # Tab view for categories
        self.tabview = ctk.CTkTabview(self, fg_color=THEME.bg_darkest, segmented_button_fg_color=THEME.ribbon_tab_bg,
                                     segmented_button_selected_color=THEME.accent_primary)
        self.tabview.pack(fill="both", expand=True, padx=int(10*s), pady=int(10*s))
        
        # === EDITOR TAB ===
        editor = self.tabview.add("Editor")
        self._create_section(editor, "Font & Display", [
            ("Font Family", "combo", "font_family", ["Consolas", "Cascadia Code", "Fira Code", "JetBrains Mono", "Monaco", "Courier New"]),
            ("Font Size", "spin", "font_size", (8, 48)),
            ("Tab Size", "combo", "tab_size", ["2", "4", "8"]),
            ("Use Spaces for Tab", "check", "use_spaces", None),
            ("Word Wrap", "check", "word_wrap", None),
            ("Show Whitespace", "check", "show_whitespace", None),
            ("Show Indent Guides", "check", "show_indent_guides", None),
        ])
        self._create_section(editor, "Line Display", [
            ("Show Line Numbers", "check", "show_line_numbers", None),
            ("Show Minimap", "check", "show_minimap", None),
            ("Highlight Current Line", "check", "highlight_current_line", None),
        ])
        
        # === BEHAVIOR TAB ===
        behavior = self.tabview.add("Behavior")
        self._create_section(behavior, "Editing", [
            ("Auto Indent", "check", "auto_indent", None),
            ("Auto-close Brackets ( [ {", "check", "auto_close_brackets", None),
            ("Auto-close Quotes \" '", "check", "auto_close_quotes", None),
            ("Smart Backspace", "check", "smart_backspace", None),
        ])
        self._create_section(behavior, "Saving", [
            ("Auto-save Enabled", "check", "auto_save_enabled", None),
            ("Auto-save Interval (sec)", "spin", "auto_save_interval", (30, 600)),
            ("Auto-save to Disk", "check", "auto_save_to_disk", None),
            ("Create Backups", "check", "create_backups", None),
            ("Backup Count", "spin", "backup_count", (1, 20)),
            ("Prompt Save on Close", "check", "prompt_save_on_close", None),
        ])
        
        # === FEATURES TAB ===
        features = self.tabview.add("Features")
        self._create_section(features, "Code Features", [
            ("Spellcheck", "check", "spellcheck_enabled", None),
            ("Multi-cursor Editing", "check", "multi_cursor_enabled", None),
            ("Code Folding", "check", "code_folding_enabled", None),
            ("Bracket Matching", "check", "bracket_matching_enabled", None),
            ("Bracket Highlighting", "check", "bracket_highlight_enabled", None),
            ("Snippets", "check", "snippets_enabled", None),
            ("Macros", "check", "macros_enabled", None),
        ])
        self._create_section(features, "Tools", [
            ("Split View", "check", "split_view_enabled", None),
            ("Terminal", "check", "terminal_enabled", None),
            ("Markdown Preview", "check", "markdown_preview_enabled", None),
            ("Git Integration", "check", "git_integration_enabled", None),
            ("Command Palette", "check", "command_palette_enabled", None),
        ])
        
        # === APPEARANCE TAB ===
        appearance = self.tabview.add("Appearance")
        self._create_section(appearance, "Theme", [
            ("Theme", "combo", "theme_name", list(THEMES.keys())),
            ("UI Scale", "combo", "ui_scale", ["1.0", "1.25", "1.5", "1.75", "2.0"]),
        ])
        self._create_section(appearance, "Panels", [
            ("Show Sidebar", "check", "sidebar_visible", None),
            ("Sidebar Width", "spin", "sidebar_width", (150, 500)),
            ("Show Clipboard Panel", "check", "clipboard_panel_visible", None),
            ("Clipboard Panel Width", "spin", "clipboard_panel_width", (150, 600)),
            ("Show Status Bar", "check", "show_status_bar", None),
            ("Show Welcome Screen", "check", "show_welcome_screen", None),
            ("Toast Notifications", "check", "toast_notifications", None),
            ("Toast Duration (ms)", "spin", "toast_duration", (1000, 10000)),
        ])
        
        # === ADVANCED TAB ===
        advanced = self.tabview.add("Advanced")
        self._create_section(advanced, "Session", [
            ("Restore Session on Start", "check", "restore_session", None),
        ])
        self._create_section(advanced, "Terminal", [
            ("Shell Path", "entry", "terminal_shell", None),
            ("Terminal Font Size", "spin", "terminal_font_size", (8, 24)),
        ])
        self._create_section(advanced, "Search", [
            ("Highlight All Matches", "check", "search_highlight_all", None),
            ("Fuzzy Search in Palette", "check", "fuzzy_search", None),
        ])
        self._create_section(advanced, "Accessibility", [
            ("Reduced Motion", "check", "reduced_motion", None),
            ("Cursor Blink Rate (ms, 0=off)", "spin", "cursor_blink_rate", (0, 1500)),
        ])
        
        # Save button
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=int(10*s), pady=int(10*s))
        ctk.CTkButton(btn_frame, text="Save & Apply", fg_color=THEME.accent_primary,
                     command=self._save).pack(side="right", padx=int(5*s))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color=THEME.bg_medium,
                     command=self.destroy).pack(side="right", padx=int(5*s))
        ctk.CTkButton(btn_frame, text="Reset to Defaults", fg_color=THEME.accent_red,
                     command=self._reset).pack(side="left", padx=int(5*s))
        
    def _create_section(self, parent, title: str, items: List[Tuple]):
        s = self.settings.ui_scale
        frame = ctk.CTkFrame(parent, fg_color=THEME.ribbon_group_bg, corner_radius=int(8*s))
        frame.pack(fill="x", padx=int(10*s), pady=int(5*s))
        
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=int(12*s), weight="bold"),
                    text_color=THEME.text_primary).pack(anchor="w", padx=int(10*s), pady=(int(8*s), int(4*s)))
        
        for label, type_, attr, options in items:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=int(10*s), pady=int(3*s))
            
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=int(10*s)),
                        text_color=THEME.text_secondary, width=int(200*s), anchor="w").pack(side="left")
            
            current = getattr(self.settings, attr)
            
            if type_ == "check":
                var = ctk.BooleanVar(value=current)
                cb = ctk.CTkCheckBox(row, text="", variable=var, fg_color=THEME.accent_primary,
                                    width=int(40*s), height=int(24*s))
                cb.pack(side="left")
                setattr(self, f"var_{attr}", var)
            elif type_ == "combo":
                var = ctk.StringVar(value=str(current))
                cb = ctk.CTkComboBox(row, values=options, variable=var, width=int(150*s),
                                    fg_color=THEME.bg_darkest, button_color=THEME.bg_medium)
                cb.pack(side="left")
                setattr(self, f"var_{attr}", var)
            elif type_ == "spin":
                var = ctk.StringVar(value=str(current))
                frame2 = ctk.CTkFrame(row, fg_color="transparent")
                frame2.pack(side="left")
                entry = ctk.CTkEntry(frame2, textvariable=var, width=int(80*s), fg_color=THEME.bg_darkest)
                entry.pack(side="left")
                setattr(self, f"var_{attr}", var)
            elif type_ == "entry":
                var = ctk.StringVar(value=str(current or ""))
                entry = ctk.CTkEntry(row, textvariable=var, width=int(200*s), fg_color=THEME.bg_darkest)
                entry.pack(side="left")
                setattr(self, f"var_{attr}", var)
                
    def _save(self):
        for attr in dir(self):
            if attr.startswith("var_"):
                setting_name = attr[4:]
                var = getattr(self, attr)
                value = var.get()
                
                # Type conversion
                current = getattr(self.settings, setting_name, None)
                if isinstance(current, bool):
                    value = bool(value)
                elif isinstance(current, int):
                    try:
                        value = int(float(value))
                    except ValueError:
                        continue
                elif isinstance(current, float):
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                        
                setattr(self.settings, setting_name, value)
                
        self.on_save()
        self.destroy()
        
    def _reset(self):
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?\nThis cannot be undone."):
            default = EditorSettings()
            for attr in dir(default):
                if not attr.startswith("_"):
                    setattr(self.settings, attr, getattr(default, attr))
            self.on_save()
            self.destroy()

# =============================================================================
# MAIN APPLICATION
# =============================================================================

class Mattpad(ctk.CTk):
    def __init__(self):
        super().__init__()
        logger.info("Initializing Mattpad v5.0")
        
        # Initialize thread-safe dispatcher FIRST
        global _dispatcher
        _dispatcher = ThreadSafeDispatcher(self)
        
        # Load settings first
        self.settings = EditorSettings()
        self._load_settings()
        
        # Apply theme
        global THEME
        THEME = get_theme(self.settings.theme_name)
        
        # State
        self.tabs: Dict[str, TabData] = {}
        self.current_tab: Optional[str] = None
        self.text_widgets: Dict[str, tk.Text] = {}
        self.line_numbers: Dict[str, LineNumberCanvas] = {}
        self.minimaps: Dict[str, Minimap] = {}
        self.highlighters: Dict[str, SyntaxHighlighter] = {}
        self.editor_frames: Dict[str, ctk.CTkFrame] = {}
        self.find_bar_visible = False
        self.file_mtimes: Dict[str, float] = {}
        self.welcome_visible = False
        self.tab_order: List[str] = []  # Track tab order for hot exit
        
        # Managers
        self.cache_manager = CacheManager()
        self.closed_tabs_manager = ClosedTabsManager()
        self.backup_manager = BackupManager(self.settings)
        self.cloud_sync = CloudSyncManager(self.settings)
        self.ai_manager = AIManager(self.settings)
        self.spellcheck = SpellCheckManager()
        self.snippets = SnippetsManager()
        self.macros = MacroManager()
        self.hot_exit = HotExitManager()  # Hot exit manager
        
        # Debouncer
        self.debouncer = Debouncer(self, 200)
        self.highlight_debouncer = Debouncer(self, 250)
        
        # Window setup
        self.title("Mattpad")
        self.configure(fg_color=THEME.bg_darkest)
        
        # Set minimum window size
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Set initial geometry first, then apply maximized state with delay
        self.geometry(self.settings.window_geometry or "1400x800")
        
        # Apply maximized state after window is fully initialized
        if self.settings.window_maximized:
            self.after(100, lambda: self.state('zoomed'))
            
        self.after(150, lambda: set_dark_title_bar(self))
        
        # Clipboard manager
        self.system_clipboard = SystemClipboardManager(self)
        
        # Toast manager
        self.toast = ToastManager(self, self.settings)
        
        # Build commands list for palette
        self._build_commands()
        
        # Build UI
        self._create_ribbon()
        self._create_main_layout()
        self._create_statusbar()
        self._bind_shortcuts()
        
        # Check for hot exit snapshot first
        if self.settings.hot_exit_enabled and self.hot_exit.has_snapshot():
            self._restore_hot_exit()
        elif self.settings.show_welcome_screen and not self.settings.recent_files:
            self._show_welcome()
        elif self.settings.restore_session:
            self._restore_session()
            
        if not self.tabs and not self.welcome_visible:
            self._new_file()
            
        # Start timers
        self._start_timers()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        logger.info("Mattpad ready")

    def _build_commands(self):
        """Build command list for command palette"""
        self.commands = [
            ("New File", "Ctrl+N", self._new_file),
            ("Open File", "Ctrl+O", self._open_file),
            ("Save", "Ctrl+S", self._save_file),
            ("Save As", "Ctrl+Shift+S", self._save_file_as),
            ("Save All", "", self._save_all),
            ("Close Tab", "Ctrl+W", self._close_current_tab),
            ("Reopen Closed Tab", "Ctrl+Shift+T", self._reopen_closed_tab),
            ("Undo", "Ctrl+Z", self._undo),
            ("Redo", "Ctrl+Y", self._redo),
            ("Cut", "Ctrl+X", self._cut),
            ("Copy", "Ctrl+C", self._copy),
            ("Paste", "Ctrl+V", self._paste),
            ("Find", "Ctrl+F", self._show_find_bar),
            ("Find in Files", "Ctrl+Shift+F", self._find_in_files),
            ("Go to Line", "Ctrl+G", self._goto_line),
            ("Duplicate Line", "Ctrl+D", self._duplicate_line),
            ("Toggle Comment", "Ctrl+/", self._toggle_comment),
            ("Toggle Sidebar", "Ctrl+B", self._toggle_sidebar),
            ("Toggle Minimap", "", lambda: self._toggle_feature("show_minimap")),
            ("Toggle Line Numbers", "", lambda: self._toggle_feature("show_line_numbers")),
            ("Toggle Word Wrap", "", lambda: self._toggle_feature("word_wrap")),
            ("Zoom In", "Ctrl++", self._zoom_in),
            ("Zoom Out", "Ctrl+-", self._zoom_out),
            ("Reset Zoom", "Ctrl+0", self._zoom_reset),
            ("Settings", "", self._show_settings),
            ("Import Notepad++ Session", "", self._import_notepadpp),
            ("Toggle Theme (Dark/Light)", "", self._toggle_theme),
            ("Show Closed Tabs", "", self._show_closed_tabs),
            ("Show Backups", "", self._show_backups),
            ("Show Dictionary", "", self._show_dictionary),
            ("AI: Summarize", "", lambda: self._ai_action("Summarize")),
            ("AI: Fix Grammar", "", lambda: self._ai_action("Fix Grammar")),
            ("AI: Explain Code", "", lambda: self._ai_action("Explain Code")),
            ("AI: Custom Prompt", "", self._ai_custom_prompt),
            ("Cloud: Sync Now", "", self._do_cloud_sync),
            ("Cloud: Configure GitHub", "", self._configure_github),
            ("Toggle Terminal", "", self._toggle_terminal),
            ("Reload File", "", lambda: self._reload_current()),
            ("Compare Files", "", self._compare_files),
        ]

    def _load_settings(self):
        if not SETTINGS_FILE.exists():
            return
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding='utf-8'))
            for k, v in data.items():
                if hasattr(self.settings, k):
                    setattr(self.settings, k, v)
            for key in ["github_token", "ai_api_key"]:
                secret = SecretStorage.get(key, "")
                if secret:
                    setattr(self.settings, key, secret)
        except Exception as e:
            logger.error(f"Settings load error: {e}")
            
    def _save_settings(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SecretStorage.store("github_token", self.settings.github_token)
            SecretStorage.store("ai_api_key", self.settings.ai_api_key)
            
            data = {}
            for attr in dir(self.settings):
                if not attr.startswith("_") and attr not in ["github_token", "ai_api_key"]:
                    val = getattr(self.settings, attr)
                    if not callable(val):
                        data[attr] = val
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Settings save error: {e}")

    def _create_ribbon(self):
        s = self.settings.ui_scale
        self.ribbon = Ribbon(self, self.settings)
        self.ribbon.pack(fill="x")
        
        # HOME TAB
        home = self.ribbon.add_tab("Home")
        
        file_grp = home.add_group("File")
        file_btns = ctk.CTkFrame(file_grp.content, fg_color="transparent")
        file_btns.pack(side="left", fill="y")
        RibbonButton(file_btns, "📄", "New", self._new_file, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(file_btns, "📂", "Open", self._open_file, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(file_btns, "💾", "Save", self._save_file, self.settings, large=True).pack(side="left", padx=int(2*s))
        
        file_btns2 = ctk.CTkFrame(file_grp.content, fg_color="transparent")
        file_btns2.pack(side="left", fill="y", padx=int(4*s))
        RibbonButton(file_btns2, "📁", "Save As", self._save_file_as, self.settings).pack(fill="x")
        RibbonButton(file_btns2, "💾", "Save All", self._save_all, self.settings).pack(fill="x")
        RibbonButton(file_btns2, "📋", "Import N++", self._import_notepadpp, self.settings).pack(fill="x")
        
        edit_grp = home.add_group("Edit")
        edit_btns = ctk.CTkFrame(edit_grp.content, fg_color="transparent")
        edit_btns.pack(side="left", fill="y")
        RibbonButton(edit_btns, "↩", "Undo", self._undo, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(edit_btns, "↪", "Redo", self._redo, self.settings, large=True).pack(side="left", padx=int(2*s))
        
        edit_btns2 = ctk.CTkFrame(edit_grp.content, fg_color="transparent")
        edit_btns2.pack(side="left", fill="y", padx=int(4*s))
        RibbonButton(edit_btns2, "✂", "Cut", self._cut, self.settings).pack(fill="x")
        RibbonButton(edit_btns2, "📋", "Copy", self._copy, self.settings).pack(fill="x")
        RibbonButton(edit_btns2, "📄", "Paste", self._paste, self.settings).pack(fill="x")
        
        find_grp = home.add_group("Find")
        find_btns = ctk.CTkFrame(find_grp.content, fg_color="transparent")
        find_btns.pack(side="left", fill="y")
        RibbonButton(find_btns, "🔍", "Find", self._show_find_bar, self.settings, large=True).pack(side="left", padx=int(2*s))
        
        find_btns2 = ctk.CTkFrame(find_grp.content, fg_color="transparent")
        find_btns2.pack(side="left", fill="y", padx=int(4*s))
        RibbonButton(find_btns2, "📁", "In Files", self._find_in_files, self.settings).pack(fill="x")
        RibbonButton(find_btns2, "↓", "Go to Line", self._goto_line, self.settings).pack(fill="x")
        RibbonButton(find_btns2, "#", "Comment", self._toggle_comment, self.settings).pack(fill="x")
        
        # VIEW TAB
        view = self.ribbon.add_tab("View")
        
        panels_grp = view.add_group("Panels")
        panels_btns = ctk.CTkFrame(panels_grp.content, fg_color="transparent")
        panels_btns.pack(side="left", fill="y")
        RibbonButton(panels_btns, "📁", "Explorer", self._toggle_sidebar, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(panels_btns, "📋", "Clipboard", self._toggle_clipboard_panel, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(panels_btns, "⌨", "Terminal", self._toggle_terminal, self.settings, large=True).pack(side="left", padx=int(2*s))
        
        editor_grp = view.add_group("Editor")
        editor_btns = ctk.CTkFrame(editor_grp.content, fg_color="transparent")
        editor_btns.pack(side="left", fill="y", padx=int(4*s))
        
        self.wrap_var = tk.BooleanVar(master=self, value=self.settings.word_wrap)
        self.linenum_var = tk.BooleanVar(master=self, value=self.settings.show_line_numbers)
        self.minimap_var = tk.BooleanVar(master=self, value=self.settings.show_minimap)
        ctk.CTkCheckBox(editor_btns, text="Word Wrap", variable=self.wrap_var, command=lambda: self._toggle_word_wrap(),
                       font=ctk.CTkFont(size=int(10*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(editor_btns, text="Line Numbers", variable=self.linenum_var, command=lambda: self._toggle_line_numbers(),
                       font=ctk.CTkFont(size=int(10*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(editor_btns, text="Minimap", variable=self.minimap_var, command=lambda: self._toggle_minimap(),
                       font=ctk.CTkFont(size=int(10*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        
        zoom_grp = view.add_group("Zoom")
        zoom_btns = ctk.CTkFrame(zoom_grp.content, fg_color="transparent")
        zoom_btns.pack(side="left", fill="y")
        RibbonButton(zoom_btns, "➕", "In", self._zoom_in, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(zoom_btns, "➖", "Out", self._zoom_out, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(zoom_btns, "⊙", "Reset", self._zoom_reset, self.settings, large=True).pack(side="left", padx=int(2*s))
        
        # OPTIONS TAB
        options = self.ribbon.add_tab("Options")
        
        prefs_grp = options.add_group("Preferences")
        prefs_btns = ctk.CTkFrame(prefs_grp.content, fg_color="transparent")
        prefs_btns.pack(side="left", fill="y", padx=int(4*s))
        
        self.spell_var = tk.BooleanVar(master=self, value=self.settings.spellcheck_enabled)
        self.autoclose_var = tk.BooleanVar(master=self, value=self.settings.auto_close_brackets)
        self.autosave_var = tk.BooleanVar(master=self, value=self.settings.auto_save_enabled)
        ctk.CTkCheckBox(prefs_btns, text="Spellcheck", variable=self.spell_var, command=lambda: self._toggle_spellcheck(),
                       font=ctk.CTkFont(size=int(10*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(prefs_btns, text="Auto-close Brackets", variable=self.autoclose_var, command=lambda: self._toggle_autoclose(),
                       font=ctk.CTkFont(size=int(10*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(prefs_btns, text="Auto-save", variable=self.autosave_var, command=lambda: self._toggle_autosave(),
                       font=ctk.CTkFont(size=int(10*s)), fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        
        prefs_btns2 = ctk.CTkFrame(prefs_grp.content, fg_color="transparent")
        prefs_btns2.pack(side="left", fill="y", padx=int(4*s))
        RibbonButton(prefs_btns2, "⚙", "All Settings", self._show_settings, self.settings).pack(fill="x")
        RibbonButton(prefs_btns2, "📖", "Dictionary", self._show_dictionary, self.settings).pack(fill="x")
        RibbonButton(prefs_btns2, "🎨", "Themes", self._show_themes, self.settings).pack(fill="x")
        
        scale_grp = options.add_group("UI Scale")
        scale_btns = ctk.CTkFrame(scale_grp.content, fg_color="transparent")
        scale_btns.pack(side="left", fill="y", padx=int(4*s))
        for sc, name in [(1.0, "100%"), (1.25, "125%"), (1.5, "150%"), (2.0, "200%")]:
            RibbonButton(scale_btns, "", name, lambda x=sc: self._set_scale(x), self.settings).pack(fill="x")
        
        # AI TAB
        ai = self.ribbon.add_tab("AI")
        ai_grp = ai.add_group("AI Tools")
        ai_btns = ctk.CTkFrame(ai_grp.content, fg_color="transparent")
        ai_btns.pack(side="left", fill="y")
        RibbonButton(ai_btns, "⚙", "Settings", self._show_ai_settings, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(ai_btns, "✨", "Custom", self._ai_custom_prompt, self.settings, large=True).pack(side="left", padx=int(2*s))
        
        ai_btns2 = ctk.CTkFrame(ai_grp.content, fg_color="transparent")
        ai_btns2.pack(side="left", fill="y", padx=int(4*s))
        for name, _ in AIManager.PROMPTS[:6]:
            RibbonButton(ai_btns2, "✨", name, lambda n=name: self._ai_action(n), self.settings).pack(fill="x")
        
        # CLOUD TAB
        cloud = self.ribbon.add_tab("Cloud")
        cloud_grp = cloud.add_group("Sync")
        cloud_btns = ctk.CTkFrame(cloud_grp.content, fg_color="transparent")
        cloud_btns.pack(side="left", fill="y")
        RibbonButton(cloud_btns, "☁", "Sync Now", self._do_cloud_sync, self.settings, large=True).pack(side="left", padx=int(2*s))
        RibbonButton(cloud_btns, "⚙", "Configure", self._configure_github, self.settings, large=True).pack(side="left", padx=int(2*s))
        
        cloud_btns2 = ctk.CTkFrame(cloud_grp.content, fg_color="transparent")
        cloud_btns2.pack(side="left", fill="y", padx=int(4*s))
        self.sync_status = ctk.CTkLabel(cloud_btns2, text="● Local", font=ctk.CTkFont(size=int(10*s)),
                                        text_color=THEME.text_secondary)
        self.sync_status.pack(anchor="w", pady=int(10*s))

    def _create_main_layout(self):
        s = self.settings.ui_scale
        
        # Main paned window (horizontal) for sidebar | editor | clipboard
        # Sash is the draggable divider between panes
        self.main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, 
                                         bg=THEME.bg_light,
                                         sashwidth=int(6*s),  # Wider for easier grabbing
                                         sashrelief=tk.RAISED,
                                         borderwidth=0,
                                         sashcursor="sb_h_double_arrow",  # Resize cursor
                                         opaqueresize=True)  # Real-time resize
        self.main_paned.pack(fill="both", expand=True)
        
        # Sidebar frame (resizable)
        self.sidebar_frame = ctk.CTkFrame(self.main_paned, fg_color=THEME.bg_dark, corner_radius=0)
        self.sidebar = FileTreeView(self.sidebar_frame, on_file_select=self._open_file,
                                   settings=self.settings)
        self.sidebar.pack(fill="both", expand=True)
        
        if self.settings.sidebar_visible:
            self.main_paned.add(self.sidebar_frame, width=int(self.settings.sidebar_width*s), 
                               minsize=int(150*s), sticky="nsew")
        
        # Editor area (center, expands)
        self.editor_container = ctk.CTkFrame(self.main_paned, fg_color=THEME.bg_darkest, corner_radius=0)
        self.main_paned.add(self.editor_container, minsize=int(400*s), sticky="nsew")
        
        # Clipboard panel frame (resizable, right side)
        self.clipboard_frame = ctk.CTkFrame(self.main_paned, fg_color=THEME.bg_dark, corner_radius=0)
        self.clipboard_panel = ClipboardPanel(self.clipboard_frame, self.system_clipboard,
                                             on_paste=self._paste_from_clipboard, settings=self.settings)
        self.clipboard_panel.pack(fill="both", expand=True)
        
        if self.settings.clipboard_panel_visible:
            self.main_paned.add(self.clipboard_frame, width=int(self.settings.clipboard_panel_width*s),
                               minsize=int(150*s), sticky="nsew")
        
        # Bind sash movement to save sizes
        self.main_paned.bind("<ButtonRelease-1>", lambda e: self._on_paned_resize(e))
        
        # Tab bar
        self.tab_bar = ctk.CTkFrame(self.editor_container, fg_color=THEME.tab_inactive, 
                                   height=int(34*s), corner_radius=0)
        self.tab_bar.pack(fill="x")
        self.tab_bar.pack_propagate(False)
        
        self.tab_container = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.tab_container.pack(side="left", fill="both", expand=True)
        
        # Click empty space in tab bar to create new tab
        self.tab_container.bind("<Button-1>", lambda e: self._new_file())
        self.tab_bar.bind("<Button-1>", lambda e: self._tab_bar_click(e))
        
        # Recent files button
        self.recent_btn = ctk.CTkButton(self.tab_bar, text="📋", width=int(30*s), height=int(26*s),
                                       fg_color="transparent", hover_color=THEME.bg_hover,
                                       font=ctk.CTkFont(size=int(14*s)), command=self._show_recent_files)
        self.recent_btn.pack(side="right", padx=int(2*s))
        
        ctk.CTkButton(self.tab_bar, text="+", width=int(30*s), height=int(26*s),
                     fg_color="transparent", hover_color=THEME.bg_hover,
                     font=ctk.CTkFont(size=int(16*s)), command=self._new_file).pack(side="right", padx=int(4*s))
        
        # Find bar
        self.find_bar = FindReplaceBar(self.editor_container, self._do_find, self._do_replace,
                                      self._do_replace_all, self._hide_find_bar, self._find_in_files,
                                      settings=self.settings)
        
        # Editor frame
        self.editor_frame = ctk.CTkFrame(self.editor_container, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_frame.pack(fill="both", expand=True)
        
        # Terminal (hidden by default)
        self.terminal_frame = ctk.CTkFrame(self.editor_container, fg_color=THEME.bg_dark, 
                                          height=int(200*s), corner_radius=0)
        self.terminal_visible = False
        
    def _create_statusbar(self):
        s = self.settings.ui_scale
        if not self.settings.show_status_bar:
            return
        self.statusbar = ctk.CTkFrame(self, fg_color=THEME.ribbon_group_bg, height=int(24*s), corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        # Left - file path (clickable)
        self.path_label = ctk.CTkLabel(self.statusbar, text="Ready", text_color=THEME.text_secondary,
                                      font=ctk.CTkFont(size=int(10*s)), anchor="w", cursor="hand2")
        self.path_label.pack(side="left", padx=int(10*s), fill="x", expand=True)
        self.path_label.bind("<Button-1>", lambda e: self._copy_current_path(e))
        
        # Right side
        right = ctk.CTkFrame(self.statusbar, fg_color="transparent")
        right.pack(side="right")
        
        self.zoom_label = ctk.CTkLabel(right, text="100%", text_color=THEME.text_secondary,
                                      font=ctk.CTkFont(size=int(10*s)), width=int(45*s), cursor="hand2")
        self.zoom_label.pack(side="right", padx=int(8*s))
        self.zoom_label.bind("<Button-1>", lambda e: self._zoom_reset())
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        self.pos_label = ctk.CTkLabel(right, text="Ln 1, Col 1", text_color=THEME.text_secondary,
                                     font=ctk.CTkFont(size=int(10*s)), width=int(90*s), cursor="hand2")
        self.pos_label.pack(side="right")
        self.pos_label.bind("<Button-1>", lambda e: self._goto_line())
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        # Line ending toggle (clickable)
        self.line_ending_label = ctk.CTkLabel(right, text="CRLF", text_color=THEME.text_secondary,
                                             font=ctk.CTkFont(size=int(10*s)), width=int(40*s), cursor="hand2")
        self.line_ending_label.pack(side="right")
        self.line_ending_label.bind("<Button-1>", lambda e: self._toggle_line_ending())
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        # Encoding toggle (clickable)
        self.enc_label = ctk.CTkLabel(right, text="UTF-8", text_color=THEME.text_secondary,
                                     font=ctk.CTkFont(size=int(10*s)), width=int(50*s), cursor="hand2")
        self.enc_label.pack(side="right")
        self.enc_label.bind("<Button-1>", lambda e: self._toggle_encoding())
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        self.lang_label = ctk.CTkLabel(right, text="Plain Text", text_color=THEME.text_secondary,
                                      font=ctk.CTkFont(size=int(10*s)), width=int(80*s), cursor="hand2")
        self.lang_label.pack(side="right")
        self.lang_label.bind("<Button-1>", lambda e: self._select_language(e))
        
    def _bind_shortcuts(self):
        bindings = [
            ("<Control-n>", lambda e: self._new_file()),
            ("<Control-o>", lambda e: self._open_file()),
            ("<Control-s>", lambda e: self._save_file()),
            ("<Control-Shift-S>", lambda e: self._save_file_as()),
            ("<Control-w>", lambda e: self._close_current_tab()),
            ("<Control-Shift-T>", lambda e: self._reopen_closed_tab()),
            ("<Control-f>", lambda e: self._show_find_bar()),
            ("<Control-Shift-F>", lambda e: self._find_in_files()),
            ("<Control-g>", lambda e: self._goto_line()),
            ("<Control-b>", lambda e: self._toggle_sidebar()),
            ("<Control-plus>", lambda e: self._zoom_in()),
            ("<Control-minus>", lambda e: self._zoom_out()),
            ("<Control-equal>", lambda e: self._zoom_in()),
            ("<Control-0>", lambda e: self._zoom_reset()),
            ("<F3>", lambda e: self._find_next()),
            ("<Escape>", lambda e: self._hide_find_bar()),
            ("<Control-d>", lambda e: self._duplicate_line()),
            ("<Control-slash>", lambda e: self._toggle_comment()),
            ("<Control-Shift-P>", lambda e: self._show_command_palette()),
            ("<Control-`>", lambda e: self._toggle_terminal()),
            ("<Control-Shift-Up>", lambda e: self._move_line_up()),
            ("<Control-Shift-Down>", lambda e: self._move_line_down()),
            ("<Control-Shift-K>", lambda e: self._delete_line()),
        ]
        for key, cmd in bindings:
            self.bind(key, cmd)

    def _show_welcome(self):
        self.welcome_visible = True
        self.welcome = WelcomeScreen(self.editor_frame, self.settings,
                                    on_new=self._new_file_from_welcome,
                                    on_open=self._open_from_welcome,
                                    on_recent=self._open_recent_from_welcome,
                                    recent_files=self.settings.recent_files)
        self.welcome.pack(fill="both", expand=True)
        
    def _hide_welcome(self):
        if self.welcome_visible and hasattr(self, 'welcome'):
            self.welcome.destroy()
            self.welcome_visible = False
            
    def _new_file_from_welcome(self):
        self._hide_welcome()
        self._new_file()
        
    def _open_from_welcome(self, path=None):
        self._hide_welcome()
        if path and os.path.isdir(path):
            self.sidebar.set_root(path)
            if not self.settings.sidebar_visible:
                self.settings.sidebar_visible = True
                s = self.settings.ui_scale
                self.main_paned.add(self.sidebar_frame, width=int(self.settings.sidebar_width*s),
                                   minsize=int(150*s), sticky="nsew", before=self.editor_container)
        else:
            self._open_file(path)
        
    def _open_recent_from_welcome(self, filepath):
        self._hide_welcome()
        self._open_file(filepath)

    # =============================================================================
    # SESSION & TIMERS
    # =============================================================================
    
    def _restore_session(self):
        tabs = self.cache_manager.load_session()
        for info in tabs:
            tab_id = info.get("tab_id")
            if tab_id:
                content, meta = self.cache_manager.load_tab(tab_id)
                if content:
                    self._create_tab(filepath=info.get("filepath"), content=content, tab_id=tab_id)
                    
    def _save_session(self):
        session = []
        for tab_id, tab_data in self.tabs.items():
            if tab_id in self.text_widgets:
                content = self.text_widgets[tab_id].get("1.0", "end-1c")
                if content.strip():
                    self.cache_manager.save_tab(tab_id, content, {"filepath": tab_data.filepath, "language": tab_data.language})
            session.append({"tab_id": tab_id, "filepath": tab_data.filepath})
        self.cache_manager.save_session(session)
        
    def _start_timers(self):
        self._session_save_loop()
        self._auto_save_loop()
        self._file_check_loop()
        
    def _session_save_loop(self):
        self._save_session()
        self.after(15000, self._session_save_loop)
        
    def _auto_save_loop(self):
        if self.settings.auto_save_enabled and self.settings.auto_save_to_disk:
            for tid, td in self.tabs.items():
                if td.modified and td.filepath and tid in self.text_widgets:
                    content = self.text_widgets[tid].get("1.0", "end-1c")
                    try:
                        Path(td.filepath).write_text(content, encoding=td.encoding)
                        td.content_hash = hashlib.md5(content.encode()).hexdigest()
                        td.modified = False
                        td.last_saved = datetime.now()
                        self.backup_manager.create_backup(td.filepath, content)
                        if td.tab_frame:
                            td.tab_frame.modified_label.configure(text="")
                        logger.info(f"Auto-saved: {td.filepath}")
                    except Exception as e:
                        logger.error(f"Auto-save failed: {e}")
        self.after(self.settings.auto_save_interval * 1000, self._auto_save_loop)
        
    def _file_check_loop(self):
        for tab_id, tab_data in list(self.tabs.items()):
            if tab_data.filepath and os.path.exists(tab_data.filepath):
                try:
                    mtime = os.path.getmtime(tab_data.filepath)
                    stored = self.file_mtimes.get(tab_data.filepath, 0)
                    if stored > 0 and mtime > stored + 1:  # Allow 1 second tolerance
                        # Prompt to reload
                        self._prompt_reload_file(tab_id, tab_data.filepath)
                    self.file_mtimes[tab_data.filepath] = mtime
                except Exception:
                    pass
        self.after(3000, self._file_check_loop)
        
    def _prompt_reload_file(self, tab_id: str, filepath: str):
        """Show dialog asking whether to reload externally changed file"""
        name = os.path.basename(filepath)
        
        # Create a custom dialog
        s = self.settings.ui_scale
        dialog = ctk.CTkToplevel(self)
        dialog.title("File Changed")
        dialog.geometry(f"{int(400*s)}x{int(150*s)}")
        dialog.configure(fg_color=THEME.bg_dark)
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - int(400*s)) // 2
        y = self.winfo_y() + (self.winfo_height() - int(150*s)) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Warning icon and message
        msg_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        msg_frame.pack(fill="x", padx=int(20*s), pady=int(15*s))
        
        ctk.CTkLabel(msg_frame, text="⚠️", font=ctk.CTkFont(size=int(24*s)),
                    text_color=THEME.accent_orange).pack(side="left", padx=(0, int(10*s)))
        ctk.CTkLabel(msg_frame, text=f"'{name}' has been changed outside Mattpad.",
                    font=ctk.CTkFont(size=int(11*s)), text_color=THEME.text_primary,
                    wraplength=int(300*s)).pack(side="left")
        
        ctk.CTkLabel(dialog, text="Do you want to reload it?",
                    font=ctk.CTkFont(size=int(11*s)), text_color=THEME.text_secondary).pack(pady=(0, int(15*s)))
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=int(20*s), pady=(0, int(15*s)))
        
        def reload():
            self._reload_file(tab_id)
            dialog.destroy()
            
        def ignore():
            # Update mtime so we don't prompt again
            self.file_mtimes[filepath] = os.path.getmtime(filepath)
            dialog.destroy()
            
        ctk.CTkButton(btn_frame, text="Reload", fg_color=THEME.accent_primary,
                     command=reload, width=int(100*s)).pack(side="right", padx=int(5*s))
        ctk.CTkButton(btn_frame, text="Ignore", fg_color=THEME.bg_medium,
                     command=ignore, width=int(100*s)).pack(side="right", padx=int(5*s))
        
        # Focus dialog
        dialog.focus_set()
        
    def _reload_file(self, tab_id: str):
        """Reload file content from disk"""
        if tab_id not in self.tabs:
            return
        tab_data = self.tabs[tab_id]
        if not tab_data.filepath or not os.path.exists(tab_data.filepath):
            return
        try:
            content = Path(tab_data.filepath).read_text(encoding=tab_data.encoding)
            if tab_id in self.text_widgets:
                text = self.text_widgets[tab_id]
                text.delete("1.0", "end")
                text.insert("1.0", content)
                text.edit_reset()
                tab_data.modified = False
                tab_data.content_hash = hashlib.md5(content.encode()).hexdigest()
                if tab_data.tab_frame:
                    tab_data.tab_frame.modified_label.configure(text="")
                self.file_mtimes[tab_data.filepath] = os.path.getmtime(tab_data.filepath)
                self._redraw_tab_components(tab_id)
                self.toast.show("File reloaded", "success")
        except Exception as e:
            self.toast.show(f"Reload failed: {e}", "error")

    # =============================================================================
    # TAB MANAGEMENT
    # =============================================================================

    def _create_tab(self, filepath: Optional[str] = None, content: str = "", tab_id: str = None) -> str:
        self._hide_welcome()
        s = self.settings.ui_scale
        tab_id = tab_id or f"tab_{int(time.time()*1000)}"
        
        ext = os.path.splitext(filepath)[1].lower() if filepath else ".txt"
        language = FILE_EXTENSIONS.get(ext, "Plain Text")
        
        # Detect line ending from content
        line_ending = detect_line_ending(content) if content else "CRLF"
        
        # Check if this is a large file
        is_large_file = len(content) > LARGE_FILE_THRESHOLD if content else False
        
        tab_data = TabData(
            tab_id=tab_id, filepath=filepath, language=language,
            content_hash=hashlib.md5(content.encode()).hexdigest() if content else "",
            encoding=self.settings.encoding,
            line_ending=line_ending,
            is_large_file=is_large_file
        )
        self.tabs[tab_id] = tab_data
        
        # Track tab order for hot exit
        if tab_id not in self.tab_order:
            self.tab_order.append(tab_id)
        
        # Tab button
        tab_frame = ctk.CTkFrame(self.tab_container, fg_color=THEME.tab_inactive, corner_radius=0, height=int(32*s))
        tab_frame.pack(side="left", padx=1)
        tab_frame.pack_propagate(False)
        
        icon = get_file_icon(filepath) if filepath else "📄"
        name = os.path.basename(filepath) if filepath else "Untitled"
        
        tab_btn = ctk.CTkButton(tab_frame, text=f"{icon} {name}", fg_color="transparent",
                               hover_color=THEME.bg_hover, font=ctk.CTkFont(size=int(11*s)),
                               command=lambda t=tab_id: self._switch_tab(t), anchor="w",
                               height=int(28*s), corner_radius=0)
        tab_btn.pack(side="left", fill="both", expand=True)
        
        modified_label = ctk.CTkLabel(tab_frame, text="", width=int(12*s), text_color=THEME.tab_modified,
                                     font=ctk.CTkFont(size=int(14*s)))
        modified_label.pack(side="left")
        
        close_btn = ctk.CTkButton(tab_frame, text="×", width=int(24*s), height=int(24*s),
                                 fg_color="transparent", hover_color=THEME.bg_hover,
                                 font=ctk.CTkFont(size=int(14*s)), command=lambda t=tab_id: self._close_tab(t))
        close_btn.pack(side="right", padx=int(2*s))
        
        tab_frame.tab_btn = tab_btn
        tab_frame.modified_label = modified_label
        tab_frame.close_btn = close_btn
        tab_data.tab_frame = tab_frame
        
        # Middle-click to close tab
        tab_frame.bind("<Button-2>", lambda e, t=tab_id: self._close_tab(t))
        tab_btn.bind("<Button-2>", lambda e, t=tab_id: self._close_tab(t))
        
        # Drag to reorder tabs
        tab_frame.bind("<ButtonPress-1>", lambda e, t=tab_id: self._start_tab_drag(e, t))
        tab_frame.bind("<B1-Motion>", lambda e, t=tab_id: self._drag_tab(e, t))
        tab_frame.bind("<ButtonRelease-1>", lambda e, t=tab_id: self._end_tab_drag(e, t))
        tab_btn.bind("<ButtonPress-1>", lambda e, t=tab_id: self._start_tab_drag(e, t))
        tab_btn.bind("<B1-Motion>", lambda e, t=tab_id: self._drag_tab(e, t))
        tab_btn.bind("<ButtonRelease-1>", lambda e, t=tab_id: self._end_tab_drag(e, t))
        
        # Context menu
        ctx = tk.Menu(tab_btn, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        ctx.add_command(label="Close", command=lambda t=tab_id: self._close_tab(t))
        ctx.add_command(label="Close Others", command=lambda t=tab_id: self._close_others(t))
        ctx.add_command(label="Close All", command=self._close_all_tabs)
        ctx.add_separator()
        ctx.add_command(label="Copy Path", command=lambda t=tab_id: self._copy_tab_path(t))
        ctx.add_command(label="Reveal in Explorer", command=lambda t=tab_id: self._reveal_in_explorer(t))
        ctx.add_separator()
        ctx.add_command(label="Reopen Closed Tabs", command=self._show_closed_tabs)
        tab_btn.bind("<Button-3>", lambda e, m=ctx: m.tk_popup(e.x_root, e.y_root))
        
        # Editor frame
        editor_frame = ctk.CTkFrame(self.editor_frame, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_frames[tab_id] = editor_frame
        
        editor_inner = ctk.CTkFrame(editor_frame, fg_color=THEME.bg_darkest, corner_radius=0)
        editor_inner.pack(fill="both", expand=True)
        
        # Line numbers
        line_canvas = LineNumberCanvas(editor_inner, self.settings)
        if self.settings.show_line_numbers:
            line_canvas.pack(side="left", fill="y")
        self.line_numbers[tab_id] = line_canvas
        
        # Text widget
        text = tk.Text(editor_inner, wrap="none" if not self.settings.word_wrap else "word",
                      bg=THEME.bg_darkest, fg=THEME.text_primary, insertbackground=THEME.text_primary,
                      selectbackground=THEME.selection_bg, selectforeground=THEME.text_primary,
                      font=(self.settings.font_family, int(self.settings.font_size * s)),
                      borderwidth=0, highlightthickness=0, undo=True, autoseparators=True,
                      insertwidth=2, tabs=(f"{self.settings.tab_size}c",))
        text.pack(side="left", fill="both", expand=True)
        self.text_widgets[tab_id] = text
        
        # Scrollbars
        yscroll = ctk.CTkScrollbar(editor_inner, command=text.yview)
        yscroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=lambda *args: self._on_scroll(tab_id, yscroll, *args))
        
        # Minimap
        minimap = Minimap(editor_inner, text, self.settings)
        if self.settings.show_minimap:
            minimap.pack(side="right", fill="y", before=yscroll)
        self.minimaps[tab_id] = minimap
        
        # Link line numbers to text
        line_canvas.text_widget = text
        line_canvas.text_font = tkfont.Font(family=self.settings.font_family, size=int(self.settings.font_size * s))
        
        # Syntax highlighter
        highlighter = SyntaxHighlighter(text, ext)
        if is_large_file:
            highlighter.set_large_file_mode(True)
            logger.info(f"Large file mode enabled for {filepath or 'Untitled'}")
        self.highlighters[tab_id] = highlighter
        
        # Insert content
        if content:
            text.insert("1.0", content)
            text.edit_reset()
        
        # Bindings - FIX PASTE DUPLICATION by returning "break"
        text.bind("<KeyRelease>", lambda e, t=tab_id: self._on_key_release(e, t))
        text.bind("<KeyPress>", lambda e, t=tab_id: self._on_key_press(e, t))
        text.bind("<Control-v>", lambda e, t=tab_id: self._handle_paste(e, t))
        text.bind("<Control-V>", lambda e, t=tab_id: self._handle_paste(e, t))
        text.bind("<Control-c>", lambda e, t=tab_id: self._handle_copy(e, t))
        text.bind("<Control-x>", lambda e, t=tab_id: self._handle_cut(e, t))
        text.bind("<Button-1>", lambda e, t=tab_id: self._on_click(e, t))
        text.bind("<Control-Button-1>", lambda e, t=tab_id: self._add_cursor(e, t))
        text.bind("<MouseWheel>", lambda e, t=tab_id: self._on_mousewheel(e, t))
        text.bind("<Control-MouseWheel>", lambda e, t=tab_id: self._on_ctrl_scroll(e, t))
        text.bind("<Button-3>", lambda e, t=tab_id: self._show_text_context_menu(e, t))
        text.bind("<<Modified>>", lambda e, t=tab_id: self._on_modified(t))
        
        # Auto-scroll (middle-click and drag)
        text.bind("<Button-2>", lambda e, t=tab_id: self._start_auto_scroll(e, t))
        text.bind("<B2-Motion>", lambda e, t=tab_id: self._auto_scroll_motion(e, t))
        text.bind("<ButtonRelease-2>", lambda e, t=tab_id: self._stop_auto_scroll(t))
        
        # Configure spellcheck tag
        text.tag_configure("misspelled", underline=True, underlinefg=THEME.misspelled)
        text.tag_configure("bracket_match", background=THEME.bracket_match)
        text.tag_configure("search_highlight", background=THEME.search_highlight)
        text.tag_configure("current_line", background=THEME.current_line)
        
        self._switch_tab(tab_id)
        return tab_id
        
    def _switch_tab(self, tab_id: str):
        if tab_id not in self.tabs:
            return
        for tid, frame in self.editor_frames.items():
            frame.pack_forget()
            if tid in self.tabs and self.tabs[tid].tab_frame:
                self.tabs[tid].tab_frame.configure(fg_color=THEME.tab_inactive)
        self.editor_frames[tab_id].pack(fill="both", expand=True)
        if self.tabs[tab_id].tab_frame:
            self.tabs[tab_id].tab_frame.configure(fg_color=THEME.tab_active)
        self.current_tab = tab_id
        self.text_widgets[tab_id].focus_set()
        self._update_statusbar()
        self._update_title()
        self.debouncer.debounce("highlight", lambda: self._highlight_current())
        
    def _redraw_tab_components(self, tab_id: str):
        """Redraw line numbers, minimap, and syntax highlighting for a tab"""
        if tab_id in self.line_numbers:
            self.line_numbers[tab_id].redraw()
        if tab_id in self.minimaps:
            self.minimaps[tab_id].redraw()
        if tab_id in self.highlighters:
            self.highlighters[tab_id].highlight_all()
        
    def _close_tab(self, tab_id: str):
        if tab_id not in self.tabs:
            return
        tab_data = self.tabs[tab_id]
        
        # Save to closed tabs for recovery
        if tab_id in self.text_widgets:
            try:
                content = self.text_widgets[tab_id].get("1.0", "end-1c")
                if content.strip():
                    self.closed_tabs_manager.save_tab(tab_id, tab_data.filepath, content, tab_data.language)
            except tk.TclError:
                pass
        
        # Remove from tab order
        if tab_id in self.tab_order:
            self.tab_order.remove(tab_id)
        
        # Clean up
        if tab_data.tab_frame:
            tab_data.tab_frame.destroy()
        if tab_id in self.editor_frames:
            self.editor_frames[tab_id].destroy()
            del self.editor_frames[tab_id]
        if tab_id in self.text_widgets:
            del self.text_widgets[tab_id]
        if tab_id in self.line_numbers:
            del self.line_numbers[tab_id]
        if tab_id in self.minimaps:
            del self.minimaps[tab_id]
        if tab_id in self.highlighters:
            del self.highlighters[tab_id]
        del self.tabs[tab_id]
        
        # Switch to another tab
        if self.tabs:
            self._switch_tab(list(self.tabs.keys())[-1])
        else:
            self.current_tab = None
            self._show_welcome()
    
    def _close_current_tab(self):
        """Close the current tab"""
        if self.current_tab:
            self._close_tab(self.current_tab)
    
    def _close_others(self, keep_tab_id: str):
        """Close all tabs except the specified one"""
        for tab_id in list(self.tabs.keys()):
            if tab_id != keep_tab_id:
                self._close_tab(tab_id)
    
    def _close_all_tabs(self):
        """Close all tabs"""
        for tab_id in list(self.tabs.keys()):
            self._close_tab(tab_id)
    
    def _reopen_closed_tab(self):
        """Reopen the last closed tab"""
        tabs = self.closed_tabs_manager.get_list()
        if tabs:
            result = self.closed_tabs_manager.get_tab(0)
            if result:
                content, filepath, language = result
                self._create_tab(filepath, content)
                self.closed_tabs_manager.remove_tab(0)
                self.toast.show("Tab reopened", "success")
    
    def _copy_tab_path(self, tab_id: str):
        """Copy tab's file path to clipboard"""
        if tab_id in self.tabs and self.tabs[tab_id].filepath:
            self.clipboard_clear()
            self.clipboard_append(self.tabs[tab_id].filepath)
            self.toast.show("Path copied", "success")
    
    def _reveal_in_explorer(self, tab_id: str):
        """Open file location in system explorer"""
        if tab_id in self.tabs and self.tabs[tab_id].filepath:
            filepath = self.tabs[tab_id].filepath
            if os.path.exists(filepath):
                folder = os.path.dirname(filepath)
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    subprocess.run(["open", folder])
                else:
                    subprocess.run(["xdg-open", folder])
    
    def _tab_bar_click(self, event):
        """Handle click on tab bar (not on a tab)"""
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget == self.tab_bar or widget == self.tab_container:
            self._new_file()
    
    # Tab drag state
    _drag_start_x = 0
    _drag_tab_id = None
    _drag_started = False
    
    def _start_tab_drag(self, event, tab_id: str):
        """Start dragging a tab"""
        self._drag_start_x = event.x_root
        self._drag_tab_id = tab_id
        self._drag_started = False
    
    def _drag_tab(self, event, tab_id: str):
        """Handle tab drag motion"""
        if not self._drag_tab_id or self._drag_tab_id != tab_id:
            return
        delta = abs(event.x_root - self._drag_start_x)
        if delta > 10:
            self._drag_started = True
            # Find tab under cursor and swap
            for tid, td in self.tabs.items():
                if tid != tab_id and td.tab_frame:
                    frame = td.tab_frame
                    fx = frame.winfo_rootx()
                    fw = frame.winfo_width()
                    if fx < event.x_root < fx + fw:
                        self._swap_tabs(tab_id, tid)
                        self._drag_start_x = event.x_root
                        break
    
    def _end_tab_drag(self, event, tab_id: str):
        """End tab drag"""
        if not self._drag_started and self._drag_tab_id == tab_id:
            self._switch_tab(tab_id)
        self._drag_tab_id = None
        self._drag_started = False
    
    def _swap_tabs(self, tab_id1: str, tab_id2: str):
        """Swap two tabs in the tab bar"""
        if tab_id1 not in self.tabs or tab_id2 not in self.tabs:
            return
        frame1 = self.tabs[tab_id1].tab_frame
        frame2 = self.tabs[tab_id2].tab_frame
        if not frame1 or not frame2:
            return
        
        # Get positions
        tabs_list = list(self.tabs.keys())
        idx1 = tabs_list.index(tab_id1)
        idx2 = tabs_list.index(tab_id2)
        
        # Swap in dict (reorder)
        items = list(self.tabs.items())
        items[idx1], items[idx2] = items[idx2], items[idx1]
        self.tabs = dict(items)
        
        # Repack frames
        for child in self.tab_container.winfo_children():
            child.pack_forget()
        for tid in self.tabs:
            if self.tabs[tid].tab_frame:
                self.tabs[tid].tab_frame.pack(side="left", padx=1)
    
    # ==========================================================================
    # FILE OPERATIONS
    # ==========================================================================
    
    def _new_file(self):
        """Create a new empty file"""
        self._create_tab()
    
    def _open_file(self, filepath: str = None):
        """Open a file"""
        if filepath is None:
            filepath = filedialog.askopenfilename(
                filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Python Files", "*.py"),
                          ("JavaScript Files", "*.js"), ("HTML Files", "*.html"), ("CSS Files", "*.css"),
                          ("JSON Files", "*.json"), ("Markdown Files", "*.md")]
            )
        if not filepath or not os.path.isfile(filepath):
            return
        
        # Check if already open
        for tab_id, tab_data in self.tabs.items():
            if tab_data.filepath == filepath:
                self._switch_tab(tab_id)
                return
        
        try:
            # Detect encoding
            encoding = "utf-8"
            if CHARDET_AVAILABLE:
                with open(filepath, 'rb') as f:
                    result = chardet.detect(f.read(10000))
                    if result['encoding']:
                        encoding = result['encoding']
            
            content = Path(filepath).read_text(encoding=encoding)
            tab_id = self._create_tab(filepath, content)
            self.tabs[tab_id].encoding = encoding
            self.file_mtimes[filepath] = os.path.getmtime(filepath)
            
            # Add to recent files
            if filepath in self.settings.recent_files:
                self.settings.recent_files.remove(filepath)
            self.settings.recent_files.insert(0, filepath)
            self.settings.recent_files = self.settings.recent_files[:MAX_RECENT_FILES]
            
            self.toast.show(f"Opened: {os.path.basename(filepath)}", "success")
        except Exception as e:
            self.toast.show(f"Failed to open: {e}", "error")
            logger.error(f"Open file error: {e}")
    
    def _save_file(self):
        """Save current file"""
        if not self.current_tab:
            return
        tab_data = self.tabs[self.current_tab]
        
        if not tab_data.filepath:
            self._save_file_as()
            return
        
        try:
            content = self.text_widgets[self.current_tab].get("1.0", "end-1c")
            Path(tab_data.filepath).write_text(content, encoding=tab_data.encoding)
            
            # Create backup
            self.backup_manager.create_backup(tab_data.filepath, content)
            
            # Update state
            tab_data.modified = False
            tab_data.content_hash = hashlib.md5(content.encode()).hexdigest()
            if tab_data.tab_frame:
                tab_data.tab_frame.modified_label.configure(text="")
            self.file_mtimes[tab_data.filepath] = os.path.getmtime(tab_data.filepath)
            
            self._update_title()
            self.toast.show("Saved", "success")
            
            # Cloud sync
            if self.settings.cloud_sync_enabled and self.settings.github_token:
                threading.Thread(target=self.cloud_sync.sync_to_github, args=(tab_data.filepath, content), daemon=True).start()
        except Exception as e:
            self.toast.show(f"Save failed: {e}", "error")
            logger.error(f"Save error: {e}")
    
    def _save_file_as(self):
        """Save file with new name"""
        if not self.current_tab:
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=self.settings.default_extension,
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Python Files", "*.py")]
        )
        if not filepath:
            return
        
        self.tabs[self.current_tab].filepath = filepath
        
        # Update tab name
        tab_data = self.tabs[self.current_tab]
        if tab_data.tab_frame:
            icon = get_file_icon(filepath)
            name = os.path.basename(filepath)
            tab_data.tab_frame.tab_btn.configure(text=f"{icon} {name}")
        
        # Update language
        ext = os.path.splitext(filepath)[1].lower()
        tab_data.language = FILE_EXTENSIONS.get(ext, "Plain Text")
        if self.current_tab in self.highlighters:
            self.highlighters[self.current_tab].language = tab_data.language
            self.highlighters[self.current_tab].highlight_all()
        
        self._save_file()
    
    def _save_all(self):
        """Save all modified files"""
        count = 0
        for tab_id, tab_data in self.tabs.items():
            if tab_data.modified and tab_data.filepath and tab_id in self.text_widgets:
                content = self.text_widgets[tab_id].get("1.0", "end-1c")
                try:
                    Path(tab_data.filepath).write_text(content, encoding=tab_data.encoding)
                    tab_data.modified = False
                    if tab_data.tab_frame:
                        tab_data.tab_frame.modified_label.configure(text="")
                    count += 1
                except Exception as e:
                    logger.error(f"Save all error for {tab_data.filepath}: {e}")
        if count:
            self.toast.show(f"Saved {count} file(s)", "success")
    
    # ==========================================================================
    # EDIT OPERATIONS
    # ==========================================================================
    
    def _undo(self):
        """Undo last action"""
        if self.current_tab and self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_undo()
            except tk.TclError:
                pass
    
    def _redo(self):
        """Redo last undone action"""
        if self.current_tab and self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_redo()
            except tk.TclError:
                pass
    
    def _cut(self):
        """Cut selected text"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                text.event_generate("<<Cut>>")
            except Exception:
                pass
    
    def _copy(self):
        """Copy selected text"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                text.event_generate("<<Copy>>")
            except Exception:
                pass
    
    def _paste(self):
        """Paste from clipboard"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                text.event_generate("<<Paste>>")
            except Exception:
                pass
    
    def _handle_paste(self, event, tab_id: str):
        """Handle paste event"""
        return None  # Let default handler run
    
    def _handle_copy(self, event, tab_id: str):
        """Handle copy event"""
        return None
    
    def _handle_cut(self, event, tab_id: str):
        """Handle cut event"""
        return None
    
    def _paste_from_clipboard(self, text: str):
        """Paste text from clipboard panel"""
        if self.current_tab and self.current_tab in self.text_widgets:
            self.text_widgets[self.current_tab].insert("insert", text)
    
    def _duplicate_line(self, event=None):
        """Duplicate current line or selection with undo support"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return "break"
        text = self.text_widgets[self.current_tab]
        
        text.edit_separator()  # Mark undo point
        
        try:
            # Check for selection
            sel_start = text.index("sel.first")
            sel_end = text.index("sel.last")
            selected_text = text.get(sel_start, sel_end)
            text.insert(sel_end, selected_text)
        except tk.TclError:
            # No selection - duplicate current line
            line = text.get("insert linestart", "insert lineend")
            text.insert("insert lineend", f"\n{line}")
        
        text.edit_separator()
        self._on_modified(self.current_tab)
        return "break"
    
    def _move_line_up(self, event=None):
        """Move current line or selection up"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return "break"
        text = self.text_widgets[self.current_tab]
        
        try:
            # Get selection range or current line
            try:
                start_line = int(text.index("sel.first").split(".")[0])
                end_line = int(text.index("sel.last").split(".")[0])
            except tk.TclError:
                start_line = int(text.index("insert").split(".")[0])
                end_line = start_line
            
            # Can't move above line 1
            if start_line <= 1:
                return "break"
            
            text.edit_separator()
            
            # Get the lines to move and the line above
            lines_to_move = text.get(f"{start_line}.0", f"{end_line}.end")
            line_above = text.get(f"{start_line - 1}.0", f"{start_line - 1}.end")
            
            # Delete from line above through selection
            text.delete(f"{start_line - 1}.0", f"{end_line}.end")
            
            # Insert in new order: moved lines, then line that was above
            text.insert(f"{start_line - 1}.0", lines_to_move + "\n" + line_above)
            
            # Restore selection in new position
            new_start = start_line - 1
            new_end = end_line - 1
            text.tag_remove("sel", "1.0", "end")
            text.tag_add("sel", f"{new_start}.0", f"{new_end}.end")
            text.mark_set("insert", f"{new_start}.0")
            
            text.edit_separator()
            self._on_modified(self.current_tab)
            
        except Exception as e:
            logger.error(f"Move line up error: {e}")
        
        return "break"
    
    def _move_line_down(self, event=None):
        """Move current line or selection down"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return "break"
        text = self.text_widgets[self.current_tab]
        
        try:
            # Get selection range or current line
            try:
                start_line = int(text.index("sel.first").split(".")[0])
                end_line = int(text.index("sel.last").split(".")[0])
            except tk.TclError:
                start_line = int(text.index("insert").split(".")[0])
                end_line = start_line
            
            # Get total lines
            total_lines = int(text.index("end-1c").split(".")[0])
            
            # Can't move below last line
            if end_line >= total_lines:
                return "break"
            
            text.edit_separator()
            
            # Get the lines to move and the line below
            lines_to_move = text.get(f"{start_line}.0", f"{end_line}.end")
            line_below = text.get(f"{end_line + 1}.0", f"{end_line + 1}.end")
            
            # Delete from selection through line below
            text.delete(f"{start_line}.0", f"{end_line + 1}.end")
            
            # Insert in new order: line that was below, then moved lines
            text.insert(f"{start_line}.0", line_below + "\n" + lines_to_move)
            
            # Restore selection in new position
            new_start = start_line + 1
            new_end = end_line + 1
            text.tag_remove("sel", "1.0", "end")
            text.tag_add("sel", f"{new_start}.0", f"{new_end}.end")
            text.mark_set("insert", f"{new_start}.0")
            
            text.edit_separator()
            self._on_modified(self.current_tab)
            
        except Exception as e:
            logger.error(f"Move line down error: {e}")
        
        return "break"
    
    def _delete_line(self, event=None):
        """Delete current line"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return "break"
        text = self.text_widgets[self.current_tab]
        
        text.edit_separator()
        
        try:
            line_num = int(text.index("insert").split(".")[0])
            total_lines = int(text.index("end-1c").split(".")[0])
            
            if total_lines == 1:
                # Single line - just clear it
                text.delete("1.0", "end")
            elif line_num == total_lines:
                # Last line - delete including previous newline
                text.delete(f"{line_num - 1}.end", "end")
            else:
                # Delete line including trailing newline
                text.delete(f"{line_num}.0", f"{line_num + 1}.0")
        except Exception as e:
            logger.error(f"Delete line error: {e}")
        
        text.edit_separator()
        self._on_modified(self.current_tab)
        return "break"
    
    def _toggle_comment(self):
        """Toggle comment on current line(s)"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return
        text = self.text_widgets[self.current_tab]
        
        try:
            start = text.index("sel.first linestart")
            end = text.index("sel.last lineend")
        except tk.TclError:
            start = text.index("insert linestart")
            end = text.index("insert lineend")
        
        lines = text.get(start, end).split("\n")
        comment_char = "#"  # Default
        
        lang = self.tabs[self.current_tab].language
        if lang in ["JavaScript", "TypeScript", "C", "C++", "C#", "Java", "Go"]:
            comment_char = "//"
        elif lang in ["HTML", "XML"]:
            comment_char = "<!--"
        elif lang == "CSS":
            comment_char = "/*"
        
        # Check if all lines are commented
        all_commented = all(line.strip().startswith(comment_char) for line in lines if line.strip())
        
        new_lines = []
        for line in lines:
            if all_commented:
                # Uncomment
                stripped = line.lstrip()
                if stripped.startswith(comment_char):
                    indent = line[:len(line) - len(stripped)]
                    new_lines.append(indent + stripped[len(comment_char):].lstrip())
                else:
                    new_lines.append(line)
            else:
                # Comment
                if line.strip():
                    indent = line[:len(line) - len(line.lstrip())]
                    new_lines.append(f"{indent}{comment_char} {line.lstrip()}")
                else:
                    new_lines.append(line)
        
        text.delete(start, end)
        text.insert(start, "\n".join(new_lines))
    
    # ==========================================================================
    # FIND/REPLACE
    # ==========================================================================
    
    def _show_find_bar(self):
        """Show the find/replace bar"""
        self.find_bar.pack(fill="x", before=self.editor_frame)
        self.find_bar.focus_find()
    
    def _hide_find_bar(self):
        """Hide the find/replace bar"""
        self.find_bar.pack_forget()
        if self.current_tab and self.current_tab in self.text_widgets:
            self.text_widgets[self.current_tab].tag_remove("search_highlight", "1.0", "end")
            self.text_widgets[self.current_tab].focus_set()
    
    def _do_find(self, query: str):
        """Find text in current document"""
        if not self.current_tab or not query:
            return
        text = self.text_widgets[self.current_tab]
        text.tag_remove("search_highlight", "1.0", "end")
        
        start = "1.0"
        count = 0
        while True:
            pos = text.search(query, start, stopindex="end", nocase=not self.find_bar.case_var.get(),
                             regexp=self.find_bar.regex_var.get())
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            text.tag_add("search_highlight", pos, end)
            if count == 0:
                text.see(pos)
                text.mark_set("insert", pos)
            start = end
            count += 1
        
        if count:
            self.toast.show(f"Found {count} match(es)", "info")
        else:
            self.toast.show("No matches found", "warning")
    
    def _do_replace(self, find_text: str, replace_text: str):
        """Replace current match"""
        if not self.current_tab or not find_text:
            return
        text = self.text_widgets[self.current_tab]
        try:
            sel_start = text.index("sel.first")
            sel_end = text.index("sel.last")
            selected = text.get(sel_start, sel_end)
            if selected.lower() == find_text.lower() or (self.find_bar.case_var.get() and selected == find_text):
                text.delete(sel_start, sel_end)
                text.insert(sel_start, replace_text)
        except tk.TclError:
            pass
        self._do_find(find_text)
    
    def _do_replace_all(self, find_text: str, replace_text: str):
        """Replace all matches"""
        if not self.current_tab or not find_text:
            return
        text = self.text_widgets[self.current_tab]
        content = text.get("1.0", "end-1c")
        
        if self.find_bar.case_var.get():
            new_content = content.replace(find_text, replace_text)
        else:
            new_content = re.sub(re.escape(find_text), replace_text, content, flags=re.IGNORECASE)
        
        count = content.count(find_text) if self.find_bar.case_var.get() else len(re.findall(re.escape(find_text), content, re.IGNORECASE))
        
        if count:
            text.delete("1.0", "end")
            text.insert("1.0", new_content)
            self.toast.show(f"Replaced {count} occurrence(s)", "success")
        else:
            self.toast.show("No matches found", "warning")
    
    def _find_in_files(self):
        """Find in files dialog"""
        self.toast.show("Find in Files - Coming soon", "info")
    
    def _find_next(self):
        """Find next occurrence"""
        if hasattr(self, 'find_bar') and self.find_bar.winfo_ismapped():
            query = self.find_bar.find_entry.get()
            if query:
                self._do_find(query)
    
    def _goto_line(self):
        """Go to a specific line"""
        if not self.current_tab:
            return
        
        line = simpledialog.askinteger("Go to Line", "Line number:", parent=self, minvalue=1)
        if line:
            text = self.text_widgets[self.current_tab]
            text.mark_set("insert", f"{line}.0")
            text.see(f"{line}.0")
            text.focus_set()
    
    # ==========================================================================
    # ZOOM
    # ==========================================================================
    
    def _zoom_in(self):
        """Increase font size"""
        self.settings.font_size = min(48, self.settings.font_size + 2)
        self._apply_font()
    
    def _zoom_out(self):
        """Decrease font size"""
        self.settings.font_size = max(6, self.settings.font_size - 2)
        self._apply_font()
    
    def _zoom_reset(self):
        """Reset font size"""
        self.settings.font_size = 12
        self._apply_font()
    
    def _apply_font(self):
        """Apply font settings to all editors"""
        for text in self.text_widgets.values():
            text.configure(font=(self.settings.font_family, self.settings.font_size))
        self._update_statusbar()
    
    # ==========================================================================
    # UI TOGGLES
    # ==========================================================================
    
    def _toggle_sidebar(self):
        """Toggle sidebar visibility"""
        s = self.settings.ui_scale
        self.settings.sidebar_visible = not self.settings.sidebar_visible
        if self.settings.sidebar_visible:
            self.main_paned.add(self.sidebar_frame, width=sp(self.settings.sidebar_width, s),
                               minsize=sp(150, s), sticky="nsew", before=self.editor_container)
        else:
            try:
                self.settings.sidebar_width = int(self.sidebar_frame.winfo_width() / s)
            except Exception:
                pass
            self.main_paned.forget(self.sidebar_frame)
    
    def _toggle_clipboard_panel(self):
        """Toggle clipboard panel visibility"""
        s = self.settings.ui_scale
        self.settings.clipboard_panel_visible = not self.settings.clipboard_panel_visible
        if self.settings.clipboard_panel_visible:
            self.main_paned.add(self.clipboard_frame, width=sp(self.settings.clipboard_panel_width, s),
                               minsize=sp(150, s), sticky="nsew")
        else:
            try:
                self.settings.clipboard_panel_width = int(self.clipboard_frame.winfo_width() / s)
            except Exception:
                pass
            self.main_paned.forget(self.clipboard_frame)
    
    def _toggle_theme(self):
        """Toggle between dark and light theme"""
        global THEME
        if self.settings.theme_name == "Light":
            self.settings.theme_name = "Professional Dark"
        else:
            self.settings.theme_name = "Light"
        THEME = get_theme(self.settings.theme_name)
        self.toast.show(f"Theme: {self.settings.theme_name} (restart for full effect)", "info")
    
    def _toggle_feature(self, feature_name: str):
        """Toggle a boolean feature setting"""
        current = getattr(self.settings, feature_name, False)
        setattr(self.settings, feature_name, not current)
        self.toast.show(f"{feature_name.replace('_', ' ').title()}: {'On' if not current else 'Off'}", "info")
        
        # Apply changes that need immediate update
        if feature_name == "word_wrap" and self.current_tab in self.text_widgets:
            wrap_mode = "word" if not current else "none"
            self.text_widgets[self.current_tab].configure(wrap=wrap_mode)
        elif feature_name == "show_minimap":
            for tab_id in self.minimaps:
                if not current:
                    self.minimaps[tab_id].pack(side="right", fill="y", padx=(2, 0))
                else:
                    self.minimaps[tab_id].pack_forget()
        elif feature_name == "show_line_numbers":
            for tab_id in self.line_numbers:
                if not current:
                    self.line_numbers[tab_id].pack(side="left", fill="y")
                else:
                    self.line_numbers[tab_id].pack_forget()
    
    def _toggle_word_wrap(self):
        """Toggle word wrap for current editor"""
        self.settings.word_wrap = self.wrap_var.get()
        wrap_mode = "word" if self.settings.word_wrap else "none"
        for tab_id in self.text_widgets:
            self.text_widgets[tab_id].configure(wrap=wrap_mode)
    
    def _toggle_minimap(self):
        """Toggle minimap visibility"""
        self.settings.show_minimap = self.minimap_var.get()
        for tab_id, minimap in self.minimaps.items():
            if self.settings.show_minimap:
                minimap.pack(side="right", fill="y", padx=(2, 0))
            else:
                minimap.pack_forget()
    
    def _toggle_line_numbers(self):
        """Toggle line numbers visibility"""
        self.settings.show_line_numbers = self.linenum_var.get()
        for tab_id, line_canvas in self.line_numbers.items():
            if self.settings.show_line_numbers:
                line_canvas.pack(side="left", fill="y")
            else:
                line_canvas.pack_forget()
    
    def _toggle_spellcheck(self):
        """Toggle spellcheck"""
        self.settings.spellcheck_enabled = self.spell_var.get()
        self.toast.show(f"Spellcheck: {'On' if self.settings.spellcheck_enabled else 'Off'}", "info")
    
    def _toggle_autoclose(self):
        """Toggle auto-close brackets"""
        self.settings.auto_close_brackets = self.autoclose_var.get()
        self.toast.show(f"Auto-close brackets: {'On' if self.settings.auto_close_brackets else 'Off'}", "info")
    
    def _toggle_autosave(self):
        """Toggle auto-save"""
        self.settings.auto_save_enabled = self.autosave_var.get()
        self.toast.show(f"Auto-save: {'On' if self.settings.auto_save_enabled else 'Off'}", "info")
    
    # ==========================================================================
    # DIALOGS
    # ==========================================================================
    
    def _show_settings(self):
        """Show settings dialog"""
        SettingsDialog(self, self.settings, self._save_settings)
    
    def _set_scale(self, scale: float):
        """Set UI scale"""
        self.settings.ui_scale = scale
        self._save_settings()
        self.toast.show(f"UI Scale set to {scale}x (restart for full effect)", "info")
    
    def _show_ai_settings(self):
        """Show AI settings dialog"""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "AI Settings", 450, 350, self.settings)
        
        fields = [
            ("Provider:", "ai_provider", ["", "OpenAI", "Anthropic", "Ollama"], "combo"),
            ("API Key:", "ai_api_key", None, "secret"),
            ("Model:", "ai_model", None, "entry"),
        ]
        
        entries = {}
        for label, attr, options, field_type in fields:
            row = ctk.CTkFrame(dialog, fg_color="transparent")
            row.pack(fill="x", padx=sp(Spacing.LG, s), pady=sp(Spacing.SM, s))
            
            ctk.CTkLabel(row, text=label, width=sp(100, s), anchor="w").pack(side="left")
            
            if field_type == "combo":
                var = ctk.StringVar(value=getattr(self.settings, attr, ""))
                entry = ctk.CTkComboBox(row, values=options, variable=var, width=sp(200, s),
                                       fg_color=THEME.bg_darkest)
                entry._var = var
            elif field_type == "secret":
                entry = ctk.CTkEntry(row, fg_color=THEME.bg_darkest, width=sp(200, s), show="*")
                entry.insert(0, getattr(self.settings, attr, ""))
            else:
                entry = ctk.CTkEntry(row, fg_color=THEME.bg_darkest, width=sp(200, s))
                entry.insert(0, getattr(self.settings, attr, ""))
            
            entry.pack(side="left")
            entries[attr] = entry
        
        def save():
            for attr, entry in entries.items():
                if hasattr(entry, '_var'):
                    setattr(self.settings, attr, entry._var.get())
                else:
                    setattr(self.settings, attr, entry.get())
            self._save_settings()
            self.toast.show("AI settings saved", "success")
            dialog.destroy()
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=sp(Spacing.LG, s), pady=sp(Spacing.LG, s))
        
        ctk.CTkButton(btn_frame, text="Save", width=sp(80, s), command=save,
                     fg_color=THEME.accent_primary).pack(side="right", padx=sp(Spacing.XS, s))
        ctk.CTkButton(btn_frame, text="Cancel", width=sp(80, s), command=dialog.destroy,
                     fg_color=THEME.bg_medium).pack(side="right", padx=sp(Spacing.XS, s))
    
    def _show_themes(self):
        """Show theme selector"""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "Themes", 400, 500, self.settings)
        
        ctk.CTkLabel(dialog, text="Select Theme", font=ctk.CTkFont(size=sp(14, s), weight="bold")).pack(pady=sp(Spacing.MD, s))
        
        frame = ctk.CTkScrollableFrame(dialog, fg_color=THEME.bg_darkest)
        frame.pack(fill="both", expand=True, padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        def select_theme(name):
            global THEME
            self.settings.theme_name = name
            THEME = get_theme(name)
            self._save_settings()
            dialog.destroy()
            self.toast.show(f"Theme set to {name} (restart for full effect)", "success")
        
        for name in THEMES.keys():
            theme = THEMES[name]
            btn_frame = ctk.CTkFrame(frame, fg_color=theme.bg_dark, corner_radius=sp(6, s))
            btn_frame.pack(fill="x", pady=sp(2, s))
            
            ctk.CTkButton(btn_frame, text=name, fg_color="transparent", hover_color=theme.bg_hover,
                         text_color=theme.text_primary, anchor="w", font=ctk.CTkFont(size=sp(12, s)),
                         command=lambda n=name: select_theme(n)).pack(fill="x", padx=sp(Spacing.SM, s), pady=sp(Spacing.SM, s))
    
    def _show_command_palette(self):
        """Show command palette"""
        if self.settings.command_palette_enabled:
            CommandPalette(self, self.commands, self.settings)
    
    def _show_closed_tabs(self):
        """Show closed tabs dialog"""
        s = self.settings.ui_scale
        tabs = self.closed_tabs_manager.get_list()
        if not tabs:
            self.toast.show("No closed tabs", "info")
            return
        
        dialog = create_dialog(self, "Closed Tabs", 500, 400, self.settings)
        
        frame = ctk.CTkScrollableFrame(dialog, fg_color=THEME.bg_darkest)
        frame.pack(fill="both", expand=True, padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        for i, tab in enumerate(tabs[:20]):
            row = ctk.CTkFrame(frame, fg_color=THEME.bg_dark, corner_radius=sp(4, s))
            row.pack(fill="x", pady=sp(2, s))
            
            preview = tab.get("preview", "")[:50]
            filepath = tab.get("filepath") or "Untitled"
            name = os.path.basename(filepath) if filepath != "Untitled" else "Untitled"
            
            ctk.CTkLabel(row, text=f"{get_file_icon(filepath)} {name}", anchor="w",
                        font=ctk.CTkFont(size=sp(11, s))).pack(side="left", padx=sp(Spacing.SM, s), pady=sp(Spacing.XS, s))
            
            def restore(idx=i):
                result = self.closed_tabs_manager.get_tab(idx)
                if result:
                    content, fp, lang = result
                    self._create_tab(fp, content)
                    self.closed_tabs_manager.remove_tab(idx)
                    dialog.destroy()
            
            ctk.CTkButton(row, text="Restore", width=sp(70, s), height=sp(24, s),
                         fg_color=THEME.bg_light, hover_color=THEME.bg_hover,
                         command=restore).pack(side="right", padx=sp(Spacing.XS, s), pady=sp(Spacing.XS, s))
    
    def _show_recent_files(self):
        """Show recent files dropdown"""
        s = self.settings.ui_scale
        if not self.settings.recent_files:
            self.toast.show("No recent files", "info")
            return
        
        menu = tk.Menu(self, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        
        for filepath in self.settings.recent_files[:20]:
            if os.path.exists(filepath):
                icon = get_file_icon(filepath)
                name = os.path.basename(filepath)
                menu.add_command(label=f"{icon} {name}", command=lambda p=filepath: self._open_file(p))
        
        if self.settings.recent_files:
            menu.add_separator()
            menu.add_command(label="Clear Recent", command=self._clear_recent_files)
        
        try:
            x = self.recent_btn.winfo_rootx()
            y = self.recent_btn.winfo_rooty() + self.recent_btn.winfo_height()
            menu.tk_popup(x, y)
        except Exception:
            pass
    
    def _clear_recent_files(self):
        """Clear recent files list"""
        self.settings.recent_files = []
        self.toast.show("Recent files cleared", "info")
    
    def _show_welcome(self):
        """Show welcome screen"""
        self.welcome_visible = True
        self.welcome_screen = WelcomeScreen(
            self.editor_frame, self.settings,
            on_new=self._new_from_welcome,
            on_open=self._open_from_welcome,
            on_recent=self._open_recent_from_welcome,
            recent_files=self.settings.recent_files
        )
        self.welcome_screen.pack(fill="both", expand=True)
    
    def _hide_welcome(self):
        """Hide welcome screen"""
        if self.welcome_visible:
            self.welcome_visible = False
            if hasattr(self, 'welcome_screen'):
                self.welcome_screen.destroy()
    
    def _new_from_welcome(self):
        """New file from welcome screen"""
        self._hide_welcome()
        self._new_file()
    
    def _open_from_welcome(self, path=None):
        """Open file/folder from welcome screen"""
        self._hide_welcome()
        if path and os.path.isdir(path):
            self.sidebar.set_root(path)
            if not self.settings.sidebar_visible:
                self._toggle_sidebar()
        else:
            self._open_file(path)
    
    def _open_recent_from_welcome(self, filepath):
        """Open recent file from welcome"""
        self._hide_welcome()
        self._open_file(filepath)
    
    def _show_text_context_menu(self, event, tab_id: str):
        """Show context menu for text widget"""
        if tab_id not in self.text_widgets:
            return
        text = self.text_widgets[tab_id]
        
        menu = tk.Menu(text, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        menu.add_command(label="Cut", command=self._cut, accelerator="Ctrl+X")
        menu.add_command(label="Copy", command=self._copy, accelerator="Ctrl+C")
        menu.add_command(label="Paste", command=self._paste, accelerator="Ctrl+V")
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: text.tag_add("sel", "1.0", "end"))
        
        menu.tk_popup(event.x_root, event.y_root)
    
    # ==========================================================================
    # EVENT HANDLERS
    # ==========================================================================
    
    def _on_key_release(self, event, tab_id: str):
        """Handle key release"""
        self._update_statusbar()
        self.debouncer.debounce("line_numbers", lambda: self._redraw_tab_components(tab_id))
        self.highlight_debouncer.debounce("highlight", lambda: self._highlight_current())
    
    def _on_key_press(self, event, tab_id: str):
        """Handle key press"""
        # Auto-indent
        if event.keysym == "Return" and self.settings.auto_indent:
            text = self.text_widgets[tab_id]
            line = text.get("insert linestart", "insert")
            indent = ""
            for char in line:
                if char in " \t":
                    indent += char
                else:
                    break
            # Extra indent after : { [
            if line.rstrip().endswith((":", "{", "[")):
                indent += "    " if self.settings.use_spaces else "\t"
            text.insert("insert", f"\n{indent}")
            return "break"
        
        # Auto-close brackets
        if self.settings.auto_close_brackets and event.char in BRACKET_PAIRS:
            text = self.text_widgets[tab_id]
            text.insert("insert", event.char + BRACKET_PAIRS[event.char])
            text.mark_set("insert", "insert-1c")
            return "break"
    
    def _on_modified(self, tab_id: str):
        """Handle text modification"""
        if tab_id not in self.text_widgets or tab_id not in self.tabs:
            return
        text = self.text_widgets[tab_id]
        tab_data = self.tabs[tab_id]
        
        # Check if actually modified
        if text.edit_modified():
            tab_data.modified = True
            if tab_data.tab_frame:
                tab_data.tab_frame.modified_label.configure(text="●")
            self._update_title()
        text.edit_modified(False)
    
    def _on_click(self, event, tab_id: str):
        """Handle text click"""
        self._stop_auto_scroll(tab_id)
        self._update_statusbar()
        if self.settings.bracket_highlight_enabled:
            self.debouncer.debounce("brackets", lambda: self._highlight_brackets(tab_id))
    
    def _on_scroll(self, tab_id: str, scrollbar, *args):
        """Handle scroll"""
        scrollbar.set(*args)
        self.debouncer.debounce("minimap", lambda: self._redraw_minimap(tab_id))
    
    def _on_mousewheel(self, event, tab_id: str):
        """Handle mousewheel scroll"""
        self._stop_auto_scroll(tab_id)
        if tab_id in self.text_widgets:
            self.text_widgets[tab_id].yview_scroll(int(-event.delta / 120), "units")
        return "break"
    
    def _on_ctrl_scroll(self, event, tab_id: str):
        """Handle Ctrl+scroll for zoom"""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
        return "break"
    
    # Auto-scroll state
    _auto_scroll_active = False
    _auto_scroll_origin_y = 0
    _auto_scroll_tab_id = None
    
    def _start_auto_scroll(self, event, tab_id: str):
        """Start auto-scroll mode"""
        self._auto_scroll_active = True
        self._auto_scroll_origin_y = event.y
        self._auto_scroll_tab_id = tab_id
        if tab_id in self.text_widgets:
            self.text_widgets[tab_id].configure(cursor="fleur")
        self._auto_scroll_loop()
    
    def _auto_scroll_motion(self, event, tab_id: str):
        """Update auto-scroll based on mouse position"""
        if self._auto_scroll_active and tab_id == self._auto_scroll_tab_id:
            delta = event.y - self._auto_scroll_origin_y
            if tab_id in self.text_widgets:
                speed = max(-15, min(15, delta // 10))
                if abs(speed) > 0:
                    self.text_widgets[tab_id].yview_scroll(speed, "units")
    
    def _auto_scroll_loop(self):
        """Auto-scroll animation loop"""
        if not self._auto_scroll_active:
            return
        self.after(50, self._auto_scroll_loop)
    
    def _stop_auto_scroll(self, tab_id: str = None):
        """Stop auto-scroll mode"""
        self._auto_scroll_active = False
        if self._auto_scroll_tab_id and self._auto_scroll_tab_id in self.text_widgets:
            self.text_widgets[self._auto_scroll_tab_id].configure(cursor="xterm")
        self._auto_scroll_tab_id = None
    
    def _add_cursor(self, event, tab_id: str):
        """Add additional cursor at click location (multi-cursor)"""
        if not self.settings.multi_cursor_enabled:
            return
        # Multi-cursor is complex to implement fully with tk.Text
        # For now, just show a toast indicating the feature
        self.toast.show("Multi-cursor: Ctrl+Click to add cursors", "info")
    
    def _highlight_current(self):
        """Highlight syntax in current editor"""
        if self.current_tab and self.current_tab in self.highlighters:
            self.highlighters[self.current_tab].highlight_visible()
    
    def _highlight_brackets(self, tab_id: str):
        """Highlight matching brackets"""
        if tab_id not in self.text_widgets:
            return
        text = self.text_widgets[tab_id]
        text.tag_remove("bracket_match", "1.0", "end")
        
        try:
            pos = text.index("insert")
            char = text.get(pos)
            
            if char in BRACKET_PAIRS:
                # Find closing bracket
                close = BRACKET_PAIRS[char]
                depth = 1
                search_pos = f"{pos}+1c"
                while depth > 0:
                    next_open = text.search(char, search_pos, stopindex="end")
                    next_close = text.search(close, search_pos, stopindex="end")
                    if not next_close:
                        break
                    if next_open and text.compare(next_open, "<", next_close):
                        depth += 1
                        search_pos = f"{next_open}+1c"
                    else:
                        depth -= 1
                        if depth == 0:
                            text.tag_add("bracket_match", pos)
                            text.tag_add("bracket_match", next_close)
                        search_pos = f"{next_close}+1c"
            elif char in CLOSE_BRACKETS:
                # Find opening bracket
                open_br = CLOSE_BRACKETS[char]
                depth = 1
                search_pos = pos
                while depth > 0:
                    # Search backwards
                    content = text.get("1.0", search_pos)
                    open_idx = content.rfind(open_br)
                    close_idx = content.rfind(char)
                    if open_idx == -1:
                        break
                    if close_idx > open_idx:
                        depth += 1
                        search_pos = f"1.0+{close_idx}c"
                    else:
                        depth -= 1
                        if depth == 0:
                            text.tag_add("bracket_match", pos)
                            text.tag_add("bracket_match", f"1.0+{open_idx}c")
                        search_pos = f"1.0+{open_idx}c"
        except Exception:
            pass
    
    def _redraw_minimap(self, tab_id: str):
        """Redraw minimap for tab"""
        if tab_id in self.minimaps:
            self.minimaps[tab_id].redraw()
    
    def _update_statusbar(self):
        """Update status bar information"""
        if not hasattr(self, 'statusbar') or not hasattr(self, 'path_label'):
            return
        
        if not self.current_tab or self.current_tab not in self.tabs:
            return
        
        tab_data = self.tabs[self.current_tab]
        
        # Path
        if tab_data.filepath:
            self.path_label.configure(text=tab_data.filepath)
        else:
            self.path_label.configure(text="Untitled")
        
        # Position
        if self.current_tab in self.text_widgets and hasattr(self, 'pos_label'):
            text = self.text_widgets[self.current_tab]
            try:
                pos = text.index("insert")
                line, col = pos.split(".")
                self.pos_label.configure(text=f"Ln {line}, Col {int(col)+1}")
            except tk.TclError:
                pass
        
        # Language
        if hasattr(self, 'lang_label'):
            self.lang_label.configure(text=tab_data.language)
        
        # Line Ending
        if hasattr(self, 'line_ending_label'):
            self.line_ending_label.configure(text=tab_data.line_ending)
        
        # Encoding
        if hasattr(self, 'enc_label'):
            display_enc = "UTF-8" if tab_data.encoding.lower() in ("utf-8", "utf8") else "ANSI"
            self.enc_label.configure(text=display_enc)
        
        # Zoom
        if hasattr(self, 'zoom_label'):
            zoom = int((self.settings.font_size / 12) * 100)
            self.zoom_label.configure(text=f"{zoom}%")
    
    def _update_title(self):
        """Update window title"""
        title = "Mattpad"
        if self.current_tab and self.current_tab in self.tabs:
            tab_data = self.tabs[self.current_tab]
            name = os.path.basename(tab_data.filepath) if tab_data.filepath else "Untitled"
            modified = "●" if tab_data.modified else ""
            title = f"{modified}{name} - Mattpad"
        self.title(title)
    
    def _toggle_line_ending(self):
        """Toggle between CRLF and LF line endings for current file"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return
        
        tab_data = self.tabs[self.current_tab]
        text = self.text_widgets[self.current_tab]
        
        # Get current content
        try:
            content = text.get("1.0", "end-1c")
        except tk.TclError:
            return
        
        # Toggle line ending
        current_ending = tab_data.line_ending
        new_ending = "LF" if current_ending == "CRLF" else "CRLF"
        
        # Convert content
        new_content = convert_line_endings(content, current_ending, new_ending)
        
        # Update text widget
        text.delete("1.0", "end")
        text.insert("1.0", new_content)
        
        # Update tab data
        tab_data.line_ending = new_ending
        tab_data.modified = True
        
        # Update UI
        self._update_tab_button(self.current_tab)
        self._update_statusbar()
        
        self.toast.show(f"Line ending changed to {new_ending}", "success")
    
    def _toggle_encoding(self):
        """Toggle between UTF-8 and ANSI (latin-1) encoding"""
        if not self.current_tab:
            return
        
        tab_data = self.tabs[self.current_tab]
        
        # Toggle encoding
        current_encoding = tab_data.encoding
        if current_encoding.lower() in ("utf-8", "utf8"):
            new_encoding = "latin-1"
        else:
            new_encoding = "utf-8"
        
        # Update tab data
        tab_data.encoding = new_encoding
        tab_data.modified = True
        
        # Update UI
        self._update_tab_button(self.current_tab)
        self._update_statusbar()
        
        display_name = "UTF-8" if new_encoding == "utf-8" else "ANSI"
        self.toast.show(f"Encoding changed to {display_name}", "success")
    
    def _copy_current_path(self, event=None):
        """Copy current file path to clipboard"""
        if self.current_tab and self.tabs[self.current_tab].filepath:
            self.clipboard_clear()
            self.clipboard_append(self.tabs[self.current_tab].filepath)
            self.toast.show("Path copied", "success")
    
    def _select_language(self, event=None):
        """Select syntax highlighting language for current file"""
        if not self.current_tab:
            return
        
        s = self.settings.ui_scale
        dialog = create_dialog(self, "Select Language", 300, 400, self.settings)
        
        # Language list
        languages = sorted(set(FILE_EXTENSIONS.values()))
        languages.insert(0, "Plain Text")
        
        listbox_frame = ctk.CTkFrame(dialog, fg_color=THEME.bg_darkest)
        listbox_frame.pack(fill="both", expand=True, padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        listbox = tk.Listbox(listbox_frame, bg=THEME.bg_darkest, fg=THEME.text_primary,
                            font=("Segoe UI", int(11*s)), selectbackground=THEME.accent_primary,
                            selectforeground=THEME.text_primary, borderwidth=0, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(listbox_frame, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)
        
        for lang in languages:
            listbox.insert("end", lang)
        
        # Select current language
        current_lang = self.tabs[self.current_tab].language
        if current_lang in languages:
            idx = languages.index(current_lang)
            listbox.selection_set(idx)
            listbox.see(idx)
        
        def apply_language():
            selection = listbox.curselection()
            if selection:
                lang = listbox.get(selection[0])
                self.tabs[self.current_tab].language = lang
                
                # Update highlighter
                if self.current_tab in self.highlighters:
                    # Find extension for this language
                    ext = ".txt"
                    for e, l in FILE_EXTENSIONS.items():
                        if l == lang:
                            ext = e
                            break
                    self.highlighters[self.current_tab] = SyntaxHighlighter(
                        self.text_widgets[self.current_tab], ext)
                    self.highlighters[self.current_tab].highlight()
                
                # Update status bar
                if hasattr(self, 'lang_label'):
                    self.lang_label.configure(text=lang)
                
                self.toast.show(f"Language: {lang}", "success")
                dialog.destroy()
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        ctk.CTkButton(btn_frame, text="Apply", width=sp(80, s), command=apply_language,
                     fg_color=THEME.accent_primary).pack(side="right", padx=sp(Spacing.XS, s))
        ctk.CTkButton(btn_frame, text="Cancel", width=sp(80, s), command=dialog.destroy,
                     fg_color=THEME.bg_medium).pack(side="right", padx=sp(Spacing.XS, s))
        
        listbox.bind("<Double-1>", lambda e: apply_language())
    
    # ==========================================================================
    # SESSION MANAGEMENT
    # ==========================================================================
    
    def _save_session(self):
        """Save current session"""
        tabs = []
        for tab_id, tab_data in self.tabs.items():
            if tab_id in self.text_widgets:
                content = self.text_widgets[tab_id].get("1.0", "end-1c")
                tabs.append({
                    "tab_id": tab_id,
                    "filepath": tab_data.filepath,
                    "language": tab_data.language,
                    "content": content if not tab_data.filepath else "",
                    "encoding": tab_data.encoding
                })
        self.cache_manager.save_session(tabs)
    
    def _restore_session(self):
        """Restore previous session"""
        tabs = self.cache_manager.load_session()
        for tab in tabs:
            filepath = tab.get("filepath")
            content = tab.get("content", "")
            
            if filepath and os.path.exists(filepath):
                try:
                    content = Path(filepath).read_text(encoding=tab.get("encoding", "utf-8"))
                except Exception:
                    pass
            
            if content or filepath:
                self._create_tab(filepath, content, tab.get("tab_id"))
    
    def _on_close(self):
        """Handle window close with hot exit support"""
        # Hot Exit: Save complete session state (Notepad++ style)
        if self.settings.hot_exit_enabled:
            try:
                self.hot_exit.save_snapshot(
                    tabs=self.tabs,
                    text_widgets=self.text_widgets,
                    current_tab=self.current_tab,
                    active_order=self.tab_order
                )
                logger.info("Hot exit snapshot saved successfully")
            except Exception as e:
                logger.error(f"Hot exit save failed: {e}")
        
        # Save session
        self._save_session()
        
        # Save panel widths
        s = self.settings.ui_scale
        try:
            if self.settings.sidebar_visible:
                self.settings.sidebar_width = int(self.sidebar_frame.winfo_width() / s)
            if self.settings.clipboard_panel_visible:
                self.settings.clipboard_panel_width = int(self.clipboard_frame.winfo_width() / s)
        except Exception:
            pass
        
        # Save window state
        try:
            if self.state() == 'zoomed':
                self.settings.window_maximized = True
            else:
                self.settings.window_maximized = False
                self.settings.window_geometry = self.geometry()
        except Exception:
            pass
        
        self._save_settings()
        
        # Auto-save files (only if hot exit is disabled)
        if not self.settings.hot_exit_enabled and self.settings.auto_save_to_disk:
            for tab_id, tab_data in self.tabs.items():
                if tab_data.modified and tab_data.filepath and tab_id in self.text_widgets:
                    try:
                        content = self.text_widgets[tab_id].get("1.0", "end-1c")
                        Path(tab_data.filepath).write_text(content, encoding=tab_data.encoding)
                        self.backup_manager.create_backup(tab_data.filepath, content)
                    except Exception as e:
                        logger.error(f"Final save failed: {e}")
        
        # Cache tabs (backup to hot exit)
        if not self.settings.hot_exit_enabled:
            for tab_id, tab_data in self.tabs.items():
                if tab_id in self.text_widgets:
                    try:
                        content = self.text_widgets[tab_id].get("1.0", "end-1c")
                        if content.strip():
                            self.cache_manager.save_tab(tab_id, content, {"filepath": tab_data.filepath, "language": tab_data.language})
                    except tk.TclError:
                        pass
        
        # Stop clipboard monitoring
        self.system_clipboard.monitoring = False
        
        # Cancel debouncers
        self.debouncer.cancel_all()
        self.highlight_debouncer.cancel_all()
        
        logger.info("Mattpad closing gracefully")
        self.destroy()
    
    def _restore_hot_exit(self):
        """Restore tabs from hot exit snapshot"""
        snapshot = self.hot_exit.load_snapshot()
        if not snapshot:
            return
        
        try:
            for tab_info in snapshot.get("tabs", []):
                tab_id = tab_info.get("tab_id")
                content = tab_info.get("content", "")
                filepath = tab_info.get("filepath")
                
                # Create tab
                new_tab_id = self._create_tab(
                    filepath=filepath,
                    content=content,
                    tab_id=tab_id
                )
                
                if new_tab_id and new_tab_id in self.tabs:
                    # Restore tab state
                    self.tabs[new_tab_id].modified = tab_info.get("modified", False)
                    self.tabs[new_tab_id].encoding = tab_info.get("encoding", "utf-8")
                    self.tabs[new_tab_id].line_ending = tab_info.get("line_ending", "CRLF")
                    
                    # Restore cursor and scroll position
                    if new_tab_id in self.text_widgets:
                        text = self.text_widgets[new_tab_id]
                        cursor_pos = tab_info.get("cursor_position", "1.0")
                        scroll_pos = tab_info.get("scroll_position", (0.0, 0.0))
                        
                        try:
                            text.mark_set(tk.INSERT, cursor_pos)
                            text.see(cursor_pos)
                            if scroll_pos:
                                text.xview_moveto(scroll_pos[0])
                                text.yview_moveto(scroll_pos[1])
                        except tk.TclError:
                            pass
                    
                    # Update tab button if modified
                    if tab_info.get("modified"):
                        self._update_tab_button(new_tab_id)
            
            # Switch to the previously active tab
            current_tab = snapshot.get("current_tab")
            if current_tab and current_tab in self.tabs:
                self._switch_tab(current_tab)
            
            # Clear snapshot after successful restore
            self.hot_exit.clear_snapshot()
            
            self.toast.show(f"Restored {len(snapshot.get('tabs', []))} tabs from previous session", "success")
            logger.info(f"Hot exit restored {len(snapshot.get('tabs', []))} tabs")
            
        except Exception as e:
            logger.error(f"Hot exit restore failed: {e}")
            self.toast.show("Failed to restore previous session", "error")
    
    # ==========================================================================
    # ADDITIONAL FEATURES
    # ==========================================================================
    
    def _import_notepadpp(self):
        """Import Notepad++ session"""
        filepath = filedialog.askopenfilename(
            title="Select Notepad++ Session File",
            filetypes=[("Session Files", "*.xml"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            count = 0
            for view in root.findall(".//File"):
                fpath = view.get("filename")
                if fpath and os.path.exists(fpath):
                    self._open_file(fpath)
                    count += 1
            self.toast.show(f"Imported {count} file(s)", "success")
        except Exception as e:
            self.toast.show(f"Import failed: {e}", "error")
    
    def _show_backups(self):
        """Show backups for current file"""
        if not self.current_tab or not self.tabs[self.current_tab].filepath:
            self.toast.show("Save file first to see backups", "info")
            return
        
        s = self.settings.ui_scale
        backups = self.backup_manager.get_backups(self.tabs[self.current_tab].filepath)
        if not backups:
            self.toast.show("No backups found", "info")
            return
        
        dialog = create_dialog(self, "Backups", 500, 400, self.settings)
        
        frame = ctk.CTkScrollableFrame(dialog, fg_color=THEME.bg_darkest)
        frame.pack(fill="both", expand=True, padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        for path, timestamp in backups[:20]:
            row = ctk.CTkFrame(frame, fg_color=THEME.bg_dark, corner_radius=sp(4, s))
            row.pack(fill="x", pady=sp(2, s))
            
            ctk.CTkLabel(row, text=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        font=ctk.CTkFont(size=sp(11, s))).pack(side="left", padx=sp(Spacing.SM, s), pady=sp(Spacing.XS, s))
            
            def restore(p=path):
                try:
                    content = p.read_text(encoding='utf-8')
                    if self.current_tab in self.text_widgets:
                        self.text_widgets[self.current_tab].delete("1.0", "end")
                        self.text_widgets[self.current_tab].insert("1.0", content)
                        self.toast.show("Backup restored", "success")
                        dialog.destroy()
                except Exception as e:
                    self.toast.show(f"Restore failed: {e}", "error")
            
            ctk.CTkButton(row, text="Restore", width=sp(70, s), height=sp(24, s),
                         fg_color=THEME.bg_light, hover_color=THEME.bg_hover,
                         command=restore).pack(side="right", padx=sp(Spacing.XS, s), pady=sp(Spacing.XS, s))
    
    def _show_dictionary(self):
        """Show custom dictionary editor"""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "Custom Dictionary", 400, 500, self.settings)
        
        ctk.CTkLabel(dialog, text="Custom Words", font=ctk.CTkFont(size=sp(14, s), weight="bold")).pack(pady=sp(Spacing.MD, s))
        
        frame = ctk.CTkFrame(dialog, fg_color=THEME.bg_darkest)
        frame.pack(fill="both", expand=True, padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        listbox = tk.Listbox(frame, bg=THEME.bg_darkest, fg=THEME.text_primary,
                            selectbackground=THEME.selection_bg, font=("Consolas", sp(11, s)),
                            borderwidth=0, highlightthickness=0)
        scroll = ctk.CTkScrollbar(frame, command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        listbox.pack(fill="both", expand=True)
        
        for word in sorted(self.spellcheck.custom_words):
            listbox.insert("end", word)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        entry = ctk.CTkEntry(btn_frame, fg_color=THEME.bg_darkest, width=sp(200, s))
        entry.pack(side="left", padx=sp(Spacing.XS, s))
        
        def add_word():
            word = entry.get().strip()
            if word:
                self.spellcheck.add_word(word)
                listbox.insert("end", word.lower())
                entry.delete(0, "end")
        
        def remove_word():
            sel = listbox.curselection()
            if sel:
                word = listbox.get(sel[0])
                self.spellcheck.remove_word(word)
                listbox.delete(sel[0])
        
        ctk.CTkButton(btn_frame, text="Add", width=sp(60, s), command=add_word,
                     fg_color=THEME.accent_primary).pack(side="left", padx=sp(Spacing.XS, s))
        ctk.CTkButton(btn_frame, text="Remove", width=sp(70, s), command=remove_word,
                     fg_color=THEME.bg_medium).pack(side="left", padx=sp(Spacing.XS, s))
    
    def _ai_action(self, action: str):
        """Perform AI action on selected text"""
        if not self.current_tab or self.current_tab not in self.text_widgets:
            return
        
        text = self.text_widgets[self.current_tab]
        try:
            selected = text.get("sel.first", "sel.last")
        except tk.TclError:
            selected = text.get("1.0", "end-1c")
        
        if not selected.strip():
            self.toast.show("No text selected", "warning")
            return
        
        prompts = {
            "Summarize": "Summarize the following text concisely:",
            "Fix Grammar": "Fix any grammar and spelling errors in the following text, preserving the original meaning:",
            "Explain Code": "Explain what this code does in simple terms:",
        }
        prompt = prompts.get(action, action)
        
        self.toast.show(f"Processing with AI...", "info")
        
        def process():
            result = self.ai_manager.process(selected, prompt)
            if result:
                self.after(0, lambda: self._show_ai_result(result))
            else:
                self.after(0, lambda: self.toast.show("AI processing failed. Check settings.", "error"))
        
        threading.Thread(target=process, daemon=True).start()
    
    def _show_ai_result(self, result: str):
        """Show AI result in dialog"""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "AI Result", 600, 400, self.settings)
        
        text = tk.Text(dialog, bg=THEME.bg_darkest, fg=THEME.text_primary,
                      font=("Consolas", sp(11, s)), wrap="word", borderwidth=0)
        text.pack(fill="both", expand=True, padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        text.insert("1.0", result)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        def insert_result():
            if self.current_tab and self.current_tab in self.text_widgets:
                self.text_widgets[self.current_tab].insert("insert", result)
            dialog.destroy()
        
        def copy_result():
            self.clipboard_clear()
            self.clipboard_append(result)
            self.toast.show("Copied to clipboard", "success")
        
        ctk.CTkButton(btn_frame, text="Insert", width=sp(80, s), command=insert_result,
                     fg_color=THEME.accent_primary).pack(side="right", padx=sp(Spacing.XS, s))
        ctk.CTkButton(btn_frame, text="Copy", width=sp(80, s), command=copy_result,
                     fg_color=THEME.bg_medium).pack(side="right", padx=sp(Spacing.XS, s))
    
    def _ai_custom_prompt(self):
        """Custom AI prompt dialog"""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "Custom AI Prompt", 500, 300, self.settings)
        
        ctk.CTkLabel(dialog, text="Enter your prompt:", font=ctk.CTkFont(size=sp(12, s))).pack(pady=sp(Spacing.MD, s))
        
        prompt_text = ctk.CTkTextbox(dialog, fg_color=THEME.bg_darkest, height=sp(150, s))
        prompt_text.pack(fill="x", padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        def execute():
            prompt = prompt_text.get("1.0", "end-1c").strip()
            if prompt:
                dialog.destroy()
                self._ai_action(prompt)
        
        ctk.CTkButton(dialog, text="Execute", width=sp(100, s), command=execute,
                     fg_color=THEME.accent_primary).pack(pady=sp(Spacing.MD, s))
    
    def _do_cloud_sync(self):
        """Sync current file to cloud"""
        if not self.current_tab or not self.tabs[self.current_tab].filepath:
            self.toast.show("Save file first to sync", "warning")
            return
        
        if not self.settings.github_token or not self.settings.github_repo:
            self.toast.show("Configure GitHub first in Options", "warning")
            return
        
        filepath = self.tabs[self.current_tab].filepath
        content = self.text_widgets[self.current_tab].get("1.0", "end-1c")
        
        self.toast.show("Syncing to GitHub...", "info")
        
        def sync():
            success = self.cloud_sync.sync_to_github(filepath, content)
            msg = "Sync complete!" if success else "Sync failed"
            toast_type = "success" if success else "error"
            self.after(0, lambda: self.toast.show(msg, toast_type))
        
        threading.Thread(target=sync, daemon=True).start()
    
    def _configure_github(self):
        """Configure GitHub sync settings"""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "GitHub Configuration", 450, 350, self.settings)
        
        fields = [
            ("GitHub Token:", "github_token", True),
            ("Repository (user/repo):", "github_repo", False),
            ("Branch:", "github_branch", False),
            ("Path:", "github_path", False),
        ]
        
        entries = {}
        for label, attr, is_secret in fields:
            row = ctk.CTkFrame(dialog, fg_color="transparent")
            row.pack(fill="x", padx=sp(Spacing.LG, s), pady=sp(Spacing.SM, s))
            
            ctk.CTkLabel(row, text=label, width=sp(150, s), anchor="w").pack(side="left")
            
            entry = ctk.CTkEntry(row, fg_color=THEME.bg_darkest, width=sp(200, s),
                                show="*" if is_secret else "")
            entry.insert(0, getattr(self.settings, attr, ""))
            entry.pack(side="left")
            entries[attr] = entry
        
        def save():
            for attr, entry in entries.items():
                setattr(self.settings, attr, entry.get())
            self._save_settings()
            self.toast.show("GitHub settings saved", "success")
            dialog.destroy()
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=sp(Spacing.LG, s), pady=sp(Spacing.LG, s))
        
        ctk.CTkButton(btn_frame, text="Save", width=sp(80, s), command=save,
                     fg_color=THEME.accent_primary).pack(side="right", padx=sp(Spacing.XS, s))
        ctk.CTkButton(btn_frame, text="Cancel", width=sp(80, s), command=dialog.destroy,
                     fg_color=THEME.bg_medium).pack(side="right", padx=sp(Spacing.XS, s))
    
    def _toggle_terminal(self):
        """Toggle integrated terminal"""
        if not self.settings.terminal_enabled:
            self.toast.show("Terminal disabled in settings", "info")
            return
        
        self.terminal_visible = not self.terminal_visible
        if self.terminal_visible:
            self._create_terminal()
            self.terminal_frame.pack(side="bottom", fill="x", before=self.editor_frame)
        else:
            self.terminal_frame.pack_forget()
    
    def _create_terminal(self):
        """Create terminal widget"""
        s = self.settings.ui_scale
        
        # Clear existing
        for child in self.terminal_frame.winfo_children():
            child.destroy()
        
        # Header
        header = ctk.CTkFrame(self.terminal_frame, fg_color=THEME.ribbon_group_bg, height=sp(30, s))
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="  TERMINAL", font=ctk.CTkFont(size=sp(11, s), weight="bold"),
                    text_color=THEME.text_secondary).pack(side="left")
        
        ctk.CTkButton(header, text="✕", width=sp(28, s), height=sp(24, s),
                     fg_color="transparent", hover_color=THEME.bg_hover,
                     command=self._toggle_terminal).pack(side="right", padx=sp(Spacing.XS, s))
        
        # Terminal text
        self.terminal_text = tk.Text(self.terminal_frame, bg=THEME.bg_darkest, fg=THEME.text_primary,
                                    font=("Consolas", self.settings.terminal_font_size),
                                    height=8, borderwidth=0, highlightthickness=0)
        self.terminal_text.pack(fill="both", expand=True, padx=sp(Spacing.XS, s), pady=sp(Spacing.XS, s))
        self.terminal_text.insert("end", "Terminal - Press Enter to execute commands\n$ ")
        self.terminal_text.bind("<Return>", lambda e: self._execute_terminal_command(e))
    
    def _execute_terminal_command(self, event):
        """Execute command in terminal"""
        content = self.terminal_text.get("1.0", "end-1c")
        lines = content.split("\n")
        last_line = lines[-1] if lines else ""
        
        if last_line.startswith("$ "):
            cmd = last_line[2:]
            self.terminal_text.insert("end", "\n")
            
            def run():
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    output = result.stdout + result.stderr
                except subprocess.TimeoutExpired:
                    output = "Command timed out"
                except Exception as e:
                    output = str(e)
                
                self.after(0, lambda: self._terminal_output(output))
            
            threading.Thread(target=run, daemon=True).start()
        return "break"
    
    def _terminal_output(self, output: str):
        """Add output to terminal"""
        self.terminal_text.insert("end", output)
        if not output.endswith("\n"):
            self.terminal_text.insert("end", "\n")
        self.terminal_text.insert("end", "$ ")
        self.terminal_text.see("end")
    
    def _reload_current(self):
        """Reload current file from disk"""
        if self.current_tab:
            self._reload_file(self.current_tab)
    
    def _compare_files(self):
        """Compare two files"""
        s = self.settings.ui_scale
        
        file1 = filedialog.askopenfilename(title="Select First File")
        if not file1:
            return
        
        file2 = filedialog.askopenfilename(title="Select Second File")
        if not file2:
            return
        
        try:
            content1 = Path(file1).read_text(encoding='utf-8')
            content2 = Path(file2).read_text(encoding='utf-8')
        except Exception as e:
            self.toast.show(f"Error reading files: {e}", "error")
            return
        
        diff = DiffEngine.compare(content1, content2)
        
        dialog = create_dialog(self, "File Comparison", 800, 600, self.settings)
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        ctk.CTkLabel(header, text=f"← {os.path.basename(file1)}", 
                    text_color=THEME.accent_red).pack(side="left")
        ctk.CTkLabel(header, text=f"→ {os.path.basename(file2)}",
                    text_color=THEME.accent_green).pack(side="right")
        
        # Diff view
        text = tk.Text(dialog, bg=THEME.bg_darkest, fg=THEME.text_primary,
                      font=("Consolas", sp(11, s)), wrap="none", borderwidth=0)
        scroll = ctk.CTkScrollbar(dialog, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True, padx=sp(Spacing.MD, s), pady=sp(Spacing.MD, s))
        
        text.tag_configure("removed", background="#3d1f1f", foreground=THEME.accent_red)
        text.tag_configure("added", background="#1f3d1f", foreground=THEME.accent_green)
        text.tag_configure("same", foreground=THEME.text_muted)
        
        for diff_type, line in diff:
            if diff_type == "removed":
                text.insert("end", f"- {line}", "removed")
            elif diff_type == "added":
                text.insert("end", f"+ {line}", "added")
            else:
                text.insert("end", f"  {line}", "same")
        
        text.configure(state="disabled")

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    app = Mattpad()
    app.mainloop()


if __name__ == "__main__":
    main()
