"""
Mattpad v6.0 - Professional Text Editor
Main Application Module
"""
import os
import sys
import re
import json
import time
import hashlib
import threading
import logging
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, font as tkfont
import tkinter as tk
import customtkinter as ctk
from typing import Dict, Optional, List, Callable

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Version
VERSION = "6.0"

# Constants
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
LARGE_FILE_THRESHOLD = 500000  # 500KB

# Import local modules
from .utils.themes import Theme, THEMES, get_theme, THEME, set_theme
from .utils.dispatcher import ThreadSafeDispatcher, set_dispatcher, get_dispatcher
from .utils.debouncer import Debouncer
from .utils.file_utils import (
    FILE_EXTENSIONS, get_file_icon, detect_line_ending,
    detect_encoding, read_file_safe, write_file_safe, get_language_from_extension
)

from .core.settings import EditorSettings, APP_DIR, SETTINGS_FILE
from .core.tabs import TabData
from .core.managers import (
    CacheManager, BackupManager, SessionManager, HotExitManager,
    ClosedTabsManager, SecretStorage
)

from .features.syntax import SyntaxHighlighter
from .features.spellcheck import SpellCheckManager
from .features.ai import AIManager
from .features.cloud import CloudSyncManager
from .features.snippets import SnippetsManager, MacroManager
from .features.clipboard import SystemClipboardManager

from .ui.ribbon import Ribbon, RibbonButton
from .ui.minimap import Minimap
from .ui.line_numbers import LineNumberCanvas
from .ui.toast import ToastManager
from .ui.welcome import WelcomeScreen
from .ui.sidebar import FileTreeView
from .ui.clipboard_panel import ClipboardPanel
from .ui.find_replace import FindReplaceBar
from .ui.dialogs import create_dialog, DiffEngine, SettingsDialog


def set_dark_title_bar(window):
    """Set dark title bar on Windows."""
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception:
            pass


