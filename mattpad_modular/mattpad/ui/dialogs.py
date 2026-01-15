"""Dialog utilities for Mattpad."""
import customtkinter as ctk
import difflib
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME


def create_dialog(parent, title: str, width: int, height: int, 
                  settings: 'EditorSettings') -> ctk.CTkToplevel:
    """Create a styled dialog window."""
    s = settings.ui_scale
    
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry(f"{int(width*s)}x{int(height*s)}")
    dialog.configure(fg_color=THEME.bg_dark)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center on parent
    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - int(width*s)) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - int(height*s)) // 2
    dialog.geometry(f"+{x}+{y}")
    
    return dialog


class DiffEngine:
    """File comparison engine."""
    
    @staticmethod
    def compare(text1: str, text2: str) -> List[Tuple[str, str]]:
        """
        Compare two texts and return list of (diff_type, line) tuples.
        diff_type is one of: 'same', 'added', 'removed'
        """
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        
        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))
        
        result = []
        for line in diff:
            if line.startswith('  '):
                result.append(('same', line[2:]))
            elif line.startswith('- '):
                result.append(('removed', line[2:]))
            elif line.startswith('+ '):
                result.append(('added', line[2:]))
            # Skip '? ' lines (diff markers)
        
        return result
    
    @staticmethod
    def unified_diff(text1: str, text2: str, filename1: str = "file1",
                    filename2: str = "file2") -> str:
        """Generate unified diff output."""
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        
        diff = difflib.unified_diff(lines1, lines2, filename1, filename2)
        return ''.join(diff)
    
    @staticmethod
    def get_similarity_ratio(text1: str, text2: str) -> float:
        """Get similarity ratio between two texts (0.0 to 1.0)."""
        return difflib.SequenceMatcher(None, text1, text2).ratio()


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog."""
    
    def __init__(self, parent, settings: 'EditorSettings', on_save: callable):
        super().__init__(parent)
        self.settings = settings
        self.on_save = on_save
        
        s = settings.ui_scale
        self.title("Settings")
        self.geometry(f"{int(600*s)}x{int(500*s)}")
        self.configure(fg_color=THEME.bg_dark)
        self.transient(parent)
        self.grab_set()
        
        self._create()
    
    def _create(self):
        """Create settings UI."""
        s = self.settings.ui_scale
        
        # Tab view for categories
        tabview = ctk.CTkTabview(self, fg_color=THEME.bg_medium)
        tabview.pack(fill="both", expand=True, padx=int(10*s), pady=int(10*s))
        
        # Editor tab
        editor_tab = tabview.add("Editor")
        self._create_editor_settings(editor_tab)
        
        # Appearance tab
        appearance_tab = tabview.add("Appearance")
        self._create_appearance_settings(appearance_tab)
        
        # Files tab
        files_tab = tabview.add("Files")
        self._create_file_settings(files_tab)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=int(10*s), pady=int(10*s))
        
        ctk.CTkButton(
            btn_frame, text="Cancel",
            fg_color=THEME.bg_medium,
            hover_color=THEME.bg_hover,
            command=self.destroy
        ).pack(side="right", padx=int(5*s))
        
        ctk.CTkButton(
            btn_frame, text="Save",
            fg_color=THEME.accent_primary,
            command=self._save
        ).pack(side="right", padx=int(5*s))
    
    def _create_editor_settings(self, parent):
        """Create editor settings."""
        s = self.settings.ui_scale
        
        # Font family
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=int(5*s))
        ctk.CTkLabel(row, text="Font Family:", width=int(120*s)).pack(side="left")
        self.font_entry = ctk.CTkEntry(row, width=int(200*s))
        self.font_entry.insert(0, self.settings.font_family)
        self.font_entry.pack(side="left")
        
        # Font size
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=int(5*s))
        ctk.CTkLabel(row, text="Font Size:", width=int(120*s)).pack(side="left")
        self.font_size_entry = ctk.CTkEntry(row, width=int(100*s))
        self.font_size_entry.insert(0, str(self.settings.font_size))
        self.font_size_entry.pack(side="left")
        
        # Tab size
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=int(5*s))
        ctk.CTkLabel(row, text="Tab Size:", width=int(120*s)).pack(side="left")
        self.tab_size_entry = ctk.CTkEntry(row, width=int(100*s))
        self.tab_size_entry.insert(0, str(self.settings.tab_size))
        self.tab_size_entry.pack(side="left")
        
        # Checkboxes
        self.word_wrap_var = ctk.BooleanVar(value=self.settings.word_wrap)
        ctk.CTkCheckBox(
            parent, text="Word Wrap",
            variable=self.word_wrap_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
        
        self.auto_indent_var = ctk.BooleanVar(value=self.settings.auto_indent)
        ctk.CTkCheckBox(
            parent, text="Auto Indent",
            variable=self.auto_indent_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
        
        self.auto_close_var = ctk.BooleanVar(value=self.settings.auto_close_brackets)
        ctk.CTkCheckBox(
            parent, text="Auto Close Brackets",
            variable=self.auto_close_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
    
    def _create_appearance_settings(self, parent):
        """Create appearance settings."""
        s = self.settings.ui_scale
        
        # Theme selection
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=int(5*s))
        ctk.CTkLabel(row, text="Theme:", width=int(120*s)).pack(side="left")
        
        from ..utils.themes import THEMES
        self.theme_combo = ctk.CTkComboBox(
            row, values=list(THEMES.keys()),
            width=int(200*s)
        )
        self.theme_combo.set(self.settings.theme_name)
        self.theme_combo.pack(side="left")
        
        # UI Scale
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=int(5*s))
        ctk.CTkLabel(row, text="UI Scale:", width=int(120*s)).pack(side="left")
        self.scale_combo = ctk.CTkComboBox(
            row, values=["1.0", "1.25", "1.5", "1.75", "2.0"],
            width=int(100*s)
        )
        self.scale_combo.set(str(self.settings.ui_scale))
        self.scale_combo.pack(side="left")
        
        # Checkboxes
        self.line_numbers_var = ctk.BooleanVar(value=self.settings.show_line_numbers)
        ctk.CTkCheckBox(
            parent, text="Show Line Numbers",
            variable=self.line_numbers_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
        
        self.minimap_var = ctk.BooleanVar(value=self.settings.show_minimap)
        ctk.CTkCheckBox(
            parent, text="Show Minimap",
            variable=self.minimap_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
        
        self.status_bar_var = ctk.BooleanVar(value=self.settings.show_status_bar)
        ctk.CTkCheckBox(
            parent, text="Show Status Bar",
            variable=self.status_bar_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
    
    def _create_file_settings(self, parent):
        """Create file settings."""
        s = self.settings.ui_scale
        
        # Default encoding
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=int(5*s))
        ctk.CTkLabel(row, text="Encoding:", width=int(120*s)).pack(side="left")
        self.encoding_combo = ctk.CTkComboBox(
            row, values=["utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii"],
            width=int(150*s)
        )
        self.encoding_combo.set(self.settings.encoding)
        self.encoding_combo.pack(side="left")
        
        # Line ending
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=int(5*s))
        ctk.CTkLabel(row, text="Line Ending:", width=int(120*s)).pack(side="left")
        self.line_ending_combo = ctk.CTkComboBox(
            row, values=["CRLF", "LF", "CR"],
            width=int(100*s)
        )
        self.line_ending_combo.set(self.settings.line_ending)
        self.line_ending_combo.pack(side="left")
        
        # Checkboxes
        self.auto_save_var = ctk.BooleanVar(value=self.settings.auto_save_enabled)
        ctk.CTkCheckBox(
            parent, text="Auto Save",
            variable=self.auto_save_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
        
        self.backup_var = ctk.BooleanVar(value=self.settings.create_backup)
        ctk.CTkCheckBox(
            parent, text="Create Backups",
            variable=self.backup_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
        
        self.restore_session_var = ctk.BooleanVar(value=self.settings.restore_session)
        ctk.CTkCheckBox(
            parent, text="Restore Session on Startup",
            variable=self.restore_session_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
        
        self.hot_exit_var = ctk.BooleanVar(value=self.settings.hot_exit_enabled)
        ctk.CTkCheckBox(
            parent, text="Hot Exit (Save unsaved on close)",
            variable=self.hot_exit_var,
            fg_color=THEME.accent_primary
        ).pack(anchor="w", pady=int(5*s))
    
    def _save(self):
        """Save settings."""
        # Editor settings
        self.settings.font_family = self.font_entry.get()
        try:
            self.settings.font_size = int(self.font_size_entry.get())
        except ValueError:
            pass
        try:
            self.settings.tab_size = int(self.tab_size_entry.get())
        except ValueError:
            pass
        self.settings.word_wrap = self.word_wrap_var.get()
        self.settings.auto_indent = self.auto_indent_var.get()
        self.settings.auto_close_brackets = self.auto_close_var.get()
        
        # Appearance settings
        self.settings.theme_name = self.theme_combo.get()
        try:
            self.settings.ui_scale = float(self.scale_combo.get())
        except ValueError:
            pass
        self.settings.show_line_numbers = self.line_numbers_var.get()
        self.settings.show_minimap = self.minimap_var.get()
        self.settings.show_status_bar = self.status_bar_var.get()
        
        # File settings
        self.settings.encoding = self.encoding_combo.get()
        self.settings.line_ending = self.line_ending_combo.get()
        self.settings.auto_save_enabled = self.auto_save_var.get()
        self.settings.create_backup = self.backup_var.get()
        self.settings.restore_session = self.restore_session_var.get()
        self.settings.hot_exit_enabled = self.hot_exit_var.get()
        
        self.on_save()
        self.destroy()