class Mattpad(ctk.CTk):
    """Main Mattpad application."""
    
    def __init__(self):
        super().__init__()
        logger.info(f"Initializing Mattpad v{VERSION}")
        
        # Initialize thread-safe dispatcher
        set_dispatcher(ThreadSafeDispatcher(self))
        
        # Load settings
        self.settings = EditorSettings()
        self._load_settings()
        
        # Apply theme
        global THEME
        THEME = set_theme(self.settings.theme_name)
        
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
        self.tab_order: List[str] = []
        
        # Managers
        self.cache_manager = CacheManager()
        self.closed_tabs_manager = ClosedTabsManager()
        self.backup_manager = BackupManager(self.settings)
        self.cloud_sync = CloudSyncManager(self.settings)
        self.ai_manager = AIManager(self.settings)
        self.spellcheck = SpellCheckManager()
        self.snippets = SnippetsManager()
        self.macros = MacroManager()
        self.hot_exit = HotExitManager()
        
        # Debouncer
        self.debouncer = Debouncer(self, 200)
        self.highlight_debouncer = Debouncer(self, 250)
        
        # Window setup
        self.title("Mattpad")
        self.configure(fg_color=THEME.bg_darkest)
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.geometry(self.settings.window_geometry or "1400x800")
        
        if self.settings.window_maximized:
            self.after(100, lambda: self.state('zoomed'))
        
        self.after(150, lambda: set_dark_title_bar(self))
        
        # Clipboard manager
        self.system_clipboard = SystemClipboardManager(self)
        
        # Toast manager
        self.toast = ToastManager(self, self.settings)
        
        # Build commands for palette
        self._build_commands()
        
        # Build UI
        self._create_ribbon()
        self._create_main_layout()
        self._create_statusbar()
        self._bind_shortcuts()
        
        # Restore session
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
        """Build command list for command palette."""
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
            ("Zoom In", "Ctrl++", self._zoom_in),
            ("Zoom Out", "Ctrl+-", self._zoom_out),
            ("Reset Zoom", "Ctrl+0", self._zoom_reset),
            ("Settings", "", self._show_settings),
            ("Toggle Terminal", "", self._toggle_terminal),
            ("Compare Files", "", self._compare_files),
        ]
    
    def _load_settings(self):
        """Load settings from file."""
        self.settings.load()
        # Load secrets
        for key in ["github_token", "ai_api_key"]:
            secret = SecretStorage.get(key, "")
            if secret:
                setattr(self.settings, key, secret)
    
    def _save_settings(self):
        """Save settings to file."""
        # Store secrets securely
        SecretStorage.store("github_token", self.settings.github_token)
        SecretStorage.store("ai_api_key", self.settings.ai_api_key)
        self.settings.save()
    
    def _create_ribbon(self):
        """Create the ribbon toolbar."""
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
        
        self.wrap_var = tk.BooleanVar(value=self.settings.word_wrap)
        self.linenum_var = tk.BooleanVar(value=self.settings.show_line_numbers)
        self.minimap_var = tk.BooleanVar(value=self.settings.show_minimap)
        
        ctk.CTkCheckBox(editor_btns, text="Word Wrap", variable=self.wrap_var, 
                       command=self._toggle_word_wrap, font=ctk.CTkFont(size=int(10*s)),
                       fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(editor_btns, text="Line Numbers", variable=self.linenum_var,
                       command=self._toggle_line_numbers, font=ctk.CTkFont(size=int(10*s)),
                       fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(editor_btns, text="Minimap", variable=self.minimap_var,
                       command=self._toggle_minimap, font=ctk.CTkFont(size=int(10*s)),
                       fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        
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
        
        self.spell_var = tk.BooleanVar(value=self.settings.spellcheck_enabled)
        self.autoclose_var = tk.BooleanVar(value=self.settings.auto_close_brackets)
        self.autosave_var = tk.BooleanVar(value=self.settings.auto_save_enabled)
        
        ctk.CTkCheckBox(prefs_btns, text="Spellcheck", variable=self.spell_var,
                       command=self._toggle_spellcheck, font=ctk.CTkFont(size=int(10*s)),
                       fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(prefs_btns, text="Auto-close Brackets", variable=self.autoclose_var,
                       command=self._toggle_autoclose, font=ctk.CTkFont(size=int(10*s)),
                       fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        ctk.CTkCheckBox(prefs_btns, text="Auto-save", variable=self.autosave_var,
                       command=self._toggle_autosave, font=ctk.CTkFont(size=int(10*s)),
                       fg_color=THEME.accent_primary, height=int(20*s)).pack(anchor="w", pady=int(2*s))
        
        prefs_btns2 = ctk.CTkFrame(prefs_grp.content, fg_color="transparent")
        prefs_btns2.pack(side="left", fill="y", padx=int(4*s))
        RibbonButton(prefs_btns2, "⚙", "All Settings", self._show_settings, self.settings).pack(fill="x")
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
    
    def _create_main_layout(self):
        """Create the main layout."""
        s = self.settings.ui_scale
        
        # Main paned window
        self.main_paned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL,
            bg=THEME.bg_light, sashwidth=int(6*s),
            sashrelief=tk.RAISED, borderwidth=0,
            sashcursor="sb_h_double_arrow", opaqueresize=True
        )
        self.main_paned.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self.main_paned, fg_color=THEME.bg_dark, corner_radius=0)
        self.sidebar = FileTreeView(self.sidebar_frame, on_file_select=self._open_file, settings=self.settings)
        self.sidebar.pack(fill="both", expand=True)
        
        if self.settings.sidebar_visible:
            self.main_paned.add(self.sidebar_frame, width=int(self.settings.sidebar_width*s), minsize=int(150*s))
        
        # Editor container
        self.editor_container = ctk.CTkFrame(self.main_paned, fg_color=THEME.bg_darkest, corner_radius=0)
        self.main_paned.add(self.editor_container, minsize=int(400*s))
        
        # Clipboard panel
        self.clipboard_frame = ctk.CTkFrame(self.main_paned, fg_color=THEME.bg_dark, corner_radius=0)
        self.clipboard_panel = ClipboardPanel(
            self.clipboard_frame, self.system_clipboard,
            on_paste=self._paste_from_clipboard, settings=self.settings
        )
        self.clipboard_panel.pack(fill="both", expand=True)
        
        if self.settings.clipboard_panel_visible:
            self.main_paned.add(self.clipboard_frame, width=int(self.settings.clipboard_panel_width*s), minsize=int(150*s))
        
        # Tab bar - theme colors
        self.tab_bar_bg = THEME.tab_bar_bg
        self.tab_active_color = THEME.tab_active
        self.tab_inactive_color = THEME.tab_inactive
        self.tab_hover_color = THEME.tab_hover
        self.tab_text_active = THEME.tab_text_active
        self.tab_text_inactive = THEME.tab_text_inactive
        
        self.tab_bar = ctk.CTkFrame(self.editor_container, fg_color=self.tab_bar_bg, height=int(38*s), corner_radius=0)
        self.tab_bar.pack(fill="x")
        self.tab_bar.pack_propagate(False)
        
        # Tab container with scrolling
        self.tab_scroll_offset = 0
        self.tab_container = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.tab_container.pack(side="left", fill="both", expand=True)
        
        self.tab_clip_frame = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.tab_clip_frame.pack(side="left", fill="both", expand=True)
        self.tab_clip_frame.pack_propagate(False)
        
        self.tab_inner_frame = ctk.CTkFrame(self.tab_clip_frame, fg_color="transparent")
        self.tab_inner_frame.place(x=0, y=0, relheight=1.0)
        
        # Tab bar bindings
        self.tab_container.bind("<MouseWheel>", self._on_tab_scroll)
        self.tab_clip_frame.bind("<MouseWheel>", self._on_tab_scroll)
        self.tab_inner_frame.bind("<MouseWheel>", self._on_tab_scroll)
        self.tab_bar.bind("<MouseWheel>", self._on_tab_scroll)
        
        # Click on empty space creates new tab
        self.tab_container.bind("<Button-1>", lambda e: self._new_file())
        self.tab_clip_frame.bind("<Button-1>", lambda e: self._new_file())
        self.tab_inner_frame.bind("<Button-1>", lambda e: self._new_file())
        self.tab_bar.bind("<Button-1>", self._tab_bar_click)
        
        # Tab list dropdown
        self.tab_list_btn = ctk.CTkButton(
            self.tab_bar, text="▼", width=int(28*s), height=int(28*s),
            fg_color="transparent", hover_color=self.tab_hover_color,
            text_color=self.tab_text_inactive, font=ctk.CTkFont(size=int(12*s)),
            command=self._show_tab_list
        )
        self.tab_list_btn.pack(side="right", padx=int(2*s))
        
        # Recent files button
        self.recent_btn = ctk.CTkButton(
            self.tab_bar, text="📋", width=int(30*s), height=int(28*s),
            fg_color="transparent", hover_color=self.tab_hover_color,
            text_color=self.tab_text_inactive, font=ctk.CTkFont(size=int(14*s)),
            command=self._show_recent_files
        )
        self.recent_btn.pack(side="right", padx=int(2*s))
        
        # New tab button
        ctk.CTkButton(
            self.tab_bar, text="+", width=int(30*s), height=int(28*s),
            fg_color="transparent", hover_color=self.tab_hover_color,
            text_color=self.tab_text_inactive, font=ctk.CTkFont(size=int(16*s)),
            command=self._new_file
        ).pack(side="right", padx=int(4*s))
        
        # Find bar
        self.find_bar = FindReplaceBar(
            self.editor_container, self._do_find, self._do_replace,
            self._do_replace_all, self._hide_find_bar, self._find_in_files,
            settings=self.settings
        )
        
        # Editor frame
        self.editor_frame = ctk.CTkFrame(self.editor_container, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_frame.pack(fill="both", expand=True)
        
        # Terminal (hidden)
        self.terminal_frame = ctk.CTkFrame(self.editor_container, fg_color=THEME.bg_dark, height=int(200*s), corner_radius=0)
        self.terminal_visible = False
    
    def _create_statusbar(self):
        """Create the status bar."""
        s = self.settings.ui_scale
        if not self.settings.show_status_bar:
            return
        
        self.statusbar = ctk.CTkFrame(self, fg_color=THEME.ribbon_group_bg, height=int(24*s), corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        # File path
        self.path_label = ctk.CTkLabel(
            self.statusbar, text="Ready", text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(10*s)), anchor="w", cursor="hand2"
        )
        self.path_label.pack(side="left", padx=int(10*s), fill="x", expand=True)
        self.path_label.bind("<Button-1>", self._copy_current_path)
        
        # Right side info
        right = ctk.CTkFrame(self.statusbar, fg_color="transparent")
        right.pack(side="right")
        
        self.zoom_label = ctk.CTkLabel(
            right, text="100%", text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(10*s)), width=int(45*s), cursor="hand2"
        )
        self.zoom_label.pack(side="right", padx=int(8*s))
        self.zoom_label.bind("<Button-1>", lambda e: self._zoom_reset())
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        self.pos_label = ctk.CTkLabel(
            right, text="Ln 1, Col 1", text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(10*s)), width=int(90*s), cursor="hand2"
        )
        self.pos_label.pack(side="right")
        self.pos_label.bind("<Button-1>", lambda e: self._goto_line())
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        self.line_ending_label = ctk.CTkLabel(
            right, text="CRLF", text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(10*s)), width=int(40*s), cursor="hand2"
        )
        self.line_ending_label.pack(side="right")
        self.line_ending_label.bind("<Button-1>", self._toggle_line_ending)
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        self.encoding_label = ctk.CTkLabel(
            right, text="UTF-8", text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(10*s)), width=int(50*s)
        )
        self.encoding_label.pack(side="right")
        
        ctk.CTkFrame(right, width=1, height=int(14*s), fg_color=THEME.bg_light).pack(side="right", padx=int(4*s))
        
        self.lang_label = ctk.CTkLabel(
            right, text="Plain Text", text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=int(10*s)), width=int(80*s)
        )
        self.lang_label.pack(side="right")
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.bind("<Control-n>", lambda e: self._new_file())
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-s>", lambda e: self._save_file())
        self.bind("<Control-S>", lambda e: self._save_file_as())
        self.bind("<Control-w>", lambda e: self._close_current_tab())
        self.bind("<Control-T>", lambda e: self._reopen_closed_tab())
        self.bind("<Control-f>", lambda e: self._show_find_bar())
        self.bind("<Control-F>", lambda e: self._find_in_files())
        self.bind("<Control-g>", lambda e: self._goto_line())
        self.bind("<Control-b>", lambda e: self._toggle_sidebar())
        self.bind("<Control-plus>", lambda e: self._zoom_in())
        self.bind("<Control-minus>", lambda e: self._zoom_out())
        self.bind("<Control-0>", lambda e: self._zoom_reset())
        self.bind("<Control-Tab>", lambda e: self._next_tab())
        self.bind("<Control-Shift-Tab>", lambda e: self._prev_tab())
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.bind("<Escape>", lambda e: self._on_escape())
    
    # =========================================================================
    # TAB MANAGEMENT
    # =========================================================================
    
    def _create_tab(self, filepath: Optional[str] = None, content: str = "", tab_id: str = None) -> str:
        """Create a new editor tab."""
        self._hide_welcome()
        s = self.settings.ui_scale
        tab_id = tab_id or f"tab_{int(time.time()*1000)}"
        
        ext = os.path.splitext(filepath)[1].lower() if filepath else ".txt"
        language = get_language_from_extension(filepath) if filepath else "Plain Text"
        line_ending = detect_line_ending(content) if content else "CRLF"
        is_large_file = len(content) > LARGE_FILE_THRESHOLD if content else False
        
        tab_data = TabData(
            tab_id=tab_id, filepath=filepath, language=language,
            content_hash=hashlib.md5(content.encode()).hexdigest() if content else "",
            encoding=self.settings.encoding, line_ending=line_ending,
            is_large_file=is_large_file
        )
        self.tabs[tab_id] = tab_data
        
        if tab_id not in self.tab_order:
            self.tab_order.append(tab_id)
        
        # Create tab button
        tab_frame = ctk.CTkFrame(self.tab_inner_frame, fg_color=self.tab_inactive_color, corner_radius=4, height=int(32*s))
        tab_frame.pack(side="left", padx=1, pady=(int(3*s), 0))
        tab_frame.pack_propagate(False)
        
        icon = get_file_icon(filepath) if filepath else "📄"
        name = os.path.basename(filepath) if filepath else "Untitled"
        
        # Store colors for updates
        tab_frame.active_color = self.tab_active_color
        tab_frame.inactive_color = self.tab_inactive_color
        tab_frame.text_active = self.tab_text_active
        tab_frame.text_inactive = self.tab_text_inactive
        tab_frame.hover_color = self.tab_hover_color
        
        tab_inner = ctk.CTkFrame(tab_frame, fg_color="transparent")
        tab_inner.pack(expand=True, fill="both", padx=int(2*s), pady=int(2*s))
        
        tab_btn = ctk.CTkButton(
            tab_inner, text=f"{icon} {name}",
            fg_color="transparent", hover_color=self.tab_hover_color,
            text_color=self.tab_text_inactive, font=ctk.CTkFont(size=int(11*s)),
            command=lambda t=tab_id: self._switch_tab(t),
            anchor="w", height=int(26*s), corner_radius=4
        )
        tab_btn.pack(side="left", fill="y")
        
        close_btn = ctk.CTkButton(
            tab_inner, text="×", width=int(20*s), height=int(20*s),
            fg_color="transparent", hover_color=THEME.tab_close_hover,
            text_color=self.tab_text_inactive, font=ctk.CTkFont(size=int(12*s)),
            command=lambda t=tab_id: self._close_tab(t)
        )
        close_btn.pack(side="right", padx=(int(4*s), 0))
        
        modified_label = ctk.CTkLabel(
            tab_inner, text="", width=int(10*s),
            text_color=THEME.tab_modified, font=ctk.CTkFont(size=int(12*s))
        )
        modified_label.pack(side="right")
        
        tab_frame.tab_btn = tab_btn
        tab_frame.modified_label = modified_label
        tab_frame.close_btn = close_btn
        tab_frame.tab_inner = tab_inner
        tab_data.tab_frame = tab_frame
        
        # Bind mousewheel for scrolling
        for widget in [tab_frame, tab_inner, tab_btn, close_btn]:
            widget.bind("<MouseWheel>", self._on_tab_scroll)
        
        # Middle-click to close
        tab_frame.bind("<Button-2>", lambda e, t=tab_id: self._close_tab(t))
        tab_inner.bind("<Button-2>", lambda e, t=tab_id: self._close_tab(t))
        tab_btn.bind("<Button-2>", lambda e, t=tab_id: self._close_tab(t))
        
        # Drag to reorder
        for widget in [tab_frame, tab_inner, tab_btn]:
            widget.bind("<ButtonPress-1>", lambda e, t=tab_id: self._start_tab_drag(e, t))
            widget.bind("<B1-Motion>", lambda e, t=tab_id: self._drag_tab(e, t))
            widget.bind("<ButtonRelease-1>", lambda e, t=tab_id: self._end_tab_drag(e, t))
        
        # Context menu
        ctx = tk.Menu(tab_btn, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        ctx.add_command(label="Close", command=lambda t=tab_id: self._close_tab(t))
        ctx.add_command(label="Close Others", command=lambda t=tab_id: self._close_others(t))
        ctx.add_command(label="Close All", command=self._close_all_tabs)
        ctx.add_separator()
        ctx.add_command(label="Copy Path", command=lambda t=tab_id: self._copy_tab_path(t))
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
        text = tk.Text(
            editor_inner, wrap="none" if not self.settings.word_wrap else "word",
            bg=THEME.bg_darkest, fg=THEME.text_primary, insertbackground=THEME.text_primary,
            selectbackground=THEME.selection_bg, selectforeground=THEME.text_primary,
            font=(self.settings.font_family, int(self.settings.font_size * s)),
            borderwidth=0, highlightthickness=0, undo=True, autoseparators=True,
            insertwidth=2, tabs=(f"{self.settings.tab_size}c",)
        )
        text.pack(side="left", fill="both", expand=True)
        self.text_widgets[tab_id] = text
        
        # Scrollbar
        yscroll = ctk.CTkScrollbar(editor_inner, command=text.yview)
        yscroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=lambda *args: self._on_scroll(tab_id, yscroll, *args))
        
        # Minimap
        minimap = Minimap(editor_inner, text, self.settings)
        if self.settings.show_minimap:
            minimap.pack(side="right", fill="y", before=yscroll)
        self.minimaps[tab_id] = minimap
        
        # Line numbers link
        line_canvas.text_widget = text
        line_canvas.text_font = tkfont.Font(family=self.settings.font_family, size=int(self.settings.font_size * s))
        
        # Syntax highlighter
        highlighter = SyntaxHighlighter(text, ext)
        if is_large_file:
            highlighter.set_large_file_mode(True)
        self.highlighters[tab_id] = highlighter
        
        # Insert content
        if content:
            text.insert("1.0", content)
            text.edit_reset()
        
        # Bindings
        text.bind("<KeyRelease>", lambda e, t=tab_id: self._on_key_release(e, t))
        text.bind("<KeyPress>", lambda e, t=tab_id: self._on_key_press(e, t))
        text.bind("<Control-v>", lambda e, t=tab_id: self._handle_paste(e, t))
        text.bind("<Control-c>", lambda e, t=tab_id: self._handle_copy(e, t))
        text.bind("<Control-x>", lambda e, t=tab_id: self._handle_cut(e, t))
        text.bind("<Button-1>", lambda e, t=tab_id: self._on_click(e, t))
        text.bind("<MouseWheel>", lambda e, t=tab_id: self._on_mousewheel(e, t))
        text.bind("<Control-MouseWheel>", lambda e, t=tab_id: self._on_ctrl_scroll(e, t))
        text.bind("<Button-3>", lambda e, t=tab_id: self._show_text_context_menu(e, t))
        text.bind("<<Modified>>", lambda e, t=tab_id: self._on_modified(t))
        
        # Auto-scroll (middle-click)
        text.bind("<Button-2>", lambda e, t=tab_id: self._start_auto_scroll(e, t))
        text.bind("<B2-Motion>", lambda e, t=tab_id: self._auto_scroll_motion(e, t))
        text.bind("<ButtonRelease-2>", lambda e, t=tab_id: self._stop_auto_scroll(t))
        
        # Tags
        text.tag_configure("misspelled", underline=True)
        text.tag_configure("bracket_match", background=THEME.bracket_match)
        text.tag_configure("search_highlight", background=THEME.search_highlight)
        text.tag_configure("current_line", background=THEME.current_line)
        
        self._switch_tab(tab_id)
        return tab_id
    
    def _switch_tab(self, tab_id: str):
        """Switch to a tab."""
        if tab_id not in self.tabs:
            return
        
        for tid, frame in self.editor_frames.items():
            frame.pack_forget()
            if tid in self.tabs and self.tabs[tid].tab_frame:
                tab_frame = self.tabs[tid].tab_frame
                tab_frame.configure(fg_color=tab_frame.inactive_color)
                tab_frame.tab_btn.configure(text_color=tab_frame.text_inactive)
                tab_frame.close_btn.configure(text_color=tab_frame.text_inactive)
        
        self.editor_frames[tab_id].pack(fill="both", expand=True)
        
        if self.tabs[tab_id].tab_frame:
            tab_frame = self.tabs[tab_id].tab_frame
            tab_frame.configure(fg_color=tab_frame.active_color)
            tab_frame.tab_btn.configure(text_color=tab_frame.text_active)
            tab_frame.close_btn.configure(text_color=THEME.text_muted)
        
        self.current_tab = tab_id
        self.text_widgets[tab_id].focus_set()
        self._update_statusbar()
        self._update_title()
        self._scroll_tab_into_view(tab_id)
        self.after(100, self._highlight_current)
    
    def _close_tab(self, tab_id: str):
        """Close a tab."""
        if tab_id not in self.tabs:
            return
        
        tab_data = self.tabs[tab_id]
        
        # Check for unsaved changes
        if tab_data.modified and not self.settings.hot_exit_enabled:
            result = messagebox.askyesnocancel(
                "Save Changes",
                f"Do you want to save changes to {tab_data.display_name}?"
            )
            if result is None:  # Cancel
                return
            if result:  # Yes
                self._save_file()
        
        # Save to closed tabs for reopening
        if tab_id in self.text_widgets:
            content = self.text_widgets[tab_id].get("1.0", "end-1c")
            cursor = self.text_widgets[tab_id].index(tk.INSERT)
            self.closed_tabs_manager.add(tab_data.filepath, content, cursor)
        
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
        if tab_id in self.tab_order:
            self.tab_order.remove(tab_id)
        
        # Switch to another tab
        if self.tabs:
            next_tab = list(self.tabs.keys())[-1]
            self._switch_tab(next_tab)
        else:
            self.current_tab = None
            self._show_welcome()
    
    def _close_current_tab(self):
        """Close the current tab."""
        if self.current_tab:
            self._close_tab(self.current_tab)
    
    def _close_others(self, tab_id: str):
        """Close all tabs except the specified one."""
        for tid in list(self.tabs.keys()):
            if tid != tab_id:
                self._close_tab(tid)
    
    def _close_all_tabs(self):
        """Close all tabs."""
        for tid in list(self.tabs.keys()):
            self._close_tab(tid)
    
    def _reopen_closed_tab(self):
        """Reopen the most recently closed tab."""
        tab_info = self.closed_tabs_manager.pop()
        if tab_info:
            tab_id = self._create_tab(tab_info["filepath"], tab_info["content"])
            if tab_id and "cursor_pos" in tab_info:
                try:
                    self.text_widgets[tab_id].mark_set(tk.INSERT, tab_info["cursor_pos"])
                except Exception:
                    pass
    
    # Tab bar helpers
    def _tab_bar_click(self, event):
        """Handle click on tab bar."""
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if widget in (self.tab_bar, self.tab_container, self.tab_clip_frame, self.tab_inner_frame):
            self._new_file()
    
    def _on_tab_scroll(self, event):
        """Handle mousewheel on tab bar."""
        if not self.tabs:
            return "break"
        
        tab_ids = list(self.tabs.keys())
        if not tab_ids:
            return "break"
        
        current_idx = tab_ids.index(self.current_tab) if self.current_tab in tab_ids else 0
        
        if event.delta > 0:
            new_idx = max(0, current_idx - 1)
        else:
            new_idx = min(len(tab_ids) - 1, current_idx + 1)
        
        if new_idx != current_idx:
            self._switch_tab(tab_ids[new_idx])
        
        return "break"
    
    def _scroll_tab_into_view(self, tab_id: str):
        """Scroll tab bar to show tab."""
        if tab_id not in self.tabs or not self.tabs[tab_id].tab_frame:
            return
        
        try:
            tab_frame = self.tabs[tab_id].tab_frame
            clip_width = self.tab_clip_frame.winfo_width()
            tab_x = tab_frame.winfo_x()
            tab_width = tab_frame.winfo_width()
            current_x = self.tab_inner_frame.winfo_x()
            
            if tab_x + tab_width > clip_width - current_x:
                new_x = clip_width - tab_x - tab_width - 20
                self.tab_inner_frame.place(x=new_x)
            elif tab_x + current_x < 0:
                new_x = -tab_x + 10
                self.tab_inner_frame.place(x=min(0, new_x))
        except Exception:
            pass
    
    def _show_tab_list(self):
        """Show dropdown list of tabs."""
        if not self.tabs:
            return
        
        menu = tk.Menu(self.tab_list_btn, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        
        for tab_id, tab_data in self.tabs.items():
            name = tab_data.display_name
            icon = get_file_icon(tab_data.filepath) if tab_data.filepath else "📄"
            
            if tab_data.modified:
                name = f"● {name}"
            
            prefix = "→ " if tab_id == self.current_tab else "   "
            menu.add_command(label=f"{prefix}{icon} {name}", command=lambda t=tab_id: self._switch_tab(t))
        
        x = self.tab_list_btn.winfo_rootx()
        y = self.tab_list_btn.winfo_rooty() + self.tab_list_btn.winfo_height()
        menu.tk_popup(x, y)
    
    def _show_recent_files(self):
        """Show recent files menu."""
        menu = tk.Menu(self.recent_btn, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        
        for filepath in self.settings.recent_files[:15]:
            if os.path.exists(filepath):
                icon = get_file_icon(filepath)
                name = os.path.basename(filepath)
                menu.add_command(label=f"{icon} {name}", command=lambda fp=filepath: self._open_file(fp))
        
        if self.settings.recent_files:
            menu.add_separator()
            menu.add_command(label="Clear Recent Files", command=self._clear_recent_files)
        
        x = self.recent_btn.winfo_rootx()
        y = self.recent_btn.winfo_rooty() + self.recent_btn.winfo_height()
        menu.tk_popup(x, y)
    
    def _clear_recent_files(self):
        """Clear recent files list."""
        self.settings.recent_files = []
        self._save_settings()
    
    # Tab drag state
    _drag_start_x = 0
    _drag_tab_id = None
    _drag_started = False
    
    def _start_tab_drag(self, event, tab_id: str):
        """Start tab drag."""
        self._drag_start_x = event.x_root
        self._drag_tab_id = tab_id
        self._drag_started = False
    
    def _drag_tab(self, event, tab_id: str):
        """Handle tab drag."""
        if not self._drag_tab_id or self._drag_tab_id != tab_id:
            return
        
        delta = abs(event.x_root - self._drag_start_x)
        if delta > 10:
            self._drag_started = True
            for tid, td in self.tabs.items():
                if tid != tab_id and td.tab_frame:
                    fx = td.tab_frame.winfo_rootx()
                    fw = td.tab_frame.winfo_width()
                    if fx < event.x_root < fx + fw:
                        self._swap_tabs(tab_id, tid)
                        self._drag_start_x = event.x_root
                        break
    
    def _end_tab_drag(self, event, tab_id: str):
        """End tab drag."""
        if not self._drag_started and self._drag_tab_id == tab_id:
            self._switch_tab(tab_id)
        self._drag_tab_id = None
        self._drag_started = False
    
    def _swap_tabs(self, tab_id1: str, tab_id2: str):
        """Swap two tabs."""
        if tab_id1 not in self.tabs or tab_id2 not in self.tabs:
            return
        
        tabs_list = list(self.tabs.keys())
        idx1, idx2 = tabs_list.index(tab_id1), tabs_list.index(tab_id2)
        
        items = list(self.tabs.items())
        items[idx1], items[idx2] = items[idx2], items[idx1]
        self.tabs = dict(items)
        
        for child in self.tab_inner_frame.winfo_children():
            child.pack_forget()
        
        s = self.settings.ui_scale
        for tid in self.tabs:
            if self.tabs[tid].tab_frame:
                self.tabs[tid].tab_frame.pack(side="left", padx=1, pady=(int(3*s), 0))
    
    def _next_tab(self):
        """Switch to next tab."""
        if not self.tabs:
            return
        tab_ids = list(self.tabs.keys())
        idx = tab_ids.index(self.current_tab) if self.current_tab in tab_ids else 0
        self._switch_tab(tab_ids[(idx + 1) % len(tab_ids)])
    
    def _prev_tab(self):
        """Switch to previous tab."""
        if not self.tabs:
            return
        tab_ids = list(self.tabs.keys())
        idx = tab_ids.index(self.current_tab) if self.current_tab in tab_ids else 0
        self._switch_tab(tab_ids[(idx - 1) % len(tab_ids)])
    
    def _copy_tab_path(self, tab_id: str):
        """Copy tab file path to clipboard."""
        if tab_id in self.tabs and self.tabs[tab_id].filepath:
            self.clipboard_clear()
            self.clipboard_append(self.tabs[tab_id].filepath)
            self.toast.show("Path copied to clipboard", "success")
    
    # =========================================================================
    # FILE OPERATIONS
    # =========================================================================
    
    def _new_file(self):
        """Create new empty file."""
        self._create_tab()
    
    def _open_file(self, filepath: str = None):
        """Open a file."""
        if filepath is None:
            filepath = filedialog.askopenfilename(
                filetypes=[
                    ("All Files", "*.*"), ("Text Files", "*.txt"),
                    ("Python Files", "*.py"), ("JavaScript Files", "*.js"),
                    ("HTML Files", "*.html"), ("CSS Files", "*.css"),
                    ("JSON Files", "*.json"), ("Markdown Files", "*.md")
                ]
            )
        
        if not filepath or not os.path.isfile(filepath):
            return
        
        # Check if already open
        for tab_id, tab_data in self.tabs.items():
            if tab_data.filepath == filepath:
                self._switch_tab(tab_id)
                return
        
        try:
            content, encoding = read_file_safe(filepath)
            tab_id = self._create_tab(filepath, content)
            if tab_id:
                self.tabs[tab_id].encoding = encoding
                self.file_mtimes[filepath] = os.path.getmtime(filepath)
                self.settings.add_recent_file(filepath)
                self._save_settings()
        except Exception as e:
            self.toast.show(f"Error opening file: {e}", "error")
    
    def _save_file(self):
        """Save current file."""
        if not self.current_tab:
            return
        
        tab_data = self.tabs[self.current_tab]
        
        if not tab_data.filepath:
            self._save_file_as()
            return
        
        try:
            content = self.text_widgets[self.current_tab].get("1.0", "end-1c")
            
            # Create backup
            self.backup_manager.create_backup(tab_data.filepath, content)
            
            # Write file
            write_file_safe(tab_data.filepath, content, tab_data.encoding, tab_data.line_ending)
            
            # Update state
            tab_data.modified = False
            tab_data.content_hash = hashlib.md5(content.encode()).hexdigest()
            self.file_mtimes[tab_data.filepath] = os.path.getmtime(tab_data.filepath)
            
            self._update_tab_button(self.current_tab)
            self._update_title()
            self.toast.show("File saved", "success")
            
        except Exception as e:
            self.toast.show(f"Error saving file: {e}", "error")
    
    def _save_file_as(self):
        """Save current file with new name."""
        if not self.current_tab:
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("All Files", "*.*"), ("Text Files", "*.txt"),
                ("Python Files", "*.py"), ("JavaScript Files", "*.js")
            ]
        )
        
        if not filepath:
            return
        
        self.tabs[self.current_tab].filepath = filepath
        self._update_tab_button(self.current_tab)
        self._save_file()
        self.settings.add_recent_file(filepath)
        self._save_settings()
    
    def _save_all(self):
        """Save all modified files."""
        for tab_id in self.tabs:
            if self.tabs[tab_id].modified:
                prev_tab = self.current_tab
                self._switch_tab(tab_id)
                self._save_file()
                self._switch_tab(prev_tab)
        self.toast.show("All files saved", "success")
    
    def _update_tab_button(self, tab_id: str):
        """Update tab button appearance."""
        if tab_id not in self.tabs:
            return
        
        tab_data = self.tabs[tab_id]
        if not tab_data.tab_frame:
            return
        
        icon = get_file_icon(tab_data.filepath) if tab_data.filepath else "📄"
        name = tab_data.display_name
        tab_data.tab_frame.tab_btn.configure(text=f"{icon} {name}")
        tab_data.tab_frame.modified_label.configure(text="●" if tab_data.modified else "")
    
    def _update_title(self):
        """Update window title."""
        if self.current_tab and self.current_tab in self.tabs:
            tab_data = self.tabs[self.current_tab]
            modified = "● " if tab_data.modified else ""
            name = tab_data.display_name
            self.title(f"{modified}{name} - Mattpad")
        else:
            self.title("Mattpad")
    
    def _update_statusbar(self):
        """Update status bar."""
        if not hasattr(self, 'statusbar'):
            return
        
        if self.current_tab and self.current_tab in self.tabs:
            tab_data = self.tabs[self.current_tab]
            text = self.text_widgets[self.current_tab]
            
            # Path
            path = tab_data.filepath or "Untitled"
            self.path_label.configure(text=path)
            
            # Position
            try:
                pos = text.index(tk.INSERT)
                line, col = pos.split(".")
                self.pos_label.configure(text=f"Ln {line}, Col {int(col)+1}")
            except Exception:
                pass
            
            # Other info
            self.encoding_label.configure(text=tab_data.encoding.upper())
            self.line_ending_label.configure(text=tab_data.line_ending)
            self.lang_label.configure(text=tab_data.language)
    
    def _copy_current_path(self, event=None):
        """Copy current file path."""
        if self.current_tab and self.tabs[self.current_tab].filepath:
            self.clipboard_clear()
            self.clipboard_append(self.tabs[self.current_tab].filepath)
            self.toast.show("Path copied", "success")
    
    # =========================================================================
    # EDITOR OPERATIONS
    # =========================================================================
    
    def _undo(self):
        """Undo last edit."""
        if self.current_tab and self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_undo()
            except tk.TclError:
                pass
    
    def _redo(self):
        """Redo last undo."""
        if self.current_tab and self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_redo()
            except tk.TclError:
                pass
    
    def _cut(self):
        """Cut selection."""
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                text.event_generate("<<Cut>>")
            except Exception:
                pass
    
    def _copy(self):
        """Copy selection."""
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                text.event_generate("<<Copy>>")
            except Exception:
                pass
    
    def _paste(self):
        """Paste from clipboard."""
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                text.event_generate("<<Paste>>")
            except Exception:
                pass
    
    def _paste_from_clipboard(self, text_content: str):
        """Paste text from clipboard panel."""
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                text.insert(tk.INSERT, text_content)
            except Exception:
                pass
    
    def _handle_paste(self, event, tab_id: str):
        """Handle paste with preprocessing."""
        return None  # Let default paste handle it
    
    def _handle_copy(self, event, tab_id: str):
        """Handle copy."""
        return None
    
    def _handle_cut(self, event, tab_id: str):
        """Handle cut."""
        return None
    
    def _duplicate_line(self):
        """Duplicate current line."""
        if not self.current_tab:
            return
        
        text = self.text_widgets[self.current_tab]
        try:
            line = text.index(tk.INSERT).split(".")[0]
            line_content = text.get(f"{line}.0", f"{line}.end")
            text.insert(f"{line}.end", f"\n{line_content}")
        except Exception:
            pass
    
    def _toggle_comment(self):
        """Toggle comment on current line."""
        if not self.current_tab:
            return
        
        text = self.text_widgets[self.current_tab]
        tab_data = self.tabs[self.current_tab]
        
        # Get comment string based on language
        comment_map = {
            "Python": "#", "JavaScript": "//", "TypeScript": "//",
            "C": "//", "C++": "//", "Java": "//", "Go": "//",
            "Rust": "//", "CSS": "/*", "HTML": "<!--", "SQL": "--",
            "Shell": "#", "PowerShell": "#", "Ruby": "#", "PHP": "//",
        }
        comment = comment_map.get(tab_data.language, "#")
        
        try:
            line = text.index(tk.INSERT).split(".")[0]
            line_content = text.get(f"{line}.0", f"{line}.end")
            
            stripped = line_content.lstrip()
            if stripped.startswith(comment):
                # Remove comment
                idx = line_content.index(comment)
                new_content = line_content[:idx] + line_content[idx+len(comment):].lstrip()
                text.delete(f"{line}.0", f"{line}.end")
                text.insert(f"{line}.0", new_content)
            else:
                # Add comment
                indent = len(line_content) - len(stripped)
                new_content = line_content[:indent] + comment + " " + stripped
                text.delete(f"{line}.0", f"{line}.end")
                text.insert(f"{line}.0", new_content)
        except Exception:
            pass
    
    # =========================================================================
    # FIND/REPLACE
    # =========================================================================
    
    def _show_find_bar(self):
        """Show find bar."""
        if not self.find_bar_visible:
            self.find_bar.pack(fill="x", before=self.editor_frame)
            self.find_bar_visible = True
        self.find_bar.focus_find()
        
        # Pre-fill with selection
        if self.current_tab and self.current_tab in self.text_widgets:
            text = self.text_widgets[self.current_tab]
            try:
                sel = text.get(tk.SEL_FIRST, tk.SEL_LAST)
                if sel:
                    self.find_bar.set_find_text(sel)
            except tk.TclError:
                pass
    
    def _hide_find_bar(self):
        """Hide find bar."""
        if self.find_bar_visible:
            self.find_bar.pack_forget()
            self.find_bar_visible = False
    
    def _do_find(self, query: str, case_sensitive: bool, regex: bool, whole_word: bool, find_all: bool = False):
        """Execute find."""
        if not self.current_tab:
            return
        
        text = self.text_widgets[self.current_tab]
        text.tag_remove("search_highlight", "1.0", "end")
        
        if not query:
            return
        
        # Build search pattern
        if regex:
            pattern = query
        else:
            pattern = re.escape(query)
        
        if whole_word:
            pattern = r"\b" + pattern + r"\b"
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            content = text.get("1.0", "end-1c")
            matches = list(re.finditer(pattern, content, flags))
            
            for match in matches:
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                text.tag_add("search_highlight", start_idx, end_idx)
            
            if matches:
                # Scroll to first match
                first = matches[0]
                text.see(f"1.0+{first.start()}c")
                self.find_bar.set_match_count(1, len(matches))
            else:
                self.find_bar.set_match_count(0, 0)
                
        except re.error as e:
            self.toast.show(f"Invalid regex: {e}", "error")
    
    def _do_replace(self, find_text: str, replace_text: str, case_sensitive: bool, regex: bool):
        """Replace current match."""
        if not self.current_tab:
            return
        
        text = self.text_widgets[self.current_tab]
        
        try:
            # Check if selection matches
            sel_start = text.index(tk.SEL_FIRST)
            sel_end = text.index(tk.SEL_LAST)
            selected = text.get(sel_start, sel_end)
            
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                if re.match(find_text, selected, flags):
                    replacement = re.sub(find_text, replace_text, selected, flags=flags)
                    text.delete(sel_start, sel_end)
                    text.insert(sel_start, replacement)
            else:
                if case_sensitive and selected == find_text:
                    text.delete(sel_start, sel_end)
                    text.insert(sel_start, replace_text)
                elif not case_sensitive and selected.lower() == find_text.lower():
                    text.delete(sel_start, sel_end)
                    text.insert(sel_start, replace_text)
            
            # Find next
            self._do_find(find_text, case_sensitive, regex, False)
            
        except tk.TclError:
            # No selection, just find
            self._do_find(find_text, case_sensitive, regex, False)
    
    def _do_replace_all(self, find_text: str, replace_text: str, case_sensitive: bool, regex: bool):
        """Replace all matches."""
        if not self.current_tab:
            return
        
        text = self.text_widgets[self.current_tab]
        content = text.get("1.0", "end-1c")
        
        try:
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                new_content, count = re.subn(find_text, replace_text, content, flags=flags)
            else:
                if case_sensitive:
                    new_content = content.replace(find_text, replace_text)
                    count = content.count(find_text)
                else:
                    pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                    new_content, count = pattern.subn(replace_text, content)
            
            if count > 0:
                text.delete("1.0", "end")
                text.insert("1.0", new_content)
                self.toast.show(f"Replaced {count} occurrences", "success")
            else:
                self.toast.show("No matches found", "info")
                
        except re.error as e:
            self.toast.show(f"Invalid regex: {e}", "error")
    
    def _find_in_files(self):
        """Find in files dialog."""
        self.toast.show("Find in files - coming soon", "info")
    
    def _goto_line(self):
        """Go to line dialog."""
        if not self.current_tab:
            return
        
        text = self.text_widgets[self.current_tab]
        total = int(text.index("end-1c").split(".")[0])
        
        from tkinter import simpledialog
        line = simpledialog.askinteger("Go to Line", f"Line number (1-{total}):", minvalue=1, maxvalue=total)
        
        if line:
            text.see(f"{line}.0")
            text.mark_set(tk.INSERT, f"{line}.0")
            text.focus_set()
    
    # =========================================================================
    # UI TOGGLES
    # =========================================================================
    
    def _toggle_sidebar(self):
        """Toggle sidebar visibility."""
        s = self.settings.ui_scale
        
        if self.settings.sidebar_visible:
            self.main_paned.forget(self.sidebar_frame)
            self.settings.sidebar_visible = False
        else:
            self.main_paned.add(self.sidebar_frame, width=int(self.settings.sidebar_width*s), minsize=int(150*s), before=self.editor_container)
            self.settings.sidebar_visible = True
        
        self._save_settings()
    
    def _toggle_clipboard_panel(self):
        """Toggle clipboard panel."""
        s = self.settings.ui_scale
        
        if self.settings.clipboard_panel_visible:
            self.main_paned.forget(self.clipboard_frame)
            self.settings.clipboard_panel_visible = False
        else:
            self.main_paned.add(self.clipboard_frame, width=int(self.settings.clipboard_panel_width*s), minsize=int(150*s))
            self.settings.clipboard_panel_visible = True
            self.clipboard_panel.refresh()
        
        self._save_settings()
    
    def _toggle_terminal(self):
        """Toggle terminal panel."""
        if not self.settings.terminal_enabled:
            self.toast.show("Terminal disabled", "info")
            return
        
        self.terminal_visible = not self.terminal_visible
        if self.terminal_visible:
            self._create_terminal()
            self.terminal_frame.pack(side="bottom", fill="x", before=self.editor_frame)
        else:
            self.terminal_frame.pack_forget()
    
    def _create_terminal(self):
        """Create terminal widget."""
        s = self.settings.ui_scale
        
        for child in self.terminal_frame.winfo_children():
            child.destroy()
        
        header = ctk.CTkFrame(self.terminal_frame, fg_color=THEME.ribbon_group_bg, height=int(30*s))
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="  TERMINAL", font=ctk.CTkFont(size=int(11*s), weight="bold"),
                    text_color=THEME.text_secondary).pack(side="left")
        
        ctk.CTkButton(header, text="✕", width=int(28*s), height=int(24*s),
                     fg_color="transparent", hover_color=THEME.bg_hover,
                     command=self._toggle_terminal).pack(side="right", padx=int(4*s))
        
        self.terminal_text = tk.Text(
            self.terminal_frame, bg=THEME.bg_darkest, fg=THEME.text_primary,
            font=("Consolas", self.settings.terminal_font_size),
            height=8, borderwidth=0, highlightthickness=0
        )
        self.terminal_text.pack(fill="both", expand=True, padx=int(4*s), pady=int(4*s))
        self.terminal_text.insert("end", "Terminal - Press Enter to execute\n$ ")
        self.terminal_text.bind("<Return>", self._execute_terminal_command)
    
    def _execute_terminal_command(self, event):
        """Execute terminal command."""
        import subprocess
        
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
                except Exception as e:
                    output = str(e)
                
                self.after(0, lambda: self._terminal_output(output))
            
            threading.Thread(target=run, daemon=True).start()
        
        return "break"
    
    def _terminal_output(self, output: str):
        """Add output to terminal."""
        self.terminal_text.insert("end", output)
        if not output.endswith("\n"):
            self.terminal_text.insert("end", "\n")
        self.terminal_text.insert("end", "$ ")
        self.terminal_text.see("end")
    
    def _toggle_word_wrap(self):
        """Toggle word wrap."""
        self.settings.word_wrap = self.wrap_var.get()
        wrap = "word" if self.settings.word_wrap else "none"
        for text in self.text_widgets.values():
            text.configure(wrap=wrap)
        self._save_settings()
    
    def _toggle_line_numbers(self):
        """Toggle line numbers."""
        self.settings.show_line_numbers = self.linenum_var.get()
        for tab_id, line_canvas in self.line_numbers.items():
            if self.settings.show_line_numbers:
                line_canvas.pack(side="left", fill="y", before=self.text_widgets[tab_id])
            else:
                line_canvas.pack_forget()
        self._save_settings()
    
    def _toggle_minimap(self):
        """Toggle minimap."""
        self.settings.show_minimap = self.minimap_var.get()
        for tab_id, minimap in self.minimaps.items():
            if self.settings.show_minimap:
                minimap.pack(side="right", fill="y")
            else:
                minimap.pack_forget()
        self._save_settings()
    
    def _toggle_spellcheck(self):
        """Toggle spellcheck."""
        self.settings.spellcheck_enabled = self.spell_var.get()
        self._save_settings()
    
    def _toggle_autoclose(self):
        """Toggle auto-close brackets."""
        self.settings.auto_close_brackets = self.autoclose_var.get()
        self._save_settings()
    
    def _toggle_autosave(self):
        """Toggle auto-save."""
        self.settings.auto_save_enabled = self.autosave_var.get()
        self._save_settings()
    
    def _toggle_line_ending(self, event=None):
        """Toggle line ending for current file."""
        if not self.current_tab:
            return
        
        endings = ["CRLF", "LF", "CR"]
        current = self.tabs[self.current_tab].line_ending
        idx = endings.index(current) if current in endings else 0
        new_ending = endings[(idx + 1) % len(endings)]
        
        self.tabs[self.current_tab].line_ending = new_ending
        self.tabs[self.current_tab].modified = True
        self._update_statusbar()
        self._update_tab_button(self.current_tab)
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.state() == 'zoomed':
            self.state('normal')
        else:
            self.state('zoomed')
    
    # =========================================================================
    # ZOOM
    # =========================================================================
    
    def _zoom_in(self):
        """Zoom in."""
        self.settings.font_size = min(72, self.settings.font_size + 2)
        self._apply_font_size()
    
    def _zoom_out(self):
        """Zoom out."""
        self.settings.font_size = max(6, self.settings.font_size - 2)
        self._apply_font_size()
    
    def _zoom_reset(self):
        """Reset zoom."""
        self.settings.font_size = 12
        self._apply_font_size()
    
    def _apply_font_size(self):
        """Apply font size to all editors."""
        s = self.settings.ui_scale
        for text in self.text_widgets.values():
            text.configure(font=(self.settings.font_family, int(self.settings.font_size * s)))
        
        if hasattr(self, 'zoom_label'):
            zoom_pct = int((self.settings.font_size / 12) * 100)
            self.zoom_label.configure(text=f"{zoom_pct}%")
        
        self._save_settings()
    
    def _set_scale(self, scale: float):
        """Set UI scale."""
        self.settings.ui_scale = scale
        self._save_settings()
        self.toast.show(f"UI scale set to {int(scale*100)}%. Restart to apply.", "info")
    
    # =========================================================================
    # SETTINGS DIALOGS
    # =========================================================================
    
    def _show_settings(self):
        """Show settings dialog."""
        SettingsDialog(self, self.settings, self._on_settings_saved)
    
    def _on_settings_saved(self):
        """Handle settings saved."""
        self._save_settings()
        self._apply_font_size()
        self.toast.show("Settings saved", "success")
    
    def _show_themes(self):
        """Show theme selection dialog."""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "Themes", 400, 500, self.settings)
        
        ctk.CTkLabel(dialog, text="Select Theme", font=ctk.CTkFont(size=int(14*s), weight="bold")).pack(pady=int(10*s))
        
        scroll = ctk.CTkScrollableFrame(dialog, fg_color=THEME.bg_medium)
        scroll.pack(fill="both", expand=True, padx=int(10*s), pady=int(10*s))
        
        for name in THEMES:
            btn = ctk.CTkButton(
                scroll, text=name,
                fg_color=THEME.accent_primary if name == self.settings.theme_name else THEME.bg_dark,
                hover_color=THEME.bg_hover,
                command=lambda n=name: self._set_theme(n, dialog)
            )
            btn.pack(fill="x", pady=int(2*s))
    
    def _set_theme(self, name: str, dialog):
        """Set theme."""
        self.settings.theme_name = name
        self._save_settings()
        dialog.destroy()
        self.toast.show(f"Theme set to {name}. Restart to apply.", "info")
    
    def _show_ai_settings(self):
        """Show AI settings dialog."""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "AI Settings", 450, 350, self.settings)
        
        # Provider
        row = ctk.CTkFrame(dialog, fg_color="transparent")
        row.pack(fill="x", padx=int(20*s), pady=int(10*s))
        ctk.CTkLabel(row, text="Provider:", width=int(100*s)).pack(side="left")
        
        provider_combo = ctk.CTkComboBox(row, values=["openai", "anthropic", "ollama"], width=int(200*s))
        provider_combo.set(self.settings.ai_provider)
        provider_combo.pack(side="left")
        
        # Model
        row = ctk.CTkFrame(dialog, fg_color="transparent")
        row.pack(fill="x", padx=int(20*s), pady=int(10*s))
        ctk.CTkLabel(row, text="Model:", width=int(100*s)).pack(side="left")
        
        model_entry = ctk.CTkEntry(row, width=int(200*s))
        model_entry.insert(0, self.settings.ai_model)
        model_entry.pack(side="left")
        
        # API Key
        row = ctk.CTkFrame(dialog, fg_color="transparent")
        row.pack(fill="x", padx=int(20*s), pady=int(10*s))
        ctk.CTkLabel(row, text="API Key:", width=int(100*s)).pack(side="left")
        
        key_entry = ctk.CTkEntry(row, width=int(200*s), show="*")
        key_entry.insert(0, self.settings.ai_api_key)
        key_entry.pack(side="left")
        
        def save():
            self.settings.ai_provider = provider_combo.get()
            self.settings.ai_model = model_entry.get()
            self.settings.ai_api_key = key_entry.get()
            SecretStorage.store("ai_api_key", self.settings.ai_api_key)
            self._save_settings()
            self.toast.show("AI settings saved", "success")
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Save", fg_color=THEME.accent_primary, command=save).pack(pady=int(20*s))
    
    def _ai_action(self, action: str):
        """Execute AI action."""
        if not self.current_tab:
            return
        
        text = self.text_widgets[self.current_tab]
        try:
            content = text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            content = text.get("1.0", "end-1c")
        
        if not content.strip():
            self.toast.show("No text to process", "warning")
            return
        
        self.toast.show(f"Processing with AI...", "info")
        
        def callback(result: str, error: str):
            if error:
                self.toast.show(f"AI error: {error}", "error")
            elif result:
                try:
                    text.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    text.delete("1.0", "end")
                text.insert(tk.INSERT, result)
                self.toast.show("AI processing complete", "success")
        
        self.ai_manager.process(content, action, callback)
    
    def _ai_custom_prompt(self):
        """Custom AI prompt dialog."""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "Custom AI Prompt", 500, 300, self.settings)
        
        ctk.CTkLabel(dialog, text="Enter your prompt:").pack(pady=int(10*s))
        
        prompt_text = ctk.CTkTextbox(dialog, width=int(450*s), height=int(150*s))
        prompt_text.pack(padx=int(20*s))
        
        def execute():
            prompt = prompt_text.get("1.0", "end-1c").strip()
            if prompt:
                dialog.destroy()
                
                if self.current_tab:
                    text = self.text_widgets[self.current_tab]
                    try:
                        content = text.get(tk.SEL_FIRST, tk.SEL_LAST)
                    except tk.TclError:
                        content = ""
                    
                    self.toast.show("Processing...", "info")
                    
                    def callback(result: str, error: str):
                        if error:
                            self.toast.show(f"Error: {error}", "error")
                        elif result:
                            text.insert(tk.INSERT, result)
                            self.toast.show("Done", "success")
                    
                    self.ai_manager.process_custom(content, prompt, callback)
        
        ctk.CTkButton(dialog, text="Execute", fg_color=THEME.accent_primary, command=execute).pack(pady=int(10*s))
    
    # =========================================================================
    # CLOUD SYNC
    # =========================================================================
    
    def _do_cloud_sync(self):
        """Sync to cloud."""
        if not self.current_tab or not self.tabs[self.current_tab].filepath:
            self.toast.show("Save file first", "warning")
            return
        
        if not self.settings.github_token or not self.settings.github_repo:
            self.toast.show("Configure GitHub first", "warning")
            return
        
        filepath = self.tabs[self.current_tab].filepath
        content = self.text_widgets[self.current_tab].get("1.0", "end-1c")
        
        self.toast.show("Syncing...", "info")
        
        def sync():
            success = self.cloud_sync.sync_to_github(filepath, content)
            msg = "Sync complete!" if success else "Sync failed"
            toast_type = "success" if success else "error"
            self.after(0, lambda: self.toast.show(msg, toast_type))
        
        threading.Thread(target=sync, daemon=True).start()
    
    def _configure_github(self):
        """Configure GitHub."""
        s = self.settings.ui_scale
        dialog = create_dialog(self, "GitHub Configuration", 450, 350, self.settings)
        
        fields = [
            ("Token:", "github_token", True),
            ("Repository:", "github_repo", False),
            ("Branch:", "github_branch", False),
            ("Path:", "github_path", False),
        ]
        
        entries = {}
        for label, attr, is_secret in fields:
            row = ctk.CTkFrame(dialog, fg_color="transparent")
            row.pack(fill="x", padx=int(20*s), pady=int(5*s))
            
            ctk.CTkLabel(row, text=label, width=int(100*s)).pack(side="left")
            entry = ctk.CTkEntry(row, width=int(250*s), show="*" if is_secret else "")
            entry.insert(0, getattr(self.settings, attr, ""))
            entry.pack(side="left")
            entries[attr] = entry
        
        def save():
            for attr, entry in entries.items():
                setattr(self.settings, attr, entry.get())
            SecretStorage.store("github_token", self.settings.github_token)
            self._save_settings()
            self.toast.show("GitHub settings saved", "success")
            dialog.destroy()
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=int(20*s), pady=int(20*s))
        
        ctk.CTkButton(btn_frame, text="Save", fg_color=THEME.accent_primary, command=save).pack(side="right", padx=int(5*s))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color=THEME.bg_medium, command=dialog.destroy).pack(side="right")
    
    def _compare_files(self):
        """Compare two files."""
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
            self.toast.show(f"Error: {e}", "error")
            return
        
        diff = DiffEngine.compare(content1, content2)
        
        s = self.settings.ui_scale
        dialog = create_dialog(self, "File Comparison", 800, 600, self.settings)
        
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=int(10*s), pady=int(10*s))
        
        ctk.CTkLabel(header, text=f"← {os.path.basename(file1)}", text_color=THEME.accent_red).pack(side="left")
        ctk.CTkLabel(header, text=f"→ {os.path.basename(file2)}", text_color=THEME.accent_green).pack(side="right")
        
        text = tk.Text(dialog, bg=THEME.bg_darkest, fg=THEME.text_primary,
                      font=("Consolas", int(11*s)), wrap="none", borderwidth=0)
        scroll = ctk.CTkScrollbar(dialog, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True, padx=int(10*s), pady=int(10*s))
        
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
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    def _on_key_release(self, event, tab_id: str):
        """Handle key release."""
        self.debouncer.debounce(f"update_{tab_id}", lambda: self._on_content_change(tab_id))
    
    def _on_key_press(self, event, tab_id: str):
        """Handle key press."""
        # Auto-close brackets
        if self.settings.auto_close_brackets and tab_id in self.text_widgets:
            text = self.text_widgets[tab_id]
            pairs = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
            if event.char in pairs:
                text.insert(tk.INSERT, pairs[event.char])
                text.mark_set(tk.INSERT, f"{tk.INSERT}-1c")
    
    def _on_content_change(self, tab_id: str):
        """Handle content change."""
        if tab_id not in self.tabs:
            return
        
        # Update line numbers
        if tab_id in self.line_numbers:
            self.line_numbers[tab_id].redraw()
        
        # Update minimap
        if tab_id in self.minimaps:
            self.minimaps[tab_id].redraw()
        
        # Highlight syntax
        self.highlight_debouncer.debounce(f"highlight_{tab_id}", lambda: self._highlight_tab(tab_id))
    
    def _on_modified(self, tab_id: str):
        """Handle text modified event."""
        if tab_id not in self.tabs or tab_id not in self.text_widgets:
            return
        
        text = self.text_widgets[tab_id]
        if text.edit_modified():
            self.tabs[tab_id].modified = True
            self._update_tab_button(tab_id)
            self._update_title()
            text.edit_modified(False)
    
    def _on_click(self, event, tab_id: str):
        """Handle text click."""
        self._update_statusbar()
    
    def _on_scroll(self, tab_id: str, scrollbar, *args):
        """Handle scroll."""
        scrollbar.set(*args)
        if tab_id in self.line_numbers:
            self.line_numbers[tab_id].redraw()
        if tab_id in self.minimaps:
            self.minimaps[tab_id].redraw()
    
    def _on_mousewheel(self, event, tab_id: str):
        """Handle mousewheel."""
        pass  # Let default handling work
    
    def _on_ctrl_scroll(self, event, tab_id: str):
        """Handle ctrl+scroll for zoom."""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
        return "break"
    
    def _show_text_context_menu(self, event, tab_id: str):
        """Show text context menu."""
        menu = tk.Menu(self, tearoff=0, bg=THEME.bg_medium, fg=THEME.text_primary)
        menu.add_command(label="Cut", command=self._cut)
        menu.add_command(label="Copy", command=self._copy)
        menu.add_command(label="Paste", command=self._paste)
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: self.text_widgets[tab_id].tag_add(tk.SEL, "1.0", "end"))
        menu.tk_popup(event.x_root, event.y_root)
    
    # Auto-scroll state
    _auto_scroll_active = False
    _auto_scroll_origin = None
    
    def _start_auto_scroll(self, event, tab_id: str):
        """Start auto-scroll."""
        self._auto_scroll_active = True
        self._auto_scroll_origin = (event.x, event.y)
    
    def _auto_scroll_motion(self, event, tab_id: str):
        """Handle auto-scroll motion."""
        if not self._auto_scroll_active or not self._auto_scroll_origin:
            return
        
        if tab_id not in self.text_widgets:
            return
        
        text = self.text_widgets[tab_id]
        dy = event.y - self._auto_scroll_origin[1]
        
        if abs(dy) > 10:
            text.yview_scroll(1 if dy > 0 else -1, "units")
    
    def _stop_auto_scroll(self, tab_id: str):
        """Stop auto-scroll."""
        self._auto_scroll_active = False
        self._auto_scroll_origin = None
    
    def _highlight_current(self):
        """Highlight current tab."""
        if self.current_tab:
            self._highlight_tab(self.current_tab)
    
    def _highlight_tab(self, tab_id: str):
        """Highlight a tab's content."""
        if tab_id in self.highlighters:
            self.highlighters[tab_id].highlight()
    
    def _on_escape(self):
        """Handle escape key."""
        if self.find_bar_visible:
            self._hide_find_bar()
    
    # =========================================================================
    # WELCOME & SESSION
    # =========================================================================
    
    def _show_welcome(self):
        """Show welcome screen."""
        self.welcome_visible = True
        self.welcome_screen = WelcomeScreen(
            self.editor_frame, self.settings,
            on_new=self._new_file,
            on_open=self._open_file,
            on_recent=self._open_file,
            recent_files=self.settings.recent_files
        )
        self.welcome_screen.pack(fill="both", expand=True)
    
    def _hide_welcome(self):
        """Hide welcome screen."""
        if self.welcome_visible:
            if hasattr(self, 'welcome_screen'):
                self.welcome_screen.destroy()
            self.welcome_visible = False
    
    def _restore_session(self):
        """Restore previous session."""
        session_mgr = SessionManager()
        tabs = session_mgr.load_session()
        
        for tab_info in tabs:
            filepath = tab_info.get("filepath")
            if filepath and os.path.exists(filepath):
                self._open_file(filepath)
    
    def _restore_hot_exit(self):
        """Restore hot exit snapshot."""
        snapshot = self.hot_exit.load_snapshot()
        if not snapshot:
            return
        
        for tab_info in snapshot.get("tabs", []):
            content = tab_info.get("content", "")
            filepath = tab_info.get("filepath")
            tab_id = self._create_tab(filepath, content, tab_info.get("tab_id"))
            
            if tab_id and tab_id in self.tabs:
                self.tabs[tab_id].modified = tab_info.get("modified", False)
                self.tabs[tab_id].encoding = tab_info.get("encoding", "utf-8")
                self._update_tab_button(tab_id)
        
        # Switch to previous current tab
        current = snapshot.get("current_tab")
        if current and current in self.tabs:
            self._switch_tab(current)
        
        self.hot_exit.clear_snapshot()
    
    def _start_timers(self):
        """Start background timers."""
        # Auto-save timer
        def auto_save():
            if self.settings.auto_save_enabled:
                for tab_id in self.tabs:
                    if self.tabs[tab_id].modified and self.tabs[tab_id].filepath:
                        prev = self.current_tab
                        self._switch_tab(tab_id)
                        self._save_file()
                        self._switch_tab(prev)
            self.after(self.settings.auto_save_interval * 1000, auto_save)
        
        self.after(self.settings.auto_save_interval * 1000, auto_save)
    
    def _on_close(self):
        """Handle window close."""
        # Save hot exit snapshot
        if self.settings.hot_exit_enabled:
            self.hot_exit.save_snapshot(
                self.tabs, self.text_widgets,
                self.current_tab, self.tab_order,
                VERSION
            )
        
        # Save window state
        self.settings.window_maximized = self.state() == 'zoomed'
        if not self.settings.window_maximized:
            self.settings.window_geometry = self.geometry()
        
        self._save_settings()
        self.destroy()


def main():
    """Main entry point."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    app = Mattpad()
    app.mainloop()


if __name__ == "__main__":
    main()
